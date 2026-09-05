"""
Reusable Address Autocomplete Widget for Linux PyQt6 (Google Maps style).
Provides continuous, non-interrupting search-as-you-type suggestions with a popup list,
instant geocoding verification status, and one-click browser map preview.
"""
import threading
from typing import Optional, Callable, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QPoint
from PyQt6.QtGui import QDesktopServices

from core.services.address_service import address_service, AddressCandidate, AddressService
from core.services.language_service import t


class QtAddressAutocompleteWidget(QWidget):
    """
    Modern Google Maps-style PyQt6 widget for smart address input.
    - Full-width typing with continuous keystroke debouncing (350ms).
    - Floating suggestions list directly underneath that never steals focus.
    - Integrated [🗺️ Map] and [💾 Save] action buttons.
    - Dynamic verification badge with canonical address.
    """
    suggestions_ready = pyqtSignal(list)
    verification_finished = pyqtSignal(bool, object, str)

    def __init__(
        self,
        placeholder: str = "",
        initial_value: str = "",
        on_save_cb: Optional[Callable[[str, Optional[AddressCandidate]], None]] = None,
        btn_gradient: str = "green",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.placeholder_str = placeholder
        self.initial_value_str = initial_value or ""
        self.on_save_cb = on_save_cb
        self.btn_gradient = btn_gradient

        self.current_candidate: Optional[AddressCandidate] = None
        self._candidates: List[AddressCandidate] = []

        self._init_ui()
        self._setup_signals()

        if self.initial_value_str:
            self._verify_initial(self.initial_value_str)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Top row: LineEdit + Map Button + Save Button
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.line_edit = QLineEdit(self)
        self.line_edit.setText(self.initial_value_str)
        self.line_edit.setPlaceholderText(self.placeholder_str)
        self.line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)
        input_row.addWidget(self.line_edit, stretch=1)

        self.map_btn = QPushButton(t("settings_address_view_map"), self)
        self.map_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_btn.setStyleSheet("""
            QPushButton {
                background: #313244;
                color: #cdd6f4;
                font-size: 11.5px;
                border-radius: 8px;
                padding: 6px 12px;
                border: 1px solid #45475a;
            }
            QPushButton:hover {
                background: #45475a;
            }
        """)
        input_row.addWidget(self.map_btn)

        grad_stops = "stop:0 #22c55e, stop:1 #16a34a" if self.btn_gradient == "green" else "stop:0 #8b5cf6, stop:1 #7c3aed"
        grad_hover = "stop:0 #16a34a, stop:1 #22c55e" if self.btn_gradient == "green" else "stop:0 #7c3aed, stop:1 #8b5cf6"
        border_col = "#4ade80" if self.btn_gradient == "green" else "#a78bfa"

        self.save_btn = QPushButton(f"💾 {t('save')}", self)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {grad_stops});
                color: #ffffff;
                font-weight: bold;
                font-size: 11.5px;
                border-radius: 8px;
                padding: 6px 16px;
                border: 1px solid {border_col};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {grad_hover});
            }}
        """)
        input_row.addWidget(self.save_btn)

        main_layout.addLayout(input_row)

        # Bottom row: Status & Canonical Preview with high contrast
        self.status_label = QLabel(t("settings_address_suggest_hint"), self)
        self.status_label.setStyleSheet("color: #cdd6f4; font-size: 11.5px;")
        main_layout.addWidget(self.status_label)

        # Popup Suggestions List (NoFocus so typing is never interrupted!)
        self.popup_list = QListWidget()
        self.popup_list.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.popup_list.setStyleSheet("""
            QListWidget {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 4px;
                font-size: 11.5px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 6px;
            }
            QListWidget::item:hover, QListWidget::item:selected {
                background-color: #313244;
                color: #89b4fa;
            }
        """)
        self.popup_list.itemClicked.connect(self._on_item_clicked)

        # Debounce Timer
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(350)
        self.debounce_timer.timeout.connect(self._on_debounced_search)

    def _setup_signals(self):
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.returnPressed.connect(self._on_save_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.map_btn.clicked.connect(self._on_open_map)

        self.suggestions_ready.connect(self._handle_suggestions_ready)
        self.verification_finished.connect(self._handle_verification_finished)

    def _on_text_changed(self, text: str):
        self.debounce_timer.start()

    def _on_debounced_search(self):
        query = self.line_edit.text().strip()
        if len(query) < 3:
            self.popup_list.hide()
            self.status_label.setText(t("settings_address_suggest_hint"))
            self.status_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
            return

        self.status_label.setText(t("settings_address_searching"))
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 11px;")

        def _worker():
            candidates = address_service.search_suggestions(query, limit=4)
            # Only emit if query is still matching current input
            if self.line_edit.text().strip() == query:
                self.suggestions_ready.emit(candidates)

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_suggestions_ready(self, candidates: List[AddressCandidate]):
        self._candidates = candidates
        self.popup_list.clear()

        if not candidates:
            self.popup_list.hide()
            self.status_label.setText(t("settings_address_not_found"))
            self.status_label.setStyleSheet("color: #fab387; font-size: 11px;")
            return

        for cand in candidates:
            label = f"📍  {cand.short_address}"
            secondary = []
            if cand.city:
                secondary.append(cand.city)
            if cand.state:
                secondary.append(cand.state)
            elif cand.country:
                secondary.append(cand.country)
            if secondary:
                label += f"   ({', '.join(secondary)})"

            item = QListWidgetItem(label)
            self.popup_list.addItem(item)

        # Position popup directly under the QLineEdit
        global_pos = self.line_edit.mapToGlobal(QPoint(0, self.line_edit.height() + 2))
        self.popup_list.setFixedWidth(max(360, self.line_edit.width()))
        self.popup_list.setFixedHeight(min(160, len(candidates) * 32 + 10))
        self.popup_list.move(global_pos)
        self.popup_list.show()

    def _on_item_clicked(self, item: QListWidgetItem):
        idx = self.popup_list.row(item)
        self.popup_list.hide()
        if 0 <= idx < len(self._candidates):
            cand = self._candidates[idx]
            self.select_candidate(cand)

    def select_candidate(self, candidate: AddressCandidate):
        self.popup_list.hide()
        self.current_candidate = candidate

        chosen_text = candidate.display_name or candidate.short_address
        self.line_edit.blockSignals(True)
        self.line_edit.setText(chosen_text)
        self.line_edit.blockSignals(False)

        self.line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #11111b;
                color: #cdd6f4;
                border: 1px solid #a6e3a1;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)

        status_text = f"🟢 {t('settings_address_verified')}: {candidate.display_name}"
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 11.5px;")

        self.save_btn.setText(f"✓ {t('saved')}")
        QTimer.singleShot(1500, lambda: self.save_btn.setText(f"💾 {t('save')}"))

        if self.on_save_cb:
            self.on_save_cb(chosen_text, candidate)

    def _on_save_clicked(self):
        query = self.line_edit.text().strip()
        self.popup_list.hide()

        if not query:
            self.current_candidate = None
            self.status_label.setText(t("settings_address_suggest_hint"))
            self.status_label.setStyleSheet("color: #cdd6f4; font-size: 11.5px;")
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #11111b;
                    color: #cdd6f4;
                    border: 1px solid #313244;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 12px;
                }
            """)
            if self.on_save_cb:
                self.on_save_cb("", None)
            self.save_btn.setText(f"✓ {t('saved')}")
            QTimer.singleShot(1500, lambda: self.save_btn.setText(f"💾 {t('save')}"))
            return

        self.status_label.setText(t("settings_address_searching"))
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 11.5px;")
        self.save_btn.setText("⏳ ...")

        def _worker():
            is_valid, cand, err = address_service.verify_address(query)
            self.verification_finished.emit(is_valid, cand, err or "")

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_verification_finished(self, is_valid: bool, cand: Optional[AddressCandidate], err: str):
        self.save_btn.setText(f"💾 {t('save')}")
        query = self.line_edit.text().strip()
        if is_valid and cand:
            self.select_candidate(cand)
        elif is_valid and not query:
            self.status_label.setText(t("settings_address_suggest_hint"))
            self.status_label.setStyleSheet("color: #cdd6f4; font-size: 11.5px;")
        else:
            self.current_candidate = None
            self.status_label.setText(f"❌ {t('settings_address_not_found')}")
            self.status_label.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 11.5px;")
            self.line_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #11111b;
                    color: #cdd6f4;
                    border: 1px solid #f38ba8;
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 12px;
                }
            """)
            if self.on_save_cb:
                self.on_save_cb(query, None)

    def _verify_initial(self, addr: str):
        def _worker():
            is_valid, cand, _ = address_service.verify_address(addr)
            if is_valid and cand:
                self.verification_finished.emit(True, cand, "")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_open_map(self):
        query = self.line_edit.text().strip()
        if not query:
            return

        lat = self.current_candidate.lat if self.current_candidate else None
        lon = self.current_candidate.lon if self.current_candidate else None
        url = AddressService.get_map_url(query, lat=lat, lon=lon)
        QDesktopServices.openUrl(QUrl(url))

    def get_address(self) -> str:
        return self.line_edit.text().strip()

    def set_address(self, addr: str, trigger_save: bool = False):
        self.line_edit.setText(addr or "")
        if trigger_save and addr:
            self._on_save_clicked()
        elif addr:
            self._verify_initial(addr)
        else:
            self.current_candidate = None
            self.status_label.setText(t("settings_address_suggest_hint"))
            self.status_label.setStyleSheet("color: #cdd6f4; font-size: 11.5px;")
