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
    
    def on_banner(event_dict, **kwargs):
        title = event_dict.get("title", "Event")
        prov = event_dict.get("provider", "Calendar")
        url = event_dict.get("action_url")
        print(f"\n🔔 [REMINDER] >>> {title} ({prov})")
        if url:
            print(f"   🚀 Meeting Link: {url}")
            import webbrowser
            webbrowser.open(url)

    event_bus.subscribe("TRIGGER_BANNER", on_banner)
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
        try:
            gi.require_version('AyatanaAppIndicator3', '0.1')
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3
        except (ValueError, ImportError):
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3

        from gi.repository import Gtk, GLib
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

    def build_menu():
        menu = Gtk.Menu()

        now = datetime.now()
        meetings = calendar_service.get_upcoming_meetings()
        today_up = [m for m in meetings if m.start_time and m.start_time.date() == now.date() and ((m.end_time and m.end_time > now) or m.start_time > now)]

        if today_up:
            nx = today_up[0]
            st = nx.start_time.strftime("%H:%M")
            header_item = Gtk.MenuItem(label=f"🦆 Next: {st} — {nx.title[:25]}")
            if nx.action_url:
                header_item.connect("activate", lambda w, u=nx.action_url: import_webbrowser().open(u))
            menu.append(header_item)
        else:
            menu.append(Gtk.MenuItem(label="🦆 QuakMeeting: No upcoming events"))

        menu.append(Gtk.SeparatorMenuItem())

        deck_item = Gtk.MenuItem(label="📊 Flight Deck HUD...")
        deck_item.connect("activate", lambda w: show_linux_flight_deck(0))
        menu.append(deck_item)

        sync_item = Gtk.MenuItem(label="🔄 Sync Calendar Now")
        sync_item.connect("activate", lambda w: threading.Thread(target=calendar_service.sync_now, daemon=True).start())
        menu.append(sync_item)

        pref_item = Gtk.MenuItem(label="⚙️ Settings & Preferences...")
        pref_item.connect("activate", lambda w: show_linux_flight_deck(2))
        menu.append(pref_item)

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

    def update_tick():
        try:
            reminder_engine.check_and_notify()
            now = datetime.now()
            meetings = calendar_service.get_upcoming_meetings()
            today_up = [m for m in meetings if m.start_time and m.start_time.date() == now.date() and ((m.end_time and m.end_time > now) or m.start_time > now)]
            
            if today_up:
                nx = today_up[0]
                diff_m = max(0, int((nx.start_time - now).total_seconds() // 60))
                indicator.set_label(f"in {diff_m}m: {nx.title[:15]}", "")
            else:
                indicator.set_label("🦆", "")
            build_menu()
        except Exception as e:
            logger.warning(f"Error in Linux tick: {e}")
        return True

    build_menu()
    GLib.timeout_add_seconds(15, update_tick)

    def on_banner_trigger(event_dict, **kwargs):
        try:
            from ui.banner.wayland_banner import show_wayland_banner
            show_wayland_banner(event_dict)
        except Exception as e:
            logger.error(f"Error showing banner: {e}")

    event_bus.subscribe("TRIGGER_BANNER", on_banner_trigger)
    updater_service.check_for_updates(background=True)

    Gtk.main()

def show_linux_flight_deck(tab_index: int = 0):
    try:
        from ui.linux_dashboard import show_linux_dashboard
        show_linux_dashboard(tab_index)
    except Exception as e:
        logger.warning(f"Linux Flight Deck window error: {e}")
