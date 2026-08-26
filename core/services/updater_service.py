"""
Auto-Updater Service for QuakMeeting.
Checks GitHub Releases for new versions, downloads platform assets,
and performs in-place upgrades for macOS and Ubuntu Linux.
"""
import os
import sys
import time
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
        self.latest_release_info: Optional[Dict[str, Any]] = None
        self.is_checking = False
        self.is_downloading = False
        self._initialized = True

    @property
    def current_version(self) -> str:
        """Dynamically detects the installed package version from local files, dpkg, NSBundle, or models.py."""
        # 1. Check native macOS NSBundle if running as AppKit app
        if sys.platform == "darwin":
            try:
                import AppKit
                bundle = AppKit.NSBundle.mainBundle()
                if bundle:
                    b_ver = bundle.objectForInfoDictionaryKey_("CFBundleShortVersionString")
                    if b_ver and str(b_ver).strip():
                        return str(b_ver).strip()
            except Exception:
                pass

        # 2. Check local VERSION file in application bundle or root
        try:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            for _ in range(4):
                ver_file = os.path.join(curr_dir, "VERSION")
                if os.path.exists(ver_file):
                    with open(ver_file, "r") as f:
                        v = f.read().strip()
                        if v:
                            return v
                curr_dir = os.path.dirname(curr_dir)
        except Exception:
            pass

        # 3. Check Info.plist on macOS
        if sys.platform == "darwin":
            try:
                res_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                plist_candidate = os.path.join(os.path.dirname(res_dir), "Info.plist")
                if not os.path.exists(plist_candidate):
                    plist_candidate = "/Applications/QuakMeeting.app/Contents/Info.plist"
                if os.path.exists(plist_candidate):
                    import plistlib
                    with open(plist_candidate, "rb") as f:
                        pl = plistlib.load(f)
                        if "CFBundleShortVersionString" in pl and pl["CFBundleShortVersionString"]:
                            return str(pl["CFBundleShortVersionString"]).strip()
            except Exception:
                pass

        # 4. Check dpkg on Linux
        if sys.platform.startswith("linux"):
            try:
                res = subprocess.run(["dpkg-query", "-W", "-f=${Version}", "quakmeeting"], capture_output=True, text=True, timeout=1.5)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass

        return __version__

    @current_version.setter
    def current_version(self, val: str):
        pass

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
                        try:
                            from ui.banner.qt_banner import get_update_preset
                            event_bus.publish("TRIGGER_BANNER", event_dict=get_update_preset(tag_name, release_info.get("html_url", "")))
                        except Exception as b_err:
                            logger.debug(f"Banner trigger on update: {b_err}")
                    else:
                        logger.info(f"✨ QuakMeeting is up to date (Current: {self.current_version})")
                        event_bus.publish("UPDATE_CHECK_COMPLETE", has_update=False, current_version=self.current_version)
                    return release_info
            except Exception as e:
                logger.warning(f"Update check failed: {e}")
                event_bus.publish("UPDATE_CHECK_COMPLETE", has_update=False, error=str(e), current_version=self.current_version)
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
            elif is_linux and name.endswith(".appimage"):
                return asset

        return assets[0] if assets else None

    def download_and_install_update(self, background: bool = True, on_progress=None) -> bool:
        """Downloads the matching asset and initiates installer / replacement."""
        if self.is_downloading:
            return False

        def _worker():
            if not self.latest_release_info or not self.latest_release_info.get("assets"):
                info = self.check_for_updates(background=False)
                if not info or not info.get("has_update"):
                    return False

            asset = self.get_platform_asset(self.latest_release_info["assets"])
            if not asset or not asset.get("browser_download_url"):
                logger.error("No compatible release asset found for current OS.")
                event_bus.publish("UPDATE_FAILED", error="No compatible release asset found.")
                return False

            download_url = asset["browser_download_url"]
            file_name = asset["name"]
            temp_dir = tempfile.mkdtemp(prefix="quakmeeting_update_")
            target_path = os.path.join(temp_dir, file_name)

            self.is_downloading = True
            event_bus.publish("UPDATE_DOWNLOADING", file_name=file_name, url=download_url)
            try:
                logger.info(f"Downloading update {file_name} from {download_url}...")

                def _reporthook(block_num, block_size, total_size):
                    if total_size > 0:
                        downloaded = block_num * block_size
                        percent = min(100, int((downloaded / total_size) * 100))
                        if on_progress:
                            on_progress(percent, downloaded, total_size)
                        event_bus.publish("UPDATE_DOWNLOAD_PROGRESS", percent=percent, downloaded=downloaded, total=total_size)

                urllib.request.urlretrieve(download_url, target_path, reporthook=_reporthook)
                event_bus.publish("UPDATE_DOWNLOADED", target_path=target_path)

                if sys.platform == "darwin":
                    return self._install_macos_update(target_path, temp_dir)
                elif sys.platform.startswith("linux"):
                    return self._install_linux_update(target_path)
                return False
            except Exception as e:
                logger.error(f"Failed to install update: {e}")
                event_bus.publish("UPDATE_FAILED", error=str(e))
                return False
            finally:
                self.is_downloading = False

        if background:
            threading.Thread(target=_worker, daemon=True).start()
            return True
        else:
            return _worker()

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

            # Clear quarantine and apply ad-hoc codesign with bundle ID to preserve TCC permissions
            if os.path.exists(app_dest):
                subprocess.run(["xattr", "-cr", app_dest], check=False)
                subprocess.run(["codesign", "--force", "--deep", "-s", "-", "-i", "com.quakmeeting.app", app_dest], check=False)

            event_bus.publish("UPDATE_INSTALLED")
            time.sleep(1.0)
            # Relaunch newly installed version cleanly by killing previous instances
            relaunch_cmd = (
                "sleep 1.2; "
                "pkill -f 'QuakMeeting' 2>/dev/null || true; "
                "sleep 0.5; "
                "open /Applications/QuakMeeting.app &"
            )
            subprocess.Popen(["bash", "-c", relaunch_cmd], start_new_session=True)
            os._exit(0)
            return True
        except Exception as e:
            logger.error(f"macOS update installation failed: {e}")
            event_bus.publish("UPDATE_FAILED", error=str(e))
            return False

    def _install_linux_update(self, package_path: str) -> bool:
        """Installs .AppImage update in-place on Ubuntu Linux without requiring root."""
        try:
            if package_path.lower().endswith(".appimage"):
                os.chmod(package_path, 0o755)
                
                # Check if we are running as an AppImage currently
                current_appimage = os.environ.get("APPIMAGE")
                target_dest = current_appimage
                
                if not target_dest:
                    # If not running as AppImage (e.g. from source), place it in ~/.local/bin
                    bin_dir = os.path.expanduser("~/.local/bin")
                    os.makedirs(bin_dir, exist_ok=True)
                    target_dest = os.path.join(bin_dir, "QuakMeeting.AppImage")
                    logger.info(f"Not running as AppImage. Installing new version to {target_dest}")
                else:
                    logger.info(f"Replacing running AppImage at {target_dest}")
                    
                # To avoid 'Text file busy', remove or rename the existing binary first
                if os.path.exists(target_dest):
                    try:
                        os.remove(target_dest)
                    except OSError:
                        os.rename(target_dest, target_dest + ".old")
                        
                shutil.move(package_path, target_dest)
                
                event_bus.publish("UPDATE_INSTALLED")
                relaunch_cmd = (
                    "sleep 1.2; "
                    "pkill -f 'quakmeeting' 2>/dev/null || true; "
                    "pkill -f 'ui.qt_dashboard' 2>/dev/null || true; "
                    "sleep 0.6; "
                    f"'{target_dest}' > /dev/null 2>&1 &"
                )
                subprocess.Popen(["bash", "-c", relaunch_cmd], start_new_session=True)
                os._exit(0)
                return True
            else:
                logger.error(f"Unsupported Linux package format: {package_path}")
                event_bus.publish("UPDATE_FAILED", error="Only .AppImage updates are supported on Linux.")
                return False
        except Exception as e:
            logger.error(f"Linux update installation failed: {e}")
            event_bus.publish("UPDATE_FAILED", error=str(e))
            return False

updater_service = UpdaterService()
