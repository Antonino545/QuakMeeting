import AppKit
import objc
from core.services.calendar_service import calendar_service
from core.services.config_service import is_debug_mode
from ui.macos.components import CardView
from ui.macos.dashboard_tabs.settings import (
    CalendarsCardController,
    ETACardController,
    SystemCardController,
    TimingCardController,
)
from ui.macos.theme import Theme


class SettingsTabController(AppKit.NSObject):
    """Coordinator for the Settings & Preferences tab on macOS."""

    def init(self):
        self = objc.super(SettingsTabController, self).init()
        self.dashboard_controller = None
        self.config = None
        self.cached_calendars = []
        self._cached_view = None
        self._cached_sig = None
        self._saved_dist_from_top = None

        self.timing_card = TimingCardController.alloc().initWithParent_(self)
        self.eta_card = ETACardController.alloc().initWithParent_(self)
        self.calendars_card = CalendarsCardController.alloc().initWithParent_(self)
        self.system_card = SystemCardController.alloc().initWithParent_(self)
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
    def refresh_data(self, force=False):
        self.invalidate_cache()
        if self.dashboard_controller and hasattr(self.dashboard_controller, "refresh_current_tab"):
            self.dashboard_controller.refresh_current_tab()

    @objc.python_method
    def render(self, container, w, h, config, cached_calendars):
        self.dashboard_controller = container
        self.config = config
        self.cached_calendars = cached_calendars

        current_sig = (
            w,
            h,
            is_debug_mode(),
            len(cached_calendars or []),
            config.get("transport_mode", "transit"),
            config.get("home_address", ""),
            config.get("exam_location", ""),
            config.get("eta_buffer_minutes", 10),
            config.get("language", "system"),
            config.get("mute_during_lessons", True),
            tuple(sorted(config.get("meeting_reminder_stages", []))),
            tuple(sorted(config.get("general_reminder_stages", []))),
            tuple(sorted(config.get("travel_reminder_stages", []))),
            tuple(sorted(config.get("ignored_calendars", []))),
        )

        if self._cached_view and self._cached_sig == current_sig:
            return self._cached_view

        view = self._render_settings_tab(w, h)
        self._cached_view = view
        self._cached_sig = current_sig
        return view

    @objc.python_method
    def _render_settings_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_w = w - 16.0
        gap = 14.0

        c1_h = 362.0  # Notification Lead Times & Staged Reminders
        c2_h = 394.0  # Home / Departure Address, University & Exam Campus, Route ETA

        # Calculate calendar section height dynamically based on wrapped rows
        cals = self.cached_calendars if self.cached_calendars else calendar_service.get_available_calendars()
        if not self.cached_calendars and cals:
            self.cached_calendars = cals

        available_w = card_w - 36.0
        curr_row_w = 0.0
        actual_rows = 1 if cals else 1
        for cal in (cals or []):
            cal_name = cal.get("name", "Calendar")
            pill_w = max(110.0, min(240.0, len(cal_name) * 8.5 + 42.0))
            if curr_row_w > 0.0 and curr_row_w + pill_w > available_w:
                actual_rows += 1
                curr_row_w = pill_w + 8.0
            else:
                curr_row_w += (pill_w + 8.0)

        c3_h = 74.0 + actual_rows * 36.0  # Included System Calendars
        is_dbg = is_debug_mode()
        c4_h = 336.0 if is_dbg else 272.0  # System, Language & (Diagnostics if Debug)

        content_h = c1_h + c2_h + c3_h + c4_h + gap * 5 + 20.0
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        curr_y = content_h - gap

        # CARD 1: TIMING & MULTI-STAGE NOTIFICATIONS
        curr_y -= c1_h
        card1 = self._create_card_container(0, curr_y, card_w, c1_h)
        self.timing_card.build_card(card1, card_w, c1_h)
        doc_view.addSubview_(card1)

        # CARD 2: DEPARTURE ADDRESS & MULTI-MODAL ROUTE ETA
        curr_y -= (c2_h + gap)
        card2 = self._create_card_container(0, curr_y, card_w, c2_h)
        self.eta_card.build_card(card2, card_w, c2_h)
        doc_view.addSubview_(card2)

        # CARD 3: INCLUDED SYSTEM CALENDARS
        curr_y -= (c3_h + gap)
        card3 = self._create_card_container(0, curr_y, card_w, c3_h)
        self.calendars_card.build_card(card3, card_w, c3_h, cals)
        doc_view.addSubview_(card3)

        # CARD 4: SYSTEM & DIAGNOSTICS
        curr_y -= (c4_h + gap)
        card4 = self._create_card_container(0, curr_y, card_w, c4_h)
        self.system_card.build_card(card4, card_w, c4_h)
        doc_view.addSubview_(card4)

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
    def _create_card_container(self, x, y, w, h):
        """Creates a solid card container with Catppuccin Mocha styling."""
        return CardView.create(
            AppKit.NSMakeRect(x, y, w, h),
            bg_color=Theme.MANTLE,
            corner_radius=12.0,
            border_width=1.0,
            border_color=Theme.SURFACE0,
        )

    # ── Backward-compatible Action Delegators ─────────────────────────────
    @objc.IBAction
    def onApplyPresetRelaxed_(self, sender):
        self.timing_card.onApplyPresetRelaxed_(sender)

    @objc.IBAction
    def onApplyPresetStandard_(self, sender):
        self.timing_card.onApplyPresetStandard_(sender)

    @objc.IBAction
    def onApplyPresetIntensive_(self, sender):
        self.timing_card.onApplyPresetIntensive_(sender)

    @objc.IBAction
    def onToggleMeetingStage_(self, sender):
        self.timing_card.onToggleMeetingStage_(sender)

    @objc.IBAction
    def onToggleGeneralStage_(self, sender):
        self.timing_card.onToggleGeneralStage_(sender)

    @objc.IBAction
    def onToggleTravelStage_(self, sender):
        self.timing_card.onToggleTravelStage_(sender)

    @objc.IBAction
    def onSelectModeBtn_(self, sender):
        self.eta_card.onSelectModeBtn_(sender)

    @objc.IBAction
    def onSaveHomeAddress_(self, sender):
        self.eta_card.onSaveHomeAddress_(sender)

    @objc.IBAction
    def onSaveExamAddress_(self, sender):
        self.eta_card.onSaveExamAddress_(sender)

    @objc.IBAction
    def onSelectETABuffer_(self, sender):
        self.eta_card.onSelectETABuffer_(sender)

    @objc.IBAction
    def onToggleCalendarSource_(self, sender):
        self.calendars_card.onToggleCalendarSource_(sender)

    @objc.IBAction
    def onSelectLanguageBtn_(self, sender):
        self.system_card.onSelectLanguageBtn_(sender)

    @objc.IBAction
    def onCheckForUpdatesMac_(self, sender):
        self.system_card.onCheckForUpdatesMac_(sender)

    @objc.IBAction
    def onInstallUpdateMac_(self, sender):
        self.system_card.onInstallUpdateMac_(sender)

    @objc.IBAction
    def onOpenConfigEditor_(self, sender):
        self.system_card.onOpenConfigEditor_(sender)

    @objc.IBAction
    def onOpenLogs_(self, sender):
        self.system_card.onOpenLogs_(sender)

    @objc.IBAction
    def onOpenLogFolder_(self, sender):
        self.system_card.onOpenLogFolder_(sender)

    @objc.IBAction
    def onOpenLicenseMac_(self, sender):
        self.system_card.onOpenLicenseMac_(sender)
