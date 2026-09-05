"""
PyQt6 Modern Dark Flight Deck Dashboard Window for Ubuntu Linux.
Matches macOS Flight Deck design:
- Today's Agenda timeline with status badges & 1-click joins
- Pilot Hangar interactive playground for all 7 mascot aircrafts
- Preferences & Timing settings with live config saving

Modularized into ui/linux/dashboard_tabs/ for maintainability and platform parity.
"""
import os
import sys

if sys.platform.startswith("linux"):
    if "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import threading
import logging

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QFrame, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from ui.linux.animated_widgets import (
    BouncingMascotLabel, AnimatedSpinButton
)
from ui.linux.dashboard_tabs import (
    QtAgendaTab, QtHangarTab, QtSettingsTab, QtMascotMiniWidget, QtUpdateBridge
)
from core.services.calendar_service import calendar_service

logger = logging.getLogger("QuakMeeting.QtDashboard")

QT_DASHBOARD_QSS = """
/* Catppuccin Mocha Palette */
QMainWindow, QWidget#CentralWidget {
    background-color: #11111b; /* Crust */
    border: none;
}

QFrame#HeaderBox {
    background-color: #181825; /* Mantle */
    border: 1px solid #313244; /* Surface0 */
    border-radius: 12px;
}

QLabel#HeaderTitle {
    font-size: 20px;
    font-weight: 800;
    color: #cdd6f4; /* Text */
}

QLabel#HeaderSub {
    font-size: 12px;
    color: #a6adc8; /* Subtext0 */
}

QLabel#ActiveBadge {
    background-color: rgba(166, 227, 161, 0.15); /* Green */
    color: #a6e3a1; /* Green */
    border: 1px solid rgba(166, 227, 161, 0.3);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

QFrame#NavbarContainer {
    background-color: #181825; /* Mantle capsule container */
    border: 1px solid #313244; /* Surface0 */
    border-radius: 10px;
    min-height: 38px;
    max-height: 38px;
}

QPushButton#NavSegmentBtn {
    background-color: transparent;
    color: #a6adc8; /* Subtext0 */
    font-weight: 600;
    font-size: 12.5px;
    border-radius: 7px;
    border: 1px solid transparent;
    padding: 0px 8px;
    min-height: 30px;
    max-height: 30px;
}

QPushButton#NavSegmentBtn:hover {
    color: #cdd6f4; /* Text */
    background-color: rgba(69, 71, 90, 0.45); /* Surface1 subtle glow */
}

QPushButton#NavSegmentBtn[active="true"] {
    color: #cdd6f4; /* Text */
    background-color: #313244; /* Surface0 elevated active pill */
    font-weight: 700;
    border: 1px solid #45475a; /* Surface1 hairline */
}

QFrame#Card, QFrame#PrefCard, QFrame#HangarCard {
    background-color: #1e1e2e; /* Base */
    border: 1px solid #313244; /* Surface0 */
    border-radius: 12px;
}

QFrame#Card:hover, QFrame#HangarCard:hover {
    background-color: #181825; /* Mantle */
    border: 1px solid #cba6f7; /* Mauve highlight on hover */
}

QLabel#CardTitle {
    font-size: 15px;
    font-weight: 700;
    color: #cdd6f4; /* Text */
}

QLabel#CardSub {
    font-size: 12px;
    color: #a6adc8; /* Subtext0 */
}

QPushButton#PrimaryBtn {
    background-color: #89b4fa; /* Blue */
    color: #11111b; /* Crust */
    font-size: 12px;
    font-weight: bold;
    border: 1px solid #89b4fa;
    border-radius: 8px;
    padding: 7px 16px;
}
QPushButton#PrimaryBtn:hover {
    background-color: #b4befe; /* Lavender */
    border: 1px solid #b4befe;
}

QPushButton#OutlineBtn {
    background-color: #313244; /* Surface0 */
    color: #cdd6f4; /* Text */
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton#OutlineBtn:hover {
    background-color: #45475a; /* Surface1 */
    border-color: #89b4fa;
    color: #89b4fa;
}

QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: #181825;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    height: 0px;
    max-height: 0px;
}
QSizeGrip {
    width: 0px;
    height: 0px;
    background: transparent;
}
"""


