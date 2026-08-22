import AppKit
import objc
import webbrowser
import os
import time
import threading
from datetime import datetime

try:
    from core.config_manager import config
    from core.calendar_scanner import get_upcoming_meetings, sync_calendar_now, get_available_calendars
    from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
    from core.services.eta_service import eta_service, MODE_ICONS, MODE_LABELS
    from ui.banner_window import _run_banner
except ImportError:
    from config_manager import config
    from calendar_scanner import get_upcoming_meetings, sync_calendar_now, get_available_calendars
    from autostart import is_autostart_enabled, enable_autostart, disable_autostart
    from eta_service import eta_service, MODE_ICONS, MODE_LABELS
    from banner_window import _run_banner

class DashboardWindowDelegate(AppKit.NSObject):
    def init(self):
        self = objc.super(DashboardWindowDelegate, self).init()
        self.controller = None
        return self

    def windowShouldClose_(self, sender):
        # Quando l'utente preme ✕, nascondiamo la finestra e rimettiamo l'app in background accessorio
        sender.orderOut_(None)
        AppKit.NSApp().setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
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
        self.current_tab = 0 # 0: Agenda, 1: Hangar, 2: Impostazioni & Timing
        self.content_container = None

    def show(self, tab_index=None):
        if self.window is None:
            self._create_window()
        if tab_index is not None:
            self.current_tab = tab_index
            if hasattr(self, 'tab_segmented') and self.tab_segmented:
                self.tab_segmented.setSelectedSegment_(tab_index)
        
        # Porta l'app in primo piano e mostra la finestra
        app = AppKit.NSApp()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        self.window.makeKeyAndOrderFront_(None)
        self.window.orderFrontRegardless()
        app.activateIgnoringOtherApps_(True)
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
        title_lbl.setStringValue_("🦆 QuakMeeting — Flight Deck")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(19))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        title_lbl.setSelectable_(False)
        header_view.addSubview_(title_lbl)

        # Sottotitolo Status Scanner
        self.status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(64, 12, 450, 22))
        self.status_lbl.setStringValue_("🟢 Scanner Attivo  •  Caricamento eventi...")
        self.status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        self.status_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.70, 0.85, 1.0))
        self.status_lbl.setBezeled_(False)
        self.status_lbl.setDrawsBackground_(False)
        self.status_lbl.setEditable_(False)
        self.status_lbl.setSelectable_(False)
        header_view.addSubview_(self.status_lbl)

        # Pulsante Sincronizza
        refresh_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 170, 20, 130, 34))
        refresh_btn.setTitle_("🔄 Sincronizza")
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
        self.tab_segmented.setLabel_forSegment_("🦆 Hangar Piloti", 1)
        self.tab_segmented.setLabel_forSegment_("⚙️ Preferenze & Timing", 2)
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
            self.status_lbl.setStringValue_(f"🟢 Scanner Attivo  •  {count} eventi in programma oggi  •  Prossimo: {s_str}")
        else:
            self.status_lbl.setStringValue_("🟢 Scanner Attivo  •  Nessun evento rimanente per oggi")
            
        self._render_current_tab()

        # 2. Se forzato o se non ci sono eventi, sincronizza in background
        if force or not self.meetings:
            self.is_loading = True
            if not self.meetings:
                self._render_current_tab()
                
            import threading

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
                    up = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > n) or (m.get("start_time") and m["start_time"] > n)]
                    cnt = len(up)
                    if up:
                        nx = up[0]
                        st = nx["start_time"].strftime("%H:%M") if nx.get("start_time") else "--:--"
                        self.status_lbl.setStringValue_(f"🟢 Scanner Attivo  •  {cnt} eventi in programma oggi  •  Prossimo: {st}")
                    else:
                        self.status_lbl.setStringValue_("🟢 Scanner Attivo  •  Nessun evento rimanente per oggi")
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
        
        # Sfondo card arrotondata con bordo sottile
        bg_effect = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        bg_effect.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
        bg_effect.setBlendingMode_(AppKit.NSVisualEffectBlendingModeWithinWindow)
        bg_effect.setState_(AppKit.NSVisualEffectStateActive)
        bg_effect.setWantsLayer_(True)
        bg_effect.layer().setCornerRadius_(12.0)
        bg_effect.layer().setMasksToBounds_(True)
        bg_effect.layer().setBorderWidth_(1.0)
        bg_effect.layer().setBorderColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.08).CGColor())
        card.addSubview_(bg_effect)

        # Icona Pilota
        p_type = m.get("pilot_type", "duck")
        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}
        icon_str = icon_map.get(p_type, "🦆")

        icon_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, 18, 40, 40))
        icon_lbl.setStringValue_(icon_str)
        icon_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(26))
        icon_lbl.setBezeled_(False)
        icon_lbl.setDrawsBackground_(False)
        icon_lbl.setEditable_(False)
        card.addSubview_(icon_lbl)

        # Titolo Evento & Orario
        s_time = m["start_time"].strftime("%H:%M") if m.get("start_time") else "--:--"
        e_time = m["end_time"].strftime("%H:%M") if m.get("end_time") else ""
        time_str = f"{s_time} - {e_time}" if e_time else s_time
        m_title = (m.get("title") or "Senza Titolo").strip()

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 38, w - 275, 24))
        title_lbl.setStringValue_(f"{time_str}  •  {m_title}")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        # Sottotitolo Dettagli / Luogo
        sub_str = m.get("provider", "Evento")
        loc = m.get("location")
        if loc and loc != "missing value":
            sub_str += f"  •  📍 {loc[:35]}"
            if m.get("travel_time_minutes"):
                t_mode = m.get("transport_mode", config.get("transport_mode", "transit"))
                icon = MODE_ICONS.get(t_mode, "🚆")
                sub_str += f" ({icon} ~{m['travel_time_minutes']}m)"
        elif m.get("action_url") and "meet.google.com" in m["action_url"]:
            sub_str += "  •  🌐 Google Meet"

        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 16, w - 275, 20))
        sub_lbl.setStringValue_(sub_str)
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        sub_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.72, 0.85, 1.0))
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        card.addSubview_(sub_lbl)

        # Pulsanti Azione (Partecipa + Copia Link)
        action_url = m.get("action_url") or m.get("meeting_url")
        if not action_url and loc and loc != "missing value":
            import urllib.parse
            action_url = f"https://maps.apple.com/?q={urllib.parse.quote(loc)}"
            m["action_url"] = action_url

        if action_url:
            btn_title = m.get("action_btn_text", "🚀 PARTECIPA")
            if "MAPPE" in btn_title or "INDICAZIONI" in btn_title or "maps.apple.com" in action_url:
                btn_short = "🗺️ Mappe"
            elif "ZOOM" in btn_title or "zoom.us" in action_url:
                btn_short = "🔷 Zoom"
            elif "TEAMS" in btn_title or "teams.microsoft" in action_url:
                btn_short = "🟣 Teams"
            elif "serenis" in action_url:
                btn_short = "🛋️ Serenis"
            else:
                btn_short = "🚀 Partecipa"

            action_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 142, 20, 126, 34))
            action_btn.setTitle_(btn_short)
            action_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
            action_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12))
            action_btn.setTarget_(self)
            action_btn.setAction_("onOpenMeetingUrl:")
            action_btn.setTag_(idx)
            card.addSubview_(action_btn)

            copy_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 238, 20, 90, 34))
            copy_btn.setTitle_("📋 Copia")
            copy_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
            copy_btn.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            copy_btn.setTarget_(self)
            copy_btn.setAction_("onCopyMeetingUrl:")
            copy_btn.setTag_(idx)
            card.addSubview_(copy_btn)

        return card

    def onOpenMeetingUrl_(self, sender):
        idx = sender.tag()
        if 0 <= idx < len(self.meetings):
            url = self.meetings[idx].get("action_url") or self.meetings[idx].get("meeting_url")
            if url:
                webbrowser.open(url)

    def onCopyMeetingUrl_(self, sender):
        idx = sender.tag()
        if 0 <= idx < len(self.meetings):
            url = self.meetings[idx].get("action_url") or self.meetings[idx].get("meeting_url")
            if url:
                pasteboard = AppKit.NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(url, AppKit.NSPasteboardTypeString)
                sender.setTitle_("✓ Copiato!")
                def reset():
                    time.sleep(1.5)
                    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(lambda: sender.setTitle_("📋 Copia"))
                threading.Thread(target=reset, daemon=True).start()

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
    # TAB 3: IMPOSTAZIONI & PREFERENZE DI TIMING
    # -------------------------------------------------------------
    def _render_settings_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_w = w - 16.0
        gap = 14.0
        
        # Calcolo dinamico altezza contenuto (6 sezioni essenziali e pulite)
        c1_h = 195.0 # Timing & Anticipi Multipli
        c_eta_h = 185.0 # Indirizzo Casa / Partenza & Stima Percorso (Apple Maps ETA)
        c2_h = 140.0 # Banner & Dinamica Volo
        c3_h = 140.0 # Audio & Chime
        c4_h = 135.0 # Calendari macOS Inclusi
        c5_h = 125.0 # Sistema & Config
        
        content_h = c1_h + c_eta_h + c2_h + c3_h + c4_h + c5_h + gap * 7 + 20.0
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        curr_y = content_h - gap

        # SEZIONE 1: TIMING & ANTICIPI MULTIPLI
        curr_y -= c1_h
        card1 = self._create_card_container(0, curr_y, card_w, c1_h)
        self._build_timing_section(card1, card_w, c1_h)
        doc_view.addSubview_(card1)

        # SEZIONE 2: INDIRIZZO DI PARTENZA & STIMA PERCORSO (APPLE MAPS ETA)
        curr_y -= (c_eta_h + gap)
        card_eta = self._create_card_container(0, curr_y, card_w, c_eta_h)
        self._build_eta_section(card_eta, card_w, c_eta_h)
        doc_view.addSubview_(card_eta)

        # SEZIONE 3: BANNER A SCHERMO & DINAMICA DI VOLO
        curr_y -= (c2_h + gap)
        card2 = self._create_card_container(0, curr_y, card_w, c2_h)
        self._build_flight_section(card2, card_w, c2_h)
        doc_view.addSubview_(card2)

        # SEZIONE 4: AUDIO & SUONI DI SISTEMA
        curr_y -= (c3_h + gap)
        card3 = self._create_card_container(0, curr_y, card_w, c3_h)
        self._build_audio_section(card3, card_w, c3_h)
        doc_view.addSubview_(card3)

        # SEZIONE 5: CALENDARI MACOS INCLUSI
        curr_y -= (c4_h + gap)
        card4 = self._create_card_container(0, curr_y, card_w, c4_h)
        self._build_calendars_section(card4, card_w, c4_h)
        doc_view.addSubview_(card4)

        # SEZIONE 6: SISTEMA & CONFIGURAZIONE JSON
        curr_y -= (c5_h + gap)
        card5 = self._create_card_container(0, curr_y, card_w, c5_h)
        self._build_system_section(card5, card_w, c5_h)
        doc_view.addSubview_(card5)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        self.content_container.addSubview_(scroll_view)

    def _create_card_container(self, x, y, w, h):
        """Crea un pannello frosted glass moderno con angoli arrotondati e bordo sottile."""
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        bg_effect = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        bg_effect.setMaterial_(AppKit.NSVisualEffectMaterialPopover)
        bg_effect.setBlendingMode_(AppKit.NSVisualEffectBlendingModeWithinWindow)
        bg_effect.setState_(AppKit.NSVisualEffectStateActive)
        bg_effect.setWantsLayer_(True)
        bg_effect.layer().setCornerRadius_(14.0)
        bg_effect.layer().setMasksToBounds_(True)
        bg_effect.layer().setBorderWidth_(1.0)
        bg_effect.layer().setBorderColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.10).CGColor())
        card.addSubview_(bg_effect)
        return card

    def _add_section_header(self, parent, title, subtitle, y, w):
        """Intestazione di sezione con titolo bold e sottotitolo descrittivo."""
        t_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, w - 36, 22))
        t_lbl.setStringValue_(title)
        t_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14))
        t_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        s_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y - 18, w - 36, 18))
        s_lbl.setStringValue_(subtitle)
        s_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        s_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.72, 0.85, 1.0))
        s_lbl.setBezeled_(False)
        s_lbl.setDrawsBackground_(False)
        s_lbl.setEditable_(False)
        parent.addSubview_(s_lbl)

    def _build_timing_section(self, card, w, h):
        self._add_section_header(card, "⏱️ Anticipi Notifiche & Promemoria Multipli", "Seleziona gli scaglioni di preavviso per ricevere promemoria progressivi nel tempo.", h - 28, w)
        
        y = h - 68.0
        # 1. Scaglioni Videochiamate
        lbl1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 230, 20))
        lbl1.setStringValue_("📹 Scaglioni Call & Riunioni:")
        lbl1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl1.setTextColor_(AppKit.NSColor.whiteColor())
        lbl1.setBezeled_(False)
        lbl1.setDrawsBackground_(False)
        lbl1.setEditable_(False)
        card.addSubview_(lbl1)
        
        curr_meeting_stages = set(config.get("meeting_reminder_stages", [20, 10, 5, 2]))
        meeting_opts = [(30, "30m"), (20, "20m"), (15, "15m"), (10, "10m"), (5, "5m"), (2, "2m"), (0, "All'inizio (0m)")]
        
        x_btn = 250.0
        for val, label in meeting_opts:
            btn_w = 64.0 if val != 0 else 102.0
            chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_btn, y, btn_w, 24))
            chk.setButtonType_(AppKit.NSButtonTypeSwitch)
            chk.setTitle_(label)
            chk.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            chk.setState_(AppKit.NSControlStateValueOn if val in curr_meeting_stages else AppKit.NSControlStateValueOff)
            chk.setTag_(val)
            chk.setTarget_(self)
            chk.setAction_("onToggleMeetingStage:")
            card.addSubview_(chk)
            x_btn += (btn_w + 6.0)
            
        y -= 44.0
        # 2. Scaglioni Viaggi
        lbl2 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 230, 20))
        lbl2.setStringValue_("🚗 Scaglioni Viaggi & Mappe:")
        lbl2.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl2.setTextColor_(AppKit.NSColor.whiteColor())
        lbl2.setBezeled_(False)
        lbl2.setDrawsBackground_(False)
        lbl2.setEditable_(False)
        card.addSubview_(lbl2)
        
        curr_travel_stages = set(config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        travel_opts = [(60, "60m"), (45, "45m"), (30, "30m"), (15, "15m"), (5, "5m"), (2, "2m"), (0, "All'inizio (0m)")]
        
        x_btn = 250.0
        for val, label in travel_opts:
            btn_w = 64.0 if val != 0 else 102.0
            chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_btn, y, btn_w, 24))
            chk.setButtonType_(AppKit.NSButtonTypeSwitch)
            chk.setTitle_(label)
            chk.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            chk.setState_(AppKit.NSControlStateValueOn if val in curr_travel_stages else AppKit.NSControlStateValueOff)
            chk.setTag_(val)
            chk.setTarget_(self)
            chk.setAction_("onToggleTravelStage:")
            card.addSubview_(chk)
            x_btn += (btn_w + 6.0)

        y -= 44.0
        # 3. Snooze
        snooze_val = config.get("default_snooze_seconds", 120) // 60
        self._add_popup_row(card, "💤 Durata Snooze Promemoria:", "Intervallo di rinvio quando premi il pulsante Snooze sul banner", [
            ("1 minuto", 1), ("2 minuti (Predefinito)", 2), ("5 minuti", 5), ("10 minuti", 10), ("15 minuti", 15)
        ], snooze_val, "onSelectSnoozeDuration:", y, w)

    def _build_eta_section(self, card, w, h):
        self._add_section_header(card, "📍 Indirizzo di Partenza & Stima Percorso (Apple Maps ETA)", "Calcola in tempo reale la durata del tragitto con Mezzi Pubblici, Auto, Piedi o Bici.", h - 28, w)

        y = h - 68.0
        # 1. Indirizzo Casa / Partenza
        lbl1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 275, 20))
        lbl1.setStringValue_("🏠 Indirizzo di Casa / Partenza:")
        lbl1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl1.setTextColor_(AppKit.NSColor.whiteColor())
        lbl1.setBezeled_(False)
        lbl1.setDrawsBackground_(False)
        lbl1.setEditable_(False)
        card.addSubview_(lbl1)

        curr_addr = str(config.get("home_address", "") or "")
        self.home_addr_field = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(300, y, 260, 26))
        self.home_addr_field.setStringValue_(curr_addr)
        self.home_addr_field.setPlaceholderString_("Es. Corso Duca degli Abruzzi 24, Torino")
        self.home_addr_field.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.home_addr_field.setTarget_(self)
        self.home_addr_field.setAction_("onSaveHomeAddress:")
        card.addSubview_(self.home_addr_field)

        save_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(570, y - 2, 90, 30))
        save_btn.setTitle_("💾 Salva")
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        save_btn.setTarget_(self)
        save_btn.setAction_("onSaveHomeAddress:")
        card.addSubview_(save_btn)

        y -= 44.0
        # 2. Modalità di Trasporto Predefinita (Segmented Control: Mezzi, Auto, Piedi, Bici)
        lbl2 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 275, 20))
        lbl2.setStringValue_("🚦 Modalità Trasporto Predefinita:")
        lbl2.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl2.setTextColor_(AppKit.NSColor.whiteColor())
        lbl2.setBezeled_(False)
        lbl2.setDrawsBackground_(False)
        lbl2.setEditable_(False)
        card.addSubview_(lbl2)

        modes = ["transit", "automobile", "walking", "bicycling"]
        curr_mode = config.get("transport_mode", "transit")
        sel_idx = modes.index(curr_mode) if curr_mode in modes else 0

        self.mode_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(300, y - 2, 360, 28))
        self.mode_segmented.setSegmentCount_(4)
        self.mode_segmented.setLabel_forSegment_("🚆 Mezzi", 0)
        self.mode_segmented.setLabel_forSegment_("🚗 Auto", 1)
        self.mode_segmented.setLabel_forSegment_("🚶 Piedi", 2)
        self.mode_segmented.setLabel_forSegment_("🚲 Bici", 3)
        self.mode_segmented.setSelectedSegment_(sel_idx)
        self.mode_segmented.setTarget_(self)
        self.mode_segmented.setAction_("onSelectTransportMode:")
        card.addSubview_(self.mode_segmented)

        y -= 44.0
        # 3. Margine di Anticipo Partenza
        buf_val = config.get("eta_buffer_minutes", 10)
        self._add_popup_row(card, "⏳ Margine di Anticipo Partenza:", "Tempo extra per raggiungere la fermata/stazione o trovare parcheggio", [
            ("5 minuti", 5), ("10 minuti (Predefinito)", 10), ("15 minuti", 15), ("20 minuti", 20), ("30 minuti", 30)
        ], buf_val, "onSelectETABuffer:", y, w)

    def _build_flight_section(self, card, w, h):
        self._add_section_header(card, "✈️ Display & Dinamica di Volo Banner", "Personalizza la posizione e la velocità di attraversamento del velivolo a schermo.", h - 28, w)

        y = h - 68.0
        # 1. Posizione Banner
        lbl1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 280, 20))
        lbl1.setStringValue_("📍 Posizione Banner a Schermo:")
        lbl1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl1.setTextColor_(AppKit.NSColor.whiteColor())
        lbl1.setBezeled_(False)
        lbl1.setDrawsBackground_(False)
        lbl1.setEditable_(False)
        card.addSubview_(lbl1)

        pos_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(300, y - 2, 250, 28))
        pos_segmented.setSegmentCount_(2)
        pos_segmented.setLabel_forSegment_("⬆️ In Alto (Top)", 0)
        pos_segmented.setLabel_forSegment_("⬇️ In Basso (Bottom)", 1)
        curr_pos = config.get("banner_position", "top")
        pos_segmented.setSelectedSegment_(0 if curr_pos == "top" else 1)
        pos_segmented.setTarget_(self)
        pos_segmented.setAction_("onSelectBannerPosition:")
        card.addSubview_(pos_segmented)

        y -= 44.0
        # 2. Velocità Volo
        curr_spd = int(float(config.get("flight_speed", 3.2)) * 10)
        self._add_popup_row(card, "🚀 Velocità Animazione Volo:", "Regola la rapidità di attraversamento orizzontale del banner", [
            ("🐢 Rilassato (2.0x)", 20), ("✈️ Standard (3.2x - Predefinito)", 32), ("🚀 Turbo (4.8x)", 48), ("⚡ Supersonico (6.0x)", 60)
        ], curr_spd, "onSelectFlightSpeed:", y, w)

    def _build_audio_section(self, card, w, h):
        self._add_section_header(card, "🔔 Effetti Sonori & Notifiche Audio", "Attiva o personalizza il chime audio riprodotto al decollo della notifica.", h - 28, w)

        y = h - 68.0
        # 1. Switch Suono Abilitato
        sound_on = config.get("sound_enabled", True)
        self.sound_switch = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, 260, 24))
        self.sound_switch.setButtonType_(AppKit.NSButtonTypeSwitch)
        self.sound_switch.setTitle_("🔊 Riproduci Suono alla Notifica")
        self.sound_switch.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        self.sound_switch.setState_(AppKit.NSControlStateValueOn if sound_on else AppKit.NSControlStateValueOff)
        self.sound_switch.setTarget_(self)
        self.sound_switch.setAction_("onToggleSoundEnabled:")
        card.addSubview_(self.sound_switch)

        y -= 44.0
        # 2. Selezione Suono + Preview
        lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 280, 20))
        lbl.setStringValue_("🎵 Timbro Chime macOS:")
        lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl.setTextColor_(AppKit.NSColor.whiteColor())
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        card.addSubview_(lbl)

        sounds = [
            ("Glass (Predefinito)", "Glass"), ("Hero", "Hero"), ("Ping", "Ping"), ("Pop", "Pop"),
            ("Submarine", "Submarine"), ("Tink", "Tink"), ("Bottle", "Bottle"), ("Funk", "Funk"),
            ("Basso", "Basso"), ("Morse", "Morse")
        ]
        curr_snd = config.get("sound_name", "Glass")
        
        self.sound_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(300, y - 2, 220, 28), False)
        self.sound_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        self.sound_popup.setTarget_(self)
        self.sound_popup.setAction_("onSelectSound:")
        for opt_title, opt_val in sounds:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(opt_title, None, "")
            item.setRepresentedObject_(opt_val)
            self.sound_popup.menu().addItem_(item)
            if opt_val == curr_snd:
                self.sound_popup.selectItem_(item)
        card.addSubview_(self.sound_popup)

        play_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(530, y - 2, 130, 28))
        play_btn.setTitle_("▶ Ascolta")
        play_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        play_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12))
        play_btn.setTarget_(self)
        play_btn.setAction_("onPlaySoundPreview:")
        card.addSubview_(play_btn)

    def _build_calendars_section(self, card, w, h):
        self._add_section_header(card, "📅 Calendari macOS Inclusi", "Seleziona quali calendari monitorare attivamente per i promemoria.", h - 28, w)
        
        cals = get_available_calendars()
        if not cals:
            lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 68, w - 36, 22))
            lbl.setStringValue_("Tutti i calendari di Apple Calendar sono inclusi.")
            lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12))
            lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.7, 0.75, 0.88, 1.0))
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            card.addSubview_(lbl)
            return

        y = h - 68.0
        x_offset = 18.0
        for cal in cals:
            chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_offset, y, 220, 24))
            chk.setButtonType_(AppKit.NSButtonTypeSwitch)
            chk.setTitle_(f"📅 {cal['name']}")
            chk.setFont_(AppKit.NSFont.systemFontOfSize_(12))
            chk.setState_(AppKit.NSControlStateValueOn if cal['enabled'] else AppKit.NSControlStateValueOff)
            chk.setTarget_(self)
            chk.setAction_("onToggleCalendarSource:")
            chk.setToolTip_(cal['name'])
            card.addSubview_(chk)
            
            x_offset += 240.0
            if x_offset + 220.0 > w:
                x_offset = 18.0
                y -= 30.0

    def _build_system_section(self, card, w, h):
        self._add_section_header(card, "🚀 Sistema & Integrazione macOS", "Gestisci l'avvio in background e la personalizzazione avanzata dei file di configurazione.", h - 28, w)

        y = h - 68.0
        # 1. Switch Autostart
        autostart_chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, 420, 24))
        autostart_chk.setButtonType_(AppKit.NSButtonTypeSwitch)
        autostart_chk.setTitle_("🚀 Avvia QuakMeeting automaticamente al login del Mac")
        autostart_chk.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        autostart_chk.setState_(AppKit.NSControlStateValueOn if is_autostart_enabled() else AppKit.NSControlStateValueOff)
        autostart_chk.setTarget_(self)
        autostart_chk.setAction_("onToggleAutostart:")
        card.addSubview_(autostart_chk)

        y -= 44.0
        # 2. Pulsanti Config JSON
        open_json_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, y - 2, 300, 32))
        open_json_btn.setTitle_("📝 Modifica Regole (config.json)...")
        open_json_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        open_json_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        open_json_btn.setTarget_(self)
        open_json_btn.setAction_("onOpenConfigEditor:")
        card.addSubview_(open_json_btn)

        reload_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(330, y - 2, 200, 32))
        reload_btn.setTitle_("🔄 Ricarica Regole")
        reload_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        reload_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        reload_btn.setTarget_(self)
        reload_btn.setAction_("onReloadConfig:")
        card.addSubview_(reload_btn)

    def _add_popup_row(self, parent, label_text, sub_text, options, current_val, action_name, y, w):
        lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y + 2, 280, 20))
        lbl.setStringValue_(label_text)
        lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        lbl.setTextColor_(AppKit.NSColor.whiteColor())
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        parent.addSubview_(lbl)

        popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(300, y - 2, 360, 28), False)
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
    def onToggleMeetingStage_(self, sender):
        val = sender.tag()
        curr = set(config.get("meeting_reminder_stages", [20, 10, 5, 2]))
        if sender.state() == AppKit.NSControlStateValueOn:
            curr.add(val)
        else:
            curr.discard(val)
        config.set("meeting_reminder_stages", sorted(list(curr), reverse=True))

    def onToggleTravelStage_(self, sender):
        val = sender.tag()
        curr = set(config.get("travel_reminder_stages", [45, 30, 15, 5]))
        if sender.state() == AppKit.NSControlStateValueOn:
            curr.add(val)
        else:
            curr.discard(val)
        config.set("travel_reminder_stages", sorted(list(curr), reverse=True))

    def onSaveHomeAddress_(self, sender):
        if hasattr(self, 'home_addr_field') and self.home_addr_field:
            addr = str(self.home_addr_field.stringValue() or "").strip()
            config.set("home_address", addr)
            self.refresh_data(force=True)

    def onSelectTransportMode_(self, sender):
        modes = ["transit", "automobile", "walking", "bicycling"]
        idx = sender.selectedSegment()
        if 0 <= idx < len(modes):
            config.set("transport_mode", modes[idx])
            self.refresh_data(force=True)

    def onSelectETABuffer_(self, sender):
        val_buf = sender.selectedItem().representedObject()
        config.set("eta_buffer_minutes", int(val_buf))
        self.refresh_data(force=True)

    def onToggleCalendarSource_(self, sender):
        cal_name = sender.toolTip() or sender.title().replace("📅 ", "")
        ignored = set(config.get("ignored_calendars", []))
        if sender.state() == AppKit.NSControlStateValueOn:
            ignored.discard(cal_name)
        else:
            ignored.add(cal_name)
        config.set("ignored_calendars", list(ignored))
        self.refresh_data(force=True)

    def onSelectSnoozeDuration_(self, sender):
        val_min = sender.selectedItem().representedObject()
        config.set("default_snooze_seconds", int(val_min) * 60)

    def onSelectBannerPosition_(self, sender):
        pos = "top" if sender.selectedSegment() == 0 else "bottom"
        config.set("banner_position", pos)

    def onSelectFlightSpeed_(self, sender):
        spd_tag = sender.selectedItem().representedObject()
        config.set("flight_speed", float(spd_tag) / 10.0)

    def onToggleSoundEnabled_(self, sender):
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        config.set("sound_enabled", is_on)

    def onSelectSound_(self, sender):
        snd_name = sender.selectedItem().representedObject()
        config.set("sound_name", str(snd_name))
        config.set("sound_enabled", True)
        if hasattr(self, 'sound_switch') and self.sound_switch:
            self.sound_switch.setState_(AppKit.NSControlStateValueOn)
        self.onPlaySoundPreview_(None)

    def onPlaySoundPreview_(self, sender):
        snd_name = config.get("sound_name", "Glass")
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

    def onReloadConfig_(self, sender):
        config.reload()
        self.refresh_data(force=True)

def show_dashboard(tab_index=None):
    controller = DashboardWindowController.sharedController()
    controller.show(tab_index)

if __name__ == "__main__":
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
    show_dashboard()
    app.run()
