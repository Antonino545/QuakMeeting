import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt

from core.services.language_service import t
from ui.linux.dashboard_tabs.settings.timing_card import TimingCardWidget
from ui.linux.dashboard_tabs.settings.eta_card import ETACardWidget
from ui.linux.dashboard_tabs.settings.arrival_card import ArrivalCardWidget
from ui.linux.dashboard_tabs.settings.calendars_card import CalendarsCardWidget
from ui.linux.dashboard_tabs.settings.system_card import SystemCardWidget, QtUpdateBridge

logger = logging.getLogger("QuakMeeting.QtSettingsTab")


class QtSettingsTab(QWidget):
    """Preferences & Timing Settings tab with two-pane sidebar navigation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # -------------------------------------------------------------
        # 1. Left Sidebar Navigation
        # -------------------------------------------------------------
        sidebar_frame = QFrame(self)
        sidebar_frame.setObjectName("SettingsSidebarFrame")
        sidebar_frame.setFixedWidth(210)
        sidebar_frame.setStyleSheet("""
            QFrame#SettingsSidebarFrame {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 12px;
            }
        """)
        s_layout = QVBoxLayout(sidebar_frame)
        s_layout.setContentsMargins(8, 12, 8, 12)
        s_layout.setSpacing(6)

        title_lbl = QLabel(t("settings_categories_header"), sidebar_frame)
        title_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #6c7086; letter-spacing: 1px; padding-left: 6px; margin-bottom: 4px;")
        s_layout.addWidget(title_lbl)

        self.category_items = [
            ("⏱️", t("settings_cat_reminders"), t("settings_cat_reminders_sub"), 0),
            ("📍", t("settings_cat_presence"), t("settings_cat_presence_sub"), 1),
            ("📅", t("settings_cat_calendars"), t("settings_cat_calendars_sub"), 2),
            ("🚗", t("settings_cat_commute"), t("settings_cat_commute_sub"), 3),
            ("⚙️", t("settings_cat_preferences"), t("settings_cat_preferences_sub"), 4),
        ]

        # -------------------------------------------------------------
        # 2. Right Content Stack
        # -------------------------------------------------------------
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                background-color: transparent;
            }
        """)

        def _wrap_in_scroll(cards):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
            """)
            if scroll.viewport():
                scroll.viewport().setStyleSheet("background-color: transparent;")

            content = QWidget()
            content.setStyleSheet("background-color: transparent;")
            c_layout = QVBoxLayout(content)
            c_layout.setContentsMargins(0, 0, 10, 0)
            c_layout.setSpacing(14)
            for c in cards:
                c_layout.addWidget(c)
            c_layout.addStretch()
            scroll.setWidget(content)

            page = QWidget()
            page.setStyleSheet("background-color: transparent;")
            p_layout = QVBoxLayout(page)
            p_layout.setContentsMargins(0, 0, 0, 0)
            p_layout.addWidget(scroll)
            return page

        # Initialize sub-cards
        self.timing_card = TimingCardWidget(self)
        self.arrival_card = ArrivalCardWidget(self)
        self.calendars_card = CalendarsCardWidget(self)
        self.eta_card = ETACardWidget(self)
        self.system_card = SystemCardWidget(self)
        self.update_bridge = self.system_card.update_bridge

        # Category pages
        self.page_timing = _wrap_in_scroll([self.timing_card])
        self.page_arrival = _wrap_in_scroll([self.arrival_card])
        self.page_calendars = _wrap_in_scroll([self.calendars_card])
        self.page_commute = _wrap_in_scroll([self.eta_card])
        self.page_preferences = _wrap_in_scroll([self.system_card])

        self.stacked_widget.addWidget(self.page_timing)
        self.stacked_widget.addWidget(self.page_arrival)
        self.stacked_widget.addWidget(self.page_calendars)
        self.stacked_widget.addWidget(self.page_commute)
        self.stacked_widget.addWidget(self.page_preferences)

        # Build sidebar buttons
        self.category_buttons = []
        for icon, title, subtitle, idx in self.category_items:
            btn = QPushButton(sidebar_frame)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(54)

            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(10, 6, 10, 6)
            btn_layout.setSpacing(10)

            icon_lbl = QLabel(icon, btn)
            icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
            btn_layout.addWidget(icon_lbl)

            text_v = QVBoxLayout()
            text_v.setSpacing(1)
            t_lbl = QLabel(title, btn)
            t_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #cdd6f4; background: transparent;")
            st_lbl = QLabel(subtitle, btn)
            st_lbl.setStyleSheet("font-size: 10px; color: #a6adc8; background: transparent;")
            text_v.addWidget(t_lbl)
            text_v.addWidget(st_lbl)
            btn_layout.addLayout(text_v, stretch=1)

            arrow_lbl = QLabel("›", btn)
            arrow_lbl.setStyleSheet("font-size: 16px; color: #89b4fa; background: transparent; font-weight: bold;")
            btn_layout.addWidget(arrow_lbl)

            btn.clicked.connect(lambda chk=False, i=idx: self.select_category(i))
            s_layout.addWidget(btn)
            self.category_buttons.append(btn)

        s_layout.addStretch()

        layout.addWidget(sidebar_frame)
        layout.addWidget(self.stacked_widget, stretch=1)

        # Set initial active category
        self.select_category(0)

    def select_category(self, index: int):
        """Switch active settings category page and update button styles."""
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.category_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #313244;
                        border: 1px solid #89b4fa;
                        border-left: 4px solid #89b4fa;
                        border-radius: 8px;
                        text-align: left;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: 1px solid transparent;
                        border-radius: 8px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #1e1e2e;
                        border-color: #45475a;
                    }
                """)


__all__ = ["QtSettingsTab", "QtUpdateBridge"]
