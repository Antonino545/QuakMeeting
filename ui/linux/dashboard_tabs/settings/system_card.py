"""
Card 4: System, Language & Diagnostics for Linux Flight Deck.
"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QWidget,
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal

from core.services.config_service import config, is_debug_mode
from core.services.updater_service import updater_service
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from core.services.event_bus import event_bus
from core.logger import open_log_file
from core.services.language_service import t
from ui.linux.animated_widgets import (
    AnimatedUpdateCard, UpdatingHUDWidget, ToggleSwitch, AnimatedSpinButton,
)


class QtUpdateBridge(QObject):
    """Bridge for receiving background updater events and emitting Qt signals."""
    update_event = pyqtSignal(str, dict)
    debug_event = pyqtSignal(bool)


class SystemCardWidget(QFrame):
    """System preferences, language picker, diagnostics, and animated updater HUD."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.update_bridge = QtUpdateBridge()

        uc_layout = QVBoxLayout(self)
        uc_layout.setContentsMargins(18, 14, 18, 14)
        uc_layout.setSpacing(10)

        is_dbg = is_debug_mode()
        self.uc_title = QLabel(t("settings_system_lang_diag") if is_dbg else t("settings_system_lang"), self)
        self.uc_title.setObjectName("CardTitle")
        uc_layout.addWidget(self.uc_title)

        # 1. Language selector row
        lang_row = QHBoxLayout()
        lang_row.setSpacing(8)
        lang_lbl = QLabel("<b>🌐 Application Language:</b>", self)
        lang_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        lang_row.addWidget(lang_lbl)

        langs = [
            ("system", "🌐 System (Auto)"),
            ("en", "English 🇬🇧"),
            ("it", "Italiano 🇮🇹")
        ]
        curr_lang = config.get("language", "system")
        self.lang_btns = {}

        def _apply_lang(l_key):
            if config.get("language", "system") != l_key:
                config.set("language", l_key)
                try:
                    event_bus.publish("CONFIG_CHANGED", key="language", value=l_key)
                except Exception:
                    pass
            if hasattr(self, "uc_title"):
                self.uc_title.setText(t("settings_system_lang_diag") if is_debug_mode() else t("settings_system_lang"))
            for k, b in self.lang_btns.items():
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
            l_btn = QPushButton(l_name, self)
            l_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            def _make_lang_cb(k=l_key):
                return lambda: _apply_lang(k)
            l_btn.clicked.connect(_make_lang_cb())
            self.lang_btns[l_key] = l_btn
            lang_row.addWidget(l_btn)

        lang_row.addStretch()
        uc_layout.addLayout(lang_row)
        _apply_lang(curr_lang)

        # 2. Autostart row
        auto_row = QHBoxLayout()
        auto_row.setSpacing(10)
        auto_lbl = QLabel("🚀 Launch FlightDeck automatically at system login", self)
        auto_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: 500;")
        auto_row.addWidget(auto_lbl)
        auto_row.addStretch()

        auto_switch = ToggleSwitch(checked=is_autostart_enabled(), parent=self)
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
        mute_lbl = QLabel("🤫 Mute banner chime during university lessons & classes", self)
        mute_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: 500;")
        mute_row.addWidget(mute_lbl)
        mute_row.addStretch()

        mute_switch = ToggleSwitch(checked=config.get("mute_during_lessons", True), parent=self)
        def _toggle_mute(checked):
            config.set("mute_during_lessons", checked)
        mute_switch.toggled = _toggle_mute
        mute_row.addWidget(mute_switch)
        uc_layout.addLayout(mute_row)

        # 4. User Action Buttons Row (Always visible: Check for Updates & License)
        self.action_row_widget = QWidget(self)
        action_row = QHBoxLayout(self.action_row_widget)
        action_row.setContentsMargins(0, 0, 0, 0)
        action_row.setSpacing(8)

        self.up_btn = AnimatedSpinButton(f"🔍 {t('check_updates')}", self.action_row_widget)
        self.up_btn.setObjectName("OutlineBtn")
        self.up_btn.setCursor(Qt.CursorShape.PointingHandCursor)

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

        lic_btn = QPushButton("📜 License && Info", self.action_row_widget)
        lic_btn.setObjectName("OutlineBtn")
        lic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lic_btn.clicked.connect(_on_show_license)

        action_row.addWidget(self.up_btn)
        action_row.addWidget(lic_btn)
        action_row.addStretch()
        uc_layout.addWidget(self.action_row_widget)

        # 5. Diagnostic Buttons Row (Only in debug mode)
        self.sys_row_widget = QWidget(self)
        sys_row = QHBoxLayout(self.sys_row_widget)
        sys_row.setContentsMargins(0, 0, 0, 0)
        sys_row.setSpacing(8)

        edit_btn = QPushButton(t("settings_config_json"), self.sys_row_widget)
        edit_btn.setObjectName("OutlineBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(config.open_config_in_editor)

        log_btn = QPushButton(t("settings_view_logs"), self.sys_row_widget)
        log_btn.setObjectName("OutlineBtn")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(open_log_file)

        demo_up_btn = QPushButton("🚀 Live Demo", self.sys_row_widget)
        demo_up_btn.setObjectName("OutlineBtn")
        demo_up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        demo_up_btn.setToolTip("Preview the rich Animated Updating HUD and Jet Rocket Thruster")

        sys_row.addWidget(edit_btn)
        sys_row.addWidget(log_btn)
        sys_row.addWidget(demo_up_btn)
        sys_row.addStretch()
        uc_layout.addWidget(self.sys_row_widget)
        self.sys_row_widget.setVisible(is_dbg)

        # Animated Update status card with radar scanning and celebratory states
        self.update_status_box = AnimatedUpdateCard(self)
        usb_layout = QVBoxLayout(self.update_status_box)
        usb_layout.setContentsMargins(14, 12, 14, 12)
        usb_layout.setSpacing(8)

        status_header_row = QHBoxLayout()
        self.update_icon_lbl = QLabel("🦆", self.update_status_box)
        self.update_icon_lbl.setStyleSheet("font-size: 22px; border: none;")
        status_header_row.addWidget(self.update_icon_lbl)

        self.update_status_lbl = QLabel(f"FlightDeck <b>v{updater_service.current_version}</b>  •  <span style='color:#a6adc8;'>Ready</span>", self.update_status_box)
        self.update_status_lbl.setStyleSheet("color: #cdd6f4; font-size: 13px; border: none;")
        status_header_row.addWidget(self.update_status_lbl, stretch=1)
        usb_layout.addLayout(status_header_row)

        self.changelog_lbl = QLabel("", self.update_status_box)
        self.changelog_lbl.setWordWrap(True)
        self.changelog_lbl.setStyleSheet("color: #bac2de; font-size: 11px; border: none; padding-left: 2px;")
        self.changelog_lbl.setVisible(False)
        usb_layout.addWidget(self.changelog_lbl)

        # Dedicated Animated Updating HUD (Flying Mascot Jet, Phase indicators & Rotating Gears)
        self.updating_hud = UpdatingHUDWidget(self.update_status_box)
        self.updating_hud.setVisible(False)
        usb_layout.addWidget(self.updating_hud)

        # Action Buttons Row
        act_row = QHBoxLayout()
        act_row.setContentsMargins(0, 4, 0, 0)
        self.install_btn = QPushButton("⚡ Download && Install Update", self.update_status_box)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setStyleSheet("""
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
        self.install_btn.setVisible(False)
        act_row.addWidget(self.install_btn)
        usb_layout.addLayout(act_row)

        uc_layout.addWidget(self.update_status_box)
        self.update_status_box.setVisible(is_dbg or bool(updater_service.latest_release_info and updater_service.latest_release_info.get("has_update")))

        # Interactive animation preview simulation
        def _run_update_animation_demo():
            self.updating_hud.start_downloading("flightdeck_latest_amd64.deb")
            demo_up_btn.setEnabled(False)
            self.install_btn.setVisible(False)
            total_size = 28 * 1024 * 1024  # 28 MB simulation
            
            def _demo_step(pct):
                if pct <= 100:
                    curr_bytes = int((pct / 100.0) * total_size)
                    self.updating_hud.set_progress(pct, curr_bytes, total_size)
                    QTimer.singleShot(40, lambda p=pct+2: _demo_step(p))
                else:
                    self.updating_hud.set_installing()
                    def _finish_install():
                        self.updating_hud.set_installed()
                        demo_up_btn.setEnabled(True)
                    QTimer.singleShot(1400, _finish_install)

            QTimer.singleShot(300, lambda: _demo_step(4))

        demo_up_btn.clicked.connect(_run_update_animation_demo)

        def _on_check_clicked():
            self.up_btn.start_spinning("Checking...")
            self.update_status_box.setVisible(True)
            self.update_status_box.set_scanning(True)
            self.update_icon_lbl.setText("📡")
            self.update_status_lbl.setText("<span style='color:#89b4fa;'><b>Scanning GitHub repository for releases...</b></span>")
            updater_service.check_for_updates(background=True)

        self.up_btn.clicked.connect(_on_check_clicked)

        def _on_update_avail(version=None, tag_name=None, name=None, body=None, **k):
            self.up_btn.stop_spinning("🔍 Check for Updates")
            self.update_status_box.setVisible(True)
            v_name = tag_name or version or "New Version"
            self.update_status_box.set_update_available(v_name)
            self.update_icon_lbl.setText("🚀")
            self.update_status_lbl.setText(f"<b style='color:#89b4fa;'>Update Available: {v_name}</b>  <span style='color:#6c7086;'>(Current: v{updater_service.current_version})</span>")
            if body:
                summary = body.strip().split("\n")[0][:120]
                self.changelog_lbl.setText(f"<i>✨ {summary}</i>")
                self.changelog_lbl.setVisible(True)
            self.install_btn.setText(f"⚡ Install {v_name} Now")
            self.install_btn.setEnabled(True)
            self.install_btn.setVisible(True)

        def _on_update_complete(has_update=False, current_version=None, error=None, **k):
            if not has_update:
                if error:
                    self.up_btn.stop_spinning("❌ Check Error", is_success=False, reset_delay_ms=2500)
                    self.update_icon_lbl.setText("⚠️")
                    self.update_status_lbl.setText(f"<span style='color:#f38ba8;'>Update check error: {error[:60]}</span>")
                else:
                    self.up_btn.stop_spinning("✨ Up to date", is_success=True, reset_delay_ms=2500)
                    self.update_status_box.set_up_to_date()
                    self.update_icon_lbl.setText("✨")
                    self.update_status_lbl.setText(f"<span style='color:#a6e3a1;'><b>You are on the latest version!</b></span>  <b>v{current_version or updater_service.current_version}</b>")
                self.install_btn.setVisible(False)
                self.changelog_lbl.setVisible(False)
                if not is_debug_mode():
                    QTimer.singleShot(4000, lambda: self.update_status_box.setVisible(False) if not is_debug_mode() and not (updater_service.latest_release_info and updater_service.latest_release_info.get("has_update")) else None)

        def _on_downloading(file_name=None, **k):
            self.update_icon_lbl.setText("📥")
            self.update_status_lbl.setText(f"<b>Downloading update package...</b> <span style='color:#a6adc8;'>({file_name or ''})</span>")
            self.install_btn.setVisible(False)
            self.updating_hud.start_downloading(file_name or "")

        def _on_download_progress(percent=0, downloaded=0, total=0, **k):
            self.updating_hud.set_progress(percent, downloaded, total)

        def _on_downloaded(target_path=None, **k):
            self.update_icon_lbl.setText("⚙️")
            self.update_status_lbl.setText("<b>Installing update...</b> Please grant system permission if prompted.")
            self.updating_hud.set_installing()

        def _on_installed(**k):
            self.update_icon_lbl.setText("🎉")
            self.update_status_lbl.setText("<b style='color:#a6e3a1;'>Update installed successfully!</b> Relaunching FlightDeck...")
            self.install_btn.setVisible(False)
            self.updating_hud.set_installed()

        def _on_failed(error=None, **k):
            self.update_icon_lbl.setText("❌")
            self.update_status_lbl.setText(f"<span style='color:#f38ba8;'>Installation failed: {error or 'Unknown error'}</span>")
            self.install_btn.setText("🔄 Try Again")
            self.install_btn.setEnabled(True)
            self.install_btn.setVisible(True)
            self.updating_hud.setVisible(False)

        def _on_install_clicked():
            self.install_btn.setText("⏳ Preparing download...")
            self.install_btn.setEnabled(False)
            updater_service.download_and_install_update(background=True)

        self.install_btn.clicked.connect(_on_install_clicked)

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

        self.update_bridge.debug_event.connect(self.set_debug_visibility)

        def _on_config_changed(key=None, value=None, **k):
            if key == "debug_mode":
                self.update_bridge.debug_event.emit(bool(value))

        event_bus.subscribe("CONFIG_CHANGED", _on_config_changed)

        if updater_service.latest_release_info and updater_service.latest_release_info.get("has_update"):
            _on_update_avail(**updater_service.latest_release_info)

    def set_debug_visibility(self, visible: bool):
        if hasattr(self, "uc_title"):
            self.uc_title.setText(t("settings_system_lang_diag") if visible else t("settings_system_lang"))
        if hasattr(self, "sys_row_widget"):
            self.sys_row_widget.setVisible(visible)
        if hasattr(self, "update_status_box"):
            has_update = updater_service.latest_release_info and updater_service.latest_release_info.get("has_update")
            self.update_status_box.setVisible(visible or bool(has_update))
