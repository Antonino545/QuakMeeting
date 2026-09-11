"""
Card 3: Included System Calendars for Linux Flight Deck.
"""

import threading

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
    QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.event_bus import event_bus
from core.services.language_service import t
from ui.linux.theme import get_combo_box_qss


class CalendarsCardWidget(QFrame):
    """Monitored system calendar sources filter and direct category mapping."""

    calendars_loaded = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        cc_layout = QVBoxLayout(self)
        cc_layout.setContentsMargins(18, 14, 18, 14)
        cc_layout.setSpacing(10)

        cc_title = QLabel(f"📅 {t('settings_calendars')}", self)
        cc_title.setObjectName("CardTitle")
        cc_sub = QLabel("Select which calendars to monitor and optionally link each directly to an event category.", self)
        cc_sub.setObjectName("CardSub")
        cc_layout.addWidget(cc_title)
        cc_layout.addWidget(cc_sub)

        self.content_host = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        loading_lbl = QLabel("Loading calendars...", self.content_host)
        loading_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
        self.content_layout.addWidget(loading_lbl)
        cc_layout.addWidget(self.content_host)

        self.calendars_loaded.connect(self._render_calendars)
        threading.Thread(target=self._load_calendars, daemon=True).start()

    def _load_calendars(self):
        try:
            self.calendars_loaded.emit(calendar_service.get_available_calendars())
        except Exception:
            self.calendars_loaded.emit([])

    def _render_calendars(self, avail_cals):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not avail_cals:
            empty_lbl = QLabel("All calendar sources are currently monitored.", self.content_host)
            empty_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
            self.content_layout.addWidget(empty_lbl)
            empty_lbl.show()
        else:
            list_widget = QWidget(self.content_host)
            list_layout = QVBoxLayout(list_widget)
            list_layout.setContentsMargins(0, 0, 0, 0)
            list_layout.setSpacing(8)

            category_options = [
                ("", t("cal_cat_auto")),
                ("study", t("cal_cat_study")),
                ("work", t("cal_cat_work")),
                ("concert", t("cal_cat_concert")),
                ("food", t("cal_cat_food")),
                ("travel", t("cal_cat_travel")),
                ("sport", t("cal_cat_sport")),
                ("in_person", t("cal_cat_in_person")),
                ("health", t("cal_cat_health")),
                ("general", t("cal_cat_general")),
            ]
            cal_map = config.get("calendar_category_map", {})
            if not isinstance(cal_map, dict):
                cal_map = {}

            for cal in avail_cals:
                c_name = cal.get("name", "Calendar")
                c_enabled = cal.get("enabled", True)
                display_name = c_name.replace("&", "&&")

                row_widget = QWidget(list_widget)
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)

                btn = QPushButton(f"📅 {display_name}", row_widget)
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setChecked(c_enabled)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #242438;
                        color: #cdd6f4;
                        border: 1px solid #45475a;
                        border-radius: 7px;
                        padding: 6px 14px;
                        font-size: 11.5px;
                        font-weight: 500;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background: #313244;
                        border-color: #a6e3a1;
                    }
                    QPushButton:checked {
                        background: #313244;
                        color: #a6e3a1;
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
                    try:
                        event_bus.publish("CONFIG_CHANGED", key="ignored_calendars", value=list(ignored))
                    except Exception:
                        pass
                btn.toggled.connect(_cal_toggled)
                row_layout.addWidget(btn)

                # Category Mapping Dropdown
                combo = QComboBox(row_widget)
                combo.setFixedHeight(28)
                combo.setFixedWidth(175)
                combo.setStyleSheet(get_combo_box_qss(bg_color="#242438", min_width=175))
                combo.setToolTip(t("cal_category_mapping"))

                mapped_val = cal_map.get(c_name, "")
                sel_idx = 0
                for opt_idx, (cat_val, cat_lbl) in enumerate(category_options):
                    combo.addItem(cat_lbl, cat_val)
                    if cat_val == mapped_val:
                        sel_idx = opt_idx
                combo.setCurrentIndex(sel_idx)

                def _cat_changed(idx_val, name=c_name, cb=combo):
                    val_cat = cb.itemData(idx_val)
                    cmap = config.get("calendar_category_map", {})
                    if not isinstance(cmap, dict):
                        cmap = {}
                    else:
                        cmap = cmap.copy()
                    if val_cat:
                        cmap[name] = val_cat
                    else:
                        cmap.pop(name, None)
                    config.set("calendar_category_map", cmap)
                    try:
                        event_bus.publish("CONFIG_CHANGED", key="calendar_category_map", value=cmap)
                    except Exception:
                        pass
                combo.currentIndexChanged.connect(_cat_changed)
                row_layout.addWidget(combo)

                list_layout.addWidget(row_widget)

            self.content_layout.addWidget(list_widget)
            list_widget.show()
