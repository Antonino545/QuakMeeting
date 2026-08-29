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

# ── Pilot data ────────────────────────────────────────────────────────────────

PILOT_QUOTES = {
    "duck":     "QUAAK! 🚀 JOIN THE CALL!",
    "chef":     "🍕 DINNER TIME, LET'S GO!",
    "captain":  "✈️ CLEARED FOR TAKEOFF!",
    "owl":      "📚 LECTURE IS STARTING!",
    "gym":      "🏋️ GET TO THE GYM!",
    "driver":   "🚗 TIME TO LEAVE, GO GO GO!",
    "zen_duck": "🌸 BREATHE... YOU GOT THIS!",
}

PILOT_COLORS = {
    "duck":     QColor(250, 204, 21),
    "chef":     QColor(244, 63, 94),
    "captain":  QColor(56, 189, 248),
    "owl":      QColor(192, 132, 252),
    "gym":      QColor(248, 113, 113),
    "driver":   QColor(251, 191, 36),
    "zen_duck": QColor(45, 212, 191),
}

PROVIDER_DOTS = {
    "google meet": QColor(52, 211, 153),
    "zoom":        QColor(56, 189, 248),
    "teams":       QColor(99, 102, 241),
    "webex":       QColor(251, 191, 36),
    "meet":        QColor(52, 211, 153),
}


def get_test_preset(pilot_type: str) -> Dict[str, Any]:
    presets = {
        "duck": {
            "title": "Weekly Team Sync (Google Meet)",
            "provider": "Google Meet 🟢",
            "pilot_type": "duck",
            "action_btn_text": "🚀 JOIN GOOGLE MEET",
            "action_url": "https://meet.google.com/test-quak-pit",
            "start_time": datetime.now(),
            "is_travel": False
        },
        "chef": {
            "title": "Dinner with Friends at Pizzeria",
            "provider": "Dinner / Food 🍕🍽️",
            "pilot_type": "chef",
            "action_btn_text": "🗺️ RESTAURANT DIRECTIONS",
            "action_url": "https://maps.apple.com/?q=Pizzeria+Napoli",
            "location": "Pizzeria Da Michele",
            "start_time": datetime.now(),
            "is_travel": True
        },
        "captain": {
            "title": "Flight to London (BA 257)",
            "provider": "Flight / Travel ✈️",
            "pilot_type": "captain",
            "action_btn_text": "🗺️ AIRPORT DIRECTIONS",
            "action_url": "https://maps.apple.com/?q=Heathrow+Airport",
            "location": "Terminal 5 - Gate B12",
            "start_time": datetime.now(),
            "is_travel": True
        },
        "owl": {
            "title": "SmartGrid & Neural Networks Lecture",
            "provider": "Study / University 🎓",
            "pilot_type": "owl",
            "action_btn_text": "📚 CLASSROOM & NOTES",
            "action_url": "https://calendar.apple.com",
            "location": "Room 3B - Campus",
            "start_time": datetime.now(),
            "is_travel": False
        },
        "gym": {
            "title": "CrossFit Training & Palestra Workout",
            "provider": "Gym & Sport 🏋️‍♂️💪",
            "pilot_type": "gym",
            "action_btn_text": "🗺️ GYM DIRECTIONS",
            "action_url": "https://maps.apple.com/?daddr=Gym+Fitness",
            "location": "Downtown Gym Club",
            "start_time": datetime.now(),
            "is_travel": True
        },
        "driver": {
            "title": "Architecture Studio Meeting",
            "provider": "In Person 📍 Travel Time!",
            "pilot_type": "driver",
            "action_btn_text": "🗺️ NAVIGATE WITH MAPS",
            "action_url": "https://maps.apple.com/?daddr=City+Center",
            "location": "Victoria Street, London",
            "start_time": datetime.now(),
            "is_travel": True
        },
        "zen_duck": {
            "title": "Serenis Online Therapy Session",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 JOIN SESSION",
            "action_url": "https://app.serenis.it/join/test",
            "start_time": datetime.now(),
            "is_travel": False
        }
    }
    return presets.get(pilot_type, presets["duck"])

def get_update_preset(version_str: str = "New Version", release_url: str = "") -> Dict[str, Any]:
    """Generates banner payload for QuakMeeting software updates."""
    return {
        "title": f"QuakMeeting {version_str} Ready!",
        "provider": "Software Update ✨",
        "pilot_type": "captain",
        "action_btn_text": "⚡ UPDATE NOW",
        "quote_text": f"🚀 {version_str} IS READY!",
        "action_url": release_url or "https://github.com/Antonino545/QuakMeeting/releases",
        "start_time": datetime.now(),
        "is_travel": False,
        "is_update_banner": True,
        "location": "Click to download & install update",
    }


# ── Layout constants ──────────────────────────────────────────────────────────

CARD_W    = 500
CARD_H    = 148
CARD_R    = 18
CABLE_LEN = 60
PLANE_SPAN = 90       # horizontal span of plane drawing
WIN_W     = CARD_W + CABLE_LEN + PLANE_SPAN + 120
WIN_H     = 200       # height includes space for speech bubble above
CARD_X    = 0
CARD_Y    = 50        # card vertically centred inside WIN_H with room for bubble
PLANE_CX  = CARD_W + CABLE_LEN + PLANE_SPAN // 2   # plane centre inside window
PLANE_CY  = CARD_Y + CARD_H // 2

# Button layout
BTN_H       = 32
BTN_Y       = CARD_Y + CARD_H - BTN_H - 12
BTN_X0      = CARD_X + 16
BTN_JOIN_W  = 170
BTN_SMALL_W = 100
BTN_ARR_W   = 100
BTN_SNOOZE_W= 100
BTN_GAP     = 8
BTN_ARRIVE_X = BTN_X0 + BTN_JOIN_W + 8
BTN_SNOOZE_X = BTN_ARRIVE_X + BTN_ARR_W + 8

CLOSE_R     = 10
CLOSE_CX    = CARD_X + CARD_W - 18
CLOSE_CY    = CARD_Y + 18



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

    # Wayland blocks window positioning — use XWayland instead
    if "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland":
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


