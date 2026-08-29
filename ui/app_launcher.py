"""
Platform-Aware Application Launcher for QuakMeeting.
Selects and launches the native UI runtime for macOS (AppKit) or Ubuntu Linux/Windows (PyQt6).
"""
import sys
import logging

logger = logging.getLogger("QuakMeeting.AppLauncher")

def launch_application():
    """Starts QuakMeeting menu bar status item and event listeners."""
    force_qt = "--qt" in sys.argv
    if sys.platform == "darwin" and not force_qt:
        from ui.macos.menu_bar_app import run_menu_bar_app
        run_menu_bar_app()
    elif sys.platform.startswith("linux") or sys.platform == "win32" or force_qt:
        from ui.linux.qt_tray_app import run_qt_tray_app
        run_qt_tray_app()
    else:
        logger.error(f"Unsupported operating system: {sys.platform}")
        sys.exit(1)
