"""
Linux Top Bar Indicator for Ubuntu (Wayland / X11).
Integrates with GNOME Shell AppIndicator / StatusNotifierItem DBus.
Includes graceful fallback and installation guidance when PyGObject is missing.
"""
import os
import sys
import time
import threading
import logging
from datetime import datetime
from typing import Optional

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.domain.models import format_duration, __version__
from core.logger import open_log_file

logger = logging.getLogger("QuakMeeting.LinuxAppIndicator")

def _print_missing_gi_help():
    print("\n" + "=" * 65)
    print(" 🐧 QuakMeeting - Missing Linux Dependencies (PyGObject / GTK3)")
    print("=" * 65)
    print(" To enable the Top Bar menu and Wayland HUD banners on Ubuntu,")
    print(" install the required system libraries by running:\n")
    print("   sudo apt update")
    print("   sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 \\")
    print("                       gir1.2-appindicator3-0.1 gir1.2-gtklayershell-0.1\n")
    print(" 💡 If you are running inside a Python Virtual Environment (venv):")
    print("   1) Recreate venv with system packages:")
    print("      python3 -m venv --system-site-packages venv && source venv/bin/activate")
    print("   OR")
    print("   2) Install PyGObject via pip:")
    print("      sudo apt install -y libgirepository1.0-dev libcairo2-dev pkg-config python3-dev")
    print("      pip install PyGObject pycairo\n")
    print(" ⚡ Running in Background Daemon Mode (Monitoring Meetings)...")
    print("=" * 65 + "\n")

def _run_headless_fallback():
    """Runs reminder engine loop in terminal if GTK/PyGObject is not installed."""
    _print_missing_gi_help()
    print("🦆 QuakMeeting active in terminal daemon mode. Press Ctrl+C to stop.")
    
    def on_banner(event_dict=None, meeting=None, stage=None, **kwargs):
        data = event_dict or (meeting.to_dict() if hasattr(meeting, "to_dict") else meeting) or {}
        title = data.get("title", "Event")
        prov = data.get("provider", "Calendar")
        url = data.get("action_url") or data.get("meeting_url")
        print(f"\n🔔 [REMINDER {f'({stage}m)' if stage is not None else ''}] >>> {title} ({prov})")
        if url:
            print(f"   🚀 Meeting Link: {url}")
            import webbrowser
            webbrowser.open(url)

    event_bus.subscribe("TRIGGER_BANNER", on_banner)
    event_bus.subscribe("REMINDER_TRIGGERED", on_banner)
    calendar_service.sync_now()

    try:
        while True:
            reminder_engine.check_and_notify()
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n👋 QuakMeeting stopped.")

