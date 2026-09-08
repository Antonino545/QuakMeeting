"""
Card 3: Included System Calendars for Linux Flight Deck.
"""

import threading

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.services.config_service import config
from core.services.calendar_service import calendar_service


class CalendarsCardWidget(QFrame):
    """Monitored system calendar sources filter."""

    calendars_loaded = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        cc_layout = QVBoxLayout(self)
        cc_layout.setContentsMargins(18, 14, 18, 14)
        cc_layout.setSpacing(10)

        cc_title = QLabel("📅 Included System Calendars", self)
        cc_title.setObjectName("CardTitle")
        cc_sub = QLabel("Select which local, EDS, or CalDAV calendars to actively monitor for reminders.", self)
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
        else:
            grid_widget = QWidget(self.content_host)
            grid_layout = QVBoxLayout(grid_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(8)

            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            count_in_row = 0

            for cal in avail_cals:
                c_name = cal.get("name", "Calendar")
                c_enabled = cal.get("enabled", True)
                display_name = c_name.replace("&", "&&")
                btn = QPushButton(f"📅 {display_name}", grid_widget)
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setChecked(c_enabled)
                btn.setMinimumWidth(btn.sizeHint().width() + 16)
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
                if count_in_row >= 2:
                    row_layout.addStretch()
                    grid_layout.addLayout(row_layout)
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(8)
                    count_in_row = 0

            if count_in_row > 0:
                row_layout.addStretch()
                grid_layout.addLayout(row_layout)

            self.content_layout.addWidget(grid_widget)
