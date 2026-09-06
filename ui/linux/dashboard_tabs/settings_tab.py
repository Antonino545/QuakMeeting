"""
PyQt6 Preferences & Settings Tab for QuakMeeting Flight Deck on Linux.
Coordinator for modular settings sub-cards:
- TimingCardWidget: staged reminder lead times & 1-click presets
- ETACardWidget: multi-modal route ETA and origin addresses
- CalendarsCardWidget: monitored calendar source filters
- SystemCardWidget: language, autostart, mute rules, animated update HUD
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt

from ui.linux.dashboard_tabs.settings.timing_card import TimingCardWidget
from ui.linux.dashboard_tabs.settings.eta_card import ETACardWidget
from ui.linux.dashboard_tabs.settings.calendars_card import CalendarsCardWidget
from ui.linux.dashboard_tabs.settings.system_card import SystemCardWidget, QtUpdateBridge

logger = logging.getLogger("QuakMeeting.QtSettingsTab")


class QtSettingsTab(QWidget):
    """Preferences & Timing Settings tab component."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        pref_scroll = QScrollArea(self)
        pref_scroll.setWidgetResizable(True)
        pref_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pref_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pref_scroll.setStyleSheet("QScrollArea { background: transparent; }")

        pref_widget = QWidget()
        pref_layout = QVBoxLayout(pref_widget)
        pref_layout.setContentsMargins(0, 0, 0, 0)
        pref_layout.setSpacing(14)

        # Sub-cards modular coordinator
        self.timing_card = TimingCardWidget(pref_widget)
        self.eta_card = ETACardWidget(pref_widget)
        self.calendars_card = CalendarsCardWidget(pref_widget)
        self.system_card = SystemCardWidget(pref_widget)
        self.update_bridge = self.system_card.update_bridge

        pref_layout.addWidget(self.timing_card)
        pref_layout.addWidget(self.eta_card)
        pref_layout.addWidget(self.calendars_card)
        pref_layout.addWidget(self.system_card)
        pref_layout.addStretch()

        pref_scroll.setWidget(pref_widget)
        layout.addWidget(pref_scroll)


__all__ = ["QtSettingsTab", "QtUpdateBridge"]