def run_linux_app():
    """Main application runner for Linux Ubuntu."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, GLib

        # Suppress harmless upstream C deprecation warning from libayatana-appindicator
        try:
            GLib.log_set_handler('libayatana-appindicator', GLib.LogLevelFlags.LEVEL_WARNING, lambda *args: None, None)
        except Exception:
            pass

        try:
            gi.require_version('AyatanaAppIndicator3', '0.1')
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3
        except (ValueError, ImportError):
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3
    except (ImportError, ValueError, ModuleNotFoundError) as e:
        system_python = "/usr/bin/python3"
        if sys.executable != system_python and os.path.exists(system_python):
            try:
                import subprocess
                chk = subprocess.run([system_python, "-c", "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"], capture_output=True)
                if chk.returncode == 0:
                    logger.info(f"Relaunching QuakMeeting using system python GTK runtime ({system_python})...")
                    os.execv(system_python, [system_python] + sys.argv)
            except Exception as re_err:
                logger.warning(f"Failed to auto-switch to system python: {re_err}")

        logger.warning(f"PyGObject / AppIndicator3 not found ({e}). Falling back to daemon mode.")
        _run_headless_fallback()
        return

    APPINDICATOR_ID = 'quakmeeting_indicator'
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "icon.png")

    indicator = AppIndicator3.Indicator.new(
        APPINDICATOR_ID,
        icon_path if os.path.exists(icon_path) else "appointment-soon",
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    from ui.viewmodels.tray_viewmodel import TrayViewModel

    def build_menu():
        menu = Gtk.Menu()
        now = datetime.now().astimezone()
        meetings = calendar_service.get_upcoming_meetings()
        today_up = [m for m in meetings if m.start_time and m.start_time.astimezone().date() == now.date() and ((m.end_time and m.end_time.astimezone() > now) or m.start_time.astimezone() > now)]

        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}

        # 1. Open Flight Deck
        deck_item = Gtk.MenuItem(label="🦆 Open Flight Deck")
        deck_item.connect("activate", lambda w: show_qt_flight_deck(0))
        menu.append(deck_item)
        menu.append(Gtk.SeparatorMenuItem())

        # 2. Next Event & Quick Join
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
                
            header_item = Gtk.MenuItem(label=next_label)
            header_item.set_sensitive(False)
            menu.append(header_item)
            
            action_url = getattr(nx, "action_url", None) or getattr(nx, "meeting_url", None)
            if action_url:
                btn_title = f"   {getattr(nx, 'action_btn_text', '🚀 Join Now')}"
                join_item = Gtk.MenuItem(label=btn_title)
                join_item.connect("activate", lambda w, u=action_url: import_webbrowser().open(u))
                menu.append(join_item)
                
            menu.append(Gtk.SeparatorMenuItem())
        else:
            none_item = Gtk.MenuItem(label="✨ No remaining events today")
            none_item.set_sensitive(False)
            menu.append(none_item)
            menu.append(Gtk.SeparatorMenuItem())

        # 3. Upcoming Today List
        if len(today_up) > 1:
            list_header = Gtk.MenuItem(label="📅 Today's Events:")
            list_header.set_sensitive(False)
            menu.append(list_header)
            
            for m in today_up[1:6]:
                start_str = m.start_time.strftime("%H:%M") if m.start_time else "--:--"
                p_type = getattr(m, "pilot_type", "duck")
                icon = icon_map.get(p_type, "🦆")
                m_title = (m.title or "Event").strip()
                title_short = m_title[:24] + "…" if len(m_title) > 24 else m_title
                
                tr_min = getattr(m, "travel_time_minutes", 0)
                sub_text = f"  {icon} {start_str} - {title_short}"
                if tr_min:
                    sub_text += f" (~{format_duration(tr_min)})"
                
                sub_item = Gtk.MenuItem(label=sub_text)
                sub_item.set_sensitive(False)
                url = getattr(m, "action_url", None) or getattr(m, "meeting_url", None)
                if url:
                    sub_item.set_sensitive(True)
                    sub_item.connect("activate", lambda w, u=url: import_webbrowser().open(u))
                menu.append(sub_item)
                
            menu.append(Gtk.SeparatorMenuItem())

        # 4. Utilities
        sync_item = Gtk.MenuItem(label="🔄 Sync Calendars")
        sync_item.connect("activate", lambda w: threading.Thread(target=calendar_service.sync_now, daemon=True).start())
        menu.append(sync_item)

        pref_item = Gtk.MenuItem(label="⚙️ Settings & Preferences...")
        pref_item.connect("activate", lambda w: show_qt_flight_deck(2))
        menu.append(pref_item)

        # Status Bar Mode
        def set_status_mode(widget, mode):
            config.set("menubar_status_mode", mode)
            build_menu()
            update_tick()
            
        mode_menu = Gtk.Menu()
        curr_mode = config.get("menubar_status_mode", "countdown")
        modes_def = [
            ("countdown", "⏳ Live Countdown"),
            ("event_time", "🕐 Start Time & Title"),
            ("time_only", "⏱️ Time & Countdown"),
            ("icon_only", "🦆 Icon Only")
        ]
        for mode_key, mode_label in modes_def:
            m_item = Gtk.CheckMenuItem(label=mode_label)
            if mode_key == curr_mode:
                m_item.set_active(True)
            m_item.connect("activate", lambda w, m=mode_key: set_status_mode(w, m))
            mode_menu.append(m_item)
            
        item_display_mode = Gtk.MenuItem(label="📊 Status Bar Mode")
        item_display_mode.set_submenu(mode_menu)
        menu.append(item_display_mode)
        
        item_logs = Gtk.MenuItem(label="📄 View Logs & Diagnostics...")
        item_logs.connect("activate", lambda w: open_log_file())
        menu.append(item_logs)
        menu.append(Gtk.SeparatorMenuItem())

        update_info = updater_service.latest_release_info
        if update_info and update_info.get("has_update"):
            up_lbl = f"🚀 Update Available: {update_info['tag_name']}"
            up_item = Gtk.MenuItem(label=up_lbl)
            up_item.connect("activate", lambda w: updater_service.download_and_install_update())
            menu.append(up_item)
        else:
            chk_item = Gtk.MenuItem(label="🔍 Check for Updates...")
            chk_item.connect("activate", lambda w: updater_service.check_for_updates(background=True))
            menu.append(chk_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quit QuakMeeting")
        quit_item.connect("activate", lambda w: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        indicator.set_menu(menu)

    def import_webbrowser():
        import webbrowser
        return webbrowser

    def on_agenda_updated(meeting_objects=None, **kwargs):
        if meeting_objects is None: return
        try:
            now = datetime.now().astimezone()
            today_up = [m for m in meeting_objects if m.start_time and m.start_time.astimezone().date() == now.date() and ((m.end_time and m.end_time.astimezone() > now) or m.start_time.astimezone() > now)]
            
            primary_m = today_up[0] if today_up else None
            max_lookahead_min = int(config.get("max_countdown_lookahead_hours", 3)) * 60
            status_mode = config.get("menubar_status_mode", "countdown")
            title_str = TrayViewModel.get_status_bar_title(primary_m, now, status_mode, max_lookahead_min)
            
            # GLib.idle_add ensures GTK operations run on the main thread
            GLib.idle_add(indicator.set_label, title_str, "QuakMeeting")
            GLib.idle_add(build_menu)
        except Exception as e:
            logger.warning(f"Error updating Linux tray: {e}")

    event_bus.subscribe("AGENDA_UPDATED", on_agenda_updated)
    build_menu()

    def on_banner_trigger(event_dict=None, meeting=None, stage=None, **kwargs):
        try:
            data = event_dict or (meeting.to_dict() if hasattr(meeting, "to_dict") else meeting) or {}
            if stage is not None and "reminder_stage" not in data:
                data["reminder_stage"] = stage
            from ui.banner.qt_banner import show_qt_banner
            show_qt_banner(data)
        except Exception as e:
            logger.error(f"Error showing Qt banner: {e}")

    def on_update_state_changed(**kwargs):
        GLib.idle_add(build_menu)

    event_bus.subscribe("UPDATE_AVAILABLE", on_update_state_changed)
    event_bus.subscribe("UPDATE_CHECK_COMPLETE", on_update_state_changed)
    event_bus.subscribe("UPDATE_INSTALLED", on_update_state_changed)

    event_bus.subscribe("TRIGGER_BANNER", on_banner_trigger)
    event_bus.subscribe("REMINDER_TRIGGERED", on_banner_trigger)
    updater_service.check_for_updates(background=True)

    Gtk.main()

def show_qt_flight_deck(tab_index: int = 0):
    try:
        import subprocess
        subprocess.Popen([sys.executable, "-m", "ui.qt_dashboard", str(tab_index)])
    except Exception as e:
        logger.warning(f"Linux Flight Deck window error: {e}")
