"""
PyQt6 Flying Mascot Banner for Ubuntu Linux.
Matches macOS QuakPit design:
  - Dark glass rounded card (provider pill, status pill, title, subtitle, 3-action buttons)
  - Mascot aircraft towing the card on a cable, entering from screen-right
    - Runs in a dedicated XCB/XWayland helper process when the main app uses Wayland
  - Zero child widgets — everything drawn in paintEvent
"""
from __future__ import annotations

import sys
import os
import json
import math
import subprocess
import logging
import webbrowser
from datetime import datetime
from typing import Dict, Any

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
    from PyQt6.QtGui import (
        QColor, QPainter, QBrush, QPen, QFont, QPainterPath,
        QLinearGradient, QRadialGradient, QFontMetrics
    )
    _HAS_PYQT6 = True
except (ImportError, ModuleNotFoundError):
    _HAS_PYQT6 = False
    QApplication = object
    QWidget = object
    Qt = object
    QTimer = object
    QRect = object
    QRectF = object
    QPointF = object
    QPainter = object
    QBrush = object
    QPen = object
    QFont = object
    QPainterPath = object
    QLinearGradient = object
    QRadialGradient = object
    QFontMetrics = object
    def QColor(*args):
        return args

from .renderers import get_pilot_renderer
from ui.linux.theme import Theme

# ── Pilot data ────────────────────────────────────────────────────────────────

PILOT_QUOTES = {
    "duck":     "QUAAK! 🚀 JOIN THE CALL!",
    "chef":     "🍕 DINNER TIME, LET'S GO!",
    "captain":  "✈️ CLEARED FOR TAKEOFF!",
    "owl":      "📚 LECTURE IS STARTING!",
    "gym":      "🏋️ GET TO THE GYM!",
    "driver":   "🚗 TIME TO LEAVE, GO GO GO!",
    "zen_duck": "🌸 BREATHE... YOU GOT THIS!",
    "platypus": "🕵️‍♂️ SECRET MISSION BRIEFING!",
    "squirrel": "🐿️ NUT-PING! TIME FOR ACTION!",
}

PILOT_COLORS = {
    "duck":     Theme.YELLOW,
    "chef":     Theme.PEACH,
    "captain":  Theme.SAPPHIRE,
    "owl":      Theme.MAUVE,
    "gym":      Theme.RED,
    "driver":   Theme.PEACH,
    "zen_duck": Theme.TEAL,
    "platypus": Theme.TEAL,
    "squirrel": Theme.MAROON,
}

PROVIDER_DOTS = {
    "google meet": Theme.GREEN,
    "zoom":        Theme.BLUE,
    "teams":       Theme.MAUVE,
    "webex":       Theme.PEACH,
    "meet":        Theme.GREEN,
}


from ui.common.banner_presets import get_test_preset, get_update_preset


# ── Layout constants ──────────────────────────────────────────────────────────

CARD_W    = 535
CARD_H    = 132
CARD_R    = 18
WIN_W     = 1000
WIN_H     = 195
CARD_X    = 10
CARD_Y    = 55
PLANE_CX  = CARD_X + 615
PLANE_CY  = CARD_Y + 54



# ── Public entry point ────────────────────────────────────────────────────────



from .qt_duck_banner import QtDuckBannerWindow
from .qt_update_banner import QtUpdateBannerWindow
_active_banners = []
_app_instance = None
_xcb_helper_process = None


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "to_serializable_dict"):
        return value.to_serializable_dict()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError(f"Unsupported banner value: {type(value).__name__}")


def _restore_banner_datetimes(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Restore datetime fields after crossing the XCB helper process boundary."""
    restored = dict(event_data)
    for key in ("start_time", "end_time", "departure_time"):
        value = restored.get(key)
        if isinstance(value, str):
            try:
                restored[key] = datetime.fromisoformat(value)
            except ValueError:
                logging.getLogger("QuakMeeting.QtBanner").warning(
                    "Ignoring invalid banner timestamp in %s: %r", key, value
                )
    return restored


def _run_xcb_helper(event_data: Dict[str, Any]) -> None:
    """Render a banner in a separate XCB process when Qt is already Wayland."""
    global _xcb_helper_process
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "xcb"
    env["QUAKMEETING_BANNER_HELPER"] = "1"
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cur_pypath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{project_root}:{cur_pypath}" if cur_pypath else project_root

    command = [sys.executable, "-m", "ui.linux.banner.qt_banner_helper"]
    try:
        if _xcb_helper_process is not None and _xcb_helper_process.poll() is None:
            _xcb_helper_process.terminate()
            try:
                _xcb_helper_process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                _xcb_helper_process.kill()
                _xcb_helper_process.wait()
        helper = subprocess.Popen(
            command,
            cwd=project_root,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        _xcb_helper_process = helper
        payload = json.dumps(event_data, default=_json_default).encode("utf-8")
        helper.stdin.write(payload)
        helper.stdin.close()
    except Exception:
        logging.getLogger("QuakMeeting.QtBanner").exception(
            "Unable to start the XCB banner helper process."
        )

def show_qt_banner(event_data: Dict[str, Any]) -> None:
    """Launch a banner using XCB, isolated from the main Qt platform."""
    global _app_instance
    # Close any existing active banner to prevent overlapping duplicates
    for old_b in list(_active_banners):
        try:
            old_b._dismiss()
        except Exception:
            pass

    app = QApplication.instance()
    if (
        app is not None
        and sys.platform.startswith("linux")
        and str(QApplication.platformName()).lower().startswith("wayland")
        and os.environ.get("QUAKMEETING_BANNER_HELPER") != "1"
    ):
        _run_xcb_helper(event_data)
        return

    if app is None and sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    if app is None:
        _app_instance = QApplication(sys.argv)
        app = _app_instance
        standalone = True
    else:
        standalone = False

    if event_data.get("is_update_banner"):
        banner = QtUpdateBannerWindow(event_data)
    else:
        banner = QtDuckBannerWindow(event_data)

    _active_banners.append(banner)
    banner.show()

    if (standalone or "--test" in sys.argv) and os.environ.get("QUAKMEETING_BANNER_HELPER") != "1":
        app.exec()


