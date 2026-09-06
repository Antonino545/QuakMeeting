"""
Card 3: Included System Calendars for Linux Flight Deck.
"""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt

from core.services.config_service import config
from core.services.calendar_service import calendar_service


class CalendarsCardWidget(QFrame):
    """Monitored system calendar sources filter."""

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

        avail_cals = calendar_service.get_available_calendars()
        if not avail_cals:
            empty_lbl = QLabel("All calendar sources are currently monitored.", self)
            empty_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
            cc_layout.addWidget(empty_lbl)
        else:
            grid_widget = QWidget(self)
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
