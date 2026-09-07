import AppKit
import objc
from core.services.calendar_service import calendar_service
from core.services.config_service import is_debug_mode
from core.services.language_service import t
from ui.macos.components import CardView, create_button
from ui.macos.dashboard_tabs.settings import (
    CalendarsCardController,
    ETACardController,
    ArrivalCardController,
    SystemCardController,
    TimingCardController,
)
from ui.macos.theme import Theme


class SettingsTabController(AppKit.NSObject):
    """Coordinator for the Settings & Preferences tab on macOS with two-pane sidebar navigation."""

    def init(self):
        self = objc.super(SettingsTabController, self).init()
        self.dashboard_controller = None
        self.config = None
        self.cached_calendars = []
        self._cached_view = None
        self._cached_sig = None
        self._saved_dist_from_top = None
        self.selected_category = 0

        self.timing_card = TimingCardController.alloc().initWithParent_(self)
        self.eta_card = ETACardController.alloc().initWithParent_(self)
        self.arrival_card = ArrivalCardController.alloc().initWithParent_(self)
        self.calendars_card = CalendarsCardController.alloc().initWithParent_(self)
        self.system_card = SystemCardController.alloc().initWithParent_(self)
        return self

    @objc.python_method
    def invalidate_cache(self):
        self._cached_view = None
        self._cached_sig = None
        self._saved_dist_from_top = None

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
            self.selected_category,
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
        main_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        sidebar_w = 210.0
        gap = 14.0
        content_w = w - sidebar_w - gap

        # 1. Left Sidebar Navigation Container
        sidebar = self._create_card_container(0, 0, sidebar_w, h)
        self._build_sidebar(sidebar, sidebar_w, h)
        main_view.addSubview_(sidebar)

        # 2. Right Content Scroll Area
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(
            AppKit.NSMakeRect(sidebar_w + gap, 0, content_w, h)
        )
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_w = content_w - 12.0
        c1_h = 362.0   # Notification Lead Times & Staged Reminders
        c2_h = 394.0   # Home / Departure Address, Campus & Route ETA
        c_arr_h = 380.0  # Smart Presence & Arrival Detection

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

        # Build content based on selected category
        if self.selected_category == 0:
            # Notification Timing & Presets
            content_h = max(h, c1_h + gap * 2)
            doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, content_w, content_h))
            card1 = self._create_card_container(0, content_h - gap - c1_h, card_w, c1_h)
            self.timing_card.build_card(card1, card_w, c1_h)
            doc_view.addSubview_(card1)

        elif self.selected_category == 1:
            # Smart Presence & Arrival Detection
            content_h = max(h, c_arr_h + gap * 2)
            doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, content_w, content_h))
            card_arr = self._create_card_container(0, content_h - gap - c_arr_h, card_w, c_arr_h)
            self.arrival_card.build_card(card_arr, card_w, c_arr_h)
            doc_view.addSubview_(card_arr)

        elif self.selected_category == 2:
            # Calendar Sources
            content_h = max(h, c3_h + gap * 2)
            doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, content_w, content_h))
            card3 = self._create_card_container(0, content_h - gap - c3_h, card_w, c3_h)
            self.calendars_card.build_card(card3, card_w, c3_h, cals)
            doc_view.addSubview_(card3)

        elif self.selected_category == 3:
            # Commute & Transit ETA
            content_h = max(h, c2_h + gap * 2)
            doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, content_w, content_h))
            card2 = self._create_card_container(0, content_h - gap - c2_h, card_w, c2_h)
            self.eta_card.build_card(card2, card_w, c2_h)
            doc_view.addSubview_(card2)

        else:
            # App Preferences & System
            content_h = max(h, c4_h + gap * 2)
            doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, content_w, content_h))
            card4 = self._create_card_container(0, content_h - gap - c4_h, card_w, c4_h)
            self.system_card.build_card(card4, card_w, c4_h)
            doc_view.addSubview_(card4)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            target_y = max(0.0, content_h - h)
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, target_y))
            scroll_view.reflectScrolledClipView_(scroll_view.contentView())

        main_view.addSubview_(scroll_view)
        return main_view

    @objc.python_method
    def _build_sidebar(self, sidebar, w, h):
        """Constructs the left category navigation sidebar with active styling."""
        header_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, h - 34, w - 28, 16))
        header_lbl.setStringValue_(t("settings_categories_header"))
        header_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(10.0))
        header_lbl.setTextColor_(Theme.OVERLAY0)
        header_lbl.setBezeled_(False)
        header_lbl.setDrawsBackground_(False)
        header_lbl.setEditable_(False)
        sidebar.addSubview_(header_lbl)

        categories = [
            (0, "⏱️ " + t("settings_cat_reminders")),
            (1, "📍 " + t("settings_cat_presence")),
            (2, "📅 " + t("settings_cat_calendars")),
            (3, "🚗 " + t("settings_cat_commute")),
            (4, "⚙️ " + t("settings_cat_preferences")),
        ]

        btn_h = 44.0
        btn_gap = 8.0
        start_y = h - 46.0 - btn_h

        for idx, title in categories:
            btn_y = start_y - idx * (btn_h + btn_gap)
            is_sel = (self.selected_category == idx)
            bg = Theme.SURFACE0 if is_sel else Theme.MANTLE
            border = Theme.BLUE if is_sel else None
            fg = Theme.TEXT if is_sel else Theme.SUBTEXT0
            btn = create_button(
                AppKit.NSMakeRect(10, btn_y, w - 20, btn_h),
                title=title,
                bg_color=bg,
                text_color=fg,
                border_color=border,
                corner_radius=8.0,
                font_size=12.0,
                bold=is_sel,
            )
            btn.setTag_(idx)
            btn.setTarget_(self)
            btn.setAction_(objc.selector(self.onSelectCategory_, signature=b"v@:@"))
            sidebar.addSubview_(btn)

    @objc.IBAction
    def onSelectCategory_(self, sender):
        tag = sender.tag()
        if tag != self.selected_category:
            self.selected_category = tag
            self.refresh_data(force=True)

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
