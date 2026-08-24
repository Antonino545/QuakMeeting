import os
import sys
import threading
import logging
import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.domain.models import format_duration
from core.logger import open_log_file

logger = logging.getLogger("QuakMeeting.QtTrayApp")

def _format_status_title(next_m, now: datetime) -> str:
    mode = config.get("menubar_status_mode", "countdown")
    if not next_m:
        return "🦆" if mode == "icon_only" else "🦆 QuakMeeting"
        
    icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}
    p_type = getattr(next_m, "pilot_type", "duck")
    icon_prefix = icon_map.get(p_type, "🦆")
    
    if mode == "icon_only":
        return icon_prefix
        
    start_dt = getattr(next_m, "start_time", None)
    end_dt = getattr(next_m, "end_time", None)
    dep_dt = getattr(next_m, "departure_time", None)
    travel_min = getattr(next_m, "travel_time_minutes", 0)
    m_title = (getattr(next_m, "title", "Event") or "Event").strip()
    title_short = m_title[:14] + "…" if len(m_title) > 14 else m_title
    
    start_str = start_dt.strftime("%H:%M") if isinstance(start_dt, datetime) else "--:--"
    max_lookahead_min = int(config.get("max_countdown_lookahead_hours", 3)) * 60

    if mode == "event_time":
        if travel_min:
            dur_str = format_duration(travel_min)
            return f"{icon_prefix} {start_str} {title_short} (~{dur_str})"
        return f"{icon_prefix} {start_str} {title_short}"
        
    elif mode == "time_only":
        if isinstance(start_dt, datetime):
            diff_m = int(round((start_dt - now).total_seconds() / 60.0))
            if 0 < diff_m <= max_lookahead_min:
                if diff_m >= 60:
                    hrs = diff_m // 60
                    mins = diff_m % 60
                    t_part = f"{hrs}h" if mins == 0 else f"{hrs}h{mins:02d}m"
                    return f"{icon_prefix} {start_str} (in {t_part})"
                return f"{icon_prefix} {start_str} (in {diff_m}m)"
            elif diff_m == 0:
                return f"{icon_prefix} {start_str} (Now!)"
            elif end_dt and isinstance(end_dt, datetime) and now < end_dt:
                return f"{icon_prefix} {start_str} (Active)"
        return f"{icon_prefix} {start_str}"
        
    else: # "countdown" (Default & Most Informative)
        if dep_dt and isinstance(dep_dt, datetime):
            diff_dep = int(round((dep_dt - now).total_seconds() / 60.0))
            if 0 < diff_dep <= max_lookahead_min:
                if diff_dep >= 60:
                    hrs = diff_dep // 60
                    mins = diff_dep % 60
                    t_part = f"{hrs}h" if mins == 0 else f"{hrs}h{mins:02d}m"
                    return f"{icon_prefix} Leave in {t_part} ({title_short})"
                return f"{icon_prefix} Leave in {diff_dep}m ({title_short})"
            elif -10 <= diff_dep <= 0:
                return f"🚨 {icon_prefix} Leave NOW! ({title_short})"
            elif diff_dep > max_lookahead_min:
                return f"{icon_prefix} {start_str} {title_short}"

        if isinstance(start_dt, datetime):
            diff_start = int(round((start_dt - now).total_seconds() / 60.0))
            if 0 < diff_start <= max_lookahead_min:
                if diff_start >= 60:
                    hrs = diff_start // 60
                    mins = diff_start % 60
                    t_part = f"{hrs}h" if mins == 0 else f"{hrs}h{mins:02d}m"
                    return f"{icon_prefix} in {t_part}: {title_short}"
                return f"{icon_prefix} in {diff_start}m: {title_short}"
            elif diff_start == 0:
                return f"🔔 {icon_prefix} Starting NOW: {title_short}"
            elif end_dt and isinstance(end_dt, datetime) and now < end_dt:
                diff_end = int(round((end_dt - now).total_seconds() / 60.0))
                return f"🟢 {icon_prefix} {title_short} ({diff_end}m left)"
            elif diff_start > max_lookahead_min:
                return f"{icon_prefix} {start_str} {title_short}"
                
        return f"{icon_prefix} {start_str} {title_short}"

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
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_tick)
        self.timer.start(15000) # 15 seconds
        
        event_bus.subscribe("TRIGGER_BANNER", self.on_banner_trigger)
        event_bus.subscribe("REMINDER_TRIGGERED", self.on_banner_trigger)
        updater_service.check_for_updates(background=True)
        
        self.update_tick()

    def build_menu(self):
        menu = QMenu()
        now = datetime.now()
        meetings = calendar_service.get_upcoming_meetings()
        today_up = [m for m in meetings if m.start_time and m.start_time.date() == now.date() and ((m.end_time and m.end_time > now) or m.start_time > now)]

        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}

        deck_act = QAction("🦆 Open Flight Deck", menu)
        deck_act.triggered.connect(lambda: self.show_flight_deck(0))
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
                join_act.triggered.connect(lambda chk, u=action_url: webbrowser.open(u))
                menu.addAction(join_act)
                
            menu.addSeparator()
        else:
            none_act = QAction("✨ No remaining events today", menu)
            none_act.setEnabled(False)
            menu.addAction(none_act)
            menu.addSeparator()

        sync_act = QAction("🔄 Sync Calendars", menu)
        sync_act.triggered.connect(lambda: threading.Thread(target=calendar_service.sync_now, daemon=True).start())
        menu.addAction(sync_act)
        
        pref_act = QAction("⚙️ Settings & Preferences...", menu)
        pref_act.triggered.connect(lambda: self.show_flight_deck(2))
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
            m_act.triggered.connect(lambda chk, m=mode_key: self.set_status_mode(m))
            mode_menu.addAction(m_act)
            
        menu.addMenu(mode_menu)
        
        logs_act = QAction("📄 View Logs & Diagnostics...", menu)
        logs_act.triggered.connect(lambda: open_log_file())
        menu.addAction(logs_act)
        menu.addSeparator()

        quit_act = QAction("Quit QuakMeeting", menu)
        quit_act.triggered.connect(self.app.quit)
        menu.addAction(quit_act)

        self.tray.setContextMenu(menu)

    def set_status_mode(self, mode):
        config.set("menubar_status_mode", mode)
        self.build_menu()
        self.update_tick()

    def update_tick(self):
        try:
            reminder_engine.check_and_notify()
            now = datetime.now()
            meetings = calendar_service.get_upcoming_meetings()
            today_up = [m for m in meetings if m.start_time and m.start_time.date() == now.date() and ((m.end_time and m.end_time > now) or m.start_time > now)]
            
            if today_up:
                title = _format_status_title(today_up[0], now)
                self.tray.setToolTip(title)
            else:
                title = _format_status_title(None, now)
                self.tray.setToolTip(title)
            self.build_menu()
        except Exception as e:
            logger.warning(f"Error in QtTray tick: {e}")

    def show_flight_deck(self, tab_index: int = 0):
        try:
            from ui.qt_dashboard import show_qt_dashboard
            show_qt_dashboard(tab_index)
        except Exception as e:
            logger.warning(f"Flight Deck window error: {e}")

    def on_banner_trigger(self, event_dict=None, meeting=None, stage=None, **kwargs):
        try:
            data = event_dict or (meeting.to_dict() if hasattr(meeting, "to_dict") else meeting) or {}
            if stage is not None and "reminder_stage" not in data:
                data["reminder_stage"] = stage
            from ui.banner.qt_banner import show_qt_banner
            show_qt_banner(data)
        except Exception as e:
            logger.error(f"Error showing Qt banner: {e}")

def run_qt_tray_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    tray = QuakMeetingTrayApp(app)
    app.exec()
