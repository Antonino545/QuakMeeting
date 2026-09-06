"""
Modular settings cards package for Linux Qt Flight Deck.
"""

from ui.linux.dashboard_tabs.settings.timing_card import TimingCardWidget
from ui.linux.dashboard_tabs.settings.eta_card import ETACardWidget
from ui.linux.dashboard_tabs.settings.calendars_card import CalendarsCardWidget
from ui.linux.dashboard_tabs.settings.system_card import SystemCardWidget, QtUpdateBridge

__all__ = [
    "TimingCardWidget",
    "ETACardWidget",
    "CalendarsCardWidget",
    "SystemCardWidget",
    "QtUpdateBridge",
]
