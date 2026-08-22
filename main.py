import sys
import os

# Assicurati che la directory corrente sia nel path di import
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.logger import setup_logging
setup_logging()

from ui import QuakMeetingMenuBar, show_banner_async, show_dashboard, _run_banner
from core import config, get_upcoming_meetings
from datetime import datetime

def main():
    print("=" * 60)
    print(" 🦆 QuakMeeting - macOS Meeting Reminders & Flight Deck")
    print(" Ispirato a QuakPit (https://github.com/Ooble-Studio/QuakPit)")
    print("=" * 60)

    if "--test" in sys.argv:
        import time
        import AppKit
        from ui.banner_window import _run_banner
        
        # Gestione delay per permettere all'utente di passare all'app Full Screen
        delay_sec = 0
        if "--delay" in sys.argv:
            try:
                idx = sys.argv.index("--delay")
                delay_sec = int(sys.argv[idx + 1])
            except Exception:
                delay_sec = 3
                
        # Gestione pilot type personalizzato
        pilot_type = "duck"
        if "--pilot" in sys.argv:
            try:
                idx = sys.argv.index("--pilot")
                pilot_type = sys.argv[idx + 1]
            except Exception:
                pilot_type = "duck"
                
        if delay_sec > 0:
            print(f"\n⏳ Attesa di {delay_sec} secondi per permetterti di passare a un'app a Schermo Intero...")
            for i in range(delay_sec, 0, -1):
                print(f"   ⏱️  {i}...")
                time.sleep(1)
            print("🚀 Lancio del banner sopra lo Schermo Intero!")
        else:
            print("\n🚀 Esecuzione Test Banner Notifica in corso...")
            
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        
        pilot_presets = {
            "chef": {
                "title": "Cena con Amici in Pizzeria",
                "provider": "Cena / Cibo 🍕🍽️",
                "pilot_type": "chef",
                "action_btn_text": "🗺️ INDICAZIONI RISTORANTE (MAPPE)",
                "action_url": "https://maps.apple.com/?q=Pizzeria+Torino",
                "location": "Pizzeria Da Michele, Torino",
                "start_time": datetime.now(),
                "is_travel": True
            },
            "captain": {
                "title": "Flight to Torino (W4 6555)",
                "provider": "Volo / Viaggio ✈️",
                "pilot_type": "captain",
                "action_btn_text": "🗺️ AEROPORTO CATANIA (MAPPE)",
                "action_url": "https://maps.apple.com/?q=Catania+Airport+CTA",
                "location": "Terminal 1 - Gate 12",
                "start_time": datetime.now(),
                "is_travel": True
            },
            "owl": {
                "title": "Lezione SmartGrid & Reti Neurali",
                "provider": "Studio / Uni 🎓",
                "pilot_type": "owl",
                "action_btn_text": "📚 AULA & APPUNTI",
                "action_url": "https://calendar.google.com",
                "location": "Aula 3B - Politecnico",
                "start_time": datetime.now(),
                "is_travel": False
            },
            "driver": {
                "title": "Incontro Studio Architettura",
                "provider": "In Presenza 📍 Tempo di Spostamento!",
                "pilot_type": "driver",
                "action_btn_text": "🗺️ VAI CON MAPPE (NAVIGA)",
                "action_url": "https://maps.apple.com/?daddr=Torino+Centro",
                "location": "Corso Vittorio Emanuele II, Torino",
                "start_time": datetime.now(),
                "is_travel": True
            },
            "zen_duck": {
                "title": "Seduta Serenis Online",
                "provider": "Serenis 🛋️",
                "pilot_type": "zen_duck",
                "action_btn_text": "🚀 PARTECIPA AL MEETING",
                "action_url": "https://app.serenis.it/join/ths_pwtsvfnwpea5b8wg",
                "start_time": datetime.now(),
                "is_travel": False
            },
            "duck": {
                "title": "Test Riunione QuakMeeting (Google Meet)",
                "provider": "Google Meet 🟢",
                "pilot_type": "duck",
                "action_btn_text": "🚀 PARTECIPA ORA",
                "action_url": "https://meet.google.com/test-quak-pit",
                "start_time": datetime.now(),
                "is_travel": False
            }
        }
        
        test_m = pilot_presets.get(pilot_type, pilot_presets["duck"])
        _run_banner(test_m)
        app.run()
        return

    print(" Avvio dell'icona nella barra dei menu e del Flight Deck...")
    print("\n 📌 NOTA SUI PERMESSI:")
    print(" Se macOS richiede l'accesso al Calendario, premi 'CONSENTI'.\n")

    app = QuakMeetingMenuBar.alloc().init()
    
    # Se avviato normalmente (interattivo o doppio clic), apri il Flight Deck
    if "--silent" not in sys.argv and "--autostart" not in sys.argv:
        show_dashboard()
        
    app.run()

if __name__ == "__main__":
    main()
