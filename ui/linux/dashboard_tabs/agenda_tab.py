"""
PyQt6 Agenda Tab for QuakMeeting Flight Deck on Linux.
Displays today's meeting timeline with countdown badges, location details,
and 1-click joins for online meetings (Zoom/Meet/Teams/Serenis) and navigation routes.
"""

import urllib.parse
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices

from core.services.calendar_service import calendar_service
from core.services.language_service import t
from core.domain.models import format_duration
from core.domain.classifier import EventClassifier
from ui.common.agenda_viewmodel import AgendaViewModel, AgendaEventVM

logger = logging.getLogger("QuakMeeting.QtAgendaTab")


class QtAgendaTab(QWidget):
    """Today's Agenda timeline tab component."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)

        layout.addWidget(self.scroll)
        self._show_status("Loading today's agenda...", "#a6adc8")
        QTimer.singleShot(0, self.refresh_agenda)

    def _show_status(self, message, color):
        """Render a safe placeholder while calendar data is unavailable."""
        status = QLabel(message)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet(f"font-size: 15px; color: {color}; border: none;")
        self.scroll_layout.addWidget(status)
        self.scroll_layout.addStretch()

    def refresh_agenda(self, meetings=None):
        """Refreshes the timeline list with today's scheduled meetings."""
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if meetings is None:
            try:
                meetings = calendar_service.get_upcoming_meetings()
            except Exception:
                logger.exception("Unable to load the cached agenda.")
                self._show_status(
                    "Unable to load the agenda. Calendar data will retry shortly.",
                    "#f38ba8",
                )
                QTimer.singleShot(5000, self.refresh_agenda)
                return

        vms = AgendaViewModel.build(meetings)
        logger.debug("Refreshing agenda with %d meetings, %d scheduled today.", len(meetings or []), len(vms))

        if not vms:
            empty_box = QVBoxLayout()
            empty_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_icon = QLabel("🧘‍♂️")
            e_icon.setStyleSheet("font-size: 48px; border: none;")
            e_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            e_msg = QLabel("No Meetings Scheduled for Today\nEnjoy your clear agenda or add events to your calendar.")
            e_msg.setStyleSheet("font-size: 15px; font-weight: bold; color: #bac2de; border: none;")
            e_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_box.addWidget(e_icon)
            empty_box.addWidget(e_msg)
            self.scroll_layout.addLayout(empty_box)
        else:
            for idx, vm in enumerate(vms):
                card = QFrame(self.scroll_content)
                card.setObjectName("Card")
                card.setStyleSheet("""
                    QFrame#Card {
                        background-color: #1e1e2e;
                        border: 1px solid #313244;
                        border-radius: 12px;
                    }
                    QFrame#Card:hover {
                        background-color: #181825;
                        border: 1px solid #cba6f7;
                    }
                """)
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(18, 14, 18, 14)
                c_layout.setSpacing(14)

                icon_l = QLabel(vm.icon, card)
                icon_l.setStyleSheet("font-size: 26px; border: none; background: transparent;")
                c_layout.addWidget(icon_l)

                info_widget = QWidget(card)
                info_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                info_box = QVBoxLayout(info_widget)
                info_box.setSpacing(2)

                t_l = QLabel(f"{vm.time_display}  •  {vm.title}", card)
                t_l.setObjectName("CardTitle")
                t_l.setStyleSheet("font-size: 14px; font-weight: 700; color: #cdd6f4; border: none; background: transparent;")

                sub_txt = vm.subtitle
                if vm.badge_text:
                    color = vm.badge_color or "#a6e3a1"
                    badge_span = f"<span style='color:{color}; font-weight:bold;'>{vm.badge_text}</span>"
                    sub_txt = f"{sub_txt}  •  {badge_span}" if sub_txt else badge_span

                s_l = QLabel(sub_txt, card)
                s_l.setObjectName("CardSub")
                s_l.setStyleSheet("font-size: 11.5px; color: #a6adc8; border: none; background: transparent;")

                info_box.addWidget(t_l)
                info_box.addWidget(s_l)
                c_layout.addWidget(info_widget, stretch=1)

                if vm.has_action:
                    btn_text = vm.action_btn_text or "🚀 Join"
                    btn = QPushButton(btn_text, card)
                    btn.setObjectName("PrimaryBtn")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #89b4fa;
                            color: #11111b;
                            font-size: 12px;
                            font-weight: bold;
                            border: 1px solid #89b4fa;
                            border-radius: 8px;
                            padding: 6px 14px;
                        }
                        QPushButton:hover {
                            background-color: #b4befe;
                            border-color: #b4befe;
                        }
                    """)
                    btn.clicked.connect(lambda chk, u=vm.action_url: QDesktopServices.openUrl(QUrl(u)))
                    c_layout.addWidget(btn)

                    copy_btn = QPushButton("📋 Copy", card)
                    copy_btn.setObjectName("OutlineBtn")
                    copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    copy_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #313244;
                            color: #cdd6f4;
                            border: 1px solid #45475a;
                            font-size: 12px;
                            font-weight: 600;
                            border-radius: 8px;
                            padding: 6px 12px;
                        }
                        QPushButton:hover {
                            background-color: #45475a;
                            border-color: #89b4fa;
                        }
                    """)
                    def _copy_url(url=vm.action_url, b=copy_btn):
                        QApplication.clipboard().setText(url)
                        b.setText("✓ Copied!")
                        QTimer.singleShot(1500, lambda: b.setText("📋 Copy"))
                    copy_btn.clicked.connect(lambda chk, u=vm.action_url, b=copy_btn: _copy_url(u, b))
                    c_layout.addWidget(copy_btn)

                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
