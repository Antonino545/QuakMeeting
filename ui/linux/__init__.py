"""
Linux / Ubuntu Native UI Package (PyQt6, Wayland / X11).
"""
try:
    from .qt_tray_app import QuakMeetingTrayApp, run_qt_tray_app
    from .qt_dashboard import show_qt_dashboard, close_qt_dashboard, QtFlightDeckWindow
    from .banner import show_qt_banner, get_test_preset, get_update_preset
except (ImportError, ModuleNotFoundError):
    QuakMeetingTrayApp = None
    run_qt_tray_app = None
    show_qt_dashboard = None
    close_qt_dashboard = None
    QtFlightDeckWindow = None
    show_qt_banner = None
    get_test_preset = None
    get_update_preset = None

__all__ = [
    "QuakMeetingTrayApp",
    "run_qt_tray_app",
    "show_qt_dashboard",
    "close_qt_dashboard",
    "QtFlightDeckWindow",
    "show_qt_banner",
    "get_test_preset",
    "get_update_preset",
]
