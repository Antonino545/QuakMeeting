import sys
import os
import logging

if "--debug" in sys.argv or "-d" in sys.argv:
    os.environ["FLIGHTDECK_DEBUG"] = "1"
    os.environ["QUAKMEETING_DEBUG"] = "1"

if sys.platform.startswith("linux"):
    if os.environ.get("FLIGHTDECK_QT_XCB", os.environ.get("QUAKMEETING_QT_XCB", "")).strip().lower() in ("1", "true", "yes", "on"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

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
            import gi
            gi.require_version('EDataServer', '1.2')
            return
        except (ImportError, ValueError):
            pass

        system_python = "/usr/bin/python3"
        if sys.executable != system_python and os.path.exists(system_python):
            try:
                import subprocess
                res = subprocess.run([system_python, "-c", "import PyQt6; import gi; gi.require_version('EDataServer', '1.2')"], capture_output=True)
                if res.returncode == 0:
                    logger.info(f"Relaunching FlightDeck using system python GUI runtime ({system_python})...")
                    os.execv(system_python, [system_python] + sys.argv)
            except Exception as err:
                logger.warning(f"Auto-switch to system python failed: {err}")

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python3 main.py [OPTIONS]")
        print("\nFlightDeck — Smart Schedule & Travel Reminders.\n")
        print("Options:")
        print("  -c, --check, --diagnostics  Run system health & arrival diagnostics check")
        print("  --test                      Trigger notification banner test flight")
        print("  --delay <sec>               Wait <sec> before launching test banner")
        print("  --pilot <mascot>            Pilot mascot for test (duck, owl, bunny)")
        print("  --stage <minutes>           Reminder stage to simulate (0, 2, 5, 10, 20, 30, 45)")
        print("  -d, --debug                 Enable debug logging and diagnostic UI cards")
        print("  --qt                        Force Qt6 UI on macOS (overrides native AppKit)")
        print("  -h, --help                  Show this help message and exit")
        return

    if "--check" in sys.argv or "-c" in sys.argv or "--diagnostics" in sys.argv:
        from core.diagnostics import run_system_diagnostics_check, format_diagnostics_report
        diag = run_system_diagnostics_check()
        print(format_diagnostics_report(diag))
        sys.exit(0 if diag.get("status") != "ERROR" else 1)

    _ensure_gui_python_environment()
    from core.services.config_service import is_debug_mode
    debug_mode = is_debug_mode()
    setup_logging(level=logging.DEBUG if debug_mode else logging.INFO)
    if debug_mode:
        logger.info("🔧 Debug mode activated; verbose diagnostics enabled")
    logger.debug("Startup arguments: %s", sys.argv)

    print("=" * 60)
    print(" ✈️ FlightDeck - Smart Schedule & Travel Reminders")
    print(" Inspired by QuakPit (https://github.com/Ooble-Studio/QuakPit)")
    print("=" * 60)

    try:
        force_qt = "--qt" in sys.argv
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

            from ui.common.banner_presets import get_test_preset

            if sys.platform == "darwin" and not force_qt:
                import AppKit
                from ui.macos.banner.banner_controller import QuakPitFlyingBanner
                from ui.macos.banner.banner_view import QuakPitBannerView
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
                from ui.linux.banner import show_qt_banner
                test_m = dict(get_test_preset(pilot_type))
                if stage_val is not None:
                    test_m["reminder_stage"] = stage_val
                show_qt_banner(test_m)
            return

        logger.info("Initializing FlightDeck Menu Bar and Flight Deck UI...")
        print(" Launching Menu Bar icon and Flight Deck...")

        if sys.platform == "darwin" and not force_qt:
            print("\n 📌 PERMISSION NOTICE:")
            print(" If macOS prompts for Calendar access, select 'ALLOW'.\n")

        from ui.app_launcher import launch_application
        launch_application()
    except Exception as e:
        logger.exception(f"Fatal error in main application run loop: {e}")
        raise

if __name__ == "__main__":
    main()
