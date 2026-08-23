import sys
from .app_launcher import launch_application

if sys.platform == "darwin":
    try:
        from .banner_window import show_banner_async, _run_banner, QuakPitFlyingBanner
        from .dashboard_window import show_dashboard, DashboardWindowController
        from .menu_bar_app import QuakMeetingMenuBar, QuakMeetingAppDelegate
    except ImportError:
        pass
elif sys.platform.startswith("linux"):
    try:
        from .banner.wayland_banner import show_wayland_banner
        from .linux_dashboard import show_linux_dashboard
        from .tray.linux_appindicator import run_linux_app
    except ImportError:
        pass

__all__ = [
    "launch_application",
    "show_banner_async",
    "_run_banner",
    "QuakPitFlyingBanner",
    "show_dashboard",
    "DashboardWindowController",
    "QuakMeetingMenuBar",
    "QuakMeetingAppDelegate",
]

