import AppKit
import objc
import webbrowser
import os
import time
import threading
import warnings
from datetime import datetime

if hasattr(objc, 'ObjCPointerWarning'):
    warnings.filterwarnings("ignore", category=objc.ObjCPointerWarning)

try:
    from core.config_manager import config
    from core.calendar_scanner import get_upcoming_meetings, sync_calendar_now, get_available_calendars
    from core.services.eta_service import eta_service, MODE_ICONS, MODE_LABELS
    from core.services.event_bus import event_bus
    from core.domain.models import format_duration
    from core.logger import open_log_file, open_log_folder
    from ui.banner_window import _run_banner
except ImportError:
    from config_manager import config
    from calendar_scanner import get_upcoming_meetings, sync_calendar_now, get_available_calendars
    from eta_service import eta_service, MODE_ICONS, MODE_LABELS
    from event_bus import event_bus
    from models import format_duration
    from logger import open_log_file, open_log_folder
    from banner_window import _run_banner

class DashboardWindowDelegate(AppKit.NSObject):
    def init(self):
        self = objc.super(DashboardWindowDelegate, self).init()
        self.controller = None
        return self

    def windowShouldClose_(self, sender):
        if self.controller:
            self.controller.window.orderOut_(None)
        else:
            sender.orderOut_(None)
        return False

