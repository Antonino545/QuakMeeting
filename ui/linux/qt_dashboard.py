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
    QProgressBar, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon, QPainter

from ui.linux.animated_widgets import (
    BouncingMascotLabel, AnimatedSpinButton, AnimatedUpdateCard, UpdatingHUDWidget, ToggleSwitch
)

class QtUpdateBridge(QObject):
    update_event = pyqtSignal(str, dict)

from core.services.config_service import config, is_debug_mode
from core.services.calendar_service import calendar_service
from core.services.updater_service import updater_service
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from core.services.event_bus import event_bus
from core.domain.models import format_duration, Meeting
from core.logger import open_log_file, open_log_folder

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
    border: 1px solid #45475a; /* Surface1 */
    font-size: 12px;
    font-weight: 600;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton#OutlineBtn:hover {
    background-color: #45475a; /* Surface1 */
    border-color: #89b4fa;
}

QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Modern Segmented Control for Transport Modes */
QPushButton#SegmentBtn {
    background-color: transparent;
    color: #a6adc8;
    font-weight: bold;
    font-size: 13px;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton#SegmentBtn:hover {
    background-color: rgba(205, 214, 244, 0.05);
}
QPushButton#SegmentBtn:checked {
    background-color: #313244; /* Surface0 */
    color: #cba6f7; /* Mauve */
}

/* Inputs and Dropdowns (Catppuccin) */
QLineEdit {
    background-color: #181825; /* Mantle */
    color: #cdd6f4; /* Text */
    border: 1px solid #313244; /* Surface0 */
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
    selection-background-color: #cba6f7;
    selection-color: #11111b;
}
QLineEdit:focus {
    border-color: #89b4fa; /* Blue */
    background-color: #11111b; /* Crust */
}

QComboBox {
    background-color: #181825; /* Mantle */
    color: #cdd6f4; /* Text */
    border: 1px solid #313244; /* Surface0 */
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    min-width: 140px;
}
QComboBox:hover {
    border-color: #45475a; /* Surface1 */
}
QComboBox:focus {
    border-color: #89b4fa; /* Blue */
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #181825; /* Mantle */
    color: #cdd6f4; /* Text */
    border: 1px solid #313244; /* Surface0 */
    selection-background-color: #313244; /* Surface0 */
    selection-color: #cba6f7; /* Mauve */
    border-radius: 6px;
    padding: 4px;
}

/* ScrollBar styling (Catppuccin) */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #45475a; /* Surface1 */
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70; /* Surface2 */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 0px;
    border: none;
    background: transparent;
}
QScrollBar::handle:horizontal {
    height: 0px;
    background: transparent;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    height: 0px;
}

