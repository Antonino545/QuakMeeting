import os
import sys
import threading
import logging
import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPainter, QPixmap, QFont, QColor, QPalette
from ui.linux.theme import Theme

from core.services.config_service import config, is_debug_mode
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.domain.models import format_duration
from core.logger import open_log_file

logger = logging.getLogger("QuakMeeting.QtTrayApp")

from ui.common.tray_viewmodel import TrayViewModel

from PyQt6.QtCore import pyqtSignal, QObject, Qt

class SignalBridge(QObject):
    banner = pyqtSignal(dict)
    menu = pyqtSignal()
    agenda = pyqtSignal()

class QuakMeetingTrayApp:
    def __init__(self, app: QApplication):
        self.app = app
        self._startup_catch_up_checked = False

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
        event_bus.subscribe("CALENDAR_SYNCED", lambda **kwargs: self._bridge.agenda.emit())
        event_bus.subscribe("CALENDAR_SYNCED", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("CALENDAR_SYNCED", self._check_startup_catch_up)
        event_bus.subscribe("UPDATE_AVAILABLE", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("UPDATE_CHECK_COMPLETE", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("UPDATE_INSTALLED", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("AGENDA_UPDATED", lambda **kwargs: self._bridge.menu.emit())
        event_bus.subscribe("CONFIG_CHANGED", lambda **kwargs: threading.Thread(target=calendar_service.sync_now, daemon=True).start())
        updater_service.check_for_updates(background=True)
        self._check_startup_catch_up(meetings=calendar_service.get_upcoming_meetings())

    def _check_startup_catch_up(self, meetings=None, **kwargs):
        """Surface one missed event after the first startup calendar result."""
        meetings = meetings or []
        if self._startup_catch_up_checked or not meetings:
            return
        self._startup_catch_up_checked = True
        reminder_engine.trigger_startup_catch_up(meetings)

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

            next_label = TrayViewModel.format_next_event_label(icon_prefix, st, m_title, travel_min, dep_dt)

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

        if is_debug_mode():
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

    def _generate_dynamic_icon(self, title_str: str) -> QIcon:
        import re
        icon_char = "🦆"
        
        # Try to find the mascot emoji
        for emoji in ["🦆", "👨‍🍳", "🧑‍✈️", "🦉", "🏋️‍♂️", "🏎️", "🦆🌸"]:
            if emoji in title_str:
                icon_char = emoji
                break
                
        short_text = ""
        if "NOW" in title_str:
            short_text = "NOW"
        elif "in " in title_str:
            parts = title_str.split("in ")
            if len(parts) > 1:
                short_text = parts[1].split(":")[0].split(" ")[0].replace("(", "").replace(")", "")
        elif "(" in title_str and "left" in title_str:
            short_text = title_str.split("(")[-1].replace(" left)", "")
        else:
            m = re.search(r'\b\d{2}:\d{2}\b', title_str)
            if m:
                short_text = m.group(0)

        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        
        font_icon = QFont("sans-serif", 24)
        painter.setFont(font_icon)
        painter.drawText(0, -4, 64, 38, Qt.AlignmentFlag.AlignCenter, icon_char)
        
        if short_text:
            font_text = QFont("sans-serif", 13, QFont.Weight.Bold)
            painter.setFont(font_text)
            
            painter.setPen(Theme.get_color('CRUST', 200))
            painter.drawText(1, 33, 64, 28, Qt.AlignmentFlag.AlignCenter, short_text[:6])
            
            if "NOW" in short_text:
                painter.setPen(Theme.RED)
            else:
                painter.setPen(Theme.TEXT)
                
            painter.drawText(0, 32, 64, 28, Qt.AlignmentFlag.AlignCenter, short_text[:6])
            
        painter.end()
        return QIcon(pixmap)

    def on_agenda_updated(self, meeting_objects=None, **kwargs):
        if meeting_objects is None:
            meeting_objects = calendar_service.get_upcoming_meetings()
        try:
            now = datetime.now().astimezone()
            today_up = [m for m in meeting_objects if m.start_time and m.start_time.astimezone().date() == now.date() and ((m.end_time and m.end_time.astimezone() > now) or m.start_time.astimezone() > now)]

            primary_m = today_up[0] if today_up else None
            max_lookahead_min = int(config.get("max_countdown_lookahead_hours", 3)) * 60
            status_mode = config.get("menubar_status_mode", "countdown")
            title = TrayViewModel.get_status_bar_title(primary_m, now, status_mode, max_lookahead_min)

            self.tray.setToolTip(title)
            
            if status_mode == "icon_only" or not primary_m:
                self.tray.setIcon(self.icon)
            else:
                self.tray.setIcon(self._generate_dynamic_icon(title))
                
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
            if isinstance(event_dict, dict) and "meeting" in event_dict:
                # The EventBus emits kwargs as a single dict if we passed kwargs to the bridge
                meeting = event_dict.get("meeting")
                stage = event_dict.get("stage", stage)
                event_dict = event_dict.get("event_dict")

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
    
    app.setApplicationName("QuakMeeting")
    app.setApplicationDisplayName("QuakMeeting")
    app.setDesktopFileName("quakmeeting")
    
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets", "icon.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, Theme.CRUST)
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, Theme.MANTLE)
    palette.setColor(QPalette.ColorRole.AlternateBase, Theme.CRUST)
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, Theme.SURFACE0)
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, Theme.BLUE)
    palette.setColor(QPalette.ColorRole.Highlight, Theme.BLUE)
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    app.setQuitOnLastWindowClosed(False)
    
    try:
        import gi
        gi.require_version('AppIndicator3', '0.1')
        from ui.linux.app_indicator_tray import AppIndicatorTrayApp
        tray = AppIndicatorTrayApp(app)
        logger.info("Successfully initialized AppIndicator3 for native GNOME text support.")
    except Exception as e:
        logger.info(f"AppIndicator3 not available, falling back to QSystemTrayIcon: {e}")
        tray = QuakMeetingTrayApp(app)

    if "--silent" not in sys.argv:
        tray.show_flight_deck(0)

    # Tray handlers are registered before the reminder loop begins, so an
    # event cannot be recorded as notified before its banner is deliverable.
    from core.app_controller import app_controller
    app_controller.start_background_loop()
    app.exec()
