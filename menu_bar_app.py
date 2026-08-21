import AppKit
import objc
import webbrowser
import threading
import time
from datetime import datetime

from calendar_scanner import get_upcoming_meetings
from banner_window import show_banner_async, _run_banner
from autostart import is_autostart_enabled, enable_autostart, disable_autostart

class QuakMeetingAppDelegate(AppKit.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        print("QuakMeeting App in esecuzione permanente nella barra dei menu macOS!")

    @objc.IBAction
    def showBannerOnMainThread_(self, meeting_data):
        _run_banner(meeting_data)

class QuakMeetingMenuBar(AppKit.NSObject):
    def init(self):
        self = objc.super(QuakMeetingMenuBar, self).init()
        if self is None:
            return None
            
        self.app = AppKit.NSApplication.sharedApplication()
        self.delegate = QuakMeetingAppDelegate.alloc().init()
        self.app.setDelegate_(self.delegate)
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        
        self.status_bar = AppKit.NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(AppKit.NSVariableStatusItemLength)
        
        self.status_item.button().setTitle_("🦆 QuakMeeting")
        
        self.menu = AppKit.NSMenu.alloc().init()
        self.status_item.setMenu_(self.menu)
        
        self.meetings = []
        self.notified_meeting_ids = set()
        
        # Scanner periodico in background permanente
        self.is_scanning = True
        self.scanner_thread = threading.Thread(target=self._background_scanner_loop, daemon=True)
        self.scanner_thread.start()
        
        self.build_menu()
        return self

    @objc.IBAction
    def refreshMenuOnMainThread_(self, sender):
        self.build_menu()

    def build_menu(self):
        self.menu.removeAllItems()
        
        now = datetime.now()
        upcoming = [m for m in self.meetings if m["end_time"] > now]
        
        # Header Prossimo Evento
        if upcoming:
            next_m = upcoming[0]
            start_str = next_m["start_time"].strftime("%H:%M")
            title_short = next_m["title"][:20]
            
            p_type = next_m.get("pilot_type", "duck")
            if p_type == "chef":
                icon_prefix = "🍕"
            elif p_type == "captain":
                icon_prefix = "✈️"
            elif p_type == "owl":
                icon_prefix = "🎓"
            elif p_type == "driver":
                icon_prefix = "🚗"
            elif p_type == "zen_duck":
                icon_prefix = "🛋️"
            else:
                icon_prefix = "🦆"
            
            self.status_item.button().setTitle_(f"{icon_prefix} {start_str} {title_short}")
            
            item_next = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"Prossimo: {start_str} - {next_m['title']}", None, ""
            )
            self.menu.addItem_(item_next)
            
            action_url = next_m.get("action_url") or next_m.get("meeting_url")
            if action_url:
                btn_title = f"  {next_m.get('action_btn_text', '🚀 Apri Ora')}"
                item_join = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    btn_title, "openNextMeeting:", ""
                )
                item_join.setTarget_(self)
                self.menu.addItem_(item_join)
        else:
            self.status_item.button().setTitle_("🦆 QuakMeeting")
            item_none = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Nessun evento imminente", None, ""
            )
            self.menu.addItem_(item_none)
            
        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        # Sezione Elenco Eventi Odierni
        lbl_header = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "--- EVENTI & RIUNIONI DI OGGI ---", None, ""
        )
        lbl_header.setEnabled_(False)
        self.menu.addItem_(lbl_header)
        
        if self.meetings:
            for idx, m in enumerate(self.meetings):
                s_time = m["start_time"].strftime("%H:%M")
                prov = m.get("provider", "Evento")
                p_type = m.get("pilot_type", "duck")
                
                if p_type == "chef":
                    icon = "🍕"
                elif p_type == "captain":
                    icon = "✈️"
                elif p_type == "owl":
                    icon = "🎓"
                elif p_type == "driver":
                    icon = "🚗"
                elif p_type == "zen_duck":
                    icon = "🛋️"
                else:
                    icon = "🟢"
                
                item_title = f"{icon} {s_time} - {m['title']} ({prov})"
                
                menu_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    item_title, "openMeetingItem:", ""
                )
                menu_item.setTarget_(self)
                menu_item.setTag_(idx)
                self.menu.addItem_(menu_item)
        else:
            item_empty = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "  Nessun evento registrato", None, ""
            )
            item_empty.setEnabled_(False)
            self.menu.addItem_(item_empty)
            
        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        # Menu Test per tutti i Piloti & Temi
        submenu_test = AppKit.NSMenu.alloc().init()
        item_test_parent = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🧪 Test Promemoria & Temi...", None, ""
        )
        item_test_parent.setSubmenu_(submenu_test)
        
        t0 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🍕 Test Cena / Cibo (Papero Chef + Pizza + Mappe)", "testFoodBanner:", "")
        t0.setTarget_(self)
        submenu_test.addItem_(t0)

        t1 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("✈️ Test Volo / Viaggio (Capitano + Mappe)", "testTravelBanner:", "")
        t1.setTarget_(self)
        submenu_test.addItem_(t1)

        t2 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🚗 Test In Presenza (Tempo Spostamento + Mappe)", "testDriveBanner:", "")
        t2.setTarget_(self)
        submenu_test.addItem_(t2)

        t3 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🎓 Test Studio / Università (Gufo Laureato)", "testStudyBanner:", "")
        t3.setTarget_(self)
        submenu_test.addItem_(t3)

        t4 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🛋️ Test Serenis / Terapia (Papero Zen)", "testSerenisBanner:", "")
        t4.setTarget_(self)
        submenu_test.addItem_(t4)

        t5 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🟢 Test Google Meet (Papero Aviatore)", "testBanner:", "")
        t5.setTarget_(self)
        submenu_test.addItem_(t5)

        self.menu.addItem_(item_test_parent)
        
        # Aggiorna e Impostazioni
        item_refresh = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔄 Aggiorna Calendario Ora", "refreshCalendar:", "r"
        )
        item_refresh.setTarget_(self)
        self.menu.addItem_(item_refresh)

        # Toggle Avvio Automatico Mac
        autostart_on = is_autostart_enabled()
        item_autostart = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🚀 Avvia Automaticamente al Login del Mac", "toggleAutostart:", ""
        )
        item_autostart.setTarget_(self)
        item_autostart.setState_(AppKit.NSControlStateValueOn if autostart_on else AppKit.NSControlStateValueOff)
        self.menu.addItem_(item_autostart)

        item_fix_perm = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Ripristina Permessi Calendario macOS", "fixPermissions:", "p"
        )
        item_fix_perm.setTarget_(self)
        self.menu.addItem_(item_fix_perm)
        
        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        item_quit = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "❌ Esci da QuakMeeting", "quitApp:", "q"
        )
        item_quit.setTarget_(self)
        self.menu.addItem_(item_quit)

    @objc.IBAction
    def toggleAutostart_(self, sender):
        if is_autostart_enabled():
            disable_autostart()
        else:
            enable_autostart()
        self.build_menu()

    @objc.IBAction
    def openNextMeeting_(self, sender):
        now = datetime.now()
        upcoming = [m for m in self.meetings if m["end_time"] > now]
        if upcoming:
            url = upcoming[0].get("action_url") or upcoming[0].get("meeting_url")
            if url:
                webbrowser.open(url)

    @objc.IBAction
    def openMeetingItem_(self, sender):
        idx = sender.tag()
        if 0 <= idx < len(self.meetings):
            m = self.meetings[idx]
            url = m.get("action_url") or m.get("meeting_url")
            if url:
                webbrowser.open(url)

    @objc.IBAction
    def refreshCalendar_(self, sender):
        print("Aggiornamento manuale del calendario...")
        self.meetings = get_upcoming_meetings()
        self.build_menu()

    @objc.IBAction
    def testFoodBanner_(self, sender):
        test_m = {
            "title": "Cena con Amici in Pizzeria",
            "provider": "Cena / Cibo 🍕🍽️",
            "pilot_type": "chef",
            "action_btn_text": "🗺️ INDICAZIONI RISTORANTE (MAPPE)",
            "action_url": "https://maps.apple.com/?q=Pizzeria+Da+Michele",
            "start_time": datetime.now(),
            "is_travel": True
        }
        _run_banner(test_m)

    @objc.IBAction
    def testTravelBanner_(self, sender):
        test_m = {
            "title": "Flight to Torino (W4 6555)",
            "provider": "Volo / Viaggio ✈️",
            "pilot_type": "captain",
            "action_btn_text": "🗺️ AEROPORTO CATANIA (MAPPE)",
            "action_url": "https://maps.apple.com/?q=Catania+Airport+CTA",
            "start_time": datetime.now(),
            "is_travel": True
        }
        _run_banner(test_m)

    @objc.IBAction
    def testDriveBanner_(self, sender):
        test_m = {
            "title": "Incontro Studio Architettura",
            "provider": "In Presenza 📍 Tempo di Spostamento!",
            "pilot_type": "driver",
            "action_btn_text": "🗺️ VAI CON MAPPE (NAVIGA)",
            "action_url": "https://maps.apple.com/?daddr=Torino+Centro",
            "start_time": datetime.now(),
            "is_travel": True
        }
        _run_banner(test_m)

    @objc.IBAction
    def testStudyBanner_(self, sender):
        test_m = {
            "title": "Lezione SmartGrid / ICT",
            "provider": "Studio / Uni 🎓",
            "pilot_type": "owl",
            "action_btn_text": "📚 AULA & APPUNTI",
            "action_url": "https://calendar.google.com",
            "start_time": datetime.now(),
            "is_travel": False
        }
        _run_banner(test_m)

    @objc.IBAction
    def testSerenisBanner_(self, sender):
        test_m = {
            "title": "Seduta Serenis Online",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 PARTECIPA AL MEETING",
            "action_url": "https://app.serenis.it/join/ths_pwtsvfnwpea5b8wg",
            "start_time": datetime.now(),
            "is_travel": False
        }
        _run_banner(test_m)

    @objc.IBAction
    def testBanner_(self, sender):
        test_m = {
            "title": "Sync Progetto Team",
            "provider": "Google Meet 🟢",
            "pilot_type": "duck",
            "action_btn_text": "🚀 PARTECIPA ORA",
            "action_url": "https://meet.google.com/test-quak-pit",
            "start_time": datetime.now(),
            "is_travel": False
        }
        _run_banner(test_m)

    @objc.IBAction
    def fixPermissions_(self, sender):
        import subprocess
        print("Ripristino permessi Calendario macOS...")
        subprocess.run(["tccutil", "reset", "Calendar"])
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Calendars"])

    @objc.IBAction
    def quitApp_(self, sender):
        self.is_scanning = False
        AppKit.NSApplication.sharedApplication().terminate_(self)

    def _background_scanner_loop(self):
        """Scansiona periodicamente e controlla reminder intelligenti."""
        while self.is_scanning:
            try:
                self.meetings = get_upcoming_meetings()
                now = datetime.now()
                
                for m in self.meetings:
                    m_id = f"{m['title']}_{m['start_time'].strftime('%Y%m%d%H%M')}"
                    diff_min = (m["start_time"] - now).total_seconds() / 60.0
                    
                    # Notifiche differenziate per ADHD & Viaggio
                    lead_time = 35.0 if m.get("is_travel") else 6.0
                    
                    if -2 <= diff_min <= lead_time and m_id not in self.notified_meeting_ids:
                        self.notified_meeting_ids.add(m_id)
                        print(f"NOTIFICA BANNER per: {m['title']} ({m.get('provider')})")
                        self.performSelectorOnMainThread_withObject_waitUntilDone_(
                            "triggerBannerOnMainThread:",
                            m,
                            False
                        )
                        
                self.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "refreshMenuOnMainThread:",
                    None,
                    False
                )
            except Exception as e:
                print(f"Errore loop scanner: {e}")
                
            time.sleep(60)

    @objc.IBAction
    def triggerBannerOnMainThread_(self, meeting_data):
        _run_banner(meeting_data)

    def run(self):
        self.app.run()

if __name__ == "__main__":
    menu_app = QuakMeetingMenuBar.alloc().init()
    menu_app.run()