QStatusBar {
    background: transparent;
    border: none;
    max-height: 0px;
}
QSizeGrip {
    width: 0px;
    height: 0px;
    background: transparent;
}
"""

class QtMascotMiniWidget(QFrame):
    def __init__(self, animal="duck", outfit="aviator", parent=None):
        super().__init__(parent)
        self.animal = animal
        self.outfit = outfit
        self.tick = 0
        self.setFixedSize(68, 64)
        self.setStyleSheet("""
            QFrame {
                background: #11111b;
                border: 1px solid #313244;
                border-radius: 8px;
            }
        """)

    def update_mascot(self, animal, outfit):
        self.animal = animal
        self.outfit = outfit
        self.update()

    def update_animal(self, animal):
        self.animal = animal
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w = self.width()
        h = self.height()
        p.save()
        p.translate(w * 0.5 - 2, h * 0.5 - 2)
        p.scale(0.68, -0.68)
        from ui.linux.banner.renderers.modular_renderer import QtModularRenderer
        renderer = QtModularRenderer(animal=self.animal, outfit=self.outfit)
        renderer.draw_pilot(p, 0, 0, self.tick)
        p.restore()

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

        # 3. Stacked Pages
        self.stacked_widget = QStackedWidget(central_widget)

        # --- TAB 1: Today's Agenda ---
        agenda_widget = QWidget()
        agenda_layout = QVBoxLayout(agenda_widget)
        agenda_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(agenda_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)
        
        self.scroll = scroll
        self._refresh_agenda()
        agenda_layout.addWidget(scroll)
        self.stacked_widget.addWidget(agenda_widget)

        # --- TAB 2: Pilot Hangar ---
        hangar_widget = QWidget()
        hangar_layout = QVBoxLayout(hangar_widget)
        hangar_layout.setContentsMargins(0, 0, 0, 0)

        self.h_scroll = QScrollArea(hangar_widget)
        self.h_scroll.setWidgetResizable(True)
        self.h_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.h_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.h_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.h_content = QWidget()
        self.h_layout = QVBoxLayout(self.h_content)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(12)

        self._refresh_hangar()
        self.h_scroll.setWidget(self.h_content)
        hangar_layout.addWidget(self.h_scroll)
        self.stacked_widget.addWidget(hangar_widget)

        # --- TAB 3: Preferences ---
        pref_widget = QWidget()
        pref_layout = QVBoxLayout(pref_widget)
        pref_layout.setContentsMargins(0, 0, 0, 0)
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

        # 1-Click Timing Presets Row
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_lbl = QLabel("<b>⚡ Quick Presets:</b>", timing_card)
        preset_lbl.setStyleSheet("color: #a6adc8; font-size: 11.5px;")
        preset_row.addWidget(preset_lbl)

        presets = [
            ("🧘 Relaxed", [15, 5, 0], [15, 5, 0], [45, 15, 0]),
            ("⚡ Standard", [20, 10, 5, 2, 0], [20, 10, 5, 2, 0], [45, 30, 15, 5, 2, 0]),
            ("🚨 Intensive", [30, 20, 15, 10, 5, 2, 0], [30, 20, 15, 10, 5, 2, 0], [60, 45, 30, 15, 5, 2, 0]),
        ]

        stage_buttons = {}

        def _apply_preset(p_meetings, p_general, p_travel):
            config.set("meeting_reminder_stages", p_meetings)
            config.set("general_reminder_stages", p_general)
            config.set("travel_reminder_stages", p_travel)
            for (k, v), btn in stage_buttons.items():
                if k == "meeting_reminder_stages":
                    btn.setChecked(v in p_meetings)
                elif k == "general_reminder_stages":
                    btn.setChecked(v in p_general)
                elif k == "travel_reminder_stages":
                    btn.setChecked(v in p_travel)

        for p_name, p_m, p_g, p_t in presets:
            p_btn = QPushButton(p_name, timing_card)
            p_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_btn.setStyleSheet("""
                QPushButton {
                    background: #242438;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 7px;
                    padding: 4px 10px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #313244;
                    border-color: #89b4fa;
                    color: #ffffff;
                }
            """)
            p_btn.clicked.connect(lambda _, m=p_m, g=p_g, t=p_t: _apply_preset(m, g, t))
            preset_row.addWidget(p_btn)

        preset_row.addStretch()
        tc_layout.addLayout(preset_row)

        tc_div_pre = QFrame(timing_card)
        tc_div_pre.setFixedHeight(1)
        tc_div_pre.setStyleSheet("background-color: #313244;")
        tc_layout.addWidget(tc_div_pre)

        def create_stage_row(title, desc, config_key, opts, accent_color="#cba6f7"):
            row_layout = QVBoxLayout()
            row_layout.setSpacing(4)
            lbl = QLabel(f"<b>{title}</b>", timing_card)
            lbl.setStyleSheet("color: #cdd6f4; font-size: 12px;")
            desc_lbl = QLabel(desc, timing_card)
            desc_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
            row_layout.addWidget(lbl)
            row_layout.addWidget(desc_lbl)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            curr_stages = set(config.get(config_key, [20, 10, 5, 2, 0]))

            for val, label in opts:
                chk = QPushButton(label, timing_card)
                chk.setCheckable(True)
                chk.setCursor(Qt.CursorShape.PointingHandCursor)
                chk.setChecked(val in curr_stages)
                stage_buttons[(config_key, val)] = chk
                chk.setStyleSheet(f"""
                    QPushButton {{
                        background: #242438;
                        color: #cdd6f4;
                        border: 1px solid #45475a;
                        border-radius: 7px;
                        padding: 5px 14px;
                        font-size: 11.5px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: #313244;
                        border-color: {accent_color};
                    }}
                    QPushButton:checked {{
                        background: {accent_color};
                        color: #11111b;
                        font-weight: bold;
                        border: 1px solid {accent_color};
                    }}
                """)
                def _toggled(checked, v=val, k=config_key):
                    c = set(config.get(k, []))
                    if checked: c.add(v)
                    else: c.discard(v)
                    c.add(0)
                    config.set(k, sorted(list(c), reverse=True))
                chk.toggled.connect(_toggled)
                btn_layout.addWidget(chk)

            btn_layout.addStretch()
            row_layout.addLayout(btn_layout)
            return row_layout

        meeting_opts = [(30, "30m"), (20, "20m"), (15, "15m"), (10, "10m"), (5, "5m"), (2, "2m")]
        travel_opts = [(60, "60m"), (45, "45m"), (30, "30m"), (15, "15m"), (5, "5m"), (2, "2m")]

        tc_layout.addLayout(create_stage_row("📹 Video Meetings", "Alert ahead of meeting start (0m is always on)", "meeting_reminder_stages", meeting_opts, accent_color="#cba6f7"))

        tc_div1 = QFrame(timing_card)
        tc_div1.setFixedHeight(1)
        tc_div1.setStyleSheet("background-color: #313244;")
        tc_layout.addWidget(tc_div1)

        tc_layout.addLayout(create_stage_row("📅 General Events", "Alert ahead of start time (0m is always on)", "general_reminder_stages", meeting_opts, accent_color="#89b4fa"))

        tc_div2 = QFrame(timing_card)
        tc_div2.setFixedHeight(1)
        tc_div2.setStyleSheet("background-color: #313244;")
        tc_layout.addWidget(tc_div2)

        tc_layout.addLayout(create_stage_row("🚗 Travel & Trips", "Alert ahead of leave time (0m is always on)", "travel_reminder_stages", travel_opts, accent_color="#fab387"))

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
        addr_row_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        ac_layout.addWidget(addr_row_lbl)

        entry_row = QHBoxLayout()
        addr_entry = QLineEdit(addr_card)
        addr_entry.setText(config.get("home_address", "") or "")
        addr_entry.setPlaceholderText("e.g. Piazza Castello, Torino or Via Roma, Torino")

        save_addr_btn = QPushButton("💾 Save Location", addr_card)
        save_addr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_addr_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a6e3a1, stop:1 #94e2d5);
                color: #11111b;
                font-weight: bold;
                font-size: 12px;
                border-radius: 8px;
                padding: 7px 16px;
                border: 1px solid #a6e3a1;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #94e2d5, stop:1 #a6e3a1);
                border: 1px solid #94e2d5;
            }
        """)
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
        mode_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; margin-top: 4px;")
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
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #74c7ec, stop:1 #89b4fa);
                            color: #11111b;
                            font-weight: bold;
                            font-size: 12px;
                            border: 1px solid #74c7ec;
                            border-radius: 8px;
                            padding: 8px 14px;
                        }
                    """)
                else:
                    b.setStyleSheet("""
                        QPushButton {
                            background: #313244;
                            color: #bac2de;
                            border: 1px solid #45475a;
                            border-radius: 8px;
                            padding: 8px 14px;
                            font-size: 12px;
                            font-weight: 500;
                        }
                        QPushButton:hover {
                            background: #45475a;
                            color: #cdd6f4;
                            border-color: #89b4fa;
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
        buf_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px;")

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
        sim_box.setStyleSheet("background: rgba(137, 180, 250, 0.06); border: 1px solid rgba(137, 180, 250, 0.2); border-radius: 10px; padding: 6px;")
        sim_layout = QVBoxLayout(sim_box)
        sim_layout.setContentsMargins(10, 8, 10, 8)
        sim_layout.setSpacing(6)

        sim_title = QLabel("🧪 Live Route & Departure Banner Test (Politecnico di Torino)", sim_box)
        sim_title.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 12px; border: none;")
        sim_layout.addWidget(sim_title)

        sim_act_row = QHBoxLayout()
        sim_info_lbl = QLabel("Calculate real-time transit & launch a live on-screen flight banner:", sim_box)
        sim_info_lbl.setStyleSheet("color: #a6adc8; font-size: 11px; border: none;")
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
        test_dep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_dep_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #74c7ec, stop:1 #89b4fa);
                color: #11111b;
                font-weight: bold;
                font-size: 12px;
                border-radius: 8px;
                padding: 7px 16px;
                border: 1px solid #74c7ec;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #74c7ec);
                border: 1px solid #89b4fa;
            }
        """)
        test_dep_btn.clicked.connect(_test_polito_banner)
        sim_act_row.addWidget(test_dep_btn)

        sim_box.setVisible(is_debug_mode())
        sim_layout.addLayout(sim_act_row)
        ac_layout.addWidget(sim_box)

        pref_layout.addWidget(addr_card)

        # --- Included Calendars Card ---
        cals_card = QFrame(pref_widget)
        cals_card.setObjectName("Card")
        cc_layout = QVBoxLayout(cals_card)
        cc_layout.setContentsMargins(18, 14, 18, 14)
        cc_layout.setSpacing(10)

        cc_title = QLabel("📅 Included System Calendars", cals_card)
        cc_title.setObjectName("CardTitle")
        cc_sub = QLabel("Select which local, EDS, or CalDAV calendars to actively monitor for reminders.", cals_card)
        cc_sub.setObjectName("CardSub")
        cc_layout.addWidget(cc_title)
        cc_layout.addWidget(cc_sub)

        avail_cals = calendar_service.get_available_calendars()
        if not avail_cals:
            empty_lbl = QLabel("All calendar sources are currently monitored.", cals_card)
            empty_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
            cc_layout.addWidget(empty_lbl)
        else:
            grid_widget = QWidget(cals_card)
            grid_layout = QVBoxLayout(grid_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(8)

            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            count_in_row = 0

            for cal in avail_cals:
                c_name = cal.get("name", "Calendar")
                c_enabled = cal.get("enabled", True)
                btn = QPushButton(f"📅 {c_name}", grid_widget)
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setChecked(c_enabled)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #242438;
                        color: #cdd6f4;
                        border: 1px solid #45475a;
                        border-radius: 7px;
                        padding: 6px 14px;
                        font-size: 11.5px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background: #313244;
                        border-color: #a6e3a1;
                    }
                    QPushButton:checked {
                        background: #a6e3a1;
                        color: #11111b;
                        font-weight: bold;
                        border: 1px solid #a6e3a1;
                    }
                """)
                def _cal_toggled(checked, name=c_name):
                    ignored = set(config.get("ignored_calendars", []))
                    if checked:
                        ignored.discard(name)
                    else:
                        ignored.add(name)
                    config.set("ignored_calendars", list(ignored))
                btn.toggled.connect(_cal_toggled)

                row_layout.addWidget(btn)
                count_in_row += 1
                if count_in_row >= 3:
                    row_layout.addStretch()
                    grid_layout.addLayout(row_layout)
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(8)
                    count_in_row = 0

            if count_in_row > 0:
                row_layout.addStretch()
                grid_layout.addLayout(row_layout)

            cc_layout.addWidget(grid_widget)

        pref_layout.addWidget(cals_card)

        # Utilities
        util_card = QFrame(pref_widget)
        util_card.setObjectName("Card")
        uc_layout = QVBoxLayout(util_card)
        uc_layout.setContentsMargins(18, 14, 18, 14)
        uc_layout.setSpacing(10)

        uc_title = QLabel("⚙️ System, Language & Diagnostics" if is_debug_mode() else "⚙️ System & Language", util_card)
        uc_title.setObjectName("CardTitle")
        uc_layout.addWidget(uc_title)

        # Language Selector Row
        lang_box = QVBoxLayout()
        lang_box.setSpacing(6)
        lang_lbl = QLabel("🌐 Language / Lingua dell'Applicazione:", util_card)
        lang_lbl.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
        lang_box.addWidget(lang_lbl)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)
        langs = [
            ("system", "🌐 System (Auto)"),
            ("en", "🇬🇧 English"),
            ("it", "🇮🇹 Italiano")
        ]
        curr_lang = config.get("language", "system")
        lang_buttons = {}

        def _update_lang_ui(sel_l):
            for lk, lb in lang_buttons.items():
                if lk == sel_l:
                    lb.setStyleSheet("""
                        QPushButton {
                            background-color: #cba6f7;
                            color: #11111b;
                            font-weight: bold;
                            border: 1px solid #b4befe;
                            border-radius: 6px;
                            padding: 6px 12px;
                            font-size: 12px;
                        }
                    """)
                else:
                    lb.setStyleSheet("""
                        QPushButton {
                            background-color: #313244;
                            color: #cdd6f4;
                            border: 1px solid #45475a;
                            border-radius: 6px;
                            padding: 6px 12px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #45475a;
                        }
                    """)

        def _make_lang_cb(lkey):
            def _cb():
                config.set("language", lkey)
                _update_lang_ui(lkey)
                event_bus.publish("CONFIG_CHANGED", key="language", value=lkey)
                self.render_hangar_tab()
            return _cb

        for lk, ltitle in langs:
            lbtn = QPushButton(ltitle, util_card)
            lbtn.setCursor(Qt.CursorShape.PointingHandCursor)
            lbtn.clicked.connect(_make_lang_cb(lk))
            lang_buttons[lk] = lbtn
            lang_row.addWidget(lbtn)

        _update_lang_ui(curr_lang)
        lang_box.addLayout(lang_row)
        uc_layout.addLayout(lang_box)
        uc_layout.addSpacing(6)

        autostart_row = QHBoxLayout()
        autostart_lbl = QLabel("🚀 Launch QuakMeeting automatically at Linux login", util_card)
        autostart_lbl.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
        
        autostart_sw = ToggleSwitch(is_autostart_enabled(), util_card)
        def _toggle_autostart(checked):
            if checked: enable_autostart()
            else: disable_autostart()
        autostart_sw.toggled = _toggle_autostart
        
        autostart_row.addWidget(autostart_lbl)
        autostart_row.addStretch()
        autostart_row.addWidget(autostart_sw)
        uc_layout.addLayout(autostart_row)
        uc_layout.addSpacing(6)

        # Debug / Developer Mode Toggle (Visible only when debug mode is enabled or active)
        dbg_container = QWidget(util_card)
        dbg_row = QHBoxLayout(dbg_container)
        dbg_row.setContentsMargins(0, 0, 0, 0)
        dbg_lbl = QLabel("🐛 Enable Developer & Debug Diagnostics Mode", dbg_container)
        dbg_lbl.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")

        dbg_sw = ToggleSwitch(is_debug_mode(), dbg_container)
        def _toggle_debug(checked):
            config.set("debug_mode", checked)
            sim_box.setVisible(checked)
            edit_btn.setVisible(checked)
            log_btn.setVisible(checked)
            demo_up_btn.setVisible(checked)
            dbg_container.setVisible(checked)
            uc_title.setText("⚙️ System, Language & Diagnostics" if checked else "⚙️ System & Language")
            self._refresh_hangar()
        dbg_sw.toggled = _toggle_debug

        dbg_row.addWidget(dbg_lbl)
        dbg_row.addStretch()
        dbg_row.addWidget(dbg_sw)
        dbg_container.setVisible(is_debug_mode())
        uc_layout.addWidget(dbg_container)
        uc_layout.addSpacing(6)
        
        sys_row = QHBoxLayout()

        edit_btn = QPushButton("📝 Edit Config JSON", util_card)
        edit_btn.setObjectName("OutlineBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda chk=False: config.open_config_in_editor())
        edit_btn.setVisible(is_debug_mode())

        log_btn = QPushButton("📄 View Live Log File", util_card)
        log_btn.setObjectName("OutlineBtn")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(lambda chk=False: open_log_file())
        log_btn.setVisible(is_debug_mode())

        up_btn = AnimatedSpinButton("🔍 Check for Updates", util_card)
        up_btn.setObjectName("OutlineBtn")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        demo_up_btn = QPushButton("🎬 Test Update Animation", util_card)
        demo_up_btn.setObjectName("OutlineBtn")
        demo_up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_up_btn.setToolTip("Preview the live rocket jet download & installation animation sequence")
        demo_up_btn.setVisible(is_debug_mode())

        def _on_show_license():
            from core.services.language_service import t
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle(t("license_title"))
            msg.setText(f"<h3>🦆 QuakMeeting v{updater_service.current_version}</h3>"
                        f"<p>{t('license_body').replace(chr(10), '<br>')}</p>")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e2e;
                    color: #cdd6f4;
                }
                QLabel {
                    color: #cdd6f4;
                    font-size: 12px;
                }
                QPushButton {
                    background-color: #89b4fa;
                    color: #11111b;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 6px 14px;
                }
            """)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        lic_btn = QPushButton("📜 License & Info", util_card)
        lic_btn.setObjectName("OutlineBtn")
        lic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lic_btn.clicked.connect(_on_show_license)

        sys_row.addWidget(up_btn)
        sys_row.addWidget(edit_btn)
        sys_row.addWidget(log_btn)
        sys_row.addWidget(demo_up_btn)
        sys_row.addWidget(lic_btn)
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

        update_status_lbl = QLabel(f"QuakMeeting <b>v{updater_service.current_version}</b>  •  <span style='color:#a6adc8;'>Ready</span>", update_status_box)
        update_status_lbl.setStyleSheet("color: #cdd6f4; font-size: 13px; border: none;")
        status_header_row.addWidget(update_status_lbl, stretch=1)
        usb_layout.addLayout(status_header_row)

        changelog_lbl = QLabel("", update_status_box)
        changelog_lbl.setWordWrap(True)
        changelog_lbl.setStyleSheet("color: #bac2de; font-size: 11px; border: none; padding-left: 2px;")
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #74c7ec, stop:1 #89b4fa);
                color: #11111b;
                font-weight: bold;
                font-size: 12px;
                border-radius: 8px;
                padding: 8px 16px;
                border: 1px solid #74c7ec;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #89b4fa);
                border: 1px solid #89b4fa;
            }
            QPushButton:disabled {
                background: rgba(205, 214, 244, 0.08);
                color: #6c7086;
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
            update_status_lbl.setText("<span style='color:#89b4fa;'><b>Scanning GitHub repository for releases...</b></span>")
            updater_service.check_for_updates(background=True)

        up_btn.clicked.connect(_on_check_clicked)

        def _on_update_avail(version=None, tag_name=None, name=None, body=None, **k):
            up_btn.stop_spinning("🔍 Check for Updates")
            v_name = tag_name or version or "New Version"
            update_status_box.set_update_available(v_name)
            update_icon_lbl.setText("🚀")
            update_status_lbl.setText(f"<b style='color:#89b4fa;'>Update Available: {v_name}</b>  <span style='color:#6c7086;'>(Current: v{updater_service.current_version})</span>")
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
                    update_status_lbl.setText(f"<span style='color:#f38ba8;'>Update check error: {error[:60]}</span>")
                else:
                    up_btn.stop_spinning("✨ Up to date", is_success=True, reset_delay_ms=2500)
                    update_status_box.set_up_to_date()
                    update_icon_lbl.setText("✨")
                    update_status_lbl.setText(f"<span style='color:#a6e3a1;'><b>You are on the latest version!</b></span>  <b>v{current_version or updater_service.current_version}</b>")
                install_btn.setVisible(False)
                changelog_lbl.setVisible(False)

        def _on_downloading(file_name=None, **k):
            update_icon_lbl.setText("📥")
            update_status_lbl.setText(f"<b>Downloading update package...</b> <span style='color:#a6adc8;'>({file_name or ''})</span>")
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
            update_status_lbl.setText("<b style='color:#a6e3a1;'>Update installed successfully!</b> Relaunching QuakMeeting...")
            install_btn.setVisible(False)
            updating_hud.set_installed()

        def _on_failed(error=None, **k):
            update_icon_lbl.setText("❌")
            update_status_lbl.setText(f"<span style='color:#f38ba8;'>Installation failed: {error or 'Unknown error'}</span>")
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
        pref_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pref_scroll.setStyleSheet("QScrollArea { background: transparent; }")
        pref_scroll.setWidget(pref_widget)

        self.stacked_widget.addWidget(pref_scroll)

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
        main_layout.addWidget(self.stacked_widget, stretch=1)

    def set_active_tab(self, index: int):
        """Switches the active tab and updates navbar segment button states."""
        self.current_tab_index = index
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(getattr(self, 'nav_buttons', [])):
            is_active = (i == index)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

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
            e_msg.setStyleSheet("font-size: 15px; font-weight: bold; color: #bac2de; border: none;")
            e_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_box.addWidget(e_icon)
            empty_box.addWidget(e_msg)
            self.scroll_layout.addLayout(empty_box)
        else:
            for idx, m in enumerate(today_meets):
                card = QFrame(self.scroll_content)
                card.setObjectName("Card")
                card.setStyleSheet("""
                    QFrame#Card {
                        background-color: #1e1e2e;
                        border: 1px solid #313244;
                        border-radius: 12px;
                    }
                    QFrame#Card:hover {
                        background-color: #181825;
                        border: 1px solid #cba6f7;
                    }
                """)
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(18, 14, 18, 14)
                c_layout.setSpacing(14)

                pilot_icon = "🦆"
                if m.pilot_type == "chef": pilot_icon = "🍕"
                elif m.pilot_type == "captain": pilot_icon = "✈️"
                elif m.pilot_type == "owl": pilot_icon = "🎓"
                elif m.pilot_type == "gym": pilot_icon = "🏋️‍♂️"
                elif m.pilot_type == "driver": pilot_icon = "🚗"
                elif m.pilot_type == "zen_duck": pilot_icon = "🛋️"

                icon_l = QLabel(pilot_icon, card)
                icon_l.setStyleSheet("font-size: 26px; border: none; background: transparent;")
                c_layout.addWidget(icon_l)

                info_box = QVBoxLayout()
                info_box.setSpacing(2)

                st = m.start_time.astimezone().strftime("%H:%M") if m.start_time else "--:--"
                et = m.end_time.astimezone().strftime("%H:%M") if m.end_time else ""
                dur_str = f" ({format_duration(m.duration_minutes)})" if m.duration_minutes else ""

                t_l = QLabel(f"{st} - {et}  •  {m.title}", card)
                t_l.setObjectName("CardTitle")
                t_l.setStyleSheet("font-size: 14px; font-weight: 700; color: #cdd6f4; border: none; background: transparent;")

                sub_txt = m.provider
                if m.location and m.location != "missing value":
                    sub_txt += f"  •  📍 {m.location[:35]}"
                if m.is_travel and m.departure_time:
                    sub_txt += f"  •  <span style='color:#f9e2af;'>🚗 Leave at {m.departure_time.astimezone().strftime('%H:%M')}</span>"
                if m.classroom:
                    sub_txt += f"  •  <span style='color:#cba6f7;'>🏫 {m.classroom}</span>"

                s_l = QLabel(sub_txt, card)
                s_l.setObjectName("CardSub")
                s_l.setStyleSheet("font-size: 11.5px; color: #a6adc8; border: none; background: transparent;")

                info_box.addWidget(t_l)
                info_box.addWidget(s_l)
                c_layout.addLayout(info_box, stretch=1)

                action_url = m.action_url or m.meeting_url
                if not action_url and m.location and m.location != "missing value":
                    import urllib.parse
                    action_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(m.location)}"
                    m.action_url = action_url

                has_real_url = bool(action_url and action_url.strip() and action_url != "https://calendar.apple.com")
                if has_real_url:
                    btn_text = m.action_btn_text or ("🚀 Join" if not m.is_travel else "🗺️ Maps")
                    btn = QPushButton(btn_text, card)
                    btn.setObjectName("PrimaryBtn")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #89b4fa;
                            color: #11111b;
                            font-size: 12px;
                            font-weight: bold;
                            border: 1px solid #89b4fa;
                            border-radius: 8px;
                            padding: 6px 14px;
                        }
                        QPushButton:hover {
                            background-color: #b4befe;
                            border-color: #b4befe;
                        }
                    """)
                    btn.clicked.connect(lambda chk, u=action_url: webbrowser.open(u))
                    c_layout.addWidget(btn)

                    copy_btn = QPushButton("📋 Copy", card)
                    copy_btn.setObjectName("OutlineBtn")
                    copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    copy_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #313244;
                            color: #cdd6f4;
                            border: 1px solid #45475a;
                            font-size: 12px;
                            font-weight: 600;
                            border-radius: 8px;
                            padding: 6px 12px;
                        }
                        QPushButton:hover {
                            background-color: #45475a;
                            border-color: #89b4fa;
                        }
                    """)
                    def _copy_url(url=action_url, b=copy_btn):
                        QApplication.clipboard().setText(url)
                        b.setText("✓ Copied!")
                        QTimer.singleShot(1500, lambda: b.setText("📋 Copy"))
                    copy_btn.clicked.connect(lambda chk, u=action_url, b=copy_btn: _copy_url(u, b))
                    c_layout.addWidget(copy_btn)

                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)

    def render_hangar_tab(self):
        self._refresh_hangar()

    def _refresh_hangar(self):
        # Clear layout safely
        while self.h_layout.count():
            child = self.h_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 1. Header Toolbar
        customs = config.get("mascot_customization", {})
        header_card = QFrame(self.h_content)
        header_card.setObjectName("HeaderCard")
        header_card.setStyleSheet("""
            QFrame#HeaderCard {
                background: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 12px;
            }
        """)
        r_box = QHBoxLayout(header_card)
        r_box.setContentsMargins(18, 10, 18, 10)
        r_box.setSpacing(10)

        r_title = QLabel("🦆 Mascot Workshop & Pilot Hangar", header_card)
        r_title.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13.5px;")
        r_box.addWidget(r_title, stretch=1)

        def _on_surprise():
            import random
            all_a = [a[0] for a in ANIMALS]
            c_dict = config.get("mascot_customization", {})
            if not isinstance(c_dict, dict):
                c_dict = {}
            for ck, _, _, fixed_outfit, _, _ in CATEGORIES:
                c_dict[ck] = {"animal": random.choice(all_a), "outfit": fixed_outfit}
            config.set("mascot_customization", c_dict)
            event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=c_dict)
            self.render_hangar_tab()

        def _on_reset():
            defs = {
                "study": {"animal": "owl", "outfit": "student"},
                "food": {"animal": "duck", "outfit": "chef"},
                "travel": {"animal": "duck", "outfit": "captain"},
                "sport": {"animal": "bunny", "outfit": "gym"},
                "in_person": {"animal": "squirrel", "outfit": "racer"},
                "health": {"animal": "bunny", "outfit": "zen"},
                "general": {"animal": "duck", "outfit": "aviator"}
            }
            config.set("mascot_customization", defs)
            event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=defs)
            self.render_hangar_tab()

        sur_btn = QPushButton("🎲 Surprise Me", header_card)
        sur_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sur_btn.setStyleSheet("background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        sur_btn.clicked.connect(_on_surprise)
        r_box.addWidget(sur_btn)

        res_btn = QPushButton("🔄 Reset Presets", header_card)
        res_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        res_btn.setStyleSheet("background: #313244; color: #a6adc8; border: 1px solid #45475a; border-radius: 6px; padding: 5px 12px; font-size: 11px;")
        res_btn.clicked.connect(_on_reset)
        r_box.addWidget(res_btn)

        self.h_layout.addWidget(header_card)

        # 2. Category Mascot Customizer Cards
        ANIMALS = [
            ("duck", "🦆 Aviator Duck"),
            ("owl", "🦉 Academic Owl"),
            ("bunny", "🐰 Clever Bunny"),
            ("platypus", "🕵️‍♂️ Secret Platypus"),
            ("squirrel", "🐿️ Hyper Squirrel")
        ]

        CATEGORIES = [
            ("study", "🎓 University & Study Sessions", "Lectures, exams, self-study, homework & thesis.", "student", "owl", "#cba6f7"),
            ("food", "🍕 Dining, Lunch & Restaurants", "Dinners, lunch dates, pizzerias & food routes.", "chef", "duck", "#fab387"),
            ("travel", "✈️ Travel, Flights & Trains", "Airports, flights, high-speed trains & trips.", "captain", "duck", "#74c7ec"),
            ("sport", "🏋️ Gym, Palestra & Sports", "Workouts, crossfit, padel, tennis & running.", "gym", "bunny", "#f38ba8"),
            ("in_person", "🏎️ In-Person & Commute", "Doctor visits, dentist & real-time navigation.", "racer", "squirrel", "#f9e2af"),
            ("health", "🌸 Wellness & Therapy", "Serenis sessions, yoga, meditation & calm.", "zen", "bunny", "#94e2d5"),
            ("general", "⏰ General Meetings & Reminders", "Video conferences (Meet, Zoom, Teams) & alerts.", "aviator", "duck", "#a6e3a1")
        ]

        for idx, (cat_key, cat_title, cat_desc, fixed_outfit, def_animal, cat_color) in enumerate(CATEGORIES):
            current_setting = customs.get(cat_key, {})
            current_animal = current_setting.get("animal", def_animal) if isinstance(current_setting, dict) else (current_setting or def_animal)

            card = QFrame(self.h_content)
            card.setObjectName("Card")
            card.setStyleSheet(f"""
                QFrame#Card {{
                    background: #181825;
                    border: 1px solid #313244;
                    border-left: 4px solid {cat_color};
                    border-radius: 10px;
                }}
            """)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(14, 12, 18, 12)
            c_layout.setSpacing(14)

            # Mini Canvas Preview on Left
            mini_preview = QtMascotMiniWidget(animal=current_animal, outfit=fixed_outfit, parent=card)
            c_layout.addWidget(mini_preview)

            p_box = QVBoxLayout()
            p_box.setSpacing(2)
            n_l = QLabel(cat_title, card)
            n_l.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
            d_l = QLabel(f"{cat_desc}  •  <span style='color:{cat_color}; font-weight:bold;'>✨ Active Pilot: {current_animal.capitalize()}</span>", card)
            d_l.setStyleSheet("color: #a6adc8; font-size: 11px;")
            p_box.addWidget(n_l)
            p_box.addWidget(d_l)
            c_layout.addLayout(p_box, stretch=1)

            # Controls Box: Label on top, ComboBox and Test Button side-by-side on same baseline
            ctrl_box = QVBoxLayout()
            ctrl_box.setSpacing(3)
            a_lbl = QLabel("Animal Mascot:", card)
            a_lbl.setStyleSheet("color: #a6adc8; font-size: 10px; font-weight: bold;")
            ctrl_box.addWidget(a_lbl)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            a_combo = QComboBox(card)
            for a_id, a_name in ANIMALS:
                a_combo.addItem(a_name, a_id)
            a_idx = next((i for i, (a_id, _) in enumerate(ANIMALS) if a_id == current_animal), 0)
            a_combo.setCurrentIndex(a_idx)
            a_combo.setFixedHeight(32)
            a_combo.setStyleSheet("""
                QComboBox {
                    background: #313244;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11.5px;
                    min-width: 145px;
                }
            """)
            def _make_animal_cb(ck, fo):
                def _on_a_changed(i_val):
                    sel_a = ANIMALS[i_val][0]
                    c_dict = config.get("mascot_customization", {})
                    if not isinstance(c_dict, dict):
                        c_dict = {}
                    c_dict[ck] = {"animal": sel_a, "outfit": fo}
                    config.set("mascot_customization", c_dict)
                    event_bus.publish("CONFIG_CHANGED", key="mascot_customization", value=c_dict)
                    self.render_hangar_tab()
                return _on_a_changed

            a_combo.currentIndexChanged.connect(_make_animal_cb(cat_key, fixed_outfit))
            btn_row.addWidget(a_combo)

            # Test Flight Button
            def _make_test_flight_cb(ck, fo):
                def _trigger_test():
                    c_dict = config.get("mascot_customization", {})
                    val = c_dict.get(ck, {})
                    an = val.get("animal", "duck") if isinstance(val, dict) else (val or "duck")
                    out = fo
                    titles = {
                        "study": "Neural Networks & AI University Lecture",
                        "food": "Dinner with Friends at Pizzeria",
                        "travel": "Flight BA 257 to London Heathrow",
                        "sport": "CrossFit & Palestra Workout Session",
                        "in_person": "Architectural Studio Consultation",
                        "health": "Serenis Mindfulness & Yoga Session",
                        "secret": "Top Secret Agent Mission Briefing",
                        "general": "Weekly Team Sprint Planning"
                    }
                    evt = {
                        "title": titles.get(ck, "Custom Mascot Test Flight"),
                        "provider": f"{an.capitalize()} wearing {out.capitalize()} Hat ✨",
                        "pilot_type": f"{an}_{out}",
                        "animal": an,
                        "outfit": out,
                        "action_btn_text": "🚀 TEST FLIGHT",
                        "action_url": "https://calendar.apple.com",
                        "start_time": datetime.now().astimezone(),
                        "is_travel": ck in ("food", "travel", "sport", "in_person")
                    }
                    from ui.linux.banner.qt_banner import show_qt_banner
                    show_qt_banner(evt)
                return _trigger_test

            t_btn = QPushButton("🚀 Test", card)
            t_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            t_btn.setFixedHeight(32)
            t_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {cat_color};
                    color: #11111b;
                    font-weight: bold;
                    font-size: 11.5px;
                    border-radius: 6px;
                    padding: 6px 16px;
                    border: 1px solid {cat_color};
                }}
            """)
            t_btn.clicked.connect(_make_test_flight_cb(cat_key, fixed_outfit))
            btn_row.addWidget(t_btn)

            ctrl_box.addLayout(btn_row)
            c_layout.addLayout(ctrl_box)
            self.h_layout.addWidget(card)

        self.h_layout.addStretch()



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

