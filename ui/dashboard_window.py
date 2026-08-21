import AppKit
import objc
import webbrowser
import os
from datetime import datetime

try:
    from core.config_manager import config
    from core.calendar_scanner import get_upcoming_meetings, sync_calendar_now
    from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
    from ui.banner_window import _run_banner
except ImportError:
    from config_manager import config
    from calendar_scanner import get_upcoming_meetings, sync_calendar_now
    from autostart import is_autostart_enabled, enable_autostart, disable_autostart
    from banner_window import _run_banner

class DashboardWindowDelegate(AppKit.NSObject):
    def init(self):
        self = objc.super(DashboardWindowDelegate, self).init()
        self.controller = None
        return self

    def windowShouldClose_(self, sender):
        # Quando l'utente preme ✕, nascondiamo la finestra senza terminare l'app in background
        sender.orderOut_(None)
        return False

class DashboardWindowController:
    _instance = None

    @classmethod
    def sharedController(cls):
        if cls._instance is None:
            cls._instance = DashboardWindowController()
        return cls._instance

    def __init__(self):
        self.window = None
        self.delegate = None
        self.meetings = []
        self.is_loading = False
        self.current_tab = 0 # 0: Agenda, 1: Hangar, 2: Impostazioni
        self.content_container = None

    def show(self):
        if self.window is None:
            self._create_window()
        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp().activateIgnoringOtherApps_(True)
        self.refresh_data()

    def _create_window(self):
        width, height = 820.0, 580.0
        screen = AppKit.NSScreen.mainScreen()
        screen_rect = screen.frame() if screen else AppKit.NSMakeRect(0, 0, 1440, 900)
        x_pos = (screen_rect.size.width - width) * 0.5
        y_pos = (screen_rect.size.height - height) * 0.5
        
        frame = AppKit.NSMakeRect(x_pos, y_pos, width, height)
        style = (
            AppKit.NSWindowStyleMaskTitled |
            AppKit.NSWindowStyleMaskClosable |
            AppKit.NSWindowStyleMaskMiniaturizable |
            AppKit.NSWindowStyleMaskFullSizeContentView
        )
        
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, style, AppKit.NSBackingStoreBuffered, False
        )
        self.window.setReleasedWhenClosed_(False)
        self.window.setTitle_("QuakMeeting — Flight Deck")
        self.window.setTitlebarAppearsTransparent_(True)
        self.window.setTitleVisibility_(AppKit.NSWindowTitleHidden)
        self.window.setMovableByWindowBackground_(True)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.11, 0.15, 1.0))

        self.delegate = DashboardWindowDelegate.alloc().init()
        self.delegate.controller = self
        self.window.setDelegate_(self.delegate)

        # Visual Effect View (Frosted Glass macOS Background)
        visual_view = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, width, height))
        visual_view.setMaterial_(AppKit.NSVisualEffectMaterialUnderWindowBackground)
        visual_view.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
        visual_view.setState_(AppKit.NSVisualEffectStateActive)
        visual_view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        self.window.setContentView_(visual_view)

        # 1. Header (Logo, Titolo, Scanner Indicator, Refresh)
        self._build_header(visual_view, width, height)

        # 2. Segmented Tab Selector
        self._build_tab_selector(visual_view, width, height)

        # 3. Content Container
        self.content_container = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(20, 20, width - 40, height - 150))
        self.content_container.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        visual_view.addSubview_(self.content_container)

    def _build_header(self, parent, w, h):
        header_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 85, w - 40, 75))
        
        # Icona App
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon_img = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
            icon_view = AppKit.NSImageView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 12, 52, 52))
            icon_view.setImage_(icon_img)
            header_view.addSubview_(icon_view)
        
        # Titolo App
        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 34, 350, 30))
        title_lbl.setStringValue_("🦆 QuakMeeting")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(20))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        title_lbl.setSelectable_(False)
        header_view.addSubview_(title_lbl)

        # Sottotitolo Status Scanner
        self.status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(64, 12, 450, 22))
        self.status_lbl.setStringValue_("● Scanner Attivo  •  Caricamento eventi...")
        self.status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        self.status_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.70, 0.85, 1.0))
        self.status_lbl.setBezeled_(False)
        self.status_lbl.setDrawsBackground_(False)
        self.status_lbl.setEditable_(False)
        self.status_lbl.setSelectable_(False)
        header_view.addSubview_(self.status_lbl)

        # Pulsante Aggiorna
        refresh_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 170, 20, 130, 34))
        refresh_btn.setTitle_("🔄 Aggiorna")
        refresh_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        refresh_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        refresh_btn.setTarget_(self)
        refresh_btn.setAction_("onRefreshClicked:")
        header_view.addSubview_(refresh_btn)

        parent.addSubview_(header_view)

    def _build_tab_selector(self, parent, w, h):
        self.tab_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 130, w - 40, 32))
        self.tab_segmented.setSegmentCount_(3)
        self.tab_segmented.setLabel_forSegment_("📅 Agenda di Oggi", 0)
        self.tab_segmented.setLabel_forSegment_("🦆 Hangar & Test Volo", 1)
        self.tab_segmented.setLabel_forSegment_("⚙️ Impostazioni & ADHD", 2)
        self.tab_segmented.setSelectedSegment_(0)
        self.tab_segmented.setTarget_(self)
        self.tab_segmented.setAction_("onTabChanged:")
        parent.addSubview_(self.tab_segmented)

    def onTabChanged_(self, sender):
        self.current_tab = sender.selectedSegment()
        self._render_current_tab()

    def onRefreshClicked_(self, sender):
        self.refresh_data(force=True)

    def refresh_data(self, force=False):
        """Carica gli eventi istantaneamente dalla cache e sincronizza in background."""
        # 1. Carica subito da cache in-memory/disco (0.001s)
        self.meetings = get_upcoming_meetings(force_refresh=False)
        now = datetime.now()
        upcoming = [m for m in self.meetings if m["end_time"] > now]
        count = len(upcoming)
        
        if upcoming:
            next_m = upcoming[0]
            s_str = next_m["start_time"].strftime("%H:%M")
            self.status_lbl.setStringValue_(f"● Scanner Attivo  •  {count} eventi in programma oggi  •  Prossimo: {s_str}")
        else:
            self.status_lbl.setStringValue_("● Scanner Attivo  •  Nessun evento rimanente per oggi")
            
        self._render_current_tab()

        # 2. Se forzato o se non ci sono eventi, sincronizza in background
        if force or not self.meetings:
            self.is_loading = True
            if not self.meetings:
                self._render_current_tab()
                
            import threading
            from calendar_scanner import sync_calendar_now

            def worker():
                try:
                    meetings = sync_calendar_now()
                except Exception as e:
                    print(f"Errore sincronizzazione: {e}")
                    meetings = self.meetings

                def on_complete():
                    self.is_loading = False
                    self.meetings = meetings
                    n = datetime.now()
                    up = [m for m in self.meetings if m["end_time"] > n]
                    cnt = len(up)
                    if up:
                        nx = up[0]
                        st = nx["start_time"].strftime("%H:%M")
                        self.status_lbl.setStringValue_(f"● Scanner Attivo  •  {cnt} eventi in programma oggi  •  Prossimo: {st}")
                    else:
                        self.status_lbl.setStringValue_("● Scanner Attivo  •  Nessun evento rimanente per oggi")
                    self._render_current_tab()

                AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(on_complete)

            threading.Thread(target=worker, daemon=True).start()

    def _render_current_tab(self):
        if not self.content_container:
            return
            
        # Pulisci contenuti precedenti
        for sv in list(self.content_container.subviews()):
            sv.removeFromSuperview()
            
        cw = self.content_container.frame().size.width
        ch = self.content_container.frame().size.height

        if self.current_tab == 0:
            self._render_agenda_tab(cw, ch)
        elif self.current_tab == 1:
            self._render_hangar_tab(cw, ch)
        elif self.current_tab == 2:
            self._render_settings_tab(cw, ch)

    # -------------------------------------------------------------
    # TAB 1: AGENDA & EVENTI DI OGGI
    # -------------------------------------------------------------
    def _render_agenda_tab(self, w, h):
        if self.is_loading and not self.meetings:
            loading_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
            
            spinner = AppKit.NSProgressIndicator.alloc().initWithFrame_(AppKit.NSMakeRect((w - 32) * 0.5, (h - 32) * 0.5 + 24, 32, 32))
            spinner.setStyle_(AppKit.NSProgressIndicatorStyleSpinning)
            spinner.setControlSize_(AppKit.NSControlSizeRegular)
            spinner.startAnimation_(None)
            loading_view.addSubview_(spinner)
            
            load_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, (h - 32) * 0.5 - 34, w - 40, 48))
            load_lbl.setStringValue_("🦆 Sincronizzazione dei tuoi Calendari macOS...\nIdentificazione orari, mappe, voli e link riunioni...")
            load_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(13.5))
            load_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.72, 0.78, 0.92, 1.0))
            load_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
            load_lbl.setBezeled_(False)
            load_lbl.setDrawsBackground_(False)
            load_lbl.setEditable_(False)
            loading_view.addSubview_(load_lbl)
            
            self.content_container.addSubview_(loading_view)
            return

        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_h = 76.0
        gap = 12.0
        total_items = max(1, len(self.meetings))
        content_h = max(h, total_items * (card_h + gap) + 20.0)
        
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))
        
        if not self.meetings:
            empty_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, content_h - 100, w - 40, 50))
            empty_lbl.setStringValue_("🧘‍♂️ Nessun evento registrato per oggi nei calendari abilitati.\nRilassati o aggiungi un evento in Apple Calendar!")
            empty_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(14))
            empty_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.6, 0.65, 0.8, 1.0))
            empty_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
            empty_lbl.setBezeled_(False)
            empty_lbl.setDrawsBackground_(False)
            empty_lbl.setEditable_(False)
            doc_view.addSubview_(empty_lbl)
        else:
            for idx, m in enumerate(self.meetings):
                y_item = content_h - (idx + 1) * (card_h + gap)
                card = self._create_meeting_card(m, idx, 0, y_item, w - 16, card_h)
                doc_view.addSubview_(card)

        scroll_view.setDocumentView_(doc_view)
        # Scroll to top
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        self.content_container.addSubview_(scroll_view)

    def _create_meeting_card(self, m, idx, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        
        # Sfondo card arrotondata
        bg_effect = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        bg_effect.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
        bg_effect.setBlendingMode_(AppKit.NSVisualEffectBlendingModeWithinWindow)
        bg_effect.setState_(AppKit.NSVisualEffectStateActive)
        bg_effect.setWantsLayer_(True)
        bg_effect.layer().setCornerRadius_(12.0)
        bg_effect.layer().setMasksToBounds_(True)
        card.addSubview_(bg_effect)

        # Icona Pilota
        p_type = m.get("pilot_type", "duck")
        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🟢"}
        icon_str = icon_map.get(p_type, "🦆")

        icon_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, 18, 40, 40))
        icon_lbl.setStringValue_(icon_str)
        icon_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(26))
        icon_lbl.setBezeled_(False)
        icon_lbl.setDrawsBackground_(False)
        icon_lbl.setEditable_(False)
        card.addSubview_(icon_lbl)

        # Titolo Evento
        s_time = m["start_time"].strftime("%H:%M")
        e_time = m["end_time"].strftime("%H:%M") if m.get("end_time") else ""
        time_text = f"{s_time} - {e_time}" if e_time else s_time

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 38, w - 240, 24))
        title_lbl.setStringValue_(f"{s_time}  •  {m['title']}")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        # Sottotitolo Dettagli / Luogo
        sub_str = m.get("provider", "Evento")
        if m.get("location") and m["location"] != "missing value":
            sub_str += f"  •  📍 {m['location'][:35]}"
        elif m.get("action_url") and "meet.google.com" in m["action_url"]:
            sub_str += "  •  🌐 Google Meet"

        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 16, w - 240, 20))
        sub_lbl.setStringValue_(sub_str)
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        sub_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.72, 0.85, 1.0))
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        card.addSubview_(sub_lbl)

        # Pulsante Azione Rapida
        action_url = m.get("action_url") or m.get("meeting_url")
        if action_url:
            btn_title = m.get("action_btn_text", "🚀 PARTECIPA")
            if "MAPPE" in btn_title or "INDICAZIONI" in btn_title:
                btn_short = "🗺️ Mappe"
            elif "ZOOM" in btn_title:
                btn_short = "🔷 Zoom"
            elif "TEAMS" in btn_title:
                btn_short = "🟣 Teams"
            else:
                btn_short = "🚀 Partecipa"

            action_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 150, 20, 134, 34))
            action_btn.setTitle_(btn_short)
            action_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
            action_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12))
            action_btn.setTarget_(self)
            action_btn.setAction_("onOpenMeetingUrl:")
            action_btn.setTag_(idx)
            card.addSubview_(action_btn)

        return card

    def onOpenMeetingUrl_(self, sender):
        idx = sender.tag()
        if 0 <= idx < len(self.meetings):
            url = self.meetings[idx].get("action_url") or self.meetings[idx].get("meeting_url")
            if url:
                webbrowser.open(url)

    # -------------------------------------------------------------
    # TAB 2: HANGAR DEI PILOTI & TEST VOLO
    # -------------------------------------------------------------
    def _render_hangar_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        
        pilots = [
            ("duck", "🦆 Papero Aviatore", "Videochiamate Google Meet, Zoom, MS Teams & Call Online.", "Google Green", self.testAviatorDuck),
            ("chef", "👨‍🍳 Papero Chef & Pizza", "Cene, Pranzi, Ristoranti, Pizzerie & Aperitivi con indicazioni Mappe.", "Coral Food", self.testChefDuck),
            ("captain", "🧑‍✈️ Capitano Jet Airliner", "Voli aerei, Aeroporti CTA/TRN, Treni Frecciarossa, Bus & Spostamenti.", "Sky Blue", self.testCaptainJet),
            ("owl", "🦉 Gufo Accademico", "Lezioni Universitarie, Politecnico, Esami, Tesi & Corsi di Studio.", "Amethyst Academic", self.testAcademicOwl),
            ("driver", "🏎️ Speed Racer Driver", "Eventi in presenza, Palestra, Appuntamenti e Spostamenti con Traffico.", "Emerald Speed", self.testSpeedRacer),
            ("zen_duck", "🦆🌸 Papero Zen", "Sedute Serenis, Terapia Psicologica, Yoga, Benessere & Meditazione.", "Teal Zen", self.testZenDuck)
        ]

        card_h = 108.0
        gap = 14.0
        content_h = len(pilots) * (card_h + gap) + 20.0
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        for idx, (p_id, p_name, p_desc, p_theme, callback) in enumerate(pilots):
            y_item = content_h - (idx + 1) * (card_h + gap)
            p_card = self._create_pilot_card(p_id, p_name, p_desc, p_theme, callback, 0, y_item, w - 16, card_h)
            doc_view.addSubview_(p_card)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        self.content_container.addSubview_(scroll_view)

    def _create_pilot_card(self, p_id, p_name, p_desc, p_theme, callback, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        
        bg_effect = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        bg_effect.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
        bg_effect.setBlendingMode_(AppKit.NSVisualEffectBlendingModeWithinWindow)
        bg_effect.setState_(AppKit.NSVisualEffectStateActive)
        bg_effect.setWantsLayer_(True)
        bg_effect.layer().setCornerRadius_(12.0)
        bg_effect.layer().setMasksToBounds_(True)
        card.addSubview_(bg_effect)

        # Titolo Pilota
        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 34, w - 200, 24))
        title_lbl.setStringValue_(p_name)
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(15))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        # Descrizione & Ruolo
        desc_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 68, w - 200, 32))
        desc_lbl.setStringValue_(p_desc)
        desc_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        desc_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.72, 0.76, 0.88, 1.0))
        desc_lbl.setBezeled_(False)
        desc_lbl.setDrawsBackground_(False)
        desc_lbl.setEditable_(False)
        card.addSubview_(desc_lbl)

        # Badge Tema
        theme_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, 12, 160, 20))
        theme_lbl.setStringValue_(f"🎨 Tema: {p_theme}")
        theme_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11))
        theme_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.5, 0.8, 0.95, 1.0))
        theme_lbl.setBezeled_(False)
        theme_lbl.setDrawsBackground_(False)
        theme_lbl.setEditable_(False)
        card.addSubview_(theme_lbl)

        # Pulsante Test Volo
        test_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 165, (h - 36) * 0.5, 145, 36))
        test_btn.setTitle_("✈️ Fai Volare")
        test_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        test_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        test_btn.setTarget_(self)
        test_btn.setAction_(f"onTestPilotClicked_{p_id}:")
        card.addSubview_(test_btn)

        return card

    # Pilot Test Dispatchers
    def onTestPilotClicked_duck_(self, sender): self.testAviatorDuck()
    def onTestPilotClicked_chef_(self, sender): self.testChefDuck()
    def onTestPilotClicked_captain_(self, sender): self.testCaptainJet()
    def onTestPilotClicked_owl_(self, sender): self.testAcademicOwl()
    def onTestPilotClicked_driver_(self, sender): self.testSpeedRacer()
    def onTestPilotClicked_zen_duck_(self, sender): self.testZenDuck()

    def testAviatorDuck(self):
        _run_banner({
            "title": "Weekly Team Sync Online",
            "provider": "Google Meet 🟢",
            "pilot_type": "duck",
            "action_btn_text": "🚀 PARTECIPA ORA",
            "action_url": "https://meet.google.com/test-quak",
            "start_time": datetime.now(),
            "is_travel": False
        })

    def testChefDuck(self):
        _run_banner({
            "title": "Cena con Amici in Pizzeria",
            "provider": "Cena / Cibo 🍕🍽️",
            "pilot_type": "chef",
            "action_btn_text": "🗺️ INDICAZIONI RISTORANTE (MAPPE)",
            "action_url": "https://maps.apple.com/?q=Pizzeria+Da+Michele",
            "location": "Pizzeria Da Michele, Torino",
            "start_time": datetime.now(),
            "is_travel": True
        })

    def testCaptainJet(self):
        _run_banner({
            "title": "Volo TRN ➔ CTA (WizzAir W4 6555)",
            "provider": "Volo / Viaggio ✈️",
            "pilot_type": "captain",
            "action_btn_text": "🗺️ AEROPORTO CASELLE (MAPPE)",
            "action_url": "https://maps.apple.com/?q=Aeroporto+Torino+TRN",
            "location": "Aeroporto di Torino Caselle",
            "start_time": datetime.now(),
            "is_travel": True
        })

    def testAcademicOwl(self):
        _run_banner({
            "title": "Lezione SmartGrid & ICT",
            "provider": "Studio / Uni 🎓",
            "pilot_type": "owl",
            "action_btn_text": "📚 AULA & APPUNTI",
            "action_url": "https://calendar.google.com",
            "location": "Politecnico di Torino - Aula 7",
            "start_time": datetime.now(),
            "is_travel": False
        })

    def testSpeedRacer(self):
        _run_banner({
            "title": "Allenamento Palestra CrossFit",
            "provider": "In Presenza 📍 Tempo di Spostamento!",
            "pilot_type": "driver",
            "action_btn_text": "🗺️ VAI CON MAPPE (NAVIGA)",
            "action_url": "https://maps.apple.com/?daddr=Palestra+Torino",
            "location": "Palestra Torino Centro",
            "start_time": datetime.now(),
            "is_travel": True
        })

    def testZenDuck(self):
        _run_banner({
            "title": "Seduta Serenis Online",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 PARTECIPA AL MEETING",
            "action_url": "https://app.serenis.it/join/test",
            "start_time": datetime.now(),
            "is_travel": False
        })

    # -------------------------------------------------------------
    # TAB 3: IMPOSTAZIONI & PREFERENZE (ADHD)
    # -------------------------------------------------------------
    def _render_settings_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)

        content_h = 440.0
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w - 16, content_h))
        bg_effect = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w - 16, content_h))
        bg_effect.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
        bg_effect.setBlendingMode_(AppKit.NSVisualEffectBlendingModeWithinWindow)
        bg_effect.setState_(AppKit.NSVisualEffectStateActive)
        bg_effect.setWantsLayer_(True)
        bg_effect.layer().setCornerRadius_(12.0)
        bg_effect.layer().setMasksToBounds_(True)
        card.addSubview_(bg_effect)

        y = content_h - 40.0

        # 1. Anticipo Videochiamate
        y = self._add_setting_row(card, "⏱️ Anticipo Videochiamate:", [
            ("3 minuti prima", 3), ("5 minuti prima", 5), ("6 minuti prima (Default)", 6), ("10 minuti prima", 10), ("15 minuti prima", 15)
        ], config.get("lead_time_meeting_minutes", 6), "onSelectMeetingLead:", y, w)

        # 2. Anticipo Viaggi
        y = self._add_setting_row(card, "🚗 Anticipo Viaggi & Spostamenti:", [
            ("20 minuti prima", 20), ("30 minuti prima", 30), ("35 minuti prima (Default)", 35), ("45 minuti prima", 45), ("60 minuti prima", 60)
        ], config.get("lead_time_travel_minutes", 35), "onSelectTravelLead:", y, w)

        # 3. Durata Snooze
        snooze_val = config.get("default_snooze_seconds", 120) // 60
        y = self._add_setting_row(card, "💤 Durata Snooze Promemoria:", [
            ("2 minuti", 2), ("5 minuti", 5), ("10 minuti", 10)
        ], snooze_val, "onSelectSnoozeDuration:", y, w)

        # 4. Velocità Volo
        curr_spd = int(float(config.get("flight_speed", 3.2)) * 10)
        y = self._add_setting_row(card, "✈️ Velocità Volo Aereo:", [
            ("Rilassato (2.0x)", 20), ("Standard (3.2x)", 32), ("Turbo (4.8x)", 48)
        ], curr_spd, "onSelectFlightSpeed:", y, w)

        # 5. Suono Notifica
        curr_snd = config.get("sound_name", "Glass")
        y = self._add_setting_row(card, "🔔 Suono Notifica Chime:", [
            ("Glass (Predefinito)", "Glass"), ("Hero", "Hero"), ("Ping", "Ping"), ("Pop", "Pop"), ("Submarine", "Submarine")
        ], curr_snd, "onSelectSound:", y, w)

        # 6. Toggle Avvio al Login Mac
        autostart_chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(20, y - 28, 400, 24))
        autostart_chk.setButtonType_(AppKit.NSButtonTypeSwitch)
        autostart_chk.setTitle_("🚀 Avvia QuakMeeting automaticamente al login del Mac")
        autostart_chk.setFont_(AppKit.NSFont.systemFontOfSize_(13))
        autostart_chk.setState_(AppKit.NSControlStateValueOn if is_autostart_enabled() else AppKit.NSControlStateValueOff)
        autostart_chk.setTarget_(self)
        autostart_chk.setAction_("onToggleAutostart:")
        card.addSubview_(autostart_chk)
        y -= 48.0

        # 7. File Regole & Editor JSON
        open_json_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(20, y - 28, 300, 32))
        open_json_btn.setTitle_("📝 Modifica Parole Chiave & Calendari (config.json)...")
        open_json_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        open_json_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        open_json_btn.setTarget_(self)
        open_json_btn.setAction_("onOpenConfigEditor:")
        card.addSubview_(open_json_btn)

        doc_view.addSubview_(card)
        scroll_view.setDocumentView_(doc_view)
        self.content_container.addSubview_(scroll_view)

    def _add_setting_row(self, parent, label_text, options, current_val, action_name, y, w):
        lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, y, 260, 24))
        lbl.setStringValue_(label_text)
        lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
        lbl.setTextColor_(AppKit.NSColor.whiteColor())
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        parent.addSubview_(lbl)

        popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(280, y - 2, 280, 28), False)
        popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        popup.setTarget_(self)
        popup.setAction_(action_name)

        for opt_title, opt_val in options:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(opt_title, None, "")
            item.setRepresentedObject_(opt_val)
            popup.menu().addItem_(item)
            if opt_val == current_val:
                popup.selectItem_(item)

        parent.addSubview_(popup)
        return y - 44.0

    # Setting Handlers
    def onSelectMeetingLead_(self, sender):
        val = sender.selectedItem().representedObject()
        config.set("lead_time_meeting_minutes", int(val))

    def onSelectTravelLead_(self, sender):
        val = sender.selectedItem().representedObject()
        config.set("lead_time_travel_minutes", int(val))

    def onSelectSnoozeDuration_(self, sender):
        val_min = sender.selectedItem().representedObject()
        config.set("default_snooze_seconds", int(val_min) * 60)

    def onSelectFlightSpeed_(self, sender):
        spd_tag = sender.selectedItem().representedObject()
        config.set("flight_speed", float(spd_tag) / 10.0)

    def onSelectSound_(self, sender):
        snd_name = sender.selectedItem().representedObject()
        config.set("sound_name", str(snd_name))
        config.set("sound_enabled", True)
        try:
            import subprocess
            subprocess.Popen(["afplay", f"/System/Library/Sounds/{snd_name}.aiff"])
        except Exception:
            pass

    def onToggleAutostart_(self, sender):
        if is_autostart_enabled():
            disable_autostart()
        else:
            enable_autostart()

    def onOpenConfigEditor_(self, sender):
        config.open_config_in_editor()

def show_dashboard():
    controller = DashboardWindowController.sharedController()
    controller.show()

if __name__ == "__main__":
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
    show_dashboard()
    app.run()
