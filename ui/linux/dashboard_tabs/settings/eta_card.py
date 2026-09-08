"""
Card 2: Departure Address & Multi-Modal Route ETA for Linux Flight Deck.
"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from core.services.config_service import config
from core.services.event_bus import event_bus
from core.services.language_service import t
from ui.linux.components.address_autocomplete_widget import QtAddressAutocompleteWidget
from ui.linux.theme import get_combo_box_qss


class RouteConnectorWidget(QWidget):
    """Paints a transit line connector graphic: blue dot at origin, vertical line, purple dot at destination."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() // 2

        y1 = 28
        y2 = max(y1 + 30, self.height() - 28)

        p = self.parent()
        if p and hasattr(p, "home_addr_auto") and hasattr(p, "exam_addr_auto"):
            if p.home_addr_auto and p.exam_addr_auto:
                p_home = p.home_addr_auto.geometry().center().y()
                p_exam = p.exam_addr_auto.geometry().center().y()
                if p_home > 0 and p_exam > p_home:
                    y1 = p_home
                    y2 = p_exam

        # Draw vertical line
        pen = QPen(QColor("#45475a"), 2)
        painter.setPen(pen)
        painter.drawLine(cx, y1 + 5, cx, y2 - 5)

        # Draw origin blue dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#89b4fa")))
        painter.drawEllipse(cx - 5, y1 - 5, 10, 10)

        # Draw destination purple dot
        painter.setBrush(QBrush(QColor("#cba6f7")))
        painter.drawEllipse(cx - 5, y2 - 5, 10, 10)
        painter.end()