class QtFlightDeckWindow(QMainWindow):
    """PyQt6 Flight Deck Dashboard Window."""

    def __init__(self, tab_index: int = 0):
        super().__init__()
        self.setWindowTitle("QuakMeeting — Flight Deck Control Center")
        self.resize(840, 620)

        # Center on screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move((geo.width() - 840) // 2, (geo.height() - 620) // 2)

        self.setStyleSheet(QT_DASHBOARD_QSS)
        self.setStatusBar(None)

        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header Box (Catppuccin Mocha Card)
        header = QFrame(self)
        header.setObjectName("HeaderBox")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(16)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        pix = None
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.mascot_lbl = BouncingMascotLabel(pix, emoji="🦆", parent=header)
        header_layout.addWidget(self.mascot_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        t_lbl = QLabel("QuakMeeting — Flight Deck", header)
        t_lbl.setObjectName("HeaderTitle")
        s_lbl = QLabel("Smart Calendar Reminders & Mascot Alert Companion", header)
        s_lbl.setObjectName("HeaderSub")

        title_box.addWidget(t_lbl)
        title_box.addWidget(s_lbl)
        header_layout.addLayout(title_box, stretch=1)

        badge = QLabel("⚡ Calendar Scanner Active", header)
        badge.setObjectName("ActiveBadge")
        header_layout.addWidget(badge)

        self.sync_btn = AnimatedSpinButton("🔄 Sync Now", header)
        sync_btn = self.sync_btn
        sync_btn.setObjectName("OutlineBtn")
        sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def _trigger_sync():
            self.sync_btn.start_spinning("Syncing...")
            threading.Thread(target=calendar_service.sync_now, daemon=True).start()
        sync_btn.clicked.connect(lambda chk=False: _trigger_sync())
        header_layout.addWidget(sync_btn)

        main_layout.addWidget(header)

        # 2. Segmented Capsule Navbar (Catppuccin Mocha macOS Native Design)
        self.navbar_container = QFrame(central_widget)
        self.navbar_container.setObjectName("NavbarContainer")
        navbar_layout = QHBoxLayout(self.navbar_container)
        navbar_layout.setContentsMargins(3, 3, 3, 3)
        navbar_layout.setSpacing(4)

        self.nav_buttons = []
        segments = [
            ("📅 Today's Agenda", 0),
            ("🦆 Pilot Hangar", 1),
            ("⚙️ Preferences && Timing", 2)
        ]
        for title, idx in segments:
            btn = QPushButton(title, self.navbar_container)
            btn.setObjectName("NavSegmentBtn")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda chk=False, i=idx: self.set_active_tab(i))
            navbar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        main_layout.addWidget(self.navbar_container)

        # 3. Stacked Tab Pages (Modularized)
        self.stacked_widget = QStackedWidget(central_widget)

        self.agenda_tab = QtAgendaTab(self)
        self.hangar_tab = QtHangarTab(self)
        self.settings_tab = QtSettingsTab(self)

        self.stacked_widget.addWidget(self.agenda_tab)
        self.stacked_widget.addWidget(self.hangar_tab)
        self.stacked_widget.addWidget(self.settings_tab)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        class _TabsFacade:
            def __init__(self, parent):
                self._parent = parent
            def setCurrentIndex(self, idx):
                self._parent.set_active_tab(idx)
            def currentIndex(self):
                return self._parent.current_tab_index
            def count(self):
                return 3
        self.tabs = _TabsFacade(self)
        self.set_active_tab(tab_index)

    @property
    def h_mini_widgets(self):
        return self.hangar_tab.h_mini_widgets

    @property
    def hangar_anim_timer(self):
        return self.hangar_tab.hangar_anim_timer

    def set_active_tab(self, index: int):
        """Switches the active tab and updates navbar segment button states."""
        self.current_tab_index = index
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self.hangar_tab.start_animation_timer()
        else:
            self.hangar_tab.stop_animation_timer()
        for i, btn in enumerate(getattr(self, 'nav_buttons', [])):
            is_active = (i == index)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def closeEvent(self, event):
        """Cleans up animation timers when window is closed."""
        if hasattr(self, 'hangar_tab'):
            self.hangar_tab.stop_animation_timer()
        super().closeEvent(event)

    def _refresh_agenda(self, meetings=None):
        """Delegates agenda timeline refresh to QtAgendaTab."""
        self.agenda_tab.refresh_agenda(meetings)

    def _refresh_hangar(self):
        """Delegates hangar customization refresh to QtHangarTab."""
        self.hangar_tab.refresh_hangar()

    def render_hangar_tab(self):
        """Public alias for refreshing hangar tab."""
        self.hangar_tab.refresh_hangar()

    @property
    def scroll_content(self):
        return self.agenda_tab.scroll_content

    @property
    def scroll(self):
        return self.agenda_tab.scroll

    @property
    def scroll_layout(self):
        return self.agenda_tab.scroll_layout

    @property
    def h_scroll(self):
        return self.hangar_tab.h_scroll

    @property
    def h_content(self):
        return self.hangar_tab.h_content

    @property
    def h_layout(self):
        return self.hangar_tab.h_layout


_dashboard_instance = None

def show_qt_dashboard(tab_index: int = 0):
    """Launches the PyQt6 Flight Deck Control Center."""
    logger.info("🟢 show_qt_dashboard called. Attempting to open the Flight Deck window...")
    global _dashboard_instance
    app = QApplication.instance()
    is_standalone = False
    if app is None:
        logger.info("🟢 Creating new QApplication instance (standalone mode)")
        app = QApplication(sys.argv)
        is_standalone = True
    else:
        logger.info("🟢 Reusing existing QApplication instance from Tray App")

    if _dashboard_instance is None or not _dashboard_instance.isVisible():
        logger.info("🟢 Creating a new QtFlightDeckWindow instance and binding it to global singleton.")
        _dashboard_instance = QtFlightDeckWindow(tab_index)
        _dashboard_instance.show()
        _dashboard_instance.raise_()
        _dashboard_instance.activateWindow()
        if hasattr(_dashboard_instance, "mascot_lbl"):
            _dashboard_instance.mascot_lbl.trigger_bounce()
        logger.info("🟢 Window successfully created and shown with mascot bounce animation!")
    else:
        logger.info("🟢 Window already exists. Bringing it to the front...")
        _dashboard_instance.tabs.setCurrentIndex(tab_index)
        _dashboard_instance.raise_()
        _dashboard_instance.activateWindow()
        if hasattr(_dashboard_instance, "mascot_lbl"):
            _dashboard_instance.mascot_lbl.trigger_bounce()

    if is_standalone:
        app.exec()

def close_qt_dashboard():
    """Safely closes the Flight Deck window if active."""
    global _dashboard_instance
    if _dashboard_instance is not None:
        try:
            _dashboard_instance.close()
        except Exception:
            pass
        _dashboard_instance = None

if __name__ == "__main__":
    t_idx = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0
    show_qt_dashboard(t_idx)
