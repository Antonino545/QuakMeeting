"""
PyQt6 Flying Mascot Banner for Ubuntu Linux.
Matches macOS QuakPit design:
  - Dark glass rounded card (provider pill, status pill, title, subtitle, 3-action buttons)
  - Mascot aircraft towing the card on a cable, entering from screen-right
  - Small window moved each frame via self.move() + QT_QPA_PLATFORM=xcb (XWayland)
  - Zero child widgets — everything drawn in paintEvent
"""
from __future__ import annotations

import sys
import os
import math
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

def show_qt_banner(event_data: Dict[str, Any]) -> None:
    """Launch flying banner. Forces XCB so self.move() works on Wayland."""
    # Close any existing active banner to prevent overlapping duplicates
    for old_b in list(_active_banners):
        try:
            old_b._dismiss()
        except Exception:
            pass

    # Wayland blocks window positioning on Linux — use XWayland instead
    if sys.platform.startswith("linux") and ("WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QApplication.instance()
    standalone = app is None
    if standalone:
        app = QApplication(sys.argv)

    
    if event_data.get("is_update_banner"):
        banner = QtUpdateBannerWindow(event_data)
    else:
        banner = QtDuckBannerWindow(event_data)

    _active_banners.append(banner)
    banner.show()

    if standalone or "--test" in sys.argv:
        app.exec()


