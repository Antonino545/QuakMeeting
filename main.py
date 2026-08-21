import sys
import os

# Assicurati che la directory corrente sia nel path di import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from menu_bar_app import QuakMeetingMenuBar
from banner_window import show_banner_async
from datetime import datetime

def main():
    print("=" * 60)
    print(" 🦆 QuakMeeting - macOS Meeting Reminders & Quick Join")
    print(" Ispirato a QuakPit (https://github.com/Ooble-Studio/QuakPit)")
    print("=" * 60)

    if "--test" in sys.argv:
        import AppKit
        from banner_window import _run_banner
        print("\n🚀 Esecuzione Test Banner Notifica in corso (Premi Ctrl+C per uscire)...")
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        test_m = {
            "title": "Test Riunione QuakMeeting (Google Meet / Serenis)",
            "provider": "Serenis 🛋️",
            "start_time": datetime.now(),
            "meeting_url": "https://app.serenis.it/join/ths_pwtsvfnwpea5b8wg"
        }
        _run_banner(test_m)
        app.run()
        return

    print(" Avvio dell'icona nella barra dei menu e dello scanner del calendario...")
    print("\n 📌 NOTA SUI PERMESSI:")
    print(" Se macOS richiede l'accesso al Calendario, premi 'CONSENTI'.")
    print(" Se avevi cliccato 'Non consentire', i permessi sono stati azzerati con successivo ripristino.\n")

    app = QuakMeetingMenuBar.alloc().init()
    app.run()

if __name__ == "__main__":
    main()
