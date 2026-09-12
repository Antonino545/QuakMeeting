"""
PyQt6 Agenda Tab for FlightDeck Flight Deck on Linux.
Displays today's Command Center (NOW / NEXT / LATER) with "Why?" transparency,
countdown badges, location details, and 1-click actions.
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
from ui.common.agenda_viewmodel import AgendaViewModel, AgendaEventVM, CommandCenterVM

logger = logging.getLogger("FlightDeck.QtAgendaTab")


class QtAgendaTab(QWidget):
    """Today's Agenda Command Center tab component."""

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

    def _create_section_label(self, title: str, color: str = "#89b4fa") -> QLabel:
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color}; padding-top: 6px; padding-bottom: 2px; border: none; background: transparent;")
        return lbl

    def _create_hero_card(self, vm: AgendaEventVM, guidance: any) -> QFrame:
        """Prominent Hero Card with Why? explanation box for active or imminent events."""
        card = QFrame(self.scroll_content)
        card.setObjectName("HeroCard")
        border_color = "#fab387" if vm.is_urgent else "#89b4fa"
        card.setStyleSheet(f"""
            QFrame#HeroCard {{
                background-color: #181825;
                border: 2px solid {border_color};
                border-radius: 14px;
            }}
            QFrame#HeroCard:hover {{
                background-color: #1e1e2e;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(10)

        # Top row: Icon + Titles + Action buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        icon_l = QLabel(vm.icon, card)
        icon_l.setStyleSheet("font-size: 32px; border: none; background: transparent;")
        top_row.addWidget(icon_l)

        info_widget = QWidget(card)
        info_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        info_box = QVBoxLayout(info_widget)
        info_box.setSpacing(2)

        t_l = QLabel(f"{vm.time_display}  •  {vm.title}", card)
        t_l.setStyleSheet("font-size: 15px; font-weight: 700; color: #cdd6f4; border: none; background: transparent;")

        sub_txt = vm.subtitle
        if vm.badge_text:
            color = vm.badge_color or "#a6e3a1"
            badge_span = f"<span style='color:{color}; font-weight:bold;'>{vm.badge_text}</span>"
            sub_txt = f"{sub_txt}  •  {badge_span}" if sub_txt else badge_span

        s_l = QLabel(sub_txt, card)
        s_l.setStyleSheet("font-size: 12px; color: #a6adc8; border: none; background: transparent;")

        info_box.addWidget(t_l)
        info_box.addWidget(s_l)
        top_row.addWidget(info_widget, stretch=1)

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
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #b4befe;
                    border-color: #b4befe;
                }
            """)
            btn.clicked.connect(lambda chk, u=vm.action_url: QDesktopServices.openUrl(QUrl(u)))
            top_row.addWidget(btn)

            copy_btn = QPushButton("📋 Copy", card)
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #313244;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 8px;
                    padding: 8px 14px;
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
            top_row.addWidget(copy_btn)

        card_layout.addLayout(top_row)

        # "Why?" Transparency Box
        why_frame = QFrame(card)
        why_frame.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        why_box = QHBoxLayout(why_frame)
        why_box.setContentsMargins(8, 4, 8, 4)

        is_active_session = False
        if guidance and getattr(guidance, "action_type", None):
            from core.domain.context_engine import ActionType
            is_active_session = (guidance.action_type == ActionType.ACTIVE_SESSION)

        if is_active_session and guidance and getattr(guidance, 'rationale', None):
            why_text = str(guidance.rationale)
        elif guidance and getattr(guidance, 'rationale', None):
            why_text = f"💡 <b>Why:</b> {guidance.rationale}"
        else:
            why_text = f"💡 {vm.countdown_text or 'Active event'}"
        why_l = QLabel(why_text, why_frame)
        why_l.setStyleSheet("font-size: 12px; color: #f9e2af; border: none; background: transparent;")
        why_box.addWidget(why_l)

        card_layout.addWidget(why_frame)
        return card

    def _create_meeting_card(self, vm: AgendaEventVM, is_completed: bool = False) -> QFrame:
        card = QFrame(self.scroll_content)
        card.setObjectName("Card")
        bg_color = "#11111b" if is_completed else "#1e1e2e"
        hover_bg = "#181825" if is_completed else "#181825"
        border_color = "#313244"
        hover_border = "#45475a" if is_completed else "#cba6f7"
        card.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QFrame#Card:hover {{
                background-color: {hover_bg};
                border: 1px solid {hover_border};
            }}
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

        title_color = "#a6adc8" if is_completed else "#cdd6f4"
        t_l = QLabel(f"{vm.time_display}  •  {vm.title}", card)
        t_l.setObjectName("CardTitle")
        t_l.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {title_color}; border: none; background: transparent;")

        sub_txt = vm.subtitle
        if vm.badge_text:
            color = vm.badge_color or ("#6c7086" if is_completed else "#a6e3a1")
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
            btn_bg = "#313244" if is_completed else "#89b4fa"
            btn_fg = "#a6adc8" if is_completed else "#11111b"
            btn_border = "#45475a" if is_completed else "#89b4fa"
            btn = QPushButton(btn_text, card)
            btn.setObjectName("PrimaryBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_bg};
                    color: {btn_fg};
                    font-size: 12px;
                    font-weight: bold;
                    border: 1px solid {btn_border};
                    border-radius: 8px;
                    padding: 6px 14px;
                }}
                QPushButton:hover {{
                    background-color: #45475a;
                    border-color: #585b70;
                }}
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

        return card

    def refresh_agenda(self, meetings=None):
        """Refreshes the Command Center with today's scheduled meetings."""
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

        cc = AgendaViewModel.build_command_center(meetings)
        logger.debug("Refreshing Command Center with %d events scheduled today.", len(cc.all_events))

        if not cc.has_events:
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
            # 1. NOW SECTION
            if cc.now_event:
                self.scroll_layout.addWidget(self._create_section_label("⚡️ NOW"))
                hero = self._create_hero_card(cc.now_event, cc.guidance)
                self.scroll_layout.addWidget(hero)

            # 2. NEXT SECTION
            if cc.next_event:
                self.scroll_layout.addWidget(self._create_section_label("🗓️ NEXT"))
                next_card = self._create_meeting_card(cc.next_event)
                self.scroll_layout.addWidget(next_card)

            # 3. LATER SECTION
            if cc.later_events:
                self.scroll_layout.addWidget(self._create_section_label("🕒 LATER TODAY"))
                for ev in cc.later_events:
                    card = self._create_meeting_card(ev)
                    self.scroll_layout.addWidget(card)

            # 4. EARLIER TODAY SECTION (Completed sessions from earlier today)
            if cc.earlier_events:
                earlier_hdr = t("agenda_earlier_today", default="🏁 EARLIER TODAY")
                self.scroll_layout.addWidget(self._create_section_label(earlier_hdr, color="#6c7086"))
                for ev in cc.earlier_events:
                    card = self._create_meeting_card(ev, is_completed=True)
                    self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
