"""
Auto-Updater Service for QuakMeeting.
Checks GitHub Releases for new versions, downloads platform assets,
and performs in-place upgrades for macOS and Ubuntu Linux.
"""
import os
import sys
import json
import shutil
import urllib.request
import tempfile
import subprocess
import threading
import logging
from typing import Optional, Dict, Any, Tuple
from core.domain.models import __version__
from core.services.event_bus import event_bus

logger = logging.getLogger("QuakMeeting.UpdaterService")

DEFAULT_REPO = "Antonino545/QuakMeeting"

class UpdaterService:
    """Manages automatic version checking and seamless updates from GitHub Releases."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UpdaterService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, repo: str = DEFAULT_REPO):
        if self._initialized:
            return
        self.repo = repo
        self.current_version = __version__
        self.latest_release_info: Optional[Dict[str, Any]] = None
        self.is_checking = False
        self.is_downloading = False
        self._initialized = True

    def parse_semver(self, v_str: str) -> Tuple[int, int, int]:
        """Parses 'v1.2.3' or '1.2.3' into (1, 2, 3) tuple."""
        cleaned = v_str.strip().lstrip("vV")
        parts = []
        for part in cleaned.split("."):
            try:
                parts.append(int(part.split("-")[0]))
            except ValueError:
                parts.append(0)
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])

    def is_newer_version(self, latest_v: str, current_v: str) -> bool:
        """Returns True if latest_v is strictly greater than current_v."""
        return self.parse_semver(latest_v) > self.parse_semver(current_v)

    def check_for_updates(self, background: bool = True) -> Optional[Dict[str, Any]]:
        """Queries GitHub Releases API for the latest release."""
        if self.is_checking:
            return self.latest_release_info

        def _worker():
            self.is_checking = True
            try:
                url = f"https://api.github.com/repos/{self.repo}/releases/latest"
                req = urllib.request.Request(url, headers={
                    "User-Agent": f"QuakMeeting-Updater/{self.current_version}",
                    "Accept": "application/vnd.github.v3+json"
                })
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    tag_name = data.get("tag_name", "")
                    has_update = self.is_newer_version(tag_name, self.current_version)
                    
                    release_info = {
                        "has_update": has_update,
                        "version": tag_name.lstrip("vV"),
                        "tag_name": tag_name,
                        "name": data.get("name", tag_name),
                        "body": data.get("body", ""),
                        "html_url": data.get("html_url", ""),
                        "assets": data.get("assets", []),
                        "published_at": data.get("published_at", "")
                    }
                    self.latest_release_info = release_info
                    if has_update:
                        logger.info(f"🚀 New QuakMeeting update found: {tag_name} (Current: {self.current_version})")
                        event_bus.publish("UPDATE_AVAILABLE", **release_info)
                    return release_info
            except Exception as e:
                logger.warning(f"Update check failed: {e}")
                return None
            finally:
                self.is_checking = False

        if background:
            threading.Thread(target=_worker, daemon=True).start()
            return self.latest_release_info
        else:
            return _worker()

    def get_platform_asset(self, assets: list) -> Optional[Dict[str, Any]]:
        """Selects the best asset for the current OS (macOS DMG/ZIP vs Ubuntu DEB)."""
        is_mac = sys.platform == "darwin"
        is_linux = sys.platform.startswith("linux")

        for asset in assets:
            name = asset.get("name", "").lower()
            if is_mac and (name.endswith(".dmg") or (name.endswith(".zip") and "macos" in name)):
                return asset
            elif is_linux and name.endswith(".deb"):
                return asset
            elif is_linux and name.endswith(".appimage"):
                return asset

        return assets[0] if assets else None

    def download_and_install_update(self, on_progress=None) -> bool:
        """Downloads the matching asset and initiates installer / replacement."""
        if not self.latest_release_info or not self.latest_release_info.get("assets"):
            info = self.check_for_updates(background=False)
            if not info or not info.get("has_update"):
                return False

        asset = self.get_platform_asset(self.latest_release_info["assets"])
        if not asset or not asset.get("browser_download_url"):
            logger.error("No compatible release asset found for current OS.")
            return False

        download_url = asset["browser_download_url"]
        file_name = asset["name"]
        temp_dir = tempfile.mkdtemp(prefix="quakmeeting_update_")
        target_path = os.path.join(temp_dir, file_name)

        self.is_downloading = True
        try:
            logger.info(f"Downloading update {file_name} from {download_url}...")
            urllib.request.urlretrieve(download_url, target_path)

            if sys.platform == "darwin":
                return self._install_macos_update(target_path, temp_dir)
            elif sys.platform.startswith("linux"):
                return self._install_linux_update(target_path)
            return False
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            return False
        finally:
            self.is_downloading = False

    def _install_macos_update(self, package_path: str, temp_dir: str) -> bool:
        """Mounts DMG or unzips update and replaces /Applications/QuakMeeting.app."""
        try:
            app_dest = "/Applications/QuakMeeting.app"
            if package_path.endswith(".dmg"):
                mount_point = os.path.join(temp_dir, "mount")
                os.makedirs(mount_point, exist_ok=True)
                subprocess.run(["hdiutil", "attach", package_path, "-mountpoint", mount_point, "-nobrowse", "-quiet"], check=True)
                
                source_app = os.path.join(mount_point, "QuakMeeting.app")
                if os.path.exists(source_app):
                    if os.path.exists(app_dest):
                        shutil.rmtree(app_dest)
                    shutil.copytree(source_app, app_dest)
                    logger.info("Successfully updated QuakMeeting.app in /Applications!")

                subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], check=False)
            elif package_path.endswith(".zip"):
                subprocess.run(["unzip", "-q", package_path, "-d", temp_dir], check=True)
                source_app = os.path.join(temp_dir, "QuakMeeting.app")
                if os.path.exists(source_app):
                    if os.path.exists(app_dest):
                        shutil.rmtree(app_dest)
                    shutil.copytree(source_app, app_dest)

            # Relaunch newly installed version
            subprocess.Popen(["open", app_dest])
            sys.exit(0)
            return True
        except Exception as e:
            logger.error(f"macOS update installation failed: {e}")
            return False

    def _install_linux_update(self, package_path: str) -> bool:
        """Installs .deb package on Ubuntu Linux via pkexec or apt."""
        try:
            if package_path.endswith(".deb"):
                cmd = ["pkexec", "dpkg", "-i", package_path]
                subprocess.Popen(cmd)
                return True
            elif package_path.endswith(".AppImage"):
                os.chmod(package_path, 0o755)
                subprocess.Popen([package_path])
                sys.exit(0)
                return True
        except Exception as e:
            logger.error(f"Linux update installation failed: {e}")
            return False

updater_service = UpdaterService()
