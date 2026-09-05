"""
PyQt6 Dashboard Tabs package for QuakMeeting on Linux.
Modular tabs matching macOS AppKit architecture:
- agenda_tab: Today's agenda timeline, countdown badges, 1-click meeting joins & maps
- hangar_tab: Mascot mini animations, category customizers, live flight previews
- settings_tab: Notification lead times, addresses, keyword rules, calendars & diagnostics
"""

from ui.linux.dashboard_tabs.agenda_tab import QtAgendaTab
from ui.linux.dashboard_tabs.hangar_tab import QtHangarTab, QtMascotMiniWidget
from ui.linux.dashboard_tabs.settings_tab import QtSettingsTab, QtUpdateBridge

__all__ = [
    "QtAgendaTab",
    "QtHangarTab",
    "QtSettingsTab",
    "QtMascotMiniWidget",
    "QtUpdateBridge",
]