class DashboardWindowController(AppKit.NSObject):
    _shared_instance = None

    @classmethod
    def sharedController(cls):
        if cls._shared_instance is None:
            cls._shared_instance = DashboardWindowController.alloc().init()
        return cls._shared_instance

    def init(self):
        self = objc.super(DashboardWindowController, self).init()
        if self is None:
            return None

        self.window = None
        self.current_tab = 0 # 0: Agenda, 1: Hangar, 2: Preferences & Settings
        self.meetings = []
        self.cached_calendars = []
        self.is_loading = False
        self._last_rendered_signature = None
        
        threading.Thread(target=self._prewarm_calendars, daemon=True).start()
        self._create_window()
        return self

    def _prewarm_calendars(self):
        try:
            self.cached_calendars = get_available_calendars()
        except Exception:
            pass

    def show(self, tab_index=None):
        if not self.window:
            self._create_window()
            
        if tab_index is not None and 0 <= tab_index <= 2:
            self.current_tab = tab_index
            if hasattr(self, 'tab_segmented') and self.tab_segmented:
                self.tab_segmented.setSelectedSegment_(tab_index)
                
        app = AppKit.NSApp()
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

        # Single Window Backdrop Frosted Glass Effect
        visual_view = AppKit.NSVisualEffectView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, width, height))
        visual_view.setMaterial_(AppKit.NSVisualEffectMaterialUnderWindowBackground)
        visual_view.setBlendingMode_(AppKit.NSVisualEffectBlendingModeBehindWindow)
        visual_view.setState_(AppKit.NSVisualEffectStateActive)
        visual_view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        self.window.setContentView_(visual_view)

        # 1. Header (Logo, Title, Scanner Indicator, Refresh)
        self._build_header(visual_view, width, height)

        # 2. Segmented Tab Selector
        self._build_tab_selector(visual_view, width, height)

        # 3. Content Container
        self.content_container = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(20, 20, width - 40, height - 150))
        self.content_container.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        visual_view.addSubview_(self.content_container)

    def _build_header(self, parent, w, h):
        header_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 85, w - 40, 75))
        
        # App Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon_img = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
            icon_view = AppKit.NSImageView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 12, 52, 52))
            icon_view.setImage_(icon_img)
            header_view.addSubview_(icon_view)
        
        # App Title
        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 34, 350, 30))
        title_lbl.setStringValue_("🦆 QuakMeeting — Flight Deck")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(19))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        title_lbl.setSelectable_(False)
        header_view.addSubview_(title_lbl)

        # Status Subtitle
        self.status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(64, 12, 450, 22))
        self.status_lbl.setStringValue_("🟢 Scanner Active  •  Loading events...")
        self.status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        self.status_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.70, 0.85, 1.0))
        self.status_lbl.setBezeled_(False)
        self.status_lbl.setDrawsBackground_(False)
        self.status_lbl.setEditable_(False)
        self.status_lbl.setSelectable_(False)
        header_view.addSubview_(self.status_lbl)

        # Sync Button
        refresh_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 170, 20, 130, 34))
        refresh_btn.setTitle_("🔄 Sync Now")
        refresh_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        refresh_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        refresh_btn.setTarget_(self)
        refresh_btn.setAction_("onRefreshClicked:")
        header_view.addSubview_(refresh_btn)

        parent.addSubview_(header_view)

    def _build_tab_selector(self, parent, w, h):
        self.tab_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 130, w - 40, 32))
        self.tab_segmented.setSegmentCount_(3)
        self.tab_segmented.setLabel_forSegment_("📅 Today's Agenda", 0)
        self.tab_segmented.setLabel_forSegment_("🦆 Pilot Hangar", 1)
        self.tab_segmented.setLabel_forSegment_("⚙️ Preferences & Timing", 2)
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
        """Loads events from cache immediately and syncs in background."""
        self.meetings = get_upcoming_meetings(force_refresh=False)
        now = datetime.now()
        
        today_meetings = [m for m in self.meetings if m.get("start_time") and m["start_time"].date() == now.date()]
        today_upcoming = [m for m in today_meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]
        
        if today_upcoming:
            next_m = today_upcoming[0]
            s_str = next_m["start_time"].strftime("%H:%M") if next_m.get("start_time") else "--:--"
            travel_info = ""
            if next_m.get("travel_time_minutes"):
                dur_str = format_duration(next_m["travel_time_minutes"])
                t_mode = next_m.get("transport_mode", config.get("transport_mode", "transit"))
                icon = MODE_ICONS.get(t_mode, "🚗")
                dep_dt = next_m.get("departure_time")
                if isinstance(dep_dt, datetime):
                    travel_info = f"  •  ⏱️ {icon} ~{dur_str} (Leave at {dep_dt.strftime('%H:%M')})"
                else:
                    travel_info = f"  •  ⏱️ {icon} ~{dur_str} travel"
            self.status_lbl.setStringValue_(f"🟢 Scanner Active  •  {len(today_meetings)} events today  •  Next: {s_str}{travel_info}")
        else:
            self.status_lbl.setStringValue_("🟢 Scanner Active  •  No upcoming events for today")
            
        self._render_current_tab()

        if force or not self.meetings:
            self.is_loading = True
            if not self.meetings:
                self._render_current_tab()
                
            def worker():
                try:
                    meetings = sync_calendar_now()
                except Exception as e:
                    print(f"Sync error: {e}")
                    meetings = self.meetings

                def on_complete():
                    self.is_loading = False
                    self.meetings = meetings
                    n = datetime.now()
                    t_meets = [m for m in self.meetings if m.get("start_time") and m["start_time"].date() == n.date()]
                    t_up = [m for m in t_meets if (m.get("end_time") and m["end_time"] > n) or (m.get("start_time") and m["start_time"] > n)]
                    
                    if t_up:
                        nx = t_up[0]
                        st = nx["start_time"].strftime("%H:%M") if nx.get("start_time") else "--:--"
                        tr_info = ""
                        if nx.get("travel_time_minutes"):
                            dur_s = format_duration(nx["travel_time_minutes"])
                            tm = nx.get("transport_mode", config.get("transport_mode", "transit"))
                            ic = MODE_ICONS.get(tm, "🚗")
                            dp = nx.get("departure_time")
                            if isinstance(dp, datetime):
                                tr_info = f"  •  ⏱️ {ic} ~{dur_s} (Leave at {dp.strftime('%H:%M')})"
                            else:
                                tr_info = f"  •  ⏱️ {ic} ~{dur_s} travel"
                        self.status_lbl.setStringValue_(f"🟢 Scanner Active  •  {len(t_meets)} events today  •  Next: {st}{tr_info}")
                    else:
                        self.status_lbl.setStringValue_("🟢 Scanner Active  •  No upcoming events for today")
                    self._render_current_tab()

                AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(on_complete)

            threading.Thread(target=worker, daemon=True).start()

    def _render_current_tab(self):
        if not self.content_container:
            return
            
        # Diff render state to prevent redundant subview rebuilds
        m_sig = tuple((m.get("title"), str(m.get("start_time")), m.get("travel_time_minutes")) for m in self.meetings)
        current_sig = (self.current_tab, self.is_loading, len(self.meetings), m_sig)
        if self._last_rendered_signature == current_sig:
            return
        self._last_rendered_signature = current_sig

        for sub in list(self.content_container.subviews()):
            sub.removeFromSuperview()

        cw = self.content_container.frame().size.width
        ch = self.content_container.frame().size.height

        if self.current_tab == 0:
            self._render_agenda_tab(cw, ch)
        elif self.current_tab == 1:
            self._render_hangar_tab(cw, ch)
        elif self.current_tab == 2:
            self._render_settings_tab(cw, ch)

    # -------------------------------------------------------------
    # TAB 1: TODAY'S AGENDA & UPCOMING EVENTS
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
            load_lbl.setStringValue_("🦆 Syncing your macOS Calendars...\nDetecting schedules, Apple Maps routes, and meeting links...")
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
        
        now = datetime.now()
        today_list = [m for m in self.meetings if m.get("start_time") and m["start_time"].date() == now.date()]
        
        total_items = max(1, len(today_list))
        content_h = max(h, total_items * (card_h + gap) + 20.0)
        
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))
        
        if not today_list:
            empty_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, content_h - 100, w - 40, 50))
            empty_lbl.setStringValue_("🧘‍♂️ No events scheduled for today in enabled calendars.\nRelax or add an event in Apple Calendar!")
            empty_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(14))
            empty_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.6, 0.65, 0.8, 1.0))
            empty_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
            empty_lbl.setBezeled_(False)
            empty_lbl.setDrawsBackground_(False)
            empty_lbl.setEditable_(False)
            doc_view.addSubview_(empty_lbl)
        else:
            for idx, m in enumerate(today_list):
                y_item = content_h - (idx + 1) * (card_h + gap)
                card = self._create_meeting_card(m, idx, 0, y_item, w - 16, card_h)
                doc_view.addSubview_(card)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        self.content_container.addSubview_(scroll_view)

    def _create_meeting_card(self, m, idx, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.14, 0.16, 0.22, 0.85).CGColor())
        card.layer().setCornerRadius_(12.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.10).CGColor())

        # Pilot Icon
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

        # Event Title & Time
        s_time = m["start_time"].strftime("%H:%M") if m.get("start_time") else "--:--"
        e_time = m["end_time"].strftime("%H:%M") if m.get("end_time") else ""
        time_str = f"{s_time} - {e_time}" if e_time else s_time
        m_title = (m.get("title") or "Untitled Event").strip()

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 38, w - 275, 24))
        title_lbl.setStringValue_(f"{time_str}  •  {m_title}")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        # Subtitle Details / Location / ETA
        sub_str = m.get("provider", "Event")
        loc = m.get("location")
        if loc and loc != "missing value":
            sub_str += f"  •  📍 {loc[:35]}"
        elif m.get("action_url") and "meet.google.com" in m["action_url"]:
            sub_str += "  •  🌐 Google Meet"

        # Dedicated Travel Time Display with clean hour/minute formatting
        if m.get("travel_time_minutes"):
            dur_str = format_duration(m["travel_time_minutes"])
            t_mode = m.get("transport_mode", config.get("transport_mode", "transit"))
            icon = MODE_ICONS.get(t_mode, "🚗")
            dep_dt = m.get("departure_time")
            if isinstance(dep_dt, datetime):
                sub_str += f"  •  ⏱️ {icon} ~{dur_str} (Leave at {dep_dt.strftime('%H:%M')})"
            else:
                sub_str += f"  •  ⏱️ {icon} ~{dur_str} travel"

        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 16, w - 275, 20))
        sub_lbl.setStringValue_(sub_str)
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        sub_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.72, 0.85, 1.0))
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        card.addSubview_(sub_lbl)

        # Action Buttons (Join + Copy Link)
        action_url = m.get("action_url") or m.get("meeting_url")
        if not action_url and loc and loc != "missing value":
            import urllib.parse
            action_url = f"https://maps.apple.com/?q={urllib.parse.quote(loc)}"
            m["action_url"] = action_url

        if action_url:
            btn_title = m.get("action_btn_text", "🚀 JOIN")
            travel_min = m.get("travel_time_minutes")
            if "MAPS" in btn_title or "MAPPE" in btn_title or "maps.apple.com" in action_url:
                btn_short = f"🗺️ Maps (~{format_duration(travel_min)})" if travel_min else "🗺️ Maps"
            elif "ZOOM" in btn_title or "zoom.us" in action_url:
                btn_short = "🔷 Zoom"
            elif "TEAMS" in btn_title or "teams.microsoft" in action_url:
                btn_short = "🟣 Teams"
            elif "serenis" in action_url:
                btn_short = "🛋️ Serenis"
            else:
                btn_short = "🚀 Join"

            action_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 142, 20, 126, 34))
            action_btn.setTitle_(btn_short)
            action_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
            action_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12))
            action_btn.setTarget_(self)
            action_btn.setAction_("onOpenMeetingUrl:")
            action_btn.setTag_(idx)
            card.addSubview_(action_btn)

            copy_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 238, 20, 90, 34))
            copy_btn.setTitle_("📋 Copy")
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
                sender.setTitle_("✓ Copied!")
                def reset():
                    time.sleep(1.5)
                    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(lambda: sender.setTitle_("📋 Copy"))
                threading.Thread(target=reset, daemon=True).start()

    # -------------------------------------------------------------
    # TAB 2: PILOT HANGAR & FLIGHT TESTS
    # -------------------------------------------------------------
    def _render_hangar_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        
        pilots = [
            ("duck", "🦆 Aviator Duck", "Video conferences: Google Meet, Zoom, MS Teams & online meetings.", "Google Green", self.testAviatorDuck_),
            ("chef", "👨‍🍳 Chef Duck & Food", "Dinners, Lunches, Restaurants, Pizzerias & Apple Maps food routes.", "Coral Food", self.testChefDuck_),
            ("captain", "🧑‍✈️ Jet Airliner Captain", "Airline Flights, Airports, High-speed trains, Buses & Travel Routes.", "Sky Blue", self.testCaptainJet_),
            ("owl", "🦉 Academic Owl", "University Lectures, Exams, Campus courses & Study sessions.", "Amethyst Academic", self.testAcademicOwl_),
            ("driver", "🏎️ Speed Racer Driver", "In-person meetings, Gym workouts, Doctor visits & Real-Time Navigation.", "Emerald Speed", self.testSpeedRacer_),
            ("zen_duck", "🦆🌸 Zen Duck", "Serenis sessions, Psychological Therapy, Yoga, Wellness & Meditation.", "Teal Zen", self.testZenDuck_)
        ]

        card_h = 108.0
        gap = 14.0
        content_h = len(pilots) * (card_h + gap) + 20.0
        
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))
        
        for idx, (p_id, p_name, p_desc, p_theme, p_action) in enumerate(pilots):
            y_item = content_h - (idx + 1) * (card_h + gap)
            card = self._create_pilot_card(p_id, p_name, p_desc, p_theme, p_action, 0, y_item, w - 16, card_h)
            doc_view.addSubview_(card)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        self.content_container.addSubview_(scroll_view)

    def _create_pilot_card(self, p_id, p_name, p_desc, p_theme, p_action, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.14, 0.16, 0.22, 0.85).CGColor())
        card.layer().setCornerRadius_(14.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.10).CGColor())

        # Pilot Title
        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 38, w - 210, 26))
        title_lbl.setStringValue_(p_name)
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(15))
        title_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        # Description
        desc_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 70, w - 210, 32))
        desc_lbl.setStringValue_(p_desc)
        desc_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        desc_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.72, 0.76, 0.88, 1.0))
        desc_lbl.setBezeled_(False)
        desc_lbl.setDrawsBackground_(False)
        desc_lbl.setEditable_(False)
        card.addSubview_(desc_lbl)

        # Theme Tag
        tag_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, 12, 180, 20))
        tag_lbl.setStringValue_(f"🎨 Theme: {p_theme}")
        tag_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11))
        tag_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.55, 0.60, 0.75, 1.0))
        tag_lbl.setBezeled_(False)
        tag_lbl.setDrawsBackground_(False)
        tag_lbl.setEditable_(False)
        card.addSubview_(tag_lbl)

        # Flight Test Button
        test_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 180, (h - 38) * 0.5, 160, 38))
        test_btn.setTitle_("🚀 Test Flight")
        test_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        test_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13))
        test_btn.setTarget_(self)
        test_btn.setAction_(p_action.__name__.rstrip('_') + ":")
        card.addSubview_(test_btn)

        return card

    # Pilot Test Presets
    @objc.IBAction
    def testAviatorDuck_(self, sender):
        _run_banner({
            "title": "Weekly Sprint Planning (Google Meet)",
            "provider": "Google Meet 🟢",
            "pilot_type": "duck",
            "action_btn_text": "🚀 JOIN GOOGLE MEET",
            "action_url": "https://meet.google.com/test-quak",
            "start_time": datetime.now(),
            "is_travel": False
        })

    @objc.IBAction
    def testChefDuck_(self, sender):
        _run_banner({
            "title": "Dinner with Friends at Pizzeria",
            "provider": "Dinner / Food 🍕🍽️",
            "pilot_type": "chef",
            "action_btn_text": "🗺️ RESTAURANT DIRECTIONS (MAPS)",
            "action_url": "https://maps.apple.com/?q=Pizzeria+Napoli",
            "location": "Pizzeria Da Michele, London",
            "start_time": datetime.now(),
            "is_travel": True
        })

    @objc.IBAction
    def testCaptainJet_(self, sender):
        _run_banner({
            "title": "Flight to London (BA 257)",
            "provider": "Flight / Travel ✈️",
            "pilot_type": "captain",
            "action_btn_text": "🗺️ AIRPORT DIRECTIONS (MAPS)",
            "action_url": "https://maps.apple.com/?q=Heathrow+Airport",
            "location": "Terminal 5 - Gate B12",
            "start_time": datetime.now(),
            "is_travel": True
        })

    @objc.IBAction
    def testAcademicOwl_(self, sender):
        _run_banner({
            "title": "ICT for smart mobility (VASSIO LUCA) - Aula 5M",
            "provider": "Study / Class 🎓 Aula 5M",
            "pilot_type": "owl",
            "classroom": "Aula 5M",
            "teacher": "VASSIO LUCA",
            "action_btn_text": "📚 CLASSROOM & NOTES",
            "action_url": "https://calendar.apple.com",
            "location": "Politecnico - Aula 5M",
            "start_time": datetime.now(),
            "is_travel": False
        })

    @objc.IBAction
    def testSpeedRacer_(self, sender):
        _run_banner({
            "title": "CrossFit Training & Workout",
            "provider": "In Person 📍 Travel Time!",
            "pilot_type": "driver",
            "action_btn_text": "🗺️ NAVIGATE WITH MAPS",
            "action_url": "https://maps.apple.com/?daddr=CrossFit+Gym",
            "location": "Downtown Gym",
            "start_time": datetime.now(),
            "is_travel": True
        })

    @objc.IBAction
    def testZenDuck_(self, sender):
        _run_banner({
            "title": "Serenis Online Therapy Session",
            "provider": "Serenis 🛋️",
            "pilot_type": "zen_duck",
            "action_btn_text": "🚀 JOIN SESSION",
            "action_url": "https://app.serenis.it/join/test",
            "start_time": datetime.now(),
            "is_travel": False
        })

    @objc.IBAction
    def onMarkArrived_(self, sender):
        idx = sender.tag()
        if 0 <= idx < len(self.meetings):
            m = self.meetings[idx]
            from core.services.reminder_engine import reminder_engine
            from core.domain.models import Meeting
            if isinstance(m, Meeting):
                m_id = m.id
            else:
                m_title = m.get("title", "")
                m_start = m.get("start_time")
                time_str = m_start.strftime("%Y%m%d%H%M") if hasattr(m_start, "strftime") else "000000000000"
                m_id = f"{m_title}_{time_str}"
            reminder_engine.mark_arrived(m_id)
            sender.setTitle_("✓ Arrived")
            sender.setEnabled_(False)

    # -------------------------------------------------------------
    # TAB 3: PREFERENCES & TIMING SETTINGS
    # -------------------------------------------------------------
    def _render_settings_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_w = w - 16.0
        gap = 14.0
        
        c1_h = 216.0 # Notification Lead Times
        c_eta_h = 216.0 # Home / Departure Address & Apple Maps ETA
        c2_h = 216.0 # Screen Banner & Menu Bar Live Display Dynamics
        c3_h = 164.0 # Sound Chimes
        
        # Calculate calendar section height dynamically
        cals = self.cached_calendars if self.cached_calendars else get_available_calendars()
        if not self.cached_calendars and cals:
            self.cached_calendars = cals
        cal_count = len(cals) if cals else 1
        cal_rows = (cal_count + 1) // 2
        c4_h = max(118.0, 76.0 + cal_rows * 36.0) # Dynamic Calendars height
        
        c5_h = 142.0 # System & JSON Config
        
        content_h = c1_h + c_eta_h + c2_h + c3_h + c4_h + c5_h + gap * 7 + 24.0
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        curr_y = content_h - gap

        # SECTION 1: TIMING & MULTI-STAGE NOTIFICATIONS
        curr_y -= c1_h
        card1 = self._create_card_container(0, curr_y, card_w, c1_h)
        self._build_timing_section(card1, card_w, c1_h)
        doc_view.addSubview_(card1)

        # SECTION 2: DEPARTURE ADDRESS & APPLE MAPS ETA
        curr_y -= (c_eta_h + gap)
        card_eta = self._create_card_container(0, curr_y, card_w, c_eta_h)
        self._build_eta_section(card_eta, card_w, c_eta_h)
        doc_view.addSubview_(card_eta)

        # SECTION 3: SCREEN BANNER & FLIGHT DYNAMICS
        curr_y -= (c2_h + gap)
        card2 = self._create_card_container(0, curr_y, card_w, c2_h)
        self._build_flight_section(card2, card_w, c2_h)
        doc_view.addSubview_(card2)

        # SECTION 4: AUDIO & SYSTEM CHIMES
        curr_y -= (c3_h + gap)
        card3 = self._create_card_container(0, curr_y, card_w, c3_h)
        self._build_audio_section(card3, card_w, c3_h)
        doc_view.addSubview_(card3)

        # SECTION 5: INCLUDED MACOS CALENDARS
        curr_y -= (c4_h + gap)
        card4 = self._create_card_container(0, curr_y, card_w, c4_h)
        self._build_calendars_section(card4, card_w, c4_h, cals)
        doc_view.addSubview_(card4)

        # SECTION 6: SYSTEM & JSON RULES
        curr_y -= (c5_h + gap)
        card5 = self._create_card_container(0, curr_y, card_w, c5_h)
        self._build_system_section(card5, card_w, c5_h)
        doc_view.addSubview_(card5)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        self.content_container.addSubview_(scroll_view)

    def _create_card_container(self, x, y, w, h):
        """Creates a modern lightweight card container with deep frosted slate styling."""
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.13, 0.15, 0.21, 0.90).CGColor())
        card.layer().setCornerRadius_(13.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.08).CGColor())
        return card

    def _add_section_header(self, parent, title, subtitle, y, w, icon_emoji="⚙️", badge_rgba=(0.2, 0.5, 1.0, 0.18), border_rgba=(0.2, 0.5, 1.0, 0.35)):
        """Section header with colored icon badge, bold title, subtitle, and bottom hairline."""
        # Icon Badge (28x28 with 7px radius)
        badge = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, y - 36, 28, 28))
        badge.setWantsLayer_(True)
        badge.layer().setBackgroundColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(*badge_rgba).CGColor())
        badge.layer().setCornerRadius_(7.0)
        badge.layer().setMasksToBounds_(True)
        badge.layer().setBorderWidth_(1.0)
        badge.layer().setBorderColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(*border_rgba).CGColor())

        icon_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(0, 2, 28, 24))
        icon_lbl.setStringValue_(icon_emoji)
        icon_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(14.5))
        icon_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
        icon_lbl.setBezeled_(False)
        icon_lbl.setDrawsBackground_(False)
        icon_lbl.setEditable_(False)
        badge.addSubview_(icon_lbl)
        parent.addSubview_(badge)

        # Title
        t_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(56, y - 28, w - 74, 20))
        t_lbl.setStringValue_(title)
        t_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13.5))
        t_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        # Subtitle
        s_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(56, y - 46, w - 74, 16))
        s_lbl.setStringValue_(subtitle)
        s_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        s_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.73, 0.88, 1.0))
        s_lbl.setBezeled_(False)
        s_lbl.setDrawsBackground_(False)
        s_lbl.setEditable_(False)
        parent.addSubview_(s_lbl)

        # Header bottom hairline divider (strictly separated with zero overlap)
        div = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, y - 54, w - 36, 1))
        div.setWantsLayer_(True)
        div.layer().setBackgroundColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.06).CGColor())
        parent.addSubview_(div)

    def _add_row_divider(self, parent, y, w):
        """Adds a subtle inner hairline divider between preference rows."""
        div = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, w - 36, 1))
        div.setWantsLayer_(True)
        div.layer().setBackgroundColor_(AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.04).CGColor())
        parent.addSubview_(div)

    def _add_row_label(self, parent, title, desc, y_center, w_label=220):
        """Creates a left-side setting label with bold title and description."""
        t_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y_center + 2, w_label, 18))
        t_lbl.setStringValue_(title)
        t_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        t_lbl.setTextColor_(AppKit.NSColor.whiteColor())
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        if desc:
            d_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y_center - 14, w_label, 15))
            d_lbl.setStringValue_(desc)
            d_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
            d_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.62, 0.68, 0.82, 1.0))
            d_lbl.setBezeled_(False)
            d_lbl.setDrawsBackground_(False)
            d_lbl.setEditable_(False)
            parent.addSubview_(d_lbl)

    def _build_timing_section(self, card, w, h):
        self._add_section_header(
            card,
            "Notification Lead Times & Staged Reminders",
            "Select reminder alert windows to receive progressive notifications ahead of time.",
            h, w,
            icon_emoji="⏱️",
            badge_rgba=(1.0, 0.6, 0.1, 0.20),
            border_rgba=(1.0, 0.6, 0.1, 0.38)
        )
        
        # 1. Video Meeting Stages
        r1_y = h - 84.0
        self._add_row_label(card, "📹 Video Meetings", "Alert ahead of meeting start time", r1_y, 220)
        
        curr_meeting_stages = set(config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        meeting_opts = [(30, "30m"), (20, "20m"), (15, "15m"), (10, "10m"), (5, "5m"), (2, "2m"), (0, "0m Start")]
        
        x_btn = 245.0
        for val, label in meeting_opts:
            btn_w = 60.0 if val != 0 else 92.0
            chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_btn, r1_y - 10, btn_w, 24))
            chk.setButtonType_(AppKit.NSButtonTypeSwitch)
            chk.setTitle_(label)
            chk.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            chk.setState_(AppKit.NSControlStateValueOn if val in curr_meeting_stages else AppKit.NSControlStateValueOff)
            chk.setTag_(val)
            chk.setTarget_(self)
            chk.setAction_("onToggleMeetingStage:")
            card.addSubview_(chk)
            x_btn += (btn_w + 6.0)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Travel Stages (Before Departure Time)
        r2_y = h - 136.0
        self._add_row_label(card, "🚗 Travel & Trips", "Alert ahead of leave / departure time", r2_y, 220)
        
        curr_travel_stages = set(config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        travel_opts = [(60, "60m"), (45, "45m"), (30, "30m"), (15, "15m"), (5, "5m"), (2, "2m"), (0, "0m Leave")]
        
        x_btn = 245.0
        for val, label in travel_opts:
            btn_w = 60.0 if val != 0 else 92.0
            chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_btn, r2_y - 10, btn_w, 24))
            chk.setButtonType_(AppKit.NSButtonTypeSwitch)
            chk.setTitle_(label)
            chk.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            chk.setState_(AppKit.NSControlStateValueOn if val in curr_travel_stages else AppKit.NSControlStateValueOff)
            chk.setTag_(val)
            chk.setTarget_(self)
            chk.setAction_("onToggleTravelStage:")
            card.addSubview_(chk)
            x_btn += (btn_w + 6.0)

        self._add_row_divider(card, h - 160.0, w)

        # 3. Snooze
        r3_y = h - 188.0
        snooze_val = config.get("default_snooze_seconds", 120) // 60
        self._add_row_label(card, "💤 Snooze Duration", "Interval delay when clicking Snooze on a banner", r3_y, 220)

        snooze_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(245, r3_y - 12, 260, 28), False)
        snooze_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        snooze_popup.setTarget_(self)
        snooze_popup.setAction_("onSelectSnoozeDuration:")
        for opt_title, opt_val in [
            ("1 minute", 1), ("2 minutes (Default)", 2), ("5 minutes", 5), ("10 minutes", 10), ("15 minutes", 15)
        ]:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(opt_title, None, "")
            item.setRepresentedObject_(opt_val)
            snooze_popup.menu().addItem_(item)
            if opt_val == snooze_val:
                snooze_popup.selectItem_(item)
        card.addSubview_(snooze_popup)

    def _build_eta_section(self, card, w, h):
        self._add_section_header(
            card,
            "Home / Departure Address & Route Estimation (Apple Maps ETA)",
            "Calculate real-time travel duration for Public Transit, Driving, Walking, or Cycling.",
            h, w,
            icon_emoji="📍",
            badge_rgba=(0.0, 0.48, 1.0, 0.20),
            border_rgba=(0.0, 0.48, 1.0, 0.38)
        )

        # 1. Home / Departure Address
        r1_y = h - 84.0
        self._add_row_label(card, "🏠 Starting Address", "Home / origin for automated Apple Maps ETA", r1_y, 220)

        curr_addr = str(config.get("home_address", "") or "")
        self.home_addr_field = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(245, r1_y - 10, 390, 26))
        self.home_addr_field.setStringValue_(curr_addr)
        self.home_addr_field.setPlaceholderString_("e.g. 24 Oxford Street, London or Piazza Castello, Torino")
        self.home_addr_field.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.home_addr_field.setTarget_(self)
        self.home_addr_field.setAction_("onSaveHomeAddress:")
        card.addSubview_(self.home_addr_field)

        self.home_save_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(645, r1_y - 12, 85, 30))
        self.home_save_btn.setTitle_("💾 Save")
        self.home_save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        self.home_save_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        self.home_save_btn.setTarget_(self)
        self.home_save_btn.setAction_("onSaveHomeAddress:")
        card.addSubview_(self.home_save_btn)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Preferred Transport Mode
        r2_y = h - 136.0
        self._add_row_label(card, "🚦 Transport Mode", "Default vehicle mode for route calculation", r2_y, 220)

        modes = ["transit", "automobile", "walking", "bicycling"]
        curr_mode = config.get("transport_mode", "transit")
        sel_idx = modes.index(curr_mode) if curr_mode in modes else 0

        self.mode_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(245, r2_y - 12, 485, 28))
        self.mode_segmented.setSegmentCount_(4)
        self.mode_segmented.setLabel_forSegment_("🚆 Transit", 0)
        self.mode_segmented.setLabel_forSegment_("🚗 Driving", 1)
        self.mode_segmented.setLabel_forSegment_("🚶 Walking", 2)
        self.mode_segmented.setLabel_forSegment_("🚲 Cycling", 3)
        self.mode_segmented.setSelectedSegment_(sel_idx)
        self.mode_segmented.setTarget_(self)
        self.mode_segmented.setAction_("onSelectTransportMode:")
        card.addSubview_(self.mode_segmented)

        self._add_row_divider(card, h - 160.0, w)

        # 3. Departure Buffer
        r3_y = h - 188.0
        buf_val = config.get("eta_buffer_minutes", 10)
        self._add_row_label(card, "⏳ Departure Buffer", "Extra margin to reach station or find parking", r3_y, 220)

        buf_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(245, r3_y - 12, 260, 28), False)
        buf_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        buf_popup.setTarget_(self)
        buf_popup.setAction_("onSelectETABuffer:")
        for opt_title, opt_val in [
            ("5 minutes", 5), ("10 minutes (Default)", 10), ("15 minutes", 15), ("20 minutes", 20), ("30 minutes", 30)
        ]:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(opt_title, None, "")
            item.setRepresentedObject_(opt_val)
            buf_popup.menu().addItem_(item)
            if opt_val == buf_val:
                buf_popup.selectItem_(item)
        card.addSubview_(buf_popup)

    def _build_flight_section(self, card, w, h):
        self._add_section_header(
            card,
            "Display & Menu Bar Live Status Modes",
            "Personalize menu bar status display style, screen position, and flight speed.",
            h, w,
            icon_emoji="✈️",
            badge_rgba=(0.6, 0.25, 1.0, 0.20),
            border_rgba=(0.6, 0.25, 1.0, 0.38)
        )

        # 1. Menu Bar Display Mode
        r1_y = h - 84.0
        self._add_row_label(card, "🦆 Menu Bar Style", "Format shown in the macOS status bar", r1_y, 220)

        modes = ["countdown", "event_time", "time_only", "icon_only"]
        curr_mb_mode = config.get("menubar_status_mode", "countdown")
        sel_mb_idx = modes.index(curr_mb_mode) if curr_mb_mode in modes else 0

        mb_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(245, r1_y - 12, 485, 28))
        mb_segmented.setSegmentCount_(4)
        mb_segmented.setLabel_forSegment_("⏳ Countdown", 0)
        mb_segmented.setLabel_forSegment_("🕐 Start Time", 1)
        mb_segmented.setLabel_forSegment_("⏱️ Time Only", 2)
        mb_segmented.setLabel_forSegment_("🦆 Icon Only", 3)
        mb_segmented.setSelectedSegment_(sel_mb_idx)
        mb_segmented.setTarget_(self)
        mb_segmented.setAction_("onSelectMenuBarMode:")
        card.addSubview_(mb_segmented)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Banner Position
        r2_y = h - 136.0
        self._add_row_label(card, "📍 Banner Position", "HUD screen location for taking off banner", r2_y, 220)

        pos_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(245, r2_y - 12, 260, 28))
        pos_segmented.setSegmentCount_(2)
        pos_segmented.setLabel_forSegment_("⬆️ Top (HUD)", 0)
        pos_segmented.setLabel_forSegment_("⬇️ Bottom", 1)
        curr_pos = config.get("banner_position", "top")
        pos_segmented.setSelectedSegment_(0 if curr_pos == "top" else 1)
        pos_segmented.setTarget_(self)
        pos_segmented.setAction_("onSelectBannerPosition:")
        card.addSubview_(pos_segmented)

        self._add_row_divider(card, h - 160.0, w)

        # 3. Flight Speed
        r3_y = h - 188.0
        curr_spd = int(float(config.get("flight_speed", 3.2)) * 10)
        self._add_row_label(card, "🚀 Flight Speed", "Horizontal glide velocity across the display", r3_y, 220)

        spd_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(245, r3_y - 12, 260, 28), False)
        spd_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        spd_popup.setTarget_(self)
        spd_popup.setAction_("onSelectFlightSpeed:")
        for opt_title, opt_val in [
            ("🐢 Relaxed (2.0x)", 20), ("✈️ Standard (3.2x - Default)", 32), ("🚀 Turbo (4.8x)", 48), ("⚡ Supersonic (6.0x)", 60)
        ]:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(opt_title, None, "")
            item.setRepresentedObject_(opt_val)
            spd_popup.menu().addItem_(item)
            if opt_val == curr_spd:
                spd_popup.selectItem_(item)
        card.addSubview_(spd_popup)

    def _build_audio_section(self, card, w, h):
        self._add_section_header(
            card,
            "Sound Effects & Audio Chimes",
            "Enable or customize the chime sound played when a reminder takes off.",
            h, w,
            icon_emoji="🔔",
            badge_rgba=(1.0, 0.2, 0.4, 0.20),
            border_rgba=(1.0, 0.2, 0.4, 0.38)
        )

        # 1. Enable Sound Switch
        r1_y = h - 84.0
        sound_on = config.get("sound_enabled", True)
        self.sound_switch = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, r1_y - 10, 320, 24))
        self.sound_switch.setButtonType_(AppKit.NSButtonTypeSwitch)
        self.sound_switch.setTitle_("🔊 Play Sound on Notification")
        self.sound_switch.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        self.sound_switch.setState_(AppKit.NSControlStateValueOn if sound_on else AppKit.NSControlStateValueOff)
        self.sound_switch.setTarget_(self)
        self.sound_switch.setAction_("onToggleSoundEnabled:")
        card.addSubview_(self.sound_switch)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Sound Tone Selection + Preview
        r2_y = h - 136.0
        self._add_row_label(card, "🎵 macOS Tone", "Select sound chime & test playback", r2_y, 220)

        sounds = [
            ("Glass (Default)", "Glass"), ("Hero", "Hero"), ("Ping", "Ping"), ("Pop", "Pop"),
            ("Submarine", "Submarine"), ("Tink", "Tink"), ("Bottle", "Bottle"), ("Funk", "Funk"),
            ("Basso", "Basso"), ("Morse", "Morse")
        ]
        curr_snd = config.get("sound_name", "Glass")
        
        self.sound_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(245, r2_y - 12, 230, 28), False)
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

        play_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(485, r2_y - 12, 120, 28))
        play_btn.setTitle_("▶ Play Tone")
        play_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        play_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        play_btn.setTarget_(self)
        play_btn.setAction_("onPlaySoundPreview:")
        card.addSubview_(play_btn)

    def _build_calendars_section(self, card, w, h, cals=None):
        self._add_section_header(
            card,
            "Included macOS Calendars",
            "Select which calendars to actively monitor for reminders.",
            h, w,
            icon_emoji="📅",
            badge_rgba=(0.2, 0.78, 0.4, 0.20),
            border_rgba=(0.2, 0.78, 0.4, 0.38)
        )
        
        if cals is None:
            cals = self.cached_calendars if self.cached_calendars else get_available_calendars()

        if not cals:
            lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 86, w - 36, 22))
            lbl.setStringValue_("All Apple Calendar accounts are currently monitored.")
            lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12))
            lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.7, 0.75, 0.88, 1.0))
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            card.addSubview_(lbl)
            return

        y = h - 88.0
        x_offset = 18.0
        for cal in cals:
            chk = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_offset, y, 340, 24))
            chk.setButtonType_(AppKit.NSButtonTypeSwitch)
            chk.setTitle_(f"📅 {cal['name']}")
            chk.setFont_(AppKit.NSFont.systemFontOfSize_(12))
            chk.setState_(AppKit.NSControlStateValueOn if cal['enabled'] else AppKit.NSControlStateValueOff)
            chk.setTarget_(self)
            chk.setAction_("onToggleCalendarSource:")
            chk.setToolTip_(cal['name'])
            card.addSubview_(chk)
            
            x_offset += 360.0
            if x_offset + 340.0 > w:
                x_offset = 18.0
                y -= 36.0

    def _build_system_section(self, card, w, h):
        self._add_section_header(
            card,
            "System Diagnostics & JSON Rules",
            "Customize classification rules and inspect real-time diagnostic logs.",
            h, w,
            icon_emoji="🛠️",
            badge_rgba=(0.1, 0.72, 0.85, 0.20),
            border_rgba=(0.1, 0.72, 0.85, 0.38)
        )

        y = h - 94.0
        btn_w = 170.0

        # 4 Sleek Action Buttons
        open_json_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, btn_w, 32))
        open_json_btn.setTitle_("📝 Edit Rules")
        open_json_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        open_json_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        open_json_btn.setTarget_(self)
        open_json_btn.setAction_("onOpenConfigEditor:")
        card.addSubview_(open_json_btn)

        reload_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18 + (btn_w + 12.0) * 1, y, btn_w, 32))
        reload_btn.setTitle_("🔄 Reload Rules")
        reload_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        reload_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        reload_btn.setTarget_(self)
        reload_btn.setAction_("onReloadConfig:")
        card.addSubview_(reload_btn)

        view_logs_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18 + (btn_w + 12.0) * 2, y, btn_w, 32))
        view_logs_btn.setTitle_("📄 View Logs")
        view_logs_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        view_logs_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        view_logs_btn.setTarget_(self)
        view_logs_btn.setAction_("onOpenLogs:")
        card.addSubview_(view_logs_btn)

        folder_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18 + (btn_w + 12.0) * 3, y, btn_w, 32))
        folder_btn.setTitle_("📂 Log Folder")
        folder_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        folder_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        folder_btn.setTarget_(self)
        folder_btn.setAction_("onOpenLogFolder:")
        card.addSubview_(folder_btn)

        # File path info tag
        info_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, 12, w - 36, 16))
        info_lbl.setStringValue_("📁 Path: ~/.quakmeeting/config.json  •  Log: ~/.quakmeeting/quakmeeting.log")
        info_lbl.setFont_(AppKit.NSFont.monospacedSystemFontOfSize_weight_(10.5, AppKit.NSFontWeightRegular))
        info_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.50, 0.55, 0.70, 1.0))
        info_lbl.setBezeled_(False)
        info_lbl.setDrawsBackground_(False)
        info_lbl.setEditable_(False)
        card.addSubview_(info_lbl)

    # Setting Handlers
    def onToggleMeetingStage_(self, sender):
        val = sender.tag()
        curr = set(config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        if sender.state() == AppKit.NSControlStateValueOn:
            curr.add(val)
        else:
            curr.discard(val)
        config.set("meeting_reminder_stages", sorted(list(curr), reverse=True))

    def onToggleTravelStage_(self, sender):
        val = sender.tag()
        curr = set(config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        if sender.state() == AppKit.NSControlStateValueOn:
            curr.add(val)
        else:
            curr.discard(val)
        config.set("travel_reminder_stages", sorted(list(curr), reverse=True))

    def onSaveHomeAddress_(self, sender):
        if hasattr(self, 'home_addr_field') and self.home_addr_field:
            addr = str(self.home_addr_field.stringValue() or "").strip()
            config.set("home_address", addr)
            if hasattr(self, 'home_save_btn') and self.home_save_btn:
                self.home_save_btn.setTitle_("✓ Saved")
                def reset_btn():
                    time.sleep(1.5)
                    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(lambda: self.home_save_btn.setTitle_("💾 Save"))
                threading.Thread(target=reset_btn, daemon=True).start()
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
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        ignored = set(config.get("ignored_calendars", []))
        if is_on:
            ignored.discard(cal_name)
        else:
            ignored.add(cal_name)
        config.set("ignored_calendars", list(ignored))
        for cal in self.cached_calendars:
            if cal.get("name") == cal_name:
                cal["enabled"] = is_on
        self.refresh_data(force=True)

    def onSelectSnoozeDuration_(self, sender):
        val_min = sender.selectedItem().representedObject()
        config.set("default_snooze_seconds", int(val_min) * 60)

    def onSelectMenuBarMode_(self, sender):
        modes = ["countdown", "event_time", "time_only", "icon_only"]
        sel = sender.selectedSegment()
        if 0 <= sel < len(modes):
            config.set("menubar_status_mode", modes[sel])
            try:
                event_bus.publish("CONFIG_CHANGED", key="menubar_status_mode")
            except Exception:
                pass

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

    def onOpenConfigEditor_(self, sender):
        config.open_config_in_editor()

    def onReloadConfig_(self, sender):
        config.reload()
        self.refresh_data(force=True)

    def onOpenLogs_(self, sender):
        open_log_file()

    def onOpenLogFolder_(self, sender):
        open_log_folder()

def show_dashboard(tab_index=None):
    controller = DashboardWindowController.sharedController()
    controller.show(tab_index)

if __name__ == "__main__":
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    show_dashboard()
    app.run()
