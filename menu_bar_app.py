import AppKit
import objc
import webbrowser
import threading
import time
from datetime import datetime

from calendar_scanner import get_upcoming_meetings
from banner_window import show_banner_async, _run_banner
from autostart import is_autostart_enabled, enable_autostart, disable_autostart
from config_manager import config

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
        
        t0 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🍕 Test Cena / Cibo (Papero Chef + Pizza)", "testFoodBanner:", "")
        t0.setTarget_(self)
        submenu_test.addItem_(t0)

        t1 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("✈️ Test Volo / Viaggio (Capitano + Mappe)", "testTravelBanner:", "")
        t1.setTarget_(self)
        submenu_test.addItem_(t1)

        t2 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🚗 Test In Presenza (Tempo Spostamento)", "testDriveBanner:", "")
        t2.setTarget_(self)
        submenu_test.addItem_(t2)

        t3 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🎓 Test Studio / Università (Gufo Laureato)", "testStudyBanner:", "")
        t3.setTarget_(self)
        submenu_test.addItem_(t3)

        t4 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🛋️ Test Serenis / Relax (Papero Zen)", "testSerenisBanner:", "")
        t4.setTarget_(self)
        submenu_test.addItem_(t4)

        t5 = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🟢 Test Google Meet (Papero Aviatore)", "testBanner:", "")
        t5.setTarget_(self)
        submenu_test.addItem_(t5)

        self.menu.addItem_(item_test_parent)

        # -------------------------------------------------------------
        # SOTTO-MENU PERSONALIZZAZIONE & IMPOSTAZIONI AVANZATE (ADHD)
        # -------------------------------------------------------------
        submenu_prefs = AppKit.NSMenu.alloc().init()
        item_prefs_parent = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Impostazioni & Personalizzazione...", None, ""
        )
        item_prefs_parent.setSubmenu_(submenu_prefs)

        # 1. Anticipo Notifiche Meeting
        curr_m_lead = config.get("lead_time_meeting_minutes", 6)
        sub_m_lead = AppKit.NSMenu.alloc().init()
        item_m_lead = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"⏱️ Anticipo Videochiamate ({curr_m_lead}m)", None, "")
        item_m_lead.setSubmenu_(sub_m_lead)
        
        for m_val in [3, 5, 6, 10, 15]:
            mi = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{m_val} minuti prima", "setMeetingLeadTime:", "")
            mi.setTarget_(self)
            mi.setTag_(m_val)
            if curr_m_lead == m_val:
                mi.setState_(AppKit.NSControlStateValueOn)
            sub_m_lead.addItem_(mi)
        submenu_prefs.addItem_(item_m_lead)

        # 2. Anticipo Viaggi & Spostamenti
        curr_t_lead = config.get("lead_time_travel_minutes", 35)
        sub_t_lead = AppKit.NSMenu.alloc().init()
        item_t_lead = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"🚗 Anticipo Viaggi & Spostamenti ({curr_t_lead}m)", None, "")
        item_t_lead.setSubmenu_(sub_t_lead)
        
        for t_val in [20, 30, 35, 45, 60]:
            ti = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{t_val} minuti prima", "setTravelLeadTime:", "")
            ti.setTarget_(self)
            ti.setTag_(t_val)
            if curr_t_lead == t_val:
                ti.setState_(AppKit.NSControlStateValueOn)
            sub_t_lead.addItem_(ti)
        submenu_prefs.addItem_(item_t_lead)

        # 3. Durata Snooze
        curr_snooze = config.get("default_snooze_seconds", 120)
        curr_snooze_min = curr_snooze // 60
        sub_snooze = AppKit.NSMenu.alloc().init()
        item_snooze = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"💤 Durata Snooze ({curr_snooze_min}m)", None, "")
        item_snooze.setSubmenu_(sub_snooze)

        for s_val in [2, 5, 10]:
            si = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"{s_val} minuti", "setSnoozeTime:", "")
            si.setTarget_(self)
            si.setTag_(s_val)
            if curr_snooze_min == s_val:
                si.setState_(AppKit.NSControlStateValueOn)
            sub_snooze.addItem_(si)
        submenu_prefs.addItem_(item_snooze)

        # 4. Velocità Volo Aereo
        curr_speed = float(config.get("flight_speed", 3.2))
        sub_speed = AppKit.NSMenu.alloc().init()
        item_speed = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"✈️ Velocità Volo Aereo ({curr_speed}x)", None, "")
        item_speed.setSubmenu_(sub_speed)

        speeds = [("Rilassato (2.0x)", 20), ("Standard (3.2x)", 32), ("Turbo (4.8x)", 48)]
        for s_label, s_tag in speeds:
            sp_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(s_label, "setFlightSpeed:", "")
            sp_item.setTarget_(self)
            sp_item.setTag_(s_tag)
            if abs(curr_speed - (s_tag / 10.0)) < 0.1:
                sp_item.setState_(AppKit.NSControlStateValueOn)
            sub_speed.addItem_(sp_item)
        submenu_prefs.addItem_(item_speed)

        # 5. Posizione Schermo
        curr_pos = config.get("banner_position", "top")
        sub_pos = AppKit.NSMenu.alloc().init()
        pos_title = "In Alto (Menu Bar)" if curr_pos == "top" else "In Basso (Sopra Dock)"
        item_pos = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"📍 Posizione Schermo ({pos_title})", None, "")
        item_pos.setSubmenu_(sub_pos)

        p_top = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("In Alto (Sotto Barra dei Menu)", "setBannerPosTop:", "")
        p_top.setTarget_(self)
        if curr_pos == "top":
            p_top.setState_(AppKit.NSControlStateValueOn)
        sub_pos.addItem_(p_top)

        p_bot = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("In Basso (Floating sopra il Dock)", "setBannerPosBottom:", "")
        p_bot.setTarget_(self)
        if curr_pos == "bottom":
            p_bot.setState_(AppKit.NSControlStateValueOn)
        sub_pos.addItem_(p_bot)
        submenu_prefs.addItem_(item_pos)

        # 6. Suoni Notifica
        sub_sound = AppKit.NSMenu.alloc().init()
        sound_on = config.get("sound_enabled", True)
        curr_snd = config.get("sound_name", "Glass")
        item_snd_parent = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"🔔 Suono Notifica ({curr_snd if sound_on else 'Silenzioso'})", None, "")
        item_snd_parent.setSubmenu_(sub_sound)

        s_toggle = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Suono Abilitato", "toggleSoundEnabled:", "")
        s_toggle.setTarget_(self)
        s_toggle.setState_(AppKit.NSControlStateValueOn if sound_on else AppKit.NSControlStateValueOff)
        sub_sound.addItem_(s_toggle)
        sub_sound.addItem_(AppKit.NSMenuItem.separatorItem())

        for snd_name in ["Glass", "Hero", "Ping", "Pop", "Submarine"]:
            s_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(snd_name, "setSoundName:", "")
            s_item.setTarget_(self)
            s_item.setRepresentedObject_(snd_name)
            if sound_on and curr_snd == snd_name:
                s_item.setState_(AppKit.NSControlStateValueOn)
            sub_sound.addItem_(s_item)
        submenu_prefs.addItem_(item_snd_parent)

        submenu_prefs.addItem_(AppKit.NSMenuItem.separatorItem())

        # 7. Modifica manuale JSON & Parole chiave
        item_open_json = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "📝 Modifica Regole & Parole Chiave (config.json)...", "openConfigJson:", ""
        )
        item_open_json.setTarget_(self)
        submenu_prefs.addItem_(item_open_json)

        item_reload_cfg = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔄 Ricarica Impostazioni Ora", "reloadConfig:", ""
        )
        item_reload_cfg.setTarget_(self)
        submenu_prefs.addItem_(item_reload_cfg)

        self.menu.addItem_(item_prefs_parent)
        
        # Aggiorna e Impostazioni di Sistema
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

    # -------------------------------------------------------------
    # AZIONI DI PERSONALIZZAZIONE (CONFIG SETTERS)
    # -------------------------------------------------------------
    @objc.IBAction
    def setMeetingLeadTime_(self, sender):
        val = sender.tag()
        config.set("lead_time_meeting_minutes", val)
        self.build_menu()

    @objc.IBAction
    def setTravelLeadTime_(self, sender):
        val = sender.tag()
        config.set("lead_time_travel_minutes", val)
        self.build_menu()

    @objc.IBAction
    def setSnoozeTime_(self, sender):
        val_min = sender.tag()
        config.set("default_snooze_seconds", val_min * 60)
        self.build_menu()

    @objc.IBAction
    def setFlightSpeed_(self, sender):
        speed_val = sender.tag() / 10.0
        config.set("flight_speed", speed_val)
        self.build_menu()

    @objc.IBAction
    def setBannerPosTop_(self, sender):
        config.set("banner_position", "top")
        self.build_menu()

    @objc.IBAction
    def setBannerPosBottom_(self, sender):
        config.set("banner_position", "bottom")
        self.build_menu()

    @objc.IBAction
    def toggleSoundEnabled_(self, sender):
        curr = config.get("sound_enabled", True)
        config.set("sound_enabled", not curr)
        self.build_menu()

    @objc.IBAction
    def setSoundName_(self, sender):
        snd_name = sender.representedObject()
        config.set("sound_name", snd_name)
        config.set("sound_enabled", True)
        try:
            import subprocess
            subprocess.Popen(["afplay", f"/System/Library/Sounds/{snd_name}.aiff"])
        except Exception:
            pass
        self.build_menu()

    @objc.IBAction
    def openConfigJson_(self, sender):
        config.open_config_in_editor()

    @objc.IBAction
    def reloadConfig_(self, sender):
        config.reload()
        self.meetings = get_upcoming_meetings()
        self.build_menu()

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
        """Scansiona periodicamente e controlla reminder intelligenti con tempi configurati."""
        while self.is_scanning:
            try:
                self.meetings = get_upcoming_meetings()
                now = datetime.now()
                
                meeting_lead = float(config.get("lead_time_meeting_minutes", 6.0))
                travel_lead = float(config.get("lead_time_travel_minutes", 35.0))

                for m in self.meetings:
                    m_id = f"{m['title']}_{m['start_time'].strftime('%Y%m%d%H%M')}"
                    diff_min = (m["start_time"] - now).total_seconds() / 60.0
                    
                    # Notifiche differenziate per ADHD & Viaggio con lead times personalizzati
                    lead_time = travel_lead if m.get("is_travel") else meeting_lead
                    
                    if -2 <= diff_min <= lead_time and m_id not in self.notified_meeting_ids:
                        self.notified_meeting_ids.add(m_id)
                        print(f"NOTIFICA BANNER per: {m['title']} ({m.get('provider')}) [Lead: {lead_time}m]")
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
