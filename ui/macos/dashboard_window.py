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
    from core.services.updater_service import updater_service
    from core.domain.models import format_duration
    from core.logger import open_log_file, open_log_folder
    from ui.macos.banner_window import _run_banner
    from ui.macos.dashboard_tabs.agenda_tab import AgendaTabController
    from ui.macos.dashboard_tabs.hangar_tab import HangarTabController
    from ui.macos.dashboard_tabs.settings_tab import SettingsTabController
    from ui.macos.theme import Theme
except ImportError:
    from config_manager import config
    from calendar_scanner import get_upcoming_meetings, sync_calendar_now, get_available_calendars
    from eta_service import eta_service, MODE_ICONS, MODE_LABELS
    from event_bus import event_bus
    from models import format_duration
    from logger import open_log_file, open_log_folder
    from banner_window import _run_banner
    from dashboard_tabs.agenda_tab import AgendaTabController
    from dashboard_tabs.hangar_tab import HangarTabController
    from dashboard_tabs.settings_tab import SettingsTabController
    from theme import Theme

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

        self.agenda_tab = AgendaTabController.alloc().init()
        self.hangar_tab = HangarTabController.alloc().init()
        self.settings_tab = SettingsTabController.alloc().init()

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
        if self.window:
            self.window.makeKeyAndOrderFront_(None)
            self.window.orderFrontRegardless()
        if app:
            try:
                app.activateIgnoringOtherApps_(True)
            except Exception:
                pass
        self.refresh_data()

    def _create_window(self):
        width, height = 830.0, 610.0
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
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())

        self.delegate = DashboardWindowDelegate.alloc().init()
        self.delegate.controller = self
        self.window.setDelegate_(self.delegate)

        root_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, width, height))
        root_view.setWantsLayer_(True)
        root_view.layer().setBackgroundColor_(Theme.CRUST.CGColor())
        root_view.layer().setCornerRadius_(16.0)
        root_view.layer().setMasksToBounds_(True)
        root_view.layer().setBorderWidth_(1.0)
        root_view.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        root_view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        self.window.setContentView_(root_view)

        self._build_header(root_view, width, height)
        self._build_tab_selector(root_view, width, height)

        self.content_container = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(20, 20, width - 40, height - 192))
        self.content_container.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        root_view.addSubview_(self.content_container)

    def _build_header(self, parent, w, h):
        header_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 116, w - 40, 74))
        header_view.setWantsLayer_(True)
        header_view.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        header_view.layer().setCornerRadius_(12.0)
        header_view.layer().setMasksToBounds_(True)
        header_view.layer().setBorderWidth_(1.0)
        header_view.layer().setBorderColor_(Theme.SURFACE0.CGColor())

        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "icon.png"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png"),
            os.path.join(os.getcwd(), "assets", "icon.png"),
        ]
        if AppKit.NSBundle.mainBundle().resourcePath():
            candidates.insert(0, os.path.join(AppKit.NSBundle.mainBundle().resourcePath(), "assets", "icon.png"))
            candidates.insert(0, os.path.join(AppKit.NSBundle.mainBundle().resourcePath(), "icon.png"))

        icon_path = next((p for p in candidates if os.path.exists(p)), None)
        if icon_path:
            icon_img = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
            icon_view = AppKit.NSImageView.alloc().initWithFrame_(AppKit.NSMakeRect(14, 11, 52, 52))
            icon_view.setImage_(icon_img)
            header_view.addSubview_(icon_view)
        else:
            icon_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, 14, 52, 48))
            icon_lbl.setStringValue_("🦆")
            icon_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(36))
            icon_lbl.setBezeled_(False)
            icon_lbl.setDrawsBackground_(False)
            icon_lbl.setEditable_(False)
            icon_lbl.setSelectable_(False)
            header_view.addSubview_(icon_lbl)

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(76, 36, 350, 30))
        title_lbl.setStringValue_("QuakMeeting — Flight Deck")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(18))
        title_lbl.setTextColor_(Theme.TEXT)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        title_lbl.setSelectable_(False)
        header_view.addSubview_(title_lbl)

        self.status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(76, 14, 450, 22))
        self.status_lbl.setStringValue_("🟢 Scanner Active  •  Loading events...")
        self.status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.status_lbl.setTextColor_(Theme.SUBTEXT0)
        self.status_lbl.setBezeled_(False)
        self.status_lbl.setDrawsBackground_(False)
        self.status_lbl.setEditable_(False)
        self.status_lbl.setSelectable_(False)
        header_view.addSubview_(self.status_lbl)

        self.sync_status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(w - 330, 28, 150, 20))
        self.sync_status_lbl.setStringValue_("🔄 Pending")
        self.sync_status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        self.sync_status_lbl.setTextColor_(Theme.SUBTEXT1)
        self.sync_status_lbl.setAlignment_(AppKit.NSTextAlignmentRight)
        self.sync_status_lbl.setBezeled_(False)
        self.sync_status_lbl.setDrawsBackground_(False)
        self.sync_status_lbl.setEditable_(False)
        self.sync_status_lbl.setSelectable_(False)
        header_view.addSubview_(self.sync_status_lbl)

        refresh_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(w - 170, 20, 130, 34))
        refresh_btn.setTitle_("🔄 Sync Now")
        Theme.style_button(refresh_btn, bg_color=Theme.SURFACE0, text_color=Theme.TEXT, border_color=Theme.SURFACE1, corner_radius=8.0, font_size=12.0, bold=True)
        refresh_btn.setTarget_(self)
        refresh_btn.setAction_("onRefreshClicked:")
        header_view.addSubview_(refresh_btn)

        parent.addSubview_(header_view)

    def _build_tab_selector(self, parent, w, h):
        self.tab_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(20, h - 160, w - 40, 32))
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
        self.meetings = get_upcoming_meetings(force_refresh=False)
        now = datetime.now().astimezone()

        today_meetings = [m for m in self.meetings if m.get("start_time") and m["start_time"].astimezone().date() == now.date()]
        today_upcoming = [m for m in today_meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]

        if today_upcoming:
            next_m = today_upcoming[0]
            s_str = next_m["start_time"].astimezone().strftime("%H:%M") if next_m.get("start_time") else "--:--"
            travel_info = ""
            if next_m.get("travel_time_minutes"):
                dur_str = format_duration(next_m["travel_time_minutes"])
                t_mode = next_m.get("transport_mode", config.get("transport_mode", "transit"))
                icon = MODE_ICONS.get(t_mode, "🚗")
                dep_dt = next_m.get("departure_time")
                if isinstance(dep_dt, datetime):
                    travel_info = f"  •  ⏱️ {icon} ~{dur_str} (Leave at {dep_dt.astimezone().strftime('%H:%M')})"
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
                    n = datetime.now().astimezone()
                    t_meets = [m for m in self.meetings if m.get("start_time") and m["start_time"].astimezone().date() == n.date()]
                    t_up = [m for m in t_meets if (m.get("end_time") and m["end_time"] > n) or (m.get("start_time") and m["start_time"] > n)]

                    if t_up:
                        nx = t_up[0]
                        st = nx["start_time"].astimezone().strftime("%H:%M") if nx.get("start_time") else "--:--"
                        tr_info = ""
                        if nx.get("travel_time_minutes"):
                            dur_s = format_duration(nx["travel_time_minutes"])
                            tm = nx.get("transport_mode", config.get("transport_mode", "transit"))
                            ic = MODE_ICONS.get(tm, "🚗")
                            dp = nx.get("departure_time")
                            if isinstance(dp, datetime):
                                tr_info = f"  •  ⏱️ {ic} ~{dur_s} (Leave at {dp.astimezone().strftime('%H:%M')})"
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

        from core.services.calendar_service import calendar_service
        
        last_sync = calendar_service.last_sync_time
        status = calendar_service.last_sync_status
        sync_str = last_sync.strftime("%H:%M:%S") if last_sync else "Never"
        
        if status == "Error":
            self.sync_status_lbl.setStringValue_(f"❌ Failed (Last: {sync_str})")
            self.sync_status_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.9, 0.4, 0.4, 1.0))
        else:
            self.sync_status_lbl.setStringValue_(f"✅ Sync: {sync_str}")
            self.sync_status_lbl.setTextColor_(AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.72, 0.85, 1.0))

        m_sig = tuple((m.get("title"), str(m.get("start_time")), m.get("travel_time_minutes")) for m in self.meetings)
        sync_time_str = calendar_service.last_sync_time.isoformat() if calendar_service.last_sync_time else ""
        current_sig = (self.current_tab, self.is_loading, len(self.meetings), m_sig, sync_time_str)
        if self._last_rendered_signature == current_sig:
            return
        self._last_rendered_signature = current_sig

        for sub in list(self.content_container.subviews()):
            sub.removeFromSuperview()

        cw = self.content_container.frame().size.width
        ch = self.content_container.frame().size.height

        if self.current_tab == 0:
            view = self.agenda_tab.render(self, cw, ch, self.meetings, self.is_loading, config)
            self.content_container.addSubview_(view)
        elif self.current_tab == 1:
            view = self.hangar_tab.render(self, cw, ch)
            self.content_container.addSubview_(view)
        elif self.current_tab == 2:
            view = self.settings_tab.render(self, cw, ch, config, self.cached_calendars)
            self.content_container.addSubview_(view)

def show_dashboard(tab_index=None):
    def _show():
        controller = DashboardWindowController.sharedController()
        controller.show(tab_index)

    if AppKit.NSThread.isMainThread():
        _show()
    else:
        AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_show)