class ETACardWidget(QFrame):
    """Departure origins, exam locations, transit modes, and buffer margins."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        ac_layout = QVBoxLayout(self)
        ac_layout.setContentsMargins(18, 14, 18, 14)
        ac_layout.setSpacing(10)

        ac_title = QLabel(t("settings_eta_title"), self)
        ac_title.setObjectName("CardTitle")
        ac_sub = QLabel(t("settings_eta_subtitle"), self)
        ac_sub.setObjectName("CardSub")
        ac_layout.addWidget(ac_title)
        ac_layout.addWidget(ac_sub)

        # =========================================================================
        # 1. UNIFIED ROUTE CONTAINER (Origin + Destination with Transit Graphic)
        # =========================================================================
        route_frame = QFrame(self)
        route_frame.setObjectName("RouteContainer")
        route_frame.setStyleSheet("""
            QFrame#RouteContainer {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 10px;
            }
        """)
        route_layout = QHBoxLayout(route_frame)
        route_layout.setContentsMargins(12, 10, 12, 10)
        route_layout.setSpacing(10)

        connector = RouteConnectorWidget(route_frame)
        route_layout.addWidget(connector)

        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(8)

        # 1A. Origin Address
        orig_lbl = QLabel(t("settings_starting_address"), route_frame)
        orig_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        fields_layout.addWidget(orig_lbl)

        def _on_home_saved(chosen_text, cand=None):
            config.set("home_address", chosen_text)
            try:
                event_bus.publish("CONFIG_CHANGED", key="home_address", value=chosen_text)
            except Exception:
                pass

        self.home_addr_auto = QtAddressAutocompleteWidget(
            placeholder=t("settings_address_placeholder"),
            initial_value=config.get("home_address", ""),
            on_save_cb=_on_home_saved,
            btn_gradient="green",
            parent=route_frame
        )
        fields_layout.addWidget(self.home_addr_auto)

        # 1B. Destination Campus
        exam_lbl = QLabel(t("settings_exam_location"), route_frame)
        exam_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold; margin-top: 4px;")
        fields_layout.addWidget(exam_lbl)

        def _on_exam_saved(chosen_text, cand=None):
            config.set("exam_location", chosen_text)
            try:
                event_bus.publish("CONFIG_CHANGED", key="exam_location", value=chosen_text)
            except Exception:
                pass

        self.exam_addr_auto = QtAddressAutocompleteWidget(
            placeholder=t("settings_exam_location_placeholder"),
            initial_value=config.get("exam_location", "Politecnico di Torino, Corso Duca degli Abruzzi 24, Torino"),
            on_save_cb=_on_exam_saved,
            btn_gradient="mauve",
            parent=route_frame
        )
        fields_layout.addWidget(self.exam_addr_auto)

        route_frame.home_addr_auto = self.home_addr_auto
        route_frame.exam_addr_auto = self.exam_addr_auto

        route_layout.addLayout(fields_layout)
        ac_layout.addWidget(route_frame)

        # =========================================================================
        # 2. CARD-LEVEL DIVIDER (Exactly ONE hairline divider on the card)
        # =========================================================================
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #313244; max-height: 1px; border: none; margin: 4px 0px;")
        ac_layout.addWidget(sep)

        # =========================================================================
        # 3. TRANSPORT MODE (Connected Segmented Control)
        # =========================================================================
        mode_lbl = QLabel(t("settings_transport_calc"), self)
        mode_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        ac_layout.addWidget(mode_lbl)

        mode_frame = QFrame(self)
        mode_frame.setObjectName("TransportSegmentedControl")
        mode_frame.setStyleSheet("""
            QFrame#TransportSegmentedControl {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
            }
        """)
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(2, 2, 2, 2)
        mode_layout.setSpacing(0)

        modes = [
            ("transit", t("settings_public_transit")),
            ("automobile", t("settings_driving_mode")),
            ("bicycling", t("settings_cycling_mode")),
            ("walking", t("settings_walking_mode"))
        ]
        curr_mode = config.get("transport_mode", "transit")
        self.mode_btns = {}

        def _get_buffer_hint(m):
            hints = {
                "transit": t("settings_buffer_hint_transit"),
                "automobile": t("settings_buffer_hint_driving"),
                "bicycling": t("settings_buffer_hint_cycling"),
                "walking": t("settings_buffer_hint_walking"),
            }
            return hints.get(m, t("settings_buffer_hint_transit"))

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
                            border: none;
                            border-radius: 6px;
                            padding: 6px 12px;
                            font-size: 12px;
                        }
                    """)
                else:
                    b.setStyleSheet("""
                        QPushButton {
                            background: transparent;
                            color: #a6adc8;
                            font-weight: 500;
                            border: none;
                            border-radius: 6px;
                            padding: 6px 12px;
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background: #45475a;
                            color: #cdd6f4;
                        }
                    """)
            if hasattr(self, "buf_hint_lbl") and self.buf_hint_lbl:
                self.buf_hint_lbl.setText(_get_buffer_hint(selected_mode))

        for m_key, m_label in modes:
            m_btn = QPushButton(m_label, mode_frame)
            m_btn.setCheckable(True)
            m_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            def _make_mode_cb(k=m_key):
                return lambda: _set_mode(k)
            m_btn.clicked.connect(_make_mode_cb())
            self.mode_btns[m_key] = m_btn
            mode_layout.addWidget(m_btn, 1)

        ac_layout.addWidget(mode_frame)

        # =========================================================================
        # 4. DEPARTURE BUFFER MARGIN (Directly beneath Transport Mode, no divider)
        # =========================================================================
        buf_row = QHBoxLayout()
        buf_row.setSpacing(10)

        buf_text_layout = QVBoxLayout()
        buf_text_layout.setSpacing(2)

        buf_lbl = QLabel(t("settings_departure_buffer"), self)
        buf_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        buf_text_layout.addWidget(buf_lbl)

        self.buf_hint_lbl = QLabel(self)
        self.buf_hint_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.buf_hint_lbl.setText(_get_buffer_hint(curr_mode))
        buf_text_layout.addWidget(self.buf_hint_lbl)

        buf_row.addLayout(buf_text_layout)
        buf_row.addStretch()

        self.buf_combo = QComboBox(self)
        self.buf_combo.setFixedHeight(30)
        self.buf_combo.setStyleSheet(get_combo_box_qss(bg_color="#242438", min_width=170))

        buf_options = [
            (0, t("buffer_0m")),
            (5, t("buffer_5m")),
            (10, t("buffer_10m_rec")),
            (15, t("buffer_15m")),
            (20, t("buffer_20m")),
            (30, t("buffer_30m"))
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
        ac_layout.addLayout(buf_row)

        _set_mode(curr_mode)

        # 5. Smart Auto-Walking Threshold
        walk_row = QHBoxLayout()
        walk_row.setSpacing(10)
        walk_lbl = QLabel("🚶 Smart Auto-Walking (auto-switch if venue is close):", self)
        walk_lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        walk_row.addWidget(walk_lbl)

        self.walk_combo = QComboBox(self)
        self.walk_combo.setFixedHeight(30)
        self.walk_combo.setStyleSheet(get_combo_box_qss(bg_color="#242438", min_width=170))

        walk_options = [
            (0.0, "Disabled"),
            (0.8, "Under 800 m"),
            (1.2, "Under 1.2 km (Recommended)"),
            (1.5, "Under 1.5 km"),
            (2.0, "Under 2.0 km")
        ]
        curr_walk = float(config.get("auto_walking_threshold_km", 1.2))
        curr_walk_idx = 2
        for idx, (w_val, w_lbl) in enumerate(walk_options):
            self.walk_combo.addItem(w_lbl, w_val)
            if abs(w_val - curr_walk) < 0.01:
                curr_walk_idx = idx
        self.walk_combo.setCurrentIndex(curr_walk_idx)

        def _walk_changed(idx_val):
            val_walk = float(self.walk_combo.itemData(idx_val))
            config.set("auto_walking_threshold_km", val_walk)
            try:
                event_bus.publish("CONFIG_CHANGED", key="auto_walking_threshold_km", value=val_walk)
            except Exception:
                pass
        self.walk_combo.currentIndexChanged.connect(_walk_changed)

        walk_row.addWidget(self.walk_combo)
        walk_row.addStretch()
        ac_layout.addLayout(walk_row)
