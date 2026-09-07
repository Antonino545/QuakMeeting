"""
Card: Smart Presence & Arrival Detection for Linux Flight Deck.
Provides user controls for auto-arrival suppression, active call detection,
campus/venue Wi-Fi monitoring, and live presence diagnostics.
"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QLineEdit, QWidget,
)
from PyQt6.QtCore import Qt, QTimer

from core.services.config_service import config
from core.services.arrival_service import arrival_service
from core.services.event_bus import event_bus
from core.services.language_service import t
from ui.linux.animated_widgets import ToggleSwitch


class ArrivalCardWidget(QFrame):
    """Smart presence detection, active call suppression, and venue Wi-Fi monitoring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        # Title & Subtitle
        title = QLabel(t("settings_arrival_title", default="📍 Smart Presence & Arrival Detection"), self)
        title.setObjectName("CardTitle")
        sub = QLabel(t("settings_arrival_subtitle", default="Automatically suppresses redundant reminders when you're already in a call or on-site."), self)
        sub.setObjectName("CardSub")
        layout.addWidget(title)
        layout.addWidget(sub)

        # 1. Master Toggle Row with Status Badge
        master_frame = QFrame(self)
        master_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 8px;
            }
        """)
        mf_layout = QHBoxLayout(master_frame)
        mf_layout.setContentsMargins(14, 12, 14, 12)
        mf_layout.setSpacing(10)

        master_text_layout = QVBoxLayout()
        master_text_layout.setSpacing(2)

        master_title_row = QHBoxLayout()
        master_title_row.setSpacing(8)

        master_title = QLabel(t("settings_arrival_enable", default="Enable Smart Presence & Auto-Arrival Detection"), master_frame)
        master_title.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        master_title.setWordWrap(True)
        master_title_row.addWidget(master_title)

        self.master_badge = QLabel(master_frame)
        master_title_row.addWidget(self.master_badge)
        master_title_row.addStretch()
        master_text_layout.addLayout(master_title_row)

        master_sub = QLabel(t("settings_arrival_enable_sub", default="Silences reminders when you've joined the call or arrived at the venue"), master_frame)
        master_sub.setStyleSheet("color: #a6adc8; font-size: 11px; border: none; background: transparent;")
        master_sub.setWordWrap(True)
        master_text_layout.addWidget(master_sub)

        mf_layout.addLayout(master_text_layout, stretch=1)

        self.master_sw = ToggleSwitch(checked=bool(config.get("enable_arrival_detection", True)), parent=master_frame)
        self.master_sw.setFixedSize(50, 26)
        self.master_sw.toggled = self._on_master_toggled
        mf_layout.addWidget(self.master_sw)

        layout.addWidget(master_frame)

        # 2. Sub-options Container Frame
        self.sub_container = QFrame(self)
        self.sub_container.setObjectName("ArrivalSubContainer")
        self.sub_container.setStyleSheet("""
            QFrame#ArrivalSubContainer {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        sub_layout = QVBoxLayout(self.sub_container)
        sub_layout.setContentsMargins(14, 12, 14, 12)
        sub_layout.setSpacing(12)

        # 2a. Call App Detection Row
        call_row = QHBoxLayout()
        call_row.setSpacing(10)

        call_text = QVBoxLayout()
        call_text.setSpacing(2)
        call_lbl = QLabel(t("settings_arrival_calls", default="Active Video Call Detection"), self.sub_container)
        call_lbl.setStyleSheet("color: #cdd6f4; font-size: 12.5px; font-weight: 600;")
        call_lbl.setWordWrap(True)
        call_sub = QLabel(t("settings_arrival_calls_sub", default="Suppresses alerts when Zoom, Teams, Webex, Skype, or Slack is active"), self.sub_container)
        call_sub.setStyleSheet("color: #a6adc8; font-size: 11px;")
        call_sub.setWordWrap(True)
        call_text.addWidget(call_lbl)
        call_text.addWidget(call_sub)
        call_row.addLayout(call_text, stretch=1)

        self.call_sw = ToggleSwitch(checked=bool(config.get("arrival_detect_active_calls", True)), parent=self.sub_container)
        self.call_sw.setFixedSize(50, 26)
        self.call_sw.toggled = lambda val: self._on_sub_toggled("arrival_detect_active_calls", val)
        call_row.addWidget(self.call_sw)
        sub_layout.addLayout(call_row)

        # Separator line between sub-options
        sep = QFrame(self.sub_container)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #313244; max-height: 1px; border: none;")
        sub_layout.addWidget(sep)

        # 2b. Venue Wi-Fi Detection Row
        wifi_row = QHBoxLayout()
        wifi_row.setSpacing(10)

        wifi_text = QVBoxLayout()
        wifi_text.setSpacing(2)
        wifi_lbl = QLabel(t("settings_arrival_wifi", default="Venue & Campus Wi-Fi Matching"), self.sub_container)
        wifi_lbl.setStyleSheet("color: #cdd6f4; font-size: 12.5px; font-weight: 600;")
        wifi_lbl.setWordWrap(True)
        wifi_sub = QLabel(t("settings_arrival_wifi_sub", default="Suppresses reminders when connected to recognized campus or office Wi-Fi"), self.sub_container)
        wifi_sub.setStyleSheet("color: #a6adc8; font-size: 11px;")
        wifi_sub.setWordWrap(True)
        wifi_text.addWidget(wifi_lbl)
        wifi_text.addWidget(wifi_sub)
        wifi_row.addLayout(wifi_text, stretch=1)

        self.wifi_sw = ToggleSwitch(checked=bool(config.get("arrival_detect_venue_wifi", True)), parent=self.sub_container)
        self.wifi_sw.setFixedSize(50, 26)
        self.wifi_sw.toggled = lambda val: self._on_sub_toggled("arrival_detect_venue_wifi", val)
        wifi_row.addWidget(self.wifi_sw)
        sub_layout.addLayout(wifi_row)

        layout.addWidget(self.sub_container)

        # 3. Live Diagnostics Panel
        diag_frame = QFrame(self)
        diag_frame.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        diag_layout = QVBoxLayout(diag_frame)
        diag_layout.setContentsMargins(12, 10, 12, 10)
        diag_layout.setSpacing(6)

        diag_header_row = QHBoxLayout()
        diag_hdr = QLabel(f"<b>{t('settings_arrival_diagnostics_title', default='Live Diagnostics & Presence Status:')}</b>", diag_frame)
        diag_hdr.setStyleSheet("color: #b4befe; font-size: 11.5px; border: none; background: transparent;")
        diag_header_row.addWidget(diag_hdr)
        diag_header_row.addStretch()

        self.refresh_btn = QPushButton(t("settings_arrival_refresh_btn", default="🔄 Check Now"), diag_frame)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
        """)
        self.refresh_btn.clicked.connect(self.update_diagnostics)
        diag_header_row.addWidget(self.refresh_btn)
        diag_layout.addLayout(diag_header_row)

        self.diag_wifi_lbl = QLabel(diag_frame)
        self.diag_wifi_lbl.setStyleSheet("color: #cdd6f4; font-size: 11.5px; border: none; background: transparent;")
        self.diag_wifi_lbl.setWordWrap(True)
        diag_layout.addWidget(self.diag_wifi_lbl)

        self.add_wifi_btn = QPushButton(diag_frame)
        self.add_wifi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_wifi_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #11111b;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
                margin-top: 2px;
                margin-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        self.add_wifi_btn.clicked.connect(self._on_add_current_wifi)
        self.add_wifi_btn.hide()
        diag_layout.addWidget(self.add_wifi_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.diag_call_lbl = QLabel(diag_frame)
        self.diag_call_lbl.setStyleSheet("color: #cdd6f4; font-size: 11.5px; border: none; background: transparent;")
        self.diag_call_lbl.setWordWrap(True)
        diag_layout.addWidget(self.diag_call_lbl)

        # Operational Meaning / Explanation Banner
        self.diag_summary_box = QFrame(diag_frame)
        self.diag_summary_box.setStyleSheet("""
            QFrame {
                background-color: #242438;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                margin-top: 4px;
            }
        """)
        sum_layout = QVBoxLayout(self.diag_summary_box)
        sum_layout.setContentsMargins(6, 4, 6, 4)
        sum_layout.setSpacing(2)

        self.diag_summary_lbl = QLabel(self.diag_summary_box)
        self.diag_summary_lbl.setStyleSheet("color: #cdd6f4; font-size: 11.5px; border: none; background: transparent;")
        self.diag_summary_lbl.setWordWrap(True)
        sum_layout.addWidget(self.diag_summary_lbl)
        diag_layout.addWidget(self.diag_summary_box)

        layout.addWidget(diag_frame)

        # 4. Monitored SSIDs Editor
        ssid_lbl = QLabel(t("settings_arrival_ssids_label", default="Monitored Venue Wi-Fi SSIDs (comma-separated):"), self)
        ssid_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold; margin-top: 4px;")
        layout.addWidget(ssid_lbl)

        ssid_hint = QLabel(t("settings_arrival_ssids_hint", default="💡 When connected to these Wi-Fi networks, reminders for matching lectures or campus events are auto-silenced."), self)
        ssid_hint.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(ssid_hint)

        curr_ssids = config.get("arrival_wifi_ssids", ["eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"])
        self.ssid_input = QLineEdit(self)
        self.ssid_input.setText(", ".join(curr_ssids))
        self.ssid_input.setPlaceholderText(t("settings_arrival_ssids_placeholder", default="eduroam, polito, campus, universit, studenti..."))
        self.ssid_input.setStyleSheet("""
            QLineEdit {
                background-color: #242438;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
        """)
        layout.addWidget(self.ssid_input)

        # SSIDs Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.save_btn = QPushButton(t("settings_arrival_save_btn", default="💾 Save SSIDs"), self)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                font-weight: bold;
                border: 1px solid #89b4fa;
                border-radius: 7px;
                padding: 6px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        self.save_btn.clicked.connect(self._on_save_ssids)
        btn_row.addWidget(self.save_btn)

        self.reset_btn = QPushButton(t("settings_arrival_reset_btn", default="↺ Reset Defaults"), self)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 7px;
                padding: 6px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
        """)
        self.reset_btn.clicked.connect(self._on_reset_ssids)
        btn_row.addWidget(self.reset_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Initial UI states
        self._sync_enabled_state(self.master_sw.isChecked())
        self.update_diagnostics()

    # Compatibility properties for test assertions
    @property
    def master_chk(self):
        return self.master_sw

    @property
    def call_chk(self):
        return self.call_sw

    @property
    def wifi_chk(self):
        return self.wifi_sw

    def _on_master_toggled(self, checked: bool):
        config.set("enable_arrival_detection", checked)
        self._sync_enabled_state(checked)
        try:
            event_bus.publish("CONFIG_CHANGED", key="enable_arrival_detection", value=checked)
        except Exception:
            pass
        self.update_diagnostics()

    def _on_sub_toggled(self, key: str, checked: bool):
        config.set(key, checked)
        try:
            event_bus.publish("CONFIG_CHANGED", key=key, value=checked)
        except Exception:
            pass
        self.update_diagnostics()

    def _sync_enabled_state(self, is_enabled: bool):
        self.sub_container.setEnabled(is_enabled)
        base_style = """
            QFrame#ArrivalSubContainer {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """
        self.sub_container.setStyleSheet(base_style)
        if is_enabled:
            self.master_badge.setText("● Active")
            self.master_badge.setStyleSheet("""
                background-color: rgba(166, 227, 161, 0.18);
                color: #a6e3a1;
                border: 1px solid #a6e3a1;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 10px;
                font-weight: bold;
            """)
        else:
            self.master_badge.setText("○ Paused")
            self.master_badge.setStyleSheet("""
                background-color: rgba(108, 112, 134, 0.18);
                color: #a6adc8;
                border: 1px solid #6c7086;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 10px;
                font-weight: bold;
            """)

    def _on_save_ssids(self):
        raw = self.ssid_input.text()
        tokens = [s.strip().lower() for s in raw.split(",") if s.strip()]
        config.set("arrival_wifi_ssids", tokens)
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_wifi_ssids", value=tokens)
        except Exception:
            pass
        self.save_btn.setText("✓ " + t("saved", default="Saved"))
        QTimer.singleShot(1500, lambda: self.save_btn.setText(t("settings_arrival_save_btn", default="💾 Save SSIDs")))
        self.update_diagnostics()

    def _on_reset_ssids(self):
        defaults = ["eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"]
        config.set("arrival_wifi_ssids", defaults)
        self.ssid_input.setText(", ".join(defaults))
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_wifi_ssids", value=defaults)
        except Exception:
            pass
        self.update_diagnostics()

    def _on_add_current_wifi(self):
        diag = arrival_service.get_presence_diagnostics()
        ssid = diag.get("current_wifi")
        if not ssid:
            return
        curr_tokens = [s.strip().lower() for s in self.ssid_input.text().split(",") if s.strip()]
        if ssid.lower() not in curr_tokens:
            curr_tokens.append(ssid.lower())
        config.set("arrival_wifi_ssids", curr_tokens)
        self.ssid_input.setText(", ".join(curr_tokens))
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_wifi_ssids", value=curr_tokens)
        except Exception:
            pass
        self.add_wifi_btn.setText(t("settings_arrival_added_wifi", default="✓ Added!").format(ssid=ssid))
        QTimer.singleShot(1500, self.update_diagnostics)

    def update_diagnostics(self):
        """Refreshes live network and call process diagnostics."""
        diag = arrival_service.get_presence_diagnostics()
        wifi_ssid = diag.get("current_wifi")
        is_venue = diag.get("is_venue_wifi", False)
        call_app = diag.get("detected_call_app")
        is_enabled = bool(config.get("enable_arrival_detection", True))

        if wifi_ssid:
            status_tag = f"<span style='color: #a6e3a1; font-weight: bold;'>{t('settings_arrival_status_matched', default='Recognized Venue ✅')}</span>" if is_venue else f"<span style='color: #f9e2af;'>{t('settings_arrival_status_unmatched', default='Standard Network')}</span>"
            self.diag_wifi_lbl.setText(f"📶 <b>{t('settings_arrival_current_wifi', default='Current Wi-Fi:')}</b> {wifi_ssid}  •  {status_tag}")
        else:
            self.diag_wifi_lbl.setText(f"📶 <b>{t('settings_arrival_current_wifi', default='Current Wi-Fi:')}</b> <span style='color: #6c7086;'>{t('settings_arrival_status_disconnected', default='Disconnected / Unavailable')}</span>")

        if call_app:
            self.diag_call_lbl.setText(f"📞 <b>{t('settings_arrival_active_call', default='Active Call App:')}</b> <span style='color: #a6e3a1; font-weight: bold;'>{call_app} (Running 🟢)</span>")
        else:
            self.diag_call_lbl.setText(f"📞 <b>{t('settings_arrival_active_call', default='Active Call App:')}</b> <span style='color: #a6adc8;'>{t('settings_arrival_no_call', default='None running')}</span>")

        # Update intuitive operational status banner
        if not is_enabled:
            self.diag_summary_lbl.setText(t("settings_arrival_summary_disabled", default="⏸️ Presence Detection Paused — Automatic arrival checks are currently disabled."))
            self.add_wifi_btn.hide()
        elif call_app:
            txt = t("settings_arrival_summary_call", default="🟢 In-Call Mode — Active video call ({app}) detected. Meeting alerts are automatically suppressed.").format(app=call_app)
            self.diag_summary_lbl.setText(txt)
            self.add_wifi_btn.hide()
        elif is_venue and wifi_ssid:
            txt = t("settings_arrival_summary_venue", default="🟢 Venue Mode — Connected to recognized venue Wi-Fi ({ssid}). Lecture & in-person reminders are suppressed.").format(ssid=wifi_ssid)
            self.diag_summary_lbl.setText(txt)
            self.add_wifi_btn.hide()
        else:
            self.diag_summary_lbl.setText(t("settings_arrival_summary_normal", default="⚪ Normal Mode — All reminder flight banners will alert as scheduled."))
            if wifi_ssid:
                btn_txt = t("settings_arrival_add_current_wifi", default="➕ Add '{ssid}' to Venue List").format(ssid=wifi_ssid)
                self.add_wifi_btn.setText(btn_txt)
                self.add_wifi_btn.show()
            else:
                self.add_wifi_btn.hide()
