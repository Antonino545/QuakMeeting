import sys
import os

# Ensure current project directory is in import path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.logger import setup_logging, log_system_diagnostics, logger
setup_logging()
log_system_diagnostics()

from core import config, get_upcoming_meetings
from datetime import datetime

def _ensure_gui_python_environment():
    """If running on Linux in an environment missing PyQt6/gi, auto-relaunch using system python3."""
    if sys.platform.startswith("linux"):
        try:
            import PyQt6
            return
        except ImportError:
            pass

        try:
            import gi
            return
        except ImportError:
            pass

        system_python = "/usr/bin/python3"
        if sys.executable != system_python and os.path.exists(system_python):
            try:
                import subprocess
                res = subprocess.run([system_python, "-c", "import PyQt6"], capture_output=True)
                if res.returncode == 0:
                    logger.info(f"Relaunching QuakMeeting using system python GUI runtime ({system_python})...")
                    os.execv(system_python, [system_python] + sys.argv)
            except Exception as err:
                logger.warning(f"Auto-switch to system python failed: {err}")

def main():
    _ensure_gui_python_environment()
    print("=" * 60)
    print(" 🦆 QuakMeeting - Smart Meeting Reminders & Flight Deck")
    print(" Inspired by QuakPit (https://github.com/Ooble-Studio/QuakPit)")
    print("=" * 60)

    try:
        if "--test" in sys.argv:
            import time
            
            delay_sec = 0
            if "--delay" in sys.argv:
                try:
                    idx = sys.argv.index("--delay")
                    delay_sec = int(sys.argv[idx + 1])
                except Exception:
                    delay_sec = 3
                    
            pilot_type = "duck"
            if "--pilot" in sys.argv:
                try:
                    idx = sys.argv.index("--pilot")
                    pilot_type = sys.argv[idx + 1]
                except Exception:
                    pilot_type = "duck"
                    
            if delay_sec > 0:
                print(f"\n⏳ Waiting {delay_sec} seconds to allow switching to a Full Screen app...")
                for i in range(delay_sec, 0, -1):
                    print(f"   ⏱️  {i}...")
                    time.sleep(1)
                print("🚀 Launching banner over Full Screen!")
            else:
                print("\n🚀 Running Notification Banner Test...")
                
            pilot_presets = {
                "chef": {
                    "title": "Dinner with Friends at Pizzeria",
                    "provider": "Dinner / Food 🍕🍽️",
                    "pilot_type": "chef",
                    "action_btn_text": "🗺️ RESTAURANT DIRECTIONS (MAPS)",
                    "action_url": "https://maps.apple.com/?q=Pizzeria+Napoli",
                    "location": "Pizzeria Da Michele, London",
                    "start_time": datetime.now(),
                    "is_travel": True
                },
                "captain": {
                    "title": "Flight to London (BA 257)",
                    "provider": "Flight / Travel ✈️",
                    "pilot_type": "captain",
                    "action_btn_text": "🗺️ AIRPORT DIRECTIONS (MAPS)",
                    "action_url": "https://maps.apple.com/?q=Heathrow+Airport",
                    "location": "Terminal 5 - Gate B12",
                    "start_time": datetime.now(),
                    "is_travel": True
                },
                "owl": {
                    "title": "SmartGrid & Neural Networks Lecture",
                    "provider": "Study / University 🎓",
                    "pilot_type": "owl",
                    "action_btn_text": "📚 CLASSROOM & NOTES",
                    "action_url": "https://calendar.apple.com",
                    "location": "Room 3B - Campus",
                    "start_time": datetime.now(),
                    "is_travel": False
                },
                "gym": {
                    "title": "CrossFit Training & Palestra Workout",
                    "provider": "Gym & Sport 🏋️‍♂️💪",
                    "pilot_type": "gym",
                    "action_btn_text": "🗺️ GYM DIRECTIONS (MAPS)",
                    "action_url": "https://maps.apple.com/?daddr=Gym+Fitness",
                    "location": "Downtown Gym Club",
                    "start_time": datetime.now(),
                    "is_travel": True
                },
                "driver": {
                    "title": "Architecture Studio Meeting",
                    "provider": "In Person 📍 Travel Time!",
                    "pilot_type": "driver",
                    "action_btn_text": "🗺️ NAVIGATE WITH MAPS",
                    "action_url": "https://maps.apple.com/?daddr=City+Center",
                    "location": "Victoria Street, London",
                    "start_time": datetime.now(),
                    "is_travel": True
                },
                "zen_duck": {
                    "title": "Serenis Online Therapy Session",
                    "provider": "Serenis 🛋️",
                    "pilot_type": "zen_duck",
                    "action_btn_text": "🚀 JOIN SESSION",
                    "action_url": "https://app.serenis.it/join/test",
                    "start_time": datetime.now(),
                    "is_travel": False
                },
                "duck": {
                    "title": "Weekly Team Sync (Google Meet)",
                    "provider": "Google Meet 🟢",
                    "pilot_type": "duck",
                    "action_btn_text": "🚀 JOIN GOOGLE MEET",
                    "action_url": "https://meet.google.com/test-quak-pit",
                    "start_time": datetime.now(),
                    "is_travel": False
                }
            }
            
            test_m = pilot_presets.get(pilot_type, pilot_presets["duck"])
            
            if sys.platform == "darwin":
                import AppKit
                from ui.banner_window import _run_banner
                app = AppKit.NSApplication.sharedApplication()
                app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
                _run_banner(test_m)
                app.run()
            else:
                from ui.banner.wayland_banner import show_wayland_banner
                show_wayland_banner(test_m)
            return

        logger.info("Initializing QuakMeeting Menu Bar and Flight Deck UI...")
        print(" Launching Menu Bar icon and Flight Deck...")

        if sys.platform == "darwin":
            from ui.menu_bar_app import QuakMeetingMenuBar
            from ui.dashboard_window import show_dashboard

            print("\n 📌 PERMISSION NOTICE:")
            print(" If macOS prompts for Calendar access, select 'ALLOW'.\n")

            app = QuakMeetingMenuBar.alloc().init()
            if app is None:
                logger.error("Failed to allocate and initialize QuakMeetingMenuBar!")
                return
            
            if "--silent" not in sys.argv:
                show_dashboard()
                
            logger.info("Entering macOS Application Run Loop...")
            app.run()
        else:
            from ui.app_launcher import launch_application
            launch_application()
    except Exception as e:
        logger.exception(f"Fatal error in main application run loop: {e}")
        raise

if __name__ == "__main__":
    main()

