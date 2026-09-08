"""
Reusable Address Autocomplete Widget for Linux PyQt6 (Google Maps style).
Provides continuous, non-interrupting search-as-you-type suggestions with a popup list,
instant geocoding verification status, and one-click browser map preview.
"""
import logging
import threading
from typing import Optional, Callable, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QPoint
from PyQt6.QtGui import QDesktopServices

from core.services.address_service import address_service, AddressCandidate, AddressService
from core.services.config_service import is_debug_mode
from core.services.language_service import t

logger = logging.getLogger("QuakMeeting.AddressAutocomplete")


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
        self._last_search_query: str = ""

        self._init_ui()
        self._setup_signals()

        if self.initial_value_str:
            self._verify_initial(self.initial_value_str)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        from PyQt6.QtWidgets import QFrame

        self.is_editing = not bool(self.initial_value_str)

        # =====================================================================
        # 1. EDITING CONTAINER (Text field + Map icon + Save button)
        # =====================================================================
        self.edit_container = QWidget(self)
        edit_layout = QVBoxLayout(self.edit_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(3)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(6)

        self.line_edit = QLineEdit(self.edit_container)
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

        self.map_btn = QPushButton("🗺️", self.edit_container)
        self.map_btn.setFixedSize(32, 28)
        self.map_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_btn.setStyleSheet("""
            QPushButton {
                background: #313244;
                color: #cdd6f4;
                font-size: 12px;
                border-radius: 6px;
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

        self.save_btn = QPushButton(f"💾 {t('save')}", self.edit_container)
        self.save_btn.setFixedHeight(28)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {grad_stops});
                color: #ffffff;
                font-weight: bold;
                font-size: 11.5px;
                border-radius: 6px;
                padding: 4px 14px;
                border: 1px solid {border_col};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {grad_hover});
            }}
        """)
        input_row.addWidget(self.save_btn)
        edit_layout.addLayout(input_row)

        self.status_label = QLabel("", self.edit_container)
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.status_label.setVisible(False)
        edit_layout.addWidget(self.status_label)

        main_layout.addWidget(self.edit_container)

        # =====================================================================
        # 2. CONFIRMED CONTAINER (Compact single-row result card)
        # =====================================================================
        self.confirmed_container = QFrame(self)
        self.confirmed_container.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
            }
        """)
        confirmed_layout = QHBoxLayout(self.confirmed_container)
        confirmed_layout.setContentsMargins(10, 4, 6, 4)
        confirmed_layout.setSpacing(8)

        self.confirmed_label = QLabel("", self.confirmed_container)
        self.confirmed_label.setStyleSheet("border: none; background: transparent;")
        confirmed_layout.addWidget(self.confirmed_label, stretch=1)

        self.confirmed_map_btn = QPushButton("🗺️", self.confirmed_container)
        self.confirmed_map_btn.setFixedSize(28, 22)
        self.confirmed_map_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirmed_map_btn.setStyleSheet("""
            QPushButton {
                background: #242438;
                color: #cdd6f4;
                font-size: 11px;
                border-radius: 5px;
                border: 1px solid #313244;
            }
            QPushButton:hover {
                background: #313244;
            }
        """)
        confirmed_layout.addWidget(self.confirmed_map_btn)

        self.edit_btn = QPushButton(f"✏️ {t('settings_address_edit')}", self.confirmed_container)
        self.edit_btn.setFixedHeight(22)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background: #313244;
                color: #cdd6f4;
                font-size: 11px;
                border-radius: 5px;
                padding: 2px 10px;
                border: 1px solid #45475a;
            }
            QPushButton:hover {
                background: #45475a;
            }
        """)
        confirmed_layout.addWidget(self.edit_btn)

        main_layout.addWidget(self.confirmed_container)

        # Popup Suggestions List — uses ToolTip window type instead of Popup
        # because Qt.WindowType.Popup grabs keyboard+mouse on Linux/X11,
        # stealing focus from the QLineEdit and blocking further typing.
        self.popup_list = QListWidget()
        self.popup_list.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.popup_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.popup_list.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
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

        if self.initial_value_str:
            self._update_confirmed_row(None, self.initial_value_str)
            self.set_editing(False)
        else:
            self.set_editing(True)

    def _setup_signals(self):
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.returnPressed.connect(self._on_save_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.map_btn.clicked.connect(self._on_open_map)
        self.confirmed_map_btn.clicked.connect(self._on_open_map)
        self.edit_btn.clicked.connect(self._on_edit_clicked)

        self.suggestions_ready.connect(self._handle_suggestions_ready)
        self.verification_finished.connect(self._handle_verification_finished)

        # Event filter to dismiss popup when focus leaves the line edit or Escape is pressed
        # (ToolTip windows don't auto-dismiss like Popup windows).
        self.line_edit.installEventFilter(self)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self.line_edit:
            if event.type() == QEvent.Type.FocusOut:
                # Small delay so item-click signals fire before the popup hides.
                QTimer.singleShot(150, self.popup_list.hide)
                if is_debug_mode():
                    logger.debug("📋 Popup hidden (line edit lost focus)")
            elif event.type() == QEvent.Type.KeyPress:
                from PyQt6.QtCore import Qt as QtConst
                if event.key() == QtConst.Key.Key_Escape:
                    self.popup_list.hide()
                    if is_debug_mode():
                        logger.debug("📋 Popup hidden (Escape pressed)")
        return super().eventFilter(obj, event)

    def _on_text_changed(self, text: str):
        self.debounce_timer.start()

    def _on_debounced_search(self):
        query = self.line_edit.text().strip()
        if len(query) < 3:
            self.popup_list.hide()
            return

        if is_debug_mode():
            logger.debug("🔍 Autocomplete search triggered for query=%r", query)

        self.popup_list.clear()
        item = QListWidgetItem(t("settings_address_searching"))
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.popup_list.addItem(item)
        global_pos = self.line_edit.mapToGlobal(QPoint(0, self.line_edit.height() + 2))
        self.popup_list.setFixedWidth(max(360, self.line_edit.width()))
        self.popup_list.setFixedHeight(36)
        self.popup_list.move(global_pos)
        self.popup_list.show()

        # Capture the current query text on the main thread so the background
        # worker never accesses Qt widgets (which would deadlock the app).
        snapshot_query = query
        self._last_search_query = snapshot_query

        def _worker():
            if is_debug_mode():
                logger.debug("🌐 Background search worker started for query=%r", snapshot_query)
            candidates = address_service.search_suggestions(snapshot_query, limit=4)
            if is_debug_mode():
                logger.debug("🌐 Background search worker finished: %d candidates for query=%r", len(candidates), snapshot_query)
            # Emit only if the query hasn't changed; the signal is thread-safe.
            self.suggestions_ready.emit(candidates)

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_suggestions_ready(self, candidates: List[AddressCandidate]):
        # Discard results from a stale search (user kept typing).
        current_text = self.line_edit.text().strip()
        if current_text != self._last_search_query:
            if is_debug_mode():
                logger.debug("📋 Discarding stale results (current=%r, search=%r)", current_text, self._last_search_query)
            return
        self._candidates = candidates
        self.popup_list.clear()

        if not candidates:
            item = QListWidgetItem(t("settings_address_not_found"))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.popup_list.addItem(item)
            self.popup_list.setFixedHeight(36)
            self.popup_list.show()
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

    def set_editing(self, is_editing: bool):
        self.is_editing = is_editing
        self.edit_container.setVisible(is_editing)
        self.confirmed_container.setVisible(not is_editing)
        if not is_editing:
            if hasattr(self, "popup_list") and self.popup_list:
                self.popup_list.hide()
            self.status_label.setVisible(False)

    def _on_edit_clicked(self):
        self.set_editing(True)
        self.line_edit.setFocus()
        self.line_edit.selectAll()

    def _update_confirmed_row(self, candidate: Optional[AddressCandidate], raw_text: str = ""):
        short_addr = ""
        secondary = ""
        if candidate:
            short_addr = candidate.short_address or candidate.display_name or raw_text
            parts = []
            if candidate.city:
                parts.append(candidate.city)
            if candidate.postcode:
                parts.append(candidate.postcode)
            secondary = ", ".join(parts)
        elif raw_text:
            short_addr = raw_text.split(",")[0].strip()
            parts = [p.strip() for p in raw_text.split(",")[1:] if p.strip()]
            secondary = ", ".join(parts[:2])

        sec_html = f"&nbsp;&nbsp;<span style='color: #a6adc8; font-size: 11px;'>· {secondary}</span>" if secondary else ""
        html = f"<span style='color: #a6e3a1; font-weight: bold; font-size: 12px;'>✓</span> &nbsp;<span style='color: #cdd6f4; font-weight: bold; font-size: 12px;'>{short_addr}</span>{sec_html}"
        self.confirmed_label.setText(html)

    def select_candidate(self, candidate: AddressCandidate):
        self.popup_list.hide()
        self.current_candidate = candidate
        if is_debug_mode():
            logger.debug("✅ Candidate selected: %s (lat=%.4f, lon=%.4f)", candidate.short_address, candidate.lat, candidate.lon)

        chosen_text = candidate.short_address or candidate.display_name
        self.line_edit.blockSignals(True)
        self.line_edit.setText(chosen_text)
        self.line_edit.blockSignals(False)

        self._update_confirmed_row(candidate, chosen_text)
        self.save_btn.setText(f"✓ {t('saved')}")

        def _transition_confirmed():
            self.save_btn.setText(f"💾 {t('save')}")
            self.set_editing(False)

        QTimer.singleShot(500, _transition_confirmed)

        if self.on_save_cb:
            self.on_save_cb(chosen_text, candidate)

    def _on_save_clicked(self):
        query = self.line_edit.text().strip()
        self.popup_list.hide()
        if is_debug_mode():
            logger.debug("💾 Save clicked, verifying address=%r", query)

        if not query:
            self.current_candidate = None
            self.status_label.setVisible(False)
            self._update_confirmed_row(None, "")
            self.set_editing(True)
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
            return

        self.status_label.setVisible(True)
        self.status_label.setText(t("settings_address_searching"))
        self.status_label.setStyleSheet("color: #89b4fa; font-size: 11px;")
        self.save_btn.setText("⏳ ...")

        def _worker():
            is_valid, cand, err = address_service.verify_address(query)
            self.verification_finished.emit(is_valid, cand, err or "")

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_verification_finished(self, is_valid: bool, cand: Optional[AddressCandidate], err: str):
        self.save_btn.setText(f"💾 {t('save')}")
        query = self.line_edit.text().strip()
        if is_debug_mode():
            logger.debug("📍 Verification result: valid=%s, candidate=%s, error=%r", is_valid, cand.short_address if cand else None, err)
        if is_valid and cand:
            self.select_candidate(cand)
        else:
            self.current_candidate = None
            self.status_label.setVisible(True)
            self.status_label.setText(f"❌ {t('settings_address_not_found')}")
            self.status_label.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 11px;")
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
            self.set_editing(True)
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
        if not query and self.current_candidate:
            query = self.current_candidate.display_name or self.current_candidate.short_address
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
            self._update_confirmed_row(None, addr)
            self.set_editing(False)
            self._verify_initial(addr)
        else:
            self.current_candidate = None
            self._update_confirmed_row(None, "")
            self.set_editing(True)
            self.status_label.setVisible(False)
