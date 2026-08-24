"""
PyQt6 Modern Dark Flight Deck Dashboard Window for Ubuntu Linux.
Matches macOS Flight Deck design:
- Today's Agenda timeline with status badges & 1-click joins
- Pilot Hangar interactive playground for all 7 mascot aircrafts
- Preferences & Timing settings with live config saving
"""
import os
import sys

if sys.platform.startswith("linux"):
    if "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import threading
import logging
from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QTabWidget, QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.domain.models import format_duration, Meeting
from core.logger import open_log_file, open_log_folder

logger = logging.getLogger("QuakMeeting.QtDashboard")

QT_DASHBOARD_QSS = """
QMainWindow {
    background-color: #0f111a;
}

QWidget#CentralWidget {
    background-color: #0f111a;
}

QFrame#HeaderBox {
    background-color: #161926;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

QLabel#HeaderTitle {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
}

QLabel#HeaderSub {
    font-size: 12px;
    color: #94a3b8;
}

QLabel#ActiveBadge {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

QTabWidget::pane {
    border: none;
    background-color: #0f111a;
}

QTabBar::tab {
    background-color: transparent;
    color: #94a3b8;
    font-weight: 600;
    font-size: 13px;
    padding: 12px 24px;
    border: none;
}

QTabBar::tab:selected {
    color: #38bdf8;
    border-bottom: 3px solid #38bdf8;
    background-color: rgba(56, 189, 248, 0.08);
}

QFrame#Card {
    background-color: #181c2b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
}

QFrame#Card:hover {
    background-color: #1e2336;
    border-color: rgba(56, 189, 248, 0.3);
}

QLabel#CardTitle {
    font-size: 15px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#CardSub {
    font-size: 12px;
    color: #94a3b8;
}

QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284c7, stop:1 #2563eb);
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
    border-radius: 8px;
    border: none;
    padding: 8px 18px;
}

QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38bdf8, stop:1 #3b82f6);
}

QPushButton#SecondaryBtn {
    background-color: #242a3d;
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 600;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 8px 16px;
}

QPushButton#SecondaryBtn:hover {
    background-color: #313850;
    color: #ffffff;
}

QLineEdit {
    background-color: #12141f;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 8px;
    color: #f8fafc;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #38bdf8;
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

        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Box
        header = QFrame(self)
        header.setObjectName("HeaderBox")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(16)

        # Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        icon_lbl = QLabel(header)
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(pix)
        else:
            icon_lbl.setText("🦆")
            icon_lbl.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_lbl)

        # Title / Subtitle
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        t_lbl = QLabel("QuakMeeting — Flight Deck", header)
        t_lbl.setObjectName("HeaderTitle")
        s_lbl = QLabel("Smart Calendar Reminders & Mascot Alert Companion", header)
        s_lbl.setObjectName("HeaderSub")
        
        title_box.addWidget(t_lbl)
        title_box.addWidget(s_lbl)
        header_layout.addLayout(title_box, stretch=1)

        # Active Badge
        badge = QLabel("⚡ Calendar Scanner Active", header)
        badge.setObjectName("ActiveBadge")
        header_layout.addWidget(badge)

        # Sync Button
        sync_btn = QPushButton("🔄 Sync Now", header)
        sync_btn.setObjectName("SecondaryBtn")
        sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sync_btn.clicked.connect(lambda: threading.Thread(target=calendar_service.sync_now, daemon=True).start())
        header_layout.addWidget(sync_btn)

        main_layout.addWidget(header)

        # 2. Tabs
        self.tabs = QTabWidget(central_widget)

        # --- TAB 1: Today's Agenda ---
        agenda_widget = QWidget()
        agenda_layout = QVBoxLayout(agenda_widget)
        agenda_layout.setContentsMargins(20, 16, 20, 16)

        scroll = QScrollArea(agenda_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget { background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        now = datetime.now()
        meetings = calendar_service.get_upcoming_meetings()
        today_meets = [m for m in meetings if m.start_time and m.start_time.date() == now.date()]

        if not today_meets:
            empty_box = QVBoxLayout()
            empty_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_icon = QLabel("🧘‍♂️")
            e_icon.setStyleSheet("font-size: 48px; border: none;")
            e_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            e_msg = QLabel("No Meetings Scheduled for Today\nEnjoy your clear agenda or add events to your calendar.")
            e_msg.setStyleSheet("font-size: 15px; font-weight: bold; color: #cbd5e1; border: none;")
            e_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_box.addWidget(e_icon)
            empty_box.addWidget(e_msg)
            scroll_layout.addLayout(empty_box)
        else:
            for m in today_meets:
                card = QFrame(scroll_content)
                card.setObjectName("Card")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(18, 14, 18, 14)
                c_layout.setSpacing(14)

                pilot_icon = "🦆"
                if m.pilot_type == "chef": pilot_icon = "👨‍🍳"
                elif m.pilot_type == "captain": pilot_icon = "🧑‍✈️"
                elif m.pilot_type == "owl": pilot_icon = "🦉"
                elif m.pilot_type == "gym": pilot_icon = "🏋️‍♂️"
                elif m.pilot_type == "driver": pilot_icon = "🏎️"
                elif m.pilot_type == "zen_duck": pilot_icon = "🦆🌸"

                icon_l = QLabel(pilot_icon, card)
                icon_l.setStyleSheet("font-size: 26px; border: none;")
                c_layout.addWidget(icon_l)

                info_box = QVBoxLayout()
                info_box.setSpacing(2)

                st = m.start_time.strftime("%H:%M") if m.start_time else "--:--"
                et = m.end_time.strftime("%H:%M") if m.end_time else ""
                dur_str = f" ({format_duration(m.duration_minutes)})" if m.duration_minutes else ""

                t_l = QLabel(m.title, card)
                t_l.setObjectName("CardTitle")

                sub_txt = f"<b style='color:#38bdf8;'>{st} - {et}{dur_str}</b>  •  {m.provider}"
                if m.is_travel and m.departure_time:
                    sub_txt += f"  •  <span style='color:#fbbf24;'>🚗 Leave at {m.departure_time.strftime('%H:%M')}</span>"
                if m.classroom:
                    sub_txt += f"  •  <span style='color:#c084fc;'>🏫 {m.classroom}</span>"

                s_l = QLabel(sub_txt, card)
                s_l.setObjectName("CardSub")

                info_box.addWidget(t_l)
                info_box.addWidget(s_l)
                c_layout.addLayout(info_box, stretch=1)

                has_real_url = bool(m.action_url and m.action_url.strip() and m.action_url != "https://calendar.apple.com")
                if has_real_url:
                    btn_text = "🚀 JOIN" if not m.is_travel else "🗺️ NAVIGATE"
                    btn = QPushButton(btn_text, card)
                    btn.setObjectName("PrimaryBtn")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.clicked.connect(lambda chk, u=m.action_url: webbrowser.open(u))
                    c_layout.addWidget(btn)

                scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        agenda_layout.addWidget(scroll)
        self.tabs.addTab(agenda_widget, "📅 Today's Agenda")

        # --- TAB 2: Pilot Hangar ---
        hangar_widget = QWidget()
        hangar_layout = QVBoxLayout(hangar_widget)
        hangar_layout.setContentsMargins(20, 16, 20, 16)

        h_scroll = QScrollArea(hangar_widget)
        h_scroll.setWidgetResizable(True)
        h_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget { background: transparent; }")

        h_content = QWidget()
        h_layout = QVBoxLayout(h_content)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(12)

        pilots = [
            ("duck", "🦆 Aviator Duck", "Google Meet / Zoom / Video Meetings", "https://meet.google.com/test"),
            ("chef", "👨‍🍳 Chef Duck", "Dinner / Lunch / Restaurants / Aperitivo", "https://maps.google.com/?q=Pizzeria"),
            ("captain", "🧑‍✈️ Jet Captain", "Flights / Airports / High-Speed Transit", "https://maps.google.com/?q=Airport"),
            ("owl", "🦉 Academic Owl", "University Lectures / Exams / Campus Study", "https://calendar.google.com"),
            ("gym", "🏋️‍♂️ Athlete Duck", "Palestra / Gym / CrossFit / Sport", "https://maps.google.com/?daddr=Gym"),
            ("driver", "🏎️ Speed Racer", "In-Person Meetings / Appointments / Travel", "https://maps.google.com/?daddr=Office"),
            ("zen_duck", "🦆🌸 Zen Duck", "Serenis / Therapy / Yoga / Wellness", "https://app.serenis.it")
        ]

        for p_id, p_name, p_desc, p_url in pilots:
            card = QFrame(h_content)
            card.setObjectName("Card")
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(18, 14, 18, 14)
            c_layout.setSpacing(14)

            p_box = QVBoxLayout()
            p_box.setSpacing(2)
            n_l = QLabel(p_name, card)
            n_l.setObjectName("CardTitle")
            d_l = QLabel(p_desc, card)
            d_l.setObjectName("CardSub")
            p_box.addWidget(n_l)
            p_box.addWidget(d_l)
            c_layout.addLayout(p_box, stretch=1)

            def _trigger_test_flight(p_id_val):
                try:
                    from ui.banner.qt_banner import get_test_preset, show_qt_banner
                    evt = get_test_preset(p_id_val)
                    show_qt_banner(evt)
                except Exception as ex:
                    logger.error(f"Error triggering test flight banner: {ex}")

            t_btn = QPushButton("🚀 Test Flight", card)
            t_btn.setObjectName("PrimaryBtn")
            t_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            t_btn.clicked.connect(lambda chk, i=p_id: _trigger_test_flight(i))
            c_layout.addWidget(t_btn)
            h_layout.addWidget(card)

        h_layout.addStretch()
        h_scroll.setWidget(h_content)
        hangar_layout.addWidget(h_scroll)
        self.tabs.addTab(hangar_widget, "🦆 Pilot Hangar")

        # --- TAB 3: Preferences ---
        pref_widget = QWidget()
        pref_layout = QVBoxLayout(pref_widget)
        pref_layout.setContentsMargins(20, 16, 20, 16)
        pref_layout.setSpacing(14)

        addr_card = QFrame(pref_widget)
        addr_card.setObjectName("Card")
        ac_layout = QVBoxLayout(addr_card)
        ac_layout.setContentsMargins(18, 14, 18, 14)
        ac_layout.setSpacing(8)

        ac_title = QLabel("🏠 Home / Departure Address", addr_card)
        ac_title.setObjectName("CardTitle")
        ac_sub = QLabel("Used to calculate transit & driving departure times via Apple/Google Maps ETA.", addr_card)
        ac_sub.setObjectName("CardSub")

        entry_row = QHBoxLayout()
        addr_entry = QLineEdit(addr_card)
        addr_entry.setText(config.get("home_address", "") or "")
        addr_entry.setPlaceholderText("e.g. Corso Duca degli Abruzzi 24, Torino")

        save_btn = QPushButton("💾 Save Location", addr_card)
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(lambda: config.set("home_address", addr_entry.text().strip()))

        entry_row.addWidget(addr_entry, stretch=1)
        entry_row.addWidget(save_btn)

        ac_layout.addWidget(ac_title)
        ac_layout.addWidget(ac_sub)
        ac_layout.addLayout(entry_row)
        pref_layout.addWidget(addr_card)

        # Utilities
        util_card = QFrame(pref_widget)
        util_card.setObjectName("Card")
        uc_layout = QVBoxLayout(util_card)
        uc_layout.setContentsMargins(18, 14, 18, 14)
        uc_layout.setSpacing(10)

        uc_title = QLabel("⚙️ System & Diagnostics", util_card)
        uc_title.setObjectName("CardTitle")
        uc_layout.addWidget(uc_title)

        sys_row = QHBoxLayout()
        edit_btn = QPushButton("📝 Edit Config JSON", util_card)
        edit_btn.setObjectName("SecondaryBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: config.open_config_in_editor())

        log_btn = QPushButton("📄 View Live Log File", util_card)
        log_btn.setObjectName("SecondaryBtn")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(lambda: open_log_file())

        up_btn = QPushButton("🔍 Check for Updates", util_card)
        up_btn.setObjectName("SecondaryBtn")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        up_btn.clicked.connect(lambda: updater_service.check_for_updates(background=True))

        sys_row.addWidget(edit_btn)
        sys_row.addWidget(log_btn)
        sys_row.addWidget(up_btn)
        uc_layout.addLayout(sys_row)
        pref_layout.addWidget(util_card)

        pref_layout.addStretch()
        self.tabs.addTab(pref_widget, "⚙️ Preferences")

        self.tabs.setCurrentIndex(tab_index)
        main_layout.addWidget(self.tabs)

def show_qt_dashboard(tab_index: int = 0):
    """Launches the PyQt6 Flight Deck Control Center."""
    app = QApplication.instance()
    is_standalone = False
    if app is None:
        app = QApplication(sys.argv)
        is_standalone = True

    win = QtFlightDeckWindow(tab_index)
    win.show()

    if is_standalone:
        app.exec()
