"""
Card 2: Departure Address & Multi-Modal Route ETA for Linux Flight Deck.
"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox,
)
from PyQt6.QtCore import Qt

from core.services.config_service import config
from core.services.event_bus import event_bus
from ui.linux.components.address_autocomplete_widget import QtAddressAutocompleteWidget


class ETACardWidget(QFrame):
    """Departure origins, exam locations, transit modes, and buffer margins."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        ac_layout = QVBoxLayout(self)
        ac_layout.setContentsMargins(18, 14, 18, 14)
        ac_layout.setSpacing(10)

        ac_title = QLabel("📍 Home / Departure Address & Multi-Modal Route ETA", self)
        ac_title.setObjectName("CardTitle")
        ac_sub = QLabel("Calculates real-time travel duration and departure times for Public Transit, Driving, Walking, or Cycling.", self)
        ac_sub.setObjectName("CardSub")
        ac_layout.addWidget(ac_title)
        ac_layout.addWidget(ac_sub)

        # 1. Starting Origin Address
        orig_lbl = QLabel("🏠 Starting Address (Origin):", self)
        orig_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        ac_layout.addWidget(orig_lbl)

        def _on_home_saved(chosen_text, cand=None):
            config.set("home_address", chosen_text)
            try:
                event_bus.publish("CONFIG_CHANGED", key="home_address", value=chosen_text)
            except Exception:
                pass

        self.home_addr_auto = QtAddressAutocompleteWidget(
            placeholder="Search home address or starting city (e.g. Corso Francia, Torino)...",
            initial_value=config.get("home_address", ""),
            on_save_cb=_on_home_saved,
            btn_gradient="green",
            parent=self
        )
        ac_layout.addWidget(self.home_addr_auto)

        # 2. University & Exam Campus Address
        exam_lbl = QLabel("🎓 University & Exam Campus:", self)
        exam_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold; margin-top: 6px;")
        ac_layout.addWidget(exam_lbl)

        exam_desc = QLabel("💡 Type any university or campus name. Automatically assigned to exams to calculate transit routes & ETA.", self)
        exam_desc.setStyleSheet("color: #a6adc8; font-size: 11px;")
        ac_layout.addWidget(exam_desc)

        def _on_exam_saved(chosen_text, cand=None):
            config.set("exam_location", chosen_text)
            try:
                event_bus.publish("CONFIG_CHANGED", key="exam_location", value=chosen_text)
            except Exception:
                pass

        self.exam_addr_auto = QtAddressAutocompleteWidget(
            placeholder="Type any university name (e.g. Politecnico di Torino, UniTo, Bocconi)...",
            initial_value=config.get("exam_location", "Politecnico di Torino, Corso Duca degli Abruzzi 24, Torino"),
            on_save_cb=_on_exam_saved,
            btn_gradient="mauve",
            parent=self
        )
        ac_layout.addWidget(self.exam_addr_auto)

        # 3. Transport Mode Selection
        mode_lbl = QLabel("🚦 Transport Mode for Route Calculation:", self)
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
        self.mode_btns = {}

        def _set_mode(selected_mode):
            config.set("transport_mode", selected_mode)
            try:
                event_bus.publish("CONFIG_CHANGED", key="transport_mode", value=selected_mode)
            except Exception:
                pass
            for m_key, b in self.mode_btns.items():
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
            m_btn = QPushButton(m_label, self)
            m_btn.setCheckable(True)
            m_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            def _make_mode_cb(k=m_key):
                return lambda: _set_mode(k)
            m_btn.clicked.connect(_make_mode_cb())
            self.mode_btns[m_key] = m_btn
            mode_row.addWidget(m_btn)

        mode_row.addStretch()
        ac_layout.addLayout(mode_row)
        _set_mode(curr_mode)

        # 4. Departure Buffer Margin
        buf_row = QHBoxLayout()
        buf_row.setSpacing(10)
        buf_lbl = QLabel("⌛ Departure Buffer Margin (station transit / parking time):", self)
        buf_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        buf_row.addWidget(buf_lbl)

        self.buf_combo = QComboBox(self)
        self.buf_combo.setFixedHeight(30)
        self.buf_combo.setStyleSheet("""
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
            self.buf_combo.addItem(b_lbl, b_val)
            if b_val == curr_buf:
                curr_buf_idx = idx
        self.buf_combo.setCurrentIndex(curr_buf_idx)

        def _buf_changed(idx_val):
            val_buf = self.buf_combo.itemData(idx_val)
            config.set("eta_buffer_minutes", int(val_buf))
            try:
                event_bus.publish("CONFIG_CHANGED", key="eta_buffer_minutes", value=int(val_buf))
            except Exception:
                pass
        self.buf_combo.currentIndexChanged.connect(_buf_changed)

        buf_row.addWidget(self.buf_combo)
        buf_row.addStretch()
        ac_layout.addLayout(buf_row)
