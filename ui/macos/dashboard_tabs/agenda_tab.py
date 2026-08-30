import AppKit
import objc
import webbrowser
import threading
import time
from datetime import datetime
from core.domain.models import format_duration
from core.services.eta_service import MODE_ICONS
from ui.macos.theme import Theme

class AgendaTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(AgendaTabController, self).init()
        self.dashboard_controller = None
        self.config = None
        return self

    @objc.python_method
    def render(self, container, w, h, meetings, is_loading, config):
        self.dashboard_controller = container
        self.meetings = meetings
        self.config = config

        if is_loading and not self.meetings:
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

            return loading_view

        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_h = 76.0
        gap = 12.0

        now = datetime.now().astimezone()
        today_list = [m for m in self.meetings if m.get("start_time") and m["start_time"].astimezone().date() == now.date()]

        total_items = max(1, len(today_list))
        content_h = max(h, total_items * (card_h + gap) + 20.0)

        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        if not today_list:
            empty_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, content_h - 100, w - 40, 50))
            empty_lbl.setStringValue_("🧘‍♂️ No events scheduled for today in enabled calendars.\nRelax or add an event in Apple Calendar!")
            empty_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(14))
            empty_lbl.setTextColor_(Theme.SUBTEXT0)
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
        return scroll_view

    @objc.python_method
    def _create_meeting_card(self, m, idx, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(Theme.BASE.CGColor())
        card.layer().setCornerRadius_(12.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(Theme.SURFACE0.CGColor())

        p_type = m.get("pilot_type", "duck")
        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "gym": "🏋️‍♂️", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}
        icon_str = icon_map.get(p_type, "🦆")

        icon_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, 18, 40, 40))
        icon_lbl.setStringValue_(icon_str)
        icon_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(26))
        icon_lbl.setBezeled_(False)
        icon_lbl.setDrawsBackground_(False)
        icon_lbl.setEditable_(False)
        card.addSubview_(icon_lbl)

        s_time = m["start_time"].astimezone().strftime("%H:%M") if m.get("start_time") else "--:--"
        e_time = m["end_time"].astimezone().strftime("%H:%M") if m.get("end_time") else ""
        time_str = f"{s_time} - {e_time}" if e_time else s_time
        m_title = (m.get("title") or "Untitled Event").strip()

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 38, w - 275, 24))
        title_lbl.setStringValue_(f"{time_str}  •  {m_title}")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14))
        title_lbl.setTextColor_(Theme.TEXT)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        sub_str = m.get("provider", "Event")
        loc = m.get("location")
        if loc and loc != "missing value":
            sub_str += f"  •  📍 {loc[:35]}"
        elif m.get("action_url") and "meet.google.com" in m["action_url"]:
            sub_str += "  •  🌐 Google Meet"

        if m.get("travel_time_minutes"):
            dur_str = format_duration(m["travel_time_minutes"])
            t_mode = m.get("transport_mode", self.config.get("transport_mode", "transit"))
            icon = MODE_ICONS.get(t_mode, "🚗")
            dep_dt = m.get("departure_time")
            if isinstance(dep_dt, datetime):
                sub_str += f"  •  ⏱️ {icon} ~{dur_str} (Leave at {dep_dt.astimezone().strftime('%H:%M')})"
            else:
                sub_str += f"  •  ⏱️ {icon} ~{dur_str} travel"

        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 16, w - 275, 20))
        sub_lbl.setStringValue_(sub_str)
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        sub_lbl.setTextColor_(Theme.SUBTEXT0)
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        card.addSubview_(sub_lbl)

        action_url = m.get("action_url") or m.get("meeting_url")
        if not action_url and loc and loc != "missing value":
            import urllib.parse
            action_url = f"https://maps.apple.com/?q={urllib.parse.quote(loc)}"

        has_real_url = bool(action_url and action_url.strip() and action_url != "https://calendar.apple.com")

        if has_real_url:
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

            action_btn = Theme.create_button(
                AppKit.NSMakeRect(w - 142, 20, 126, 34),
                title=btn_short,
                bg_color=Theme.BLUE,
                text_color=Theme.CRUST,
                border_color=None,
                corner_radius=8.0,
                font_size=12.0,
                bold=True
            )
            action_btn.setTarget_(self)
            action_btn.setAction_("onOpenMeetingUrl:")
            action_btn.setTag_(idx)
            card.addSubview_(action_btn)

            copy_btn = Theme.create_button(
                AppKit.NSMakeRect(w - 238, 20, 90, 34),
                title="📋 Copy",
                bg_color=Theme.SURFACE0,
                text_color=Theme.TEXT,
                border_color=Theme.SURFACE1,
                corner_radius=8.0,
                font_size=11.5,
                bold=False
            )
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
