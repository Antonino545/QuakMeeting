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
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QTabWidget, QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon

from ui.linux.animated_widgets import (
    BouncingMascotLabel, AnimatedSpinButton, AnimatedUpdateCard, UpdatingHUDWidget
)

class QtUpdateBridge(QObject):
    update_event = pyqtSignal(str, dict)

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.updater_service import updater_service
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
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

        # Mascot Icon with bouncy float & click reaction
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        pix = None
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.mascot_lbl = BouncingMascotLabel(pix, emoji="🦆", parent=header)
        header_layout.addWidget(self.mascot_lbl)

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

        # Sync Button with frame-by-frame spinner animation
        self.sync_btn = AnimatedSpinButton("🔄 Sync Now", header)
        sync_btn = self.sync_btn
        sync_btn.setObjectName("SecondaryBtn")
        sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def _trigger_sync():
            self.sync_btn.start_spinning("Syncing...")
            threading.Thread(target=calendar_service.sync_now, daemon=True).start()
        sync_btn.clicked.connect(lambda chk=False: _trigger_sync())
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

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)
        
        self.scroll = scroll
        self._refresh_agenda()
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
            ("travel_departure", "🚦 Multi-Modal Route ETA", "Transit, Driving & Cycling Departure Countdown", "https://maps.google.com"),
            ("chef", "👨‍🍳 Chef Duck", "Dinner / Lunch / Restaurants / Aperitivo", "https://maps.google.com/?q=Pizzeria"),
            ("captain", "🧑‍✈️ Jet Captain", "Flights / Airports / High-Speed Transit", "https://maps.google.com/?q=Airport"),
            ("owl", "🦉 Academic Owl", "University Lectures / Exams / Campus Study", "https://calendar.google.com"),
            ("gym", "🏋️‍♂️ Athlete Duck", "Palestra / Gym / CrossFit / Sport", "https://maps.google.com/?daddr=Gym"),
            ("driver", "🏎️ Speed Racer", "In-Person Meetings / Appointments / Travel", "https://maps.google.com/?daddr=Office"),
            ("zen_duck", "🦆🌸 Zen Duck", "Serenis / Therapy / Yoga / Wellness", "https://app.serenis.it")
        ]

        for idx, (p_id, p_name, p_desc, p_url) in enumerate(pilots):
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
                    if p_id_val == "travel_departure":
                        from core.services.eta_service import eta_service
                        t_mode = config.get("transport_mode", "transit")
                        res = eta_service.calculate_eta("Piazza Castello, Torino", "Politecnico di Torino, Corso Duca degli Abruzzi 24, Torino", mode=t_mode)
                        dur = res["duration_minutes"] if res else 12
                        evt = {
                            "title": "ICT for Smart Mobility (Politecnico di Torino)",
                            "location": "Corso Duca degli Abruzzi 24, Torino",
                            "pilot_type": "owl",
                            "provider": "Politecnico Calendar 📅",
                            "start_time": datetime.now().astimezone() + timedelta(minutes=dur + 15),
                            "departure_time": datetime.now().astimezone() + timedelta(minutes=15),
                            "travel_time_minutes": dur,
                            "transport_mode": t_mode,
                            "is_travel": True,
                            "reminder_stage": 15,
                            "action_btn_text": f"🗺️ NAVIGATE ({dur}m)",
                            "maps_url": res["maps_url"] if res else "https://maps.google.com"
                        }
                    else:
                        from ui.linux.banner.qt_banner import get_test_preset
                        evt = dict(get_test_preset(p_id_val))

                    from ui.linux.banner.qt_banner import show_qt_banner
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


        # --- Timing & Stages Card ---
        timing_card = QFrame(pref_widget)
        timing_card.setObjectName("Card")
        tc_layout = QVBoxLayout(timing_card)
        tc_layout.setContentsMargins(18, 14, 18, 14)
        tc_layout.setSpacing(10)

        tc_title = QLabel("⏱️ Notification Lead Times & Staged Reminders", timing_card)
        tc_title.setObjectName("CardTitle")
        tc_sub = QLabel("Select reminder alert windows to receive progressive notifications ahead of time.", timing_card)
        tc_sub.setObjectName("CardSub")
        tc_layout.addWidget(tc_title)
        tc_layout.addWidget(tc_sub)

        def create_stage_row(title, desc, config_key, opts):
            row_layout = QVBoxLayout()
            row_layout.setSpacing(4)
            lbl = QLabel(f"<b>{title}</b>", timing_card)
            lbl.setStyleSheet("color: #e2e8f0; font-size: 12px;")
            desc_lbl = QLabel(desc, timing_card)
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            row_layout.addWidget(lbl)
            row_layout.addWidget(desc_lbl)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            curr_stages = set(config.get(config_key, [20, 10, 5, 2, 0]))

            for val, label in opts:
                chk = QCheckBox(label, timing_card)
                chk.setStyleSheet("QCheckBox { color: #cbd5e1; font-size: 12px; } QCheckBox::indicator { width: 14px; height: 14px; }")
                chk.setChecked(val in curr_stages)
                def _toggled(checked, v=val, k=config_key):
                    c = set(config.get(k, []))
                    if checked: c.add(v)
                    else: c.discard(v)
                    config.set(k, sorted(list(c), reverse=True))
                chk.toggled.connect(_toggled)
                btn_layout.addWidget(chk)

            btn_layout.addStretch()
            row_layout.addLayout(btn_layout)
            return row_layout

        meeting_opts = [(30, "30m"), (20, "20m"), (15, "15m"), (10, "10m"), (5, "5m"), (2, "2m"), (0, "0m Start")]
        travel_opts = [(60, "60m"), (45, "45m"), (30, "30m"), (15, "15m"), (5, "5m"), (2, "2m"), (0, "0m Leave")]

        tc_layout.addLayout(create_stage_row("📹 Video Meetings", "Alert ahead of meeting start time", "meeting_reminder_stages", meeting_opts))

        tc_div1 = QFrame(timing_card)
        tc_div1.setFixedHeight(1)
        tc_div1.setStyleSheet("background-color: rgba(255,255,255,0.05);")
        tc_layout.addWidget(tc_div1)

        tc_layout.addLayout(create_stage_row("📅 General Events", "Alert ahead of start time (non-travel)", "general_reminder_stages", meeting_opts))

        tc_div2 = QFrame(timing_card)
        tc_div2.setFixedHeight(1)
        tc_div2.setStyleSheet("background-color: rgba(255,255,255,0.05);")
        tc_layout.addWidget(tc_div2)

        tc_layout.addLayout(create_stage_row("🚗 Travel & Trips", "Alert ahead of leave / departure time", "travel_reminder_stages", travel_opts))

        pref_layout.addWidget(timing_card)

        # --- Multi-Modal Travel & Route Estimation Card ---
        addr_card = QFrame(pref_widget)
        addr_card.setObjectName("Card")
        ac_layout = QVBoxLayout(addr_card)
        ac_layout.setContentsMargins(18, 14, 18, 14)
        ac_layout.setSpacing(10)

        ac_title = QLabel("📍 Home / Departure Address & Multi-Modal Route ETA", addr_card)
        ac_title.setObjectName("CardTitle")
        ac_sub = QLabel("Calculates real-time travel duration and departure times for Public Transit, Driving, Walking, or Cycling.", addr_card)
        ac_sub.setObjectName("CardSub")
        ac_layout.addWidget(ac_title)
        ac_layout.addWidget(ac_sub)

        # 1. Starting Address Row
        addr_row_lbl = QLabel("<b>🏠 Starting Address (Origin)</b>", addr_card)
        addr_row_lbl.setStyleSheet("color: #e2e8f0; font-size: 12px;")
        ac_layout.addWidget(addr_row_lbl)

        entry_row = QHBoxLayout()
        addr_entry = QLineEdit(addr_card)
        addr_entry.setText(config.get("home_address", "") or "")
        addr_entry.setPlaceholderText("e.g. Piazza Castello, Torino or Via Roma, Torino")

        save_addr_btn = QPushButton("💾 Save Location", addr_card)
        save_addr_btn.setObjectName("PrimaryBtn")
        save_addr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def _save_addr():
            val = addr_entry.text().strip()
            config.set("home_address", val)
            save_addr_btn.setText("✓ Saved")
            QTimer.singleShot(1500, lambda: save_addr_btn.setText("💾 Save Location"))
        save_addr_btn.clicked.connect(_save_addr)

        entry_row.addWidget(addr_entry, stretch=1)
        entry_row.addWidget(save_addr_btn)
        ac_layout.addLayout(entry_row)

        # 2. Preferred Transport Mode
        mode_lbl = QLabel("<b>🚦 Transport Mode for Route Calculation</b>", addr_card)
        mode_lbl.setStyleSheet("color: #e2e8f0; font-size: 12px; margin-top: 4px;")
        ac_layout.addWidget(mode_lbl)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        current_mode = config.get("transport_mode", "transit")

        mode_buttons = {}
        modes_spec = [
            ("transit", "🚆 Public Transit"),
            ("automobile", "🚗 Driving"),
            ("bicycling", "🚲 Cycling"),
            ("walking", "🚶 Walking")
        ]

        def _update_mode_styles(active_key):
            for k, b in mode_buttons.items():
                if k == active_key:
                    b.setStyleSheet("""
                        QPushButton {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                            color: #ffffff;
                            font-weight: bold;
                            border: 1px solid #38bdf8;
                            border-radius: 8px;
                            padding: 8px 12px;
                        }
                    """)
                else:
                    b.setStyleSheet("""
                        QPushButton {
                            background: rgba(255, 255, 255, 0.05);
                            color: #cbd5e1;
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            border-radius: 8px;
                            padding: 8px 12px;
                        }
                        QPushButton:hover {
                            background: rgba(255, 255, 255, 0.10);
                            color: #f8fafc;
                        }
                    """)

        for m_key, m_name in modes_spec:
            btn = QPushButton(m_name, addr_card)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            mode_buttons[m_key] = btn
            def _select_m(chk=False, k=m_key):
                config.set("transport_mode", k)
                _update_mode_styles(k)
                try:
                    event_bus.publish("CONFIG_CHANGED", key="transport_mode", value=k)
                except Exception:
                    pass
            btn.clicked.connect(_select_m)
            mode_row.addWidget(btn)

        _update_mode_styles(current_mode)
        ac_layout.addLayout(mode_row)

        # 3. Departure Buffer Margin
        buf_row = QHBoxLayout()
        buf_lbl = QLabel("<b>⏳ Departure Buffer Margin</b> (station transit / parking time):", addr_card)
        buf_lbl.setStyleSheet("color: #e2e8f0; font-size: 12px;")

        buf_combo = QComboBox(addr_card)
        buf_combo.addItems(["5 minutes", "10 minutes (Recommended)", "15 minutes", "20 minutes"])
        buf_map = {5: 0, 10: 1, 15: 2, 20: 3}
        rev_buf_map = [5, 10, 15, 20]
        cur_buf = config.get("eta_buffer_minutes", 10)
        buf_combo.setCurrentIndex(buf_map.get(cur_buf, 1))

        def _on_buf_change(idx):
            val = rev_buf_map[idx]
            config.set("eta_buffer_minutes", val)
            try:
                event_bus.publish("CONFIG_CHANGED", key="eta_buffer_minutes", value=val)
            except Exception:
                pass
        buf_combo.currentIndexChanged.connect(_on_buf_change)

        buf_row.addWidget(buf_lbl, stretch=1)
        buf_row.addWidget(buf_combo)
        ac_layout.addLayout(buf_row)

        # 4. Live Route Simulation & Banner Test Row
        sim_box = QFrame(addr_card)
        sim_box.setStyleSheet("background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 10px; padding: 6px;")
        sim_layout = QVBoxLayout(sim_box)
        sim_layout.setContentsMargins(10, 8, 10, 8)
        sim_layout.setSpacing(6)

        sim_title = QLabel("🧪 Live Route & Departure Banner Test (Politecnico di Torino)", sim_box)
        sim_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px; border: none;")
        sim_layout.addWidget(sim_title)

        sim_act_row = QHBoxLayout()
        sim_info_lbl = QLabel("Calculate real-time transit & launch a live on-screen flight banner:", sim_box)
        sim_info_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; border: none;")
        sim_act_row.addWidget(sim_info_lbl, stretch=1)

        def _test_polito_banner():
            try:
                from core.services.eta_service import eta_service
                orig = addr_entry.text().strip() or "Piazza Castello, Torino"
                dest = "Politecnico di Torino, Corso Duca degli Abruzzi 24, Torino"
                t_mode = config.get("transport_mode", "transit")
                res = eta_service.calculate_eta(orig, dest, mode=t_mode)
                dur = res["duration_minutes"] if res else 15
                dist = res["distance_km"] if res else 2.7
                maps_url = res["maps_url"] if res else "https://maps.google.com"

                evt = {
                    "title": "ICT for Smart Mobility (Politecnico di Torino) - Aula 5M",
                    "location": dest,
                    "pilot_type": "owl",
                    "provider": "Politecnico Calendar 📅",
                    "start_time": datetime.now().astimezone() + timedelta(minutes=dur + 15),
                    "departure_time": datetime.now().astimezone() + timedelta(minutes=15),
                    "travel_time_minutes": dur,
                    "transport_mode": t_mode,
                    "is_travel": True,
                    "reminder_stage": 15,
                    "action_btn_text": f"🗺️ NAVIGATE ({dur}m)",
                    "maps_url": maps_url
                }

                from ui.linux.banner.qt_banner import show_qt_banner
                show_qt_banner(evt)
            except Exception as e:
                logger.error(f"Error testing live departure banner: {e}")

        test_dep_btn = QPushButton("🚀 Launch Departure Banner", sim_box)
        test_dep_btn.setObjectName("PrimaryBtn")
        test_dep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_dep_btn.clicked.connect(_test_polito_banner)
        sim_act_row.addWidget(test_dep_btn)

        sim_layout.addLayout(sim_act_row)
        ac_layout.addWidget(sim_box)

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

        
        autostart_chk = QCheckBox("🚀 Launch QuakMeeting automatically at Linux login", util_card)
        autostart_chk.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 13px;")
        autostart_chk.setCursor(Qt.CursorShape.PointingHandCursor)
        autostart_chk.setChecked(is_autostart_enabled())
        def _toggle_autostart(checked):
            if checked:
                enable_autostart()
            else:
                disable_autostart()
        autostart_chk.toggled.connect(_toggle_autostart)
        uc_layout.addWidget(autostart_chk)
        uc_layout.addSpacing(10)
        
        sys_row = QHBoxLayout()

        edit_btn = QPushButton("📝 Edit Config JSON", util_card)
        edit_btn.setObjectName("SecondaryBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda chk=False: config.open_config_in_editor())

        log_btn = QPushButton("📄 View Live Log File", util_card)
        log_btn.setObjectName("SecondaryBtn")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(lambda chk=False: open_log_file())

        up_btn = AnimatedSpinButton("🔍 Check for Updates", util_card)
        up_btn.setObjectName("SecondaryBtn")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        demo_up_btn = QPushButton("🎬 Test Update Animation", util_card)
        demo_up_btn.setObjectName("SecondaryBtn")
        demo_up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_up_btn.setToolTip("Preview the live rocket jet download & installation animation sequence")

        sys_row.addWidget(edit_btn)
        sys_row.addWidget(log_btn)
        sys_row.addWidget(up_btn)
        sys_row.addWidget(demo_up_btn)
        uc_layout.addLayout(sys_row)

        # Animated Update status card with radar scanning and celebratory states
        update_status_box = AnimatedUpdateCard(util_card)
        usb_layout = QVBoxLayout(update_status_box)
        usb_layout.setContentsMargins(14, 12, 14, 12)
        usb_layout.setSpacing(8)

        status_header_row = QHBoxLayout()
        update_icon_lbl = QLabel("🦆", update_status_box)
        update_icon_lbl.setStyleSheet("font-size: 22px; border: none;")
        status_header_row.addWidget(update_icon_lbl)

        update_status_lbl = QLabel(f"QuakMeeting <b>v{updater_service.current_version}</b>  •  <span style='color:#94a3b8;'>Ready</span>", update_status_box)
        update_status_lbl.setStyleSheet("color: #f1f5f9; font-size: 13px; border: none;")
        status_header_row.addWidget(update_status_lbl, stretch=1)
        usb_layout.addLayout(status_header_row)

        changelog_lbl = QLabel("", update_status_box)
        changelog_lbl.setWordWrap(True)
        changelog_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; border: none; padding-left: 2px;")
        changelog_lbl.setVisible(False)
        usb_layout.addWidget(changelog_lbl)

        # Dedicated Animated Updating HUD (Flying Mascot Jet, Phase indicators & Rotating Gears)
        updating_hud = UpdatingHUDWidget(update_status_box)
        updating_hud.setVisible(False)
        usb_layout.addWidget(updating_hud)

        # Action Buttons Row
        act_row = QHBoxLayout()
        act_row.setContentsMargins(0, 4, 0, 0)
        install_btn = QPushButton("⚡ Download & Install Update", update_status_box)
        install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        install_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #3b82f6);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.08);
                color: #64748b;
            }
        """)
        install_btn.setVisible(False)
        act_row.addWidget(install_btn)
        usb_layout.addLayout(act_row)

        uc_layout.addWidget(update_status_box)

        # Interactive animation preview simulation
        def _run_update_animation_demo():
            updating_hud.start_downloading("quakmeeting_latest_amd64.deb")
            demo_up_btn.setEnabled(False)
            install_btn.setVisible(False)
            total_size = 28 * 1024 * 1024  # 28 MB simulation
            
            def _demo_step(pct):
                if pct <= 100:
                    curr_bytes = int((pct / 100.0) * total_size)
                    updating_hud.set_progress(pct, curr_bytes, total_size)
                    QTimer.singleShot(40, lambda p=pct+2: _demo_step(p))
                else:
                    updating_hud.set_installing()
                    def _finish_install():
                        updating_hud.set_installed()
                        demo_up_btn.setEnabled(True)
                    QTimer.singleShot(1400, _finish_install)

            QTimer.singleShot(300, lambda: _demo_step(4))

        demo_up_btn.clicked.connect(_run_update_animation_demo)

        def _on_check_clicked():
            up_btn.start_spinning("Checking...")
            update_status_box.set_scanning(True)
            update_icon_lbl.setText("📡")
            update_status_lbl.setText("<span style='color:#38bdf8;'><b>Scanning GitHub repository for releases...</b></span>")
            updater_service.check_for_updates(background=True)

        up_btn.clicked.connect(_on_check_clicked)

        def _on_update_avail(version=None, tag_name=None, name=None, body=None, **k):
            up_btn.stop_spinning("🔍 Check for Updates")
            v_name = tag_name or version or "New Version"
            update_status_box.set_update_available(v_name)
            update_icon_lbl.setText("🚀")
            update_status_lbl.setText(f"<b style='color:#38bdf8;'>Update Available: {v_name}</b>  <span style='color:#64748b;'>(Current: v{updater_service.current_version})</span>")
            if body:
                summary = body.strip().split("\n")[0][:120]
                changelog_lbl.setText(f"<i>✨ {summary}</i>")
                changelog_lbl.setVisible(True)
            install_btn.setText(f"⚡ Install {v_name} Now")
            install_btn.setEnabled(True)
            install_btn.setVisible(True)

        def _on_update_complete(has_update=False, current_version=None, error=None, **k):
            if not has_update:
                if error:
                    up_btn.stop_spinning("❌ Check Error", is_success=False, reset_delay_ms=2500)
                    update_icon_lbl.setText("⚠️")
                    update_status_lbl.setText(f"<span style='color:#f87171;'>Update check error: {error[:60]}</span>")
                else:
                    up_btn.stop_spinning("✨ Up to date", is_success=True, reset_delay_ms=2500)
                    update_status_box.set_up_to_date()
                    update_icon_lbl.setText("✨")
                    update_status_lbl.setText(f"<span style='color:#4ade80;'><b>You are on the latest version!</b></span>  <b>v{current_version or updater_service.current_version}</b>")
                install_btn.setVisible(False)
                changelog_lbl.setVisible(False)

        def _on_downloading(file_name=None, **k):
            update_icon_lbl.setText("📥")
            update_status_lbl.setText(f"<b>Downloading update package...</b> <span style='color:#94a3b8;'>({file_name or ''})</span>")
            install_btn.setVisible(False)
            updating_hud.start_downloading(file_name or "")

        def _on_download_progress(percent=0, downloaded=0, total=0, **k):
            updating_hud.set_progress(percent, downloaded, total)

        def _on_downloaded(target_path=None, **k):
            update_icon_lbl.setText("⚙️")
            update_status_lbl.setText("<b>Installing update...</b> Please grant system permission if prompted.")
            updating_hud.set_installing()

        def _on_installed(**k):
            update_icon_lbl.setText("🎉")
            update_status_lbl.setText("<b style='color:#4ade80;'>Update installed successfully!</b> Relaunching QuakMeeting...")
            install_btn.setVisible(False)
            updating_hud.set_installed()

        def _on_failed(error=None, **k):
            update_icon_lbl.setText("❌")
            update_status_lbl.setText(f"<span style='color:#f87171;'>Installation failed: {error or 'Unknown error'}</span>")
            install_btn.setText("🔄 Try Again")
            install_btn.setEnabled(True)
            install_btn.setVisible(True)
            updating_hud.setVisible(False)

        def _on_install_clicked():
            install_btn.setText("⏳ Preparing download...")
            install_btn.setEnabled(False)
            updater_service.download_and_install_update(background=True)

        install_btn.clicked.connect(_on_install_clicked)

        self.update_bridge = QtUpdateBridge(self)

        def _on_bridge_event(event_name: str, data: dict):
            if event_name == "CALENDAR_SYNCED":
                self.sync_btn.stop_spinning("✅ Synced!", is_success=True, reset_delay_ms=2000)
                self._refresh_agenda(data.get("meetings"))
            elif event_name == "UPDATE_AVAILABLE":
                _on_update_avail(**data)
            elif event_name == "UPDATE_CHECK_COMPLETE":
                _on_update_complete(**data)
            elif event_name == "UPDATE_DOWNLOADING":
                _on_downloading(**data)
            elif event_name == "UPDATE_DOWNLOAD_PROGRESS":
                _on_download_progress(**data)
            elif event_name == "UPDATE_DOWNLOADED":
                _on_downloaded(**data)
            elif event_name == "UPDATE_INSTALLED":
                _on_installed(**data)
            elif event_name == "UPDATE_FAILED":
                _on_failed(**data)

        self.update_bridge.update_event.connect(_on_bridge_event)

        event_bus.subscribe("UPDATE_AVAILABLE", lambda **k: self.update_bridge.update_event.emit("UPDATE_AVAILABLE", k))
        event_bus.subscribe("UPDATE_CHECK_COMPLETE", lambda **k: self.update_bridge.update_event.emit("UPDATE_CHECK_COMPLETE", k))
        event_bus.subscribe("UPDATE_DOWNLOADING", lambda **k: self.update_bridge.update_event.emit("UPDATE_DOWNLOADING", k))
        event_bus.subscribe("UPDATE_DOWNLOAD_PROGRESS", lambda **k: self.update_bridge.update_event.emit("UPDATE_DOWNLOAD_PROGRESS", k))
        event_bus.subscribe("UPDATE_DOWNLOADED", lambda **k: self.update_bridge.update_event.emit("UPDATE_DOWNLOADED", k))
        event_bus.subscribe("UPDATE_INSTALLED", lambda **k: self.update_bridge.update_event.emit("UPDATE_INSTALLED", k))
        event_bus.subscribe("UPDATE_FAILED", lambda **k: self.update_bridge.update_event.emit("UPDATE_FAILED", k))
        event_bus.subscribe("CALENDAR_SYNCED", lambda **k: self.update_bridge.update_event.emit("CALENDAR_SYNCED", k))

        # Initialize with current release info if already available
        if updater_service.latest_release_info and updater_service.latest_release_info.get("has_update"):
            _on_update_avail(**updater_service.latest_release_info)

        pref_layout.addWidget(util_card)

        pref_layout.addStretch()

        pref_scroll = QScrollArea()
        pref_scroll.setWidgetResizable(True)
        pref_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pref_scroll.setStyleSheet("QScrollArea { background: transparent; }")
        pref_scroll.setWidget(pref_widget)

        self.tabs.addTab(pref_scroll, "⚙️ Preferences")

        self.tabs.setCurrentIndex(tab_index)
        main_layout.addWidget(self.tabs)

    def _refresh_agenda(self, meetings=None):
        # Clear layout safely
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        now = datetime.now().astimezone()
        if meetings is None:
            meetings = calendar_service.get_upcoming_meetings()
            
        today_meets = [m for m in meetings if m.start_time and m.start_time.astimezone().date() == now.date()]

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
            self.scroll_layout.addLayout(empty_box)
        else:
            for idx, m in enumerate(today_meets):
                card = QFrame(self.scroll_content)
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

                st = m.start_time.astimezone().strftime("%H:%M") if m.start_time else "--:--"
                et = m.end_time.astimezone().strftime("%H:%M") if m.end_time else ""
                dur_str = f" ({format_duration(m.duration_minutes)})" if m.duration_minutes else ""

                t_l = QLabel(m.title, card)
                t_l.setObjectName("CardTitle")

                sub_txt = f"<b style='color:#38bdf8;'>{st} - {et}{dur_str}</b>  •  {m.provider}"
                if m.is_travel and m.departure_time:
                    sub_txt += f"  •  <span style='color:#fbbf24;'>🚗 Leave at {m.departure_time.astimezone().strftime('%H:%M')}</span>"
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

                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)



_dashboard_instance = None

def show_qt_dashboard(tab_index: int = 0):
    """Launches the PyQt6 Flight Deck Control Center."""
    import logging
    logger = logging.getLogger("QuakMeeting.FlightDeck")
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

