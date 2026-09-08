"""Standalone XCB entry point for banners launched from a Wayland Qt app."""

import json
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .qt_banner import _active_banners, _restore_banner_datetimes, show_qt_banner


def main() -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    payload = _restore_banner_datetimes(json.loads(sys.stdin.read()))
    show_qt_banner(payload)

    def quit_when_idle() -> None:
        if not _active_banners:
            app.quit()
        else:
            QTimer.singleShot(250, quit_when_idle)

    QTimer.singleShot(250, quit_when_idle)
    app.exec()


if __name__ == "__main__":
    main()
