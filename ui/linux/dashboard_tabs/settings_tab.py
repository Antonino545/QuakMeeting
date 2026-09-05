"""
PyQt6 Preferences & Settings Tab for QuakMeeting Flight Deck on Linux.
Provides staged notification lead times, multi-modal route ETA and origin addresses,
smart mascot & keyword rules manager, calendar source filters, and developer diagnostics.
"""

import sys
import threading
import webbrowser
import logging
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal

from core.services.config_service import config, is_debug_mode
from core.services.calendar_service import calendar_service
from core.services.updater_service import updater_service
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from core.services.event_bus import event_bus
from core.domain.classifier import EventClassifier
from core.logger import open_log_file, open_log_folder
from core.services.language_service import t
from ui.linux.animated_widgets import (
    AnimatedUpdateCard, UpdatingHUDWidget, ToggleSwitch, AnimatedSpinButton
)
from ui.linux.components.address_autocomplete_widget import QtAddressAutocompleteWidget

logger = logging.getLogger("QuakMeeting.QtSettingsTab")


class QtUpdateBridge(QObject):
    """Bridge for receiving background updater events and emitting Qt signals."""
    update_event = pyqtSignal(str, dict)


class QtSettingsTab(QWidget):
    """Preferences & Timing Settings tab component."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.update_bridge = QtUpdateBridge()

        pref_scroll = QScrollArea(self)
        pref_scroll.setWidgetResizable(True)
        pref_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pref_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pref_scroll.setStyleSheet("QScrollArea { background: transparent; }")

        pref_widget = QWidget()
        pref_layout = QVBoxLayout(pref_widget)
        pref_layout.setContentsMargins(0, 0, 0, 0)
        pref_layout.setSpacing(14)

        # ── CARD 1: TIMING & STAGED REMINDERS ─────────────────────────────────
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
                    color: #89b4fa;
                }
            """)
            def _make_preset_cb(pm=p_m, pg=p_g, pt=p_t):
                return lambda: _apply_preset(pm, pg, pt)
            p_btn.clicked.connect(_make_preset_cb())
            preset_row.addWidget(p_btn)

        preset_row.addStretch()
        tc_layout.addLayout(preset_row)

        div_p = QFrame(timing_card)
        div_p.setFrameShape(QFrame.Shape.HLine)
        div_p.setStyleSheet("color: #313244; background: #313244;")
        div_p.setFixedHeight(1)
        tc_layout.addWidget(div_p)

        def _build_stage_row(title, subtitle, config_key, default_stages, active_accent="#cba6f7"):
            sec_box = QVBoxLayout()
            sec_box.setSpacing(4)

            t_l = QLabel(title, timing_card)
            t_l.setStyleSheet("font-size: 12.5px; font-weight: bold; color: #cdd6f4;")
            s_l = QLabel(subtitle, timing_card)
            s_l.setStyleSheet("font-size: 11px; color: #a6adc8;")
            sec_box.addWidget(t_l)
            sec_box.addWidget(s_l)

            row = QHBoxLayout()
            row.setSpacing(6)

            all_stages = [60, 45, 30, 20, 15, 10, 5, 2]
            current_stages = set(config.get(config_key, default_stages))

            for stg in all_stages:
                btn = QPushButton(f"{stg}m", timing_card)
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setChecked(stg in current_stages)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: #242438;
                        color: #cdd6f4;
                        border: 1px solid #45475a;
                        border-radius: 7px;
                        padding: 5px 10px;
                        font-size: 11.5px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: #313244;
                        border-color: {active_accent};
                    }}
                    QPushButton:checked {{
                        background: {active_accent};
                        color: #11111b;
                        font-weight: bold;
                        border: 1px solid {active_accent};
                    }}
                """)
                def _toggled(checked, val=stg, ck=config_key, def_s=default_stages):
                    stages = set(config.get(ck, def_s))
                    if checked:
                        stages.add(val)
                    else:
                        stages.discard(val)
                    stages.add(0)
                    config.set(ck, sorted(list(stages), reverse=True))

                btn.toggled.connect(_toggled)
                stage_buttons[(config_key, stg)] = btn
                row.addWidget(btn)

            row.addStretch()
            sec_box.addLayout(row)
            return sec_box

        tc_layout.addLayout(_build_stage_row("📹 Video Meetings", "Reminders for Zoom, Google Meet, Microsoft Teams, etc.", "meeting_reminder_stages", [20, 10, 5, 2, 0], "#cba6f7"))
        tc_layout.addLayout(_build_stage_row("📅 General Events", "Tasks, personal appointments, syncs, and routines.", "general_reminder_stages", [20, 10, 5, 2, 0], "#89b4fa"))
        tc_layout.addLayout(_build_stage_row("🚗 Travel & Trips", "Reminders ahead of calculated departure times for in-person destinations.", "travel_reminder_stages", [45, 30, 15, 5, 2, 0], "#fab387"))

        pref_layout.addWidget(timing_card)

        # ── CARD 2: ADDRESS & TRANSIT ─────────────────────────────────────────
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

        # 1. Starting Origin Address
        orig_lbl = QLabel("🏠 Starting Address (Origin):", addr_card)
        orig_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        ac_layout.addWidget(orig_lbl)

        def _on_home_saved(chosen_text, cand=None):
            config.set("home_address", chosen_text)
            try:
                event_bus.publish("CONFIG_CHANGED", key="home_address", value=chosen_text)
            except Exception:
                pass

        home_addr_auto = QtAddressAutocompleteWidget(
            placeholder="Search home address or starting city (e.g. Corso Francia, Torino)...",
            initial_value=config.get("home_address", ""),
            on_save_cb=_on_home_saved,
            btn_gradient="green",
            parent=addr_card
        )
        ac_layout.addWidget(home_addr_auto)

        # 2. University & Exam Campus Address
        exam_lbl = QLabel("🎓 University & Exam Campus:", addr_card)
        exam_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold; margin-top: 6px;")
        ac_layout.addWidget(exam_lbl)

        exam_desc = QLabel("💡 Type any university or campus name. Automatically assigned to exams to calculate transit routes & ETA.", addr_card)
        exam_desc.setStyleSheet("color: #a6adc8; font-size: 11px;")
        ac_layout.addWidget(exam_desc)

        def _on_exam_saved(chosen_text, cand=None):
            config.set("exam_location", chosen_text)
            try:
                event_bus.publish("CONFIG_CHANGED", key="exam_location", value=chosen_text)
            except Exception:
                pass

        exam_addr_auto = QtAddressAutocompleteWidget(
            placeholder="Type any university name (e.g. Politecnico di Torino, UniTo, Bocconi)...",
            initial_value=config.get("exam_location", "Politecnico di Torino, Corso Duca degli Abruzzi 24, Torino"),
            on_save_cb=_on_exam_saved,
            btn_gradient="mauve",
            parent=addr_card
        )
        ac_layout.addWidget(exam_addr_auto)

        # 3. Transport Mode Selection
        mode_lbl = QLabel("🚦 Transport Mode for Route Calculation:", addr_card)
        mode_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold; margin-top: 6px;")
        ac_layout.addWidget(mode_lbl)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)

        modes = [
            ("transit", "🚆 Public Transit"),
            ("automobile", "🚗 Driving"),
            ("bicycling", "🚲 Cycling"),
            ("walking", "🚶 Walking")
        ]
        curr_mode = config.get("transport_mode", "transit")
        mode_btns = {}

        def _set_mode(selected_mode):
            config.set("transport_mode", selected_mode)
            try:
                event_bus.publish("CONFIG_CHANGED", key="transport_mode", value=selected_mode)
            except Exception:
                pass
            for m_key, b in mode_btns.items():
                is_active = (m_key == selected_mode)
                b.setChecked(is_active)
                if is_active:
                    b.setStyleSheet("""
                        QPushButton {
                            background: #89b4fa;
                            color: #11111b;
                            font-weight: bold;
                            border: 1px solid #89b4fa;
                            border-radius: 7px;
                            padding: 6px 14px;
                            font-size: 12px;
                        }
                    """)
                else:
                    b.setStyleSheet("""
                        QPushButton {
                            background: #242438;
                            color: #cdd6f4;
                            border: 1px solid #45475a;
                            border-radius: 7px;
                            padding: 6px 14px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background: #313244;
                            border-color: #89b4fa;
                        }
                    """)

        for m_key, m_label in modes:
            m_btn = QPushButton(m_label, addr_card)
            m_btn.setCheckable(True)
            m_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            def _make_mode_cb(k=m_key):
                return lambda: _set_mode(k)
            m_btn.clicked.connect(_make_mode_cb())
            mode_btns[m_key] = m_btn
            mode_row.addWidget(m_btn)

        mode_row.addStretch()
        ac_layout.addLayout(mode_row)
        _set_mode(curr_mode)

        # 4. Departure Buffer Margin
        buf_row = QHBoxLayout()
        buf_row.setSpacing(10)
        buf_lbl = QLabel("⌛ Departure Buffer Margin (station transit / parking time):", addr_card)
        buf_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        buf_row.addWidget(buf_lbl)

        buf_combo = QComboBox(addr_card)
        buf_combo.setFixedHeight(30)
        buf_combo.setStyleSheet("""
            QComboBox {
                background: #242438;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 11.5px;
                min-width: 170px;
            }
        """)
        buf_options = [
            (0, "0 minutes (Exact ETA)"),
            (5, "5 minutes"),
            (10, "10 minutes (Recommended)"),
            (15, "15 minutes"),
            (20, "20 minutes"),
            (30, "30 minutes")
        ]
        curr_buf = config.get("eta_buffer_minutes", 10)
        curr_buf_idx = 2
        for idx, (b_val, b_lbl) in enumerate(buf_options):
            buf_combo.addItem(b_lbl, b_val)
            if b_val == curr_buf:
                curr_buf_idx = idx
        buf_combo.setCurrentIndex(curr_buf_idx)

        def _buf_changed(idx_val):
            val_buf = buf_combo.itemData(idx_val)
            config.set("eta_buffer_minutes", int(val_buf))
            try:
                event_bus.publish("CONFIG_CHANGED", key="eta_buffer_minutes", value=int(val_buf))
            except Exception:
                pass
        buf_combo.currentIndexChanged.connect(_buf_changed)

        buf_row.addWidget(buf_combo)
        buf_row.addStretch()
        ac_layout.addLayout(buf_row)

        pref_layout.addWidget(addr_card)

        # ── CARD 3: INCLUDED CALENDARS ────────────────────────────────────────
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

        # ── CARD 4: SYSTEM & DIAGNOSTICS ──────────────────────────────────────
        util_card = QFrame(pref_widget)
        util_card.setObjectName("Card")
        uc_layout = QVBoxLayout(util_card)
        uc_layout.setContentsMargins(18, 14, 18, 14)
        uc_layout.setSpacing(10)

        uc_title = QLabel("⚙️ System, Language & Diagnostics", util_card)
        uc_title.setObjectName("CardTitle")
        uc_layout.addWidget(uc_title)

        # 1. Language selector row
        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)
        lang_lbl = QLabel("<b>🌐 Application Language:</b>", util_card)
        lang_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        lang_row.addWidget(lang_lbl)

        langs = [
            ("system", "🌐 System (Auto)"),
            ("en", "English 🇬🇧"),
            ("it", "Italiano 🇮🇹")
        ]
        curr_lang = config.get("language", "system")
        lang_btns = {}

        def _apply_lang(l_key):
            config.set("language", l_key)
            try:
                event_bus.publish("CONFIG_CHANGED", key="language", value=l_key)
            except Exception:
                pass
            for k, b in lang_btns.items():
                is_sel = (k == l_key)
                if is_sel:
                    b.setStyleSheet("""
                        QPushButton {
                            background: #cba6f7;
                            color: #11111b;
                            font-weight: bold;
                            border: 1px solid #cba6f7;
                            border-radius: 7px;
                            padding: 4px 12px;
                            font-size: 11.5px;
                        }
                    """)
                else:
                    b.setStyleSheet("""
                        QPushButton {
                            background: #242438;
                            color: #cdd6f4;
                            border: 1px solid #45475a;
                            border-radius: 7px;
                            padding: 4px 12px;
                            font-size: 11.5px;
                        }
                        QPushButton:hover {
                            background: #313244;
                            border-color: #cba6f7;
                        }
                    """)

        for l_key, l_name in langs:
            l_btn = QPushButton(l_name, util_card)
            l_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            def _make_lang_cb(k=l_key):
                return lambda: _apply_lang(k)
            l_btn.clicked.connect(_make_lang_cb())
            lang_btns[l_key] = l_btn
            lang_row.addWidget(l_btn)

        lang_row.addStretch()
        uc_layout.addLayout(lang_row)
        _apply_lang(curr_lang)

        # 2. Autostart row
        auto_row = QHBoxLayout()
        auto_row.setSpacing(10)
        auto_lbl = QLabel("🚀 Launch QuakMeeting automatically at system login", util_card)
        auto_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: 500;")
        auto_row.addWidget(auto_lbl)
        auto_row.addStretch()

        auto_switch = ToggleSwitch(checked=is_autostart_enabled(), parent=util_card)
        def _toggle_auto(checked):
            if checked:
                enable_autostart()
            else:
                disable_autostart()
        auto_switch.toggled = _toggle_auto
        auto_row.addWidget(auto_switch)
        uc_layout.addLayout(auto_row)

        # 3. Lesson mute row
        mute_row = QHBoxLayout()
        mute_row.setSpacing(10)
        mute_lbl = QLabel("🤫 Mute banner chime during university lessons & classes", util_card)
        mute_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: 500;")
        mute_row.addWidget(mute_lbl)
        mute_row.addStretch()

        mute_switch = ToggleSwitch(checked=config.get("mute_during_lessons", True), parent=util_card)
        def _toggle_mute(checked):
            config.set("mute_during_lessons", checked)
        mute_switch.toggled = _toggle_mute
        mute_row.addWidget(mute_switch)
        uc_layout.addLayout(mute_row)

        # 4. Action Buttons Row
        sys_row = QHBoxLayout()
        sys_row.setSpacing(8)

        up_btn = AnimatedSpinButton("🔍 Check for Updates", util_card)
        up_btn.setObjectName("OutlineBtn")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        edit_btn = QPushButton("⚙️ Edit config.json", util_card)
        edit_btn.setObjectName("OutlineBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(config.open_config_in_editor)

        log_btn = QPushButton("📄 View Logs", util_card)
        log_btn.setObjectName("OutlineBtn")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(open_log_file)

        demo_up_btn = QPushButton("🚀 Live Demo", util_card)
        demo_up_btn.setObjectName("OutlineBtn")
        demo_up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_up_btn.setToolTip("Preview the rich Animated Updating HUD and Jet Rocket Thruster")

        def _on_show_license():
            msg = QMessageBox(self)
            msg.setWindowTitle(t("license_title"))
            msg.setText(t("license_body"))
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e2e;
                }
                QLabel {
                    color: #cdd6f4;
                    font-size: 13px;
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

        def _on_bridge_event(event_name, data):
            if event_name == "UPDATE_AVAILABLE":
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

        if updater_service.latest_release_info and updater_service.latest_release_info.get("has_update"):
            _on_update_avail(**updater_service.latest_release_info)

        pref_layout.addWidget(util_card)
        pref_layout.addStretch()

        pref_scroll.setWidget(pref_widget)
        layout.addWidget(pref_scroll)
