import AppKit
import objc
import webbrowser
import threading
import time
from datetime import datetime
from core.domain.models import format_duration
from core.services.eta_service import MODE_ICONS
from core.services.arrival_service import arrival_service
from core.services.language_service import t, get_active_language
from ui.common.agenda_viewmodel import AgendaViewModel, AgendaEventVM
from ui.macos.theme import Theme

class AgendaTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(AgendaTabController, self).init()
        self.dashboard_controller = None
        self.config = None
        self.vms = []
        self._cached_view = None
        self._cached_sig = None
        self._saved_dist_from_top = None
        return self

    @objc.python_method
    def invalidate_cache(self):
        if self._cached_view and self._cached_view.contentView() and self._cached_view.documentView():
            old_doc_h = self._cached_view.documentView().frame().size.height
            clip_y = self._cached_view.contentView().bounds().origin.y
            clip_h = self._cached_view.contentView().bounds().size.height
            self._saved_dist_from_top = max(0.0, old_doc_h - (clip_y + clip_h))
        self._cached_view = None
        self._cached_sig = None

    @objc.python_method
    def render(self, container, w, h, meetings, is_loading, config):
        self.dashboard_controller = container
        self.meetings = meetings or []
        self.config = config
        self.vms = AgendaViewModel.build(self.meetings, lang=get_active_language())

        if is_loading and not self.meetings:
            loading_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))

            spinner = AppKit.NSProgressIndicator.alloc().initWithFrame_(AppKit.NSMakeRect((w - 32) * 0.5, (h - 32) * 0.5 + 24, 32, 32))
            spinner.setStyle_(AppKit.NSProgressIndicatorStyleSpinning)
            spinner.setControlSize_(AppKit.NSControlSizeRegular)
            spinner.startAnimation_(None)
            loading_view.addSubview_(spinner)

            load_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, (h - 32) * 0.5 - 34, w - 40, 48))
            load_lbl.setStringValue_(f"🦆 {t('agenda_today_flights')}...\n{t('scanner_active_no_events')}")
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

        total_items = max(1, len(self.vms))
        content_h = max(h, total_items * (card_h + gap) + 20.0)

        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        if not self.vms:
            empty_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(20, content_h - 100, w - 40, 50))
            empty_lbl.setStringValue_(f"🧘‍♂️ {t('agenda_no_flights')}\n{t('all_caught_up')}")
            empty_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(14))
            empty_lbl.setTextColor_(Theme.SUBTEXT0)
            empty_lbl.setAlignment_(AppKit.NSTextAlignmentCenter)
            empty_lbl.setBezeled_(False)
            empty_lbl.setDrawsBackground_(False)
            empty_lbl.setEditable_(False)
            doc_view.addSubview_(empty_lbl)
        else:
            for idx, vm in enumerate(self.vms):
                y_item = content_h - (idx + 1) * (card_h + gap)
                card = self._create_meeting_card(vm, idx, 0, y_item, w - 16, card_h)
                doc_view.addSubview_(card)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            if hasattr(self, "_saved_dist_from_top") and self._saved_dist_from_top is not None:
                target_y = max(0.0, min(content_h - h, content_h - h - self._saved_dist_from_top))
            else:
                target_y = max(0.0, content_h - h)
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, target_y))
            scroll_view.reflectScrolledClipView_(scroll_view.contentView())
        return scroll_view

    @objc.python_method
    def _create_meeting_card(self, vm, idx, x, y, w, h):
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(Theme.BASE.CGColor())
        card.layer().setCornerRadius_(12.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(Theme.SURFACE0.CGColor())

        icon_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, 18, 40, 40))
        icon_lbl.setStringValue_(vm.icon)
        icon_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(26))
        icon_lbl.setBezeled_(False)
        icon_lbl.setDrawsBackground_(False)
        icon_lbl.setEditable_(False)
        card.addSubview_(icon_lbl)

        title_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 38, w - 275, 24))
        title_lbl.setStringValue_(f"{vm.time_display}  •  {vm.title}")
        title_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14))
        title_lbl.setTextColor_(Theme.TEXT)
        title_lbl.setBezeled_(False)
        title_lbl.setDrawsBackground_(False)
        title_lbl.setEditable_(False)
        card.addSubview_(title_lbl)

        sub_str = vm.subtitle
        if vm.badge_text:
            sub_str = f"{sub_str}  •  {vm.badge_text}" if sub_str else vm.badge_text

        sub_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(62, 16, w - 275, 20))
        sub_lbl.setStringValue_(sub_str)
        sub_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        sub_lbl.setTextColor_(Theme.SUBTEXT0)
        sub_lbl.setBezeled_(False)
        sub_lbl.setDrawsBackground_(False)
        sub_lbl.setEditable_(False)
        card.addSubview_(sub_lbl)

        if vm.has_action:
            action_btn = Theme.create_button(
                AppKit.NSMakeRect(w - 142, 20, 126, 34),
                title=vm.action_btn_text or t("agenda_join_button", default="🚀 Join"),
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

            copy_title = "📋 " + t("copy")
            copy_btn = Theme.create_button(
                AppKit.NSMakeRect(w - 238, 20, 90, 34),
                title=copy_title,
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
        if hasattr(self, "vms") and 0 <= idx < len(self.vms):
            url = self.vms[idx].action_url
            if url:
                webbrowser.open(url)

    def onCopyMeetingUrl_(self, sender):
        idx = sender.tag()
        if hasattr(self, "vms") and 0 <= idx < len(self.vms):
            url = self.vms[idx].action_url
            if url:
                pasteboard = AppKit.NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(url, AppKit.NSPasteboardTypeString)
                sender.setTitle_("✓ " + t("saved"))
                def reset():
                    time.sleep(1.5)
                    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(lambda: sender.setTitle_("📋 " + t("copy")))
                threading.Thread(target=reset, daemon=True).start()
