import sys
import os

if sys.platform.startswith("linux"):
    if "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"

# Ensure current project directory is in import path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.logger import setup_logging, log_system_diagnostics, logger
setup_logging()
log_system_diagnostics()

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

            stage_val = None
            if "--stage" in sys.argv:
                try:
                    idx = sys.argv.index("--stage")
                    stage_val = int(sys.argv[idx + 1])
                except Exception:
                    stage_val = None

            if delay_sec > 0:
                print(f"\n⏳ Waiting {delay_sec} seconds to allow switching to a Full Screen app...")
                for i in range(delay_sec, 0, -1):
                    print(f"   ⏱️  {i}...")
                    time.sleep(1)
                print("🚀 Launching banner over Full Screen!")
            else:
                print("\n🚀 Running Notification Banner Test...")

            if sys.platform == "darwin":
                import AppKit
                from ui.macos.banner.banner_controller import QuakPitFlyingBanner
                from ui.macos.banner.banner_view import QuakPitBannerView
                # Preset mapping
                from ui.linux.banner import get_test_preset
                test_m = dict(get_test_preset(pilot_type))
                if stage_val is not None:
                    test_m["reminder_stage"] = stage_val

                app = AppKit.NSApplication.sharedApplication()
                app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
                def _on_test_done():
                    app.terminate_(None)
                controller = QuakPitFlyingBanner.alloc().initWithMeetingData_callback_(test_m, _on_test_done)
                controller.show()
                app.run()
            else:
                from ui.linux.banner import get_test_preset, show_qt_banner
                test_m = dict(get_test_preset(pilot_type))
                if stage_val is not None:
                    test_m["reminder_stage"] = stage_val
                show_qt_banner(test_m)
            return

        logger.info("Initializing QuakMeeting Menu Bar and Flight Deck UI...")
        print(" Launching Menu Bar icon and Flight Deck...")

        from core.app_controller import app_controller
        app_controller.start_background_loop()

        if sys.platform == "darwin":
            from ui.macos.menu_bar_app import QuakMeetingMenuBar
            from ui.macos.dashboard_window import show_dashboard

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

