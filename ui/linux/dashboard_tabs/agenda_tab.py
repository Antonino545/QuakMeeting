"""
PyQt6 Agenda Tab for QuakMeeting Flight Deck on Linux.
Displays today's meeting timeline with countdown badges, location details,
and 1-click joins for online meetings (Zoom/Meet/Teams/Serenis) and navigation routes.
"""

import urllib.parse
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices

from core.services.calendar_service import calendar_service
from core.domain.models import format_duration
from core.domain.classifier import EventClassifier


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
        self.refresh_agenda()

    def refresh_agenda(self, meetings=None):
        """Refreshes the timeline list with today's scheduled meetings."""
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        now = datetime.now().astimezone()
        if meetings is None:
            meetings = calendar_service.get_upcoming_meetings()

        today_meets = [m for m in meetings if m.start_time and m.start_time.astimezone().date() == now.date()]

        if not today_meets:
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
            for idx, m in enumerate(today_meets):
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

                pilot_icon = "🦆"
                if m.pilot_type == "chef": pilot_icon = "🍕"
                elif m.pilot_type == "captain": pilot_icon = "✈️"
                elif m.pilot_type == "owl": pilot_icon = "🎓"
                elif m.pilot_type == "gym": pilot_icon = "🏋️‍♂️"
                elif m.pilot_type == "driver": pilot_icon = "🚗"
                elif m.pilot_type == "zen_duck": pilot_icon = "🛋️"

                icon_l = QLabel(pilot_icon, card)
                icon_l.setStyleSheet("font-size: 26px; border: none; background: transparent;")
                c_layout.addWidget(icon_l)

                info_widget = QWidget(card)
                info_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                info_box = QVBoxLayout(info_widget)
                info_box.setSpacing(2)

                st = m.start_time.astimezone().strftime("%H:%M") if m.start_time else "--:--"
                et = m.end_time.astimezone().strftime("%H:%M") if m.end_time else ""
                dur_str = f" ({format_duration(m.duration_minutes)})" if m.duration_minutes else ""

                t_l = QLabel(f"{st} - {et}  •  {m.title}{dur_str}", card)
                t_l.setObjectName("CardTitle")
                t_l.setStyleSheet("font-size: 14px; font-weight: 700; color: #cdd6f4; border: none; background: transparent;")

                sub_txt = m.provider
                if m.location and m.location != "missing value":
                    sub_txt += f"  •  📍 {m.location[:35]}"
                if m.is_travel and m.departure_time:
                    sub_txt += f"  •  <span style='color:#f9e2af;'>🚗 Leave at {m.departure_time.astimezone().strftime('%H:%M')}</span>"
                if m.classroom:
                    sub_txt += f"  •  <span style='color:#cba6f7;'>🏫 {m.classroom}</span>"

                s_l = QLabel(sub_txt, card)
                s_l.setObjectName("CardSub")
                s_l.setStyleSheet("font-size: 11.5px; color: #a6adc8; border: none; background: transparent;")

                info_box.addWidget(t_l)
                info_box.addWidget(s_l)
                c_layout.addWidget(info_widget, stretch=1)

                extracted_meeting_url = EventClassifier.extract_meeting_url(
                    f"{m.location} {m.description}"
                )
                action_url = m.action_url or m.meeting_url
                if extracted_meeting_url and (
                    not action_url or action_url == "https://calendar.apple.com"
                ):
                    action_url = extracted_meeting_url
                if not action_url and m.location and m.location != "missing value":
                    action_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(m.location)}"

                has_real_url = bool(action_url and action_url.strip() and action_url != "https://calendar.apple.com")
                if has_real_url:
                    btn_text = m.action_btn_text or ("🚀 Join" if not m.is_travel else "🗺️ Maps")
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
                    btn.clicked.connect(lambda chk, u=action_url: QDesktopServices.openUrl(QUrl(u)))
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
                    def _copy_url(url=action_url, b=copy_btn):
                        QApplication.clipboard().setText(url)
                        b.setText("✓ Copied!")
                        QTimer.singleShot(1500, lambda: b.setText("📋 Copy"))
                    copy_btn.clicked.connect(lambda chk, u=action_url, b=copy_btn: _copy_url(u, b))
                    c_layout.addWidget(copy_btn)

                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
