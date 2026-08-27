"""
Autostart / Launch-at-Login Management Subsystem for QuakMeeting.
Supports native macOS 13+ SMAppService and universal Aqua LaunchAgents plist.
"""
import os
import subprocess
import logging
from typing import Optional

logger = logging.getLogger("QuakMeeting.Autostart")

PLIST_LABEL = "com.quakmeeting.app"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_LABEL}.plist")


def _get_target_app_path() -> str:
    """Resolves the installed or running QuakMeeting.app bundle path."""
    standard_app = "/Applications/QuakMeeting.app"
    if os.path.exists(standard_app):
        return standard_app

    # Check if running within a bundle
    try:
        import AppKit
        bundle = AppKit.NSBundle.mainBundle()
        if bundle and bundle.bundlePath() and bundle.bundlePath().endswith(".app"):
            return bundle.bundlePath()
    except Exception:
        pass

    # Check project directory app bundle
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_app = os.path.join(project_dir, "QuakMeeting.app")
    if os.path.exists(local_app):
        return local_app

    return standard_app


def generate_launchagent_plist(app_path: Optional[str] = None) -> str:
    """Generates the launchd Aqua session LaunchAgent plist XML."""
    if not app_path:
        app_path = _get_target_app_path()

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>{app_path}</string>
        <string>--args</string>
        <string>--silent</string>
        <string>--autostart</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>LimitLoadToSessionType</key>
    <string>Aqua</string>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
"""


def _check_smappservice_status() -> Optional[bool]:
    """Checks autostart status using macOS 13+ ServiceManagement SMAppService."""
    try:
        import ServiceManagement
        import AppKit
        bundle = AppKit.NSBundle.mainBundle()
        if not bundle or not bundle.bundleIdentifier() or not bundle.bundlePath().endswith(".app"):
            return None

        service = ServiceManagement.SMAppService.mainAppService()
        if service is None:
            return None

        # SMAppServiceStatusEnabled = 1, SMAppServiceStatusRequiresApproval = 2
        status = service.status()
        if status in (1, 2):
            return True
        elif status == 0:  # SMAppServiceStatusNotRegistered
            return False
    except Exception as e:
        logger.debug(f"SMAppService check not available or error: {e}")
    return None


def is_autostart_enabled() -> bool:
    """Determines whether QuakMeeting is configured to launch at macOS login."""
    sm_status = _check_smappservice_status()
    if sm_status is not None:
        return sm_status

    return os.path.exists(PLIST_PATH)


def enable_autostart() -> bool:
    """Enables launch at login using SMAppService (macOS 13+) or LaunchAgent plist."""
    logger.info("Enabling Launch-at-Login for QuakMeeting...")

    # 1. Try SMAppService if inside an app bundle
    try:
        import ServiceManagement
        import AppKit
        bundle = AppKit.NSBundle.mainBundle()
        if bundle and bundle.bundleIdentifier() and bundle.bundlePath().endswith(".app"):
            service = ServiceManagement.SMAppService.mainAppService()
            if service is not None:
                success, err = service.registerAndReturnError_(None)
                if success:
                    logger.info("✅ Successfully registered with SMAppService (macOS Login Items).")
                    return True
                else:
                    logger.warning(f"SMAppService registration failed ({err}), falling back to LaunchAgent plist.")
    except Exception as e:
        logger.debug(f"SMAppService registration skipped/failed: {e}")

    # 2. Universal LaunchAgent fallback
    try:
        app_path = _get_target_app_path()
        plist_content = generate_launchagent_plist(app_path)
        os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)

        with open(PLIST_PATH, "w", encoding="utf-8") as f:
            f.write(plist_content.strip() + "\n")

        uid = os.getuid()
        # Unload/bootout previous state if present
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{PLIST_LABEL}"], capture_output=True)
        subprocess.run(["launchctl", "unload", "-w", PLIST_PATH], capture_output=True)

        # Bootstrap / Load
        res = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", PLIST_PATH], capture_output=True)
        if res.returncode != 0:
            subprocess.run(["launchctl", "load", "-w", PLIST_PATH], capture_output=True)

        logger.info(f"✅ Successfully wrote and loaded LaunchAgent: {PLIST_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable LaunchAgent autostart: {e}", exc_info=True)
        return False


def disable_autostart() -> bool:
    """Disables launch at login by unregistering SMAppService and removing LaunchAgent plist."""
    logger.info("Disabling Launch-at-Login for QuakMeeting...")
    success = True

    # 1. Try SMAppService unregister
    try:
        import ServiceManagement
        import AppKit
        bundle = AppKit.NSBundle.mainBundle()
        if bundle and bundle.bundleIdentifier() and bundle.bundlePath().endswith(".app"):
            service = ServiceManagement.SMAppService.mainAppService()
            if service is not None:
                service.unregisterAndReturnError_(None)
                logger.info("Unregistered from SMAppService.")
    except Exception as e:
        logger.debug(f"SMAppService unregister: {e}")

    # 2. Remove LaunchAgent plist
    try:
        if os.path.exists(PLIST_PATH):
            uid = os.getuid()
            subprocess.run(["launchctl", "bootout", f"gui/{uid}/{PLIST_LABEL}"], capture_output=True)
            subprocess.run(["launchctl", "unload", "-w", PLIST_PATH], capture_output=True)
            os.remove(PLIST_PATH)
            logger.info(f"Removed LaunchAgent plist: {PLIST_PATH}")
    except Exception as e:
        logger.error(f"Failed to remove LaunchAgent plist: {e}", exc_info=True)
        success = False

    return success


def toggle_autostart() -> bool:
    """Toggles current autostart state."""
    if is_autostart_enabled():
        disable_autostart()
        return False
    else:
        enable_autostart()
        return True
