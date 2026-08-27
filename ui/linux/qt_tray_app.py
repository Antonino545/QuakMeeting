import os
import sys
import threading
import logging
import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.domain.models import format_duration
from core.logger import open_log_file

logger = logging.getLogger("QuakMeeting.QtTrayApp")

from ui.common.tray_viewmodel import TrayViewModel

from PyQt6.QtCore import pyqtSignal, QObject

class SignalBridge(QObject):
    banner = pyqtSignal(dict)
    menu = pyqtSignal()
    agenda = pyqtSignal()

class QuakMeetingTrayApp:
    def __init__(self, app: QApplication):
        self.app = app

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets", "icon.png"
        )
        if os.path.exists(icon_path):
            self.icon = QIcon(icon_path)
        else:
            self.icon = QIcon()

        self.tray = QSystemTrayIcon(self.icon, self.app)
        self.tray.setToolTip("QuakMeeting")

        self.build_menu()
        self.tray.show()

        self.tray.activated.connect(self._on_tray_activated)

        self._bridge = SignalBridge()
        self._bridge.banner.connect(self.on_banner_trigger)
        self._bridge.menu.connect(self.build_menu)
        self._bridge.agenda.connect(self.on_agenda_updated)

        event_bus.subscribe("TRIGGER_BANNER", lambda **kwargs: self._bridge.banner.emit(kwargs.get("event_dict") or kwargs))
        event_bus.subscribe("REMINDER_TRIGGERED", lambda **kwargs: self._bridge.banner.emit(kwargs.get("event_dict") or kwargs))
        event_bus.subscribe("AGENDA_UPDATED", lambda **kwargs: self._bridge.agenda.emit())
        event_bus.subscribe("UPDATE_AVAILABLE", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("UPDATE_CHECK_COMPLETE", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("UPDATE_INSTALLED", lambda **kwargs: self._bridge.menu.emit())
        updater_service.check_for_updates(background=True)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_flight_deck(0)

    def build_menu(self):
        if hasattr(self, '_menu'):
            menu = self._menu
            menu.clear()
        else:
            menu = QMenu()
            self._menu = menu
            self.tray.setContextMenu(self._menu)

        now = datetime.now().astimezone()
        meetings = calendar_service.get_upcoming_meetings()
        today_up = [m for m in meetings if m.start_time and m.start_time.astimezone().date() == now.date() and ((m.end_time and m.end_time.astimezone() > now) or m.start_time.astimezone() > now)]

        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}

        deck_act = QAction("🦆 Open Flight Deck", menu)
        deck_act.triggered.connect(lambda chk=False: self.show_flight_deck(0))
        menu.addAction(deck_act)
        menu.addSeparator()

        if today_up:
            nx = today_up[0]
            st = nx.start_time.strftime("%H:%M") if nx.start_time else "--:--"
            m_title = (nx.title or "Event").strip()
            p_type = getattr(nx, "pilot_type", "duck")
            icon_prefix = icon_map.get(p_type, "🦆")

            travel_min = getattr(nx, "travel_time_minutes", 0)
            dep_dt = getattr(nx, "departure_time", None)

            if travel_min and isinstance(dep_dt, datetime):
                dur_str = format_duration(travel_min)
                next_label = f"{icon_prefix} Next: {st} — {m_title} (🚗 ~{dur_str} • Leave at {dep_dt.strftime('%H:%M')})"
            elif travel_min:
                dur_str = format_duration(travel_min)
                next_label = f"{icon_prefix} Next: {st} — {m_title} (🚗 ~{dur_str})"
            else:
                next_label = f"{icon_prefix} Next: {st} — {m_title}"

            header_act = QAction(next_label, menu)
            header_act.setEnabled(False)
            menu.addAction(header_act)

            action_url = getattr(nx, "action_url", None) or getattr(nx, "meeting_url", None)
            if action_url:
                btn_title = f"   {getattr(nx, 'action_btn_text', '🚀 Join Now')}"
                join_act = QAction(btn_title, menu)
                join_act.triggered.connect(lambda chk=False, u=action_url: webbrowser.open(u))
                menu.addAction(join_act)

            menu.addSeparator()
        else:
            none_act = QAction("✨ No remaining events today", menu)
            none_act.setEnabled(False)
            menu.addAction(none_act)
            menu.addSeparator()

        sync_act = QAction("🔄 Sync Calendars", menu)
        sync_act.triggered.connect(lambda chk=False: threading.Thread(target=calendar_service.sync_now, daemon=True).start())
        menu.addAction(sync_act)

        pref_act = QAction("⚙️ Settings & Preferences...", menu)
        pref_act.triggered.connect(lambda chk=False: self.show_flight_deck(2))
        menu.addAction(pref_act)

        mode_menu = QMenu("📊 Status Bar Mode", menu)
        curr_mode = config.get("menubar_status_mode", "countdown")
        modes_def = [
            ("countdown", "⏳ Live Countdown"),
            ("event_time", "🕐 Start Time & Title"),
            ("time_only", "⏱️ Time & Countdown"),
            ("icon_only", "🦆 Icon Only")
        ]
        for mode_key, mode_label in modes_def:
            m_act = QAction(mode_label, mode_menu, checkable=True)
            if mode_key == curr_mode:
                m_act.setChecked(True)
            m_act.triggered.connect(lambda chk=False, m=mode_key: self.set_status_mode(m))
            mode_menu.addAction(m_act)

        menu.addMenu(mode_menu)

        logs_act = QAction("📄 View Logs & Diagnostics...", menu)
        logs_act.triggered.connect(lambda chk=False: open_log_file())
        menu.addAction(logs_act)
        menu.addSeparator()

        update_info = updater_service.latest_release_info
        if update_info and update_info.get("has_update"):
            up_act = QAction(f"🚀 Update Available: {update_info['tag_name']}", menu)
            up_act.triggered.connect(lambda chk=False: updater_service.download_and_install_update())
            menu.addAction(up_act)
        else:
            chk_act = QAction("🔍 Check for Updates...", menu)
            chk_act.triggered.connect(lambda chk=False: updater_service.check_for_updates(background=True))
            menu.addAction(chk_act)

        menu.addSeparator()

        quit_act = QAction("Quit QuakMeeting", menu)
        quit_act.triggered.connect(lambda chk=False: self.app.quit())
        menu.addAction(quit_act)

    def set_status_mode(self, mode):
        config.set("menubar_status_mode", mode)
        self.build_menu()
        from core.services.calendar_service import calendar_service
        self.on_agenda_updated(calendar_service.get_upcoming_meetings())

    def on_agenda_updated(self, meeting_objects=None, **kwargs):
        if meeting_objects is None: return
        try:
            now = datetime.now().astimezone()
            today_up = [m for m in meeting_objects if m.start_time and m.start_time.astimezone().date() == now.date() and ((m.end_time and m.end_time.astimezone() > now) or m.start_time.astimezone() > now)]

            primary_m = today_up[0] if today_up else None
            max_lookahead_min = int(config.get("max_countdown_lookahead_hours", 3)) * 60
            status_mode = config.get("menubar_status_mode", "countdown")
            title = TrayViewModel.get_status_bar_title(primary_m, now, status_mode, max_lookahead_min)

            self.tray.setToolTip(title)
            self.build_menu()
        except Exception as e:
            logger.warning(f"Error in QtTray agenda update: {e}")

    def show_flight_deck(self, tab_index: int = 0):
        logger.info('🚀 show_flight_deck SIGNAL RECEIVED!')
        try:
            from ui.linux.qt_dashboard import show_qt_dashboard
            show_qt_dashboard(tab_index)
        except Exception as e:
            logger.warning(f"Flight Deck window error: {e}")

    def on_banner_trigger(self, event_dict=None, meeting=None, stage=None, **kwargs):
        try:
            data = event_dict or (meeting.to_dict() if hasattr(meeting, "to_dict") else meeting) or {}
            if stage is not None and "reminder_stage" not in data:
                data["reminder_stage"] = stage
            from ui.linux.banner.qt_banner import show_qt_banner
            show_qt_banner(data)
        except Exception as e:
            logger.error(f"Error showing Qt banner: {e}")

def run_qt_tray_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = QuakMeetingTrayApp(app)

    if "--silent" not in sys.argv:
        tray.show_flight_deck(0)

    app.exec()

