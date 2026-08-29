import AppKit
import objc
import os
import time
import threading
from core.calendar_scanner import get_available_calendars
from core.services.event_bus import event_bus
from core.services.updater_service import updater_service
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from core.logger import open_log_file, open_log_folder
try:
    from ui.macos.theme import Theme
except ImportError:
    from theme import Theme

class SettingsTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(SettingsTabController, self).init()
        self.dashboard_controller = None
        self.config = None
        self.cached_calendars = []
        return self

    @objc.python_method
    def refresh_data(self, force=False):
        if self.dashboard_controller and hasattr(self.dashboard_controller, 'refresh_data'):
            self.dashboard_controller.refresh_data(force=force)

    @objc.python_method
    def render(self, container, w, h, config, cached_calendars):
        self.dashboard_controller = container
        self.config = config
        self.cached_calendars = cached_calendars
        return self._render_settings_tab(w, h)

    # TAB 3: PREFERENCES & TIMING SETTINGS
    # -------------------------------------------------------------
    @objc.python_method
    def _render_settings_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_w = w - 16.0
        gap = 14.0

        c1_h = 356.0 # Notification Lead Times & Staged Reminders (Upgraded Pill Chips)
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

        c_up_h = 136.0 # Software Updates & Releases
        c5_h = 200.0 # System, Launch at Login & JSON Config

        content_h = c1_h + c_eta_h + c2_h + c3_h + c4_h + c_up_h + c5_h + gap * 8 + 24.0
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

        # SECTION 6: SOFTWARE UPDATES & RELEASES
        curr_y -= (c_up_h + gap)
        card_up = self._create_card_container(0, curr_y, card_w, c_up_h)
        self._build_update_section(card_up, card_w, c_up_h)
        doc_view.addSubview_(card_up)

        # SECTION 7: SYSTEM & JSON RULES
        curr_y -= (c5_h + gap)
        card5 = self._create_card_container(0, curr_y, card_w, c5_h)
        self._build_system_section(card5, card_w, c5_h)
        doc_view.addSubview_(card5)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        return scroll_view

    @objc.python_method
    def _create_card_container(self, x, y, w, h):
        """Creates a modern solid card container with Catppuccin Mocha styling."""
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(Theme.BASE.CGColor())
        card.layer().setCornerRadius_(12.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        return card

    @objc.python_method
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
        t_lbl.setTextColor_(Theme.TEXT)
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        # Subtitle
        s_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(56, y - 46, w - 74, 16))
        s_lbl.setStringValue_(subtitle)
        s_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        s_lbl.setTextColor_(Theme.SUBTEXT0)
        s_lbl.setBezeled_(False)
        s_lbl.setDrawsBackground_(False)
        s_lbl.setEditable_(False)
        parent.addSubview_(s_lbl)

        # Header bottom hairline divider (strictly separated with zero overlap)
        div = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, y - 54, w - 36, 1))
        div.setWantsLayer_(True)
        div.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        parent.addSubview_(div)

    @objc.python_method
    def _add_row_divider(self, parent, y, w):
        """Adds a subtle inner hairline divider between preference rows."""
        div = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, w - 36, 1))
        div.setWantsLayer_(True)
        div.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        parent.addSubview_(div)

    @objc.python_method
    def _add_row_label(self, parent, title, desc, y_center, w_label=240):
        """Creates a left-side setting label with bold title and description."""
        t_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y_center + 4, w_label, 22))
        t_lbl.setStringValue_(title)
        t_lbl.setFont_(AppKit.NSFont.systemFontOfSize_weight_(15.0, AppKit.NSFontWeightSemibold))
        t_lbl.setTextColor_(Theme.TEXT)
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        if desc:
            d_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y_center - 16, w_label, 18))
            d_lbl.setStringValue_(desc)
            d_lbl.setFont_(AppKit.NSFont.systemFontOfSize_weight_(12.0, AppKit.NSFontWeightRegular))
            d_lbl.setTextColor_(Theme.SUBTEXT0)
            d_lbl.setBezeled_(False)
            d_lbl.setDrawsBackground_(False)
            d_lbl.setEditable_(False)
            parent.addSubview_(d_lbl)

    @objc.python_method
    def _create_pill_chip(self, parent, title, tag, is_checked, action_name, x, y, width=54.0, height=26.0, accent_type="mauve"):
        """Creates a modern dark pill chip toggle button."""
        btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, width, height))
        btn.setButtonType_(AppKit.NSButtonTypePushOnPushOff)
        btn.setBordered_(False)
        btn.setWantsLayer_(True)
        btn.layer().setCornerRadius_(7.0)
        btn.layer().setMasksToBounds_(True)
        btn.setTag_(tag)
        btn.setTitle_(title)
        btn.setTarget_(self)
        btn.setAction_(action_name)
        btn.setState_(AppKit.NSControlStateValueOn if is_checked else AppKit.NSControlStateValueOff)
        self._update_pill_chip_style(btn, is_checked, accent_type)
        parent.addSubview_(btn)
        return btn

    @objc.python_method
    def _update_pill_chip_style(self, btn, is_checked, accent_type="mauve"):
        """Applies Catppuccin-themed active/inactive styling with smooth typography and colors."""
        if accent_type == "blue":
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.706, 0.980, 1.0) # #89b4fa
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.455, 0.780, 0.925, 1.0).CGColor() # #74c7ec
        elif accent_type == "peach":
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0) # #fab387
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0).CGColor()
        elif accent_type == "green":
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0) # #a6e3a1 Green
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0).CGColor()
        else:
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0) # #cba6f7
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0).CGColor()

        if is_checked:
            btn.layer().setBackgroundColor_(active_bg.CGColor())
            btn.layer().setBorderWidth_(1.0)
            btn.layer().setBorderColor_(border_col)
            fg_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.067, 0.067, 0.106, 1.0) # #11111b Crust
            font = AppKit.NSFont.boldSystemFontOfSize_(11.5)
        else:
            btn.layer().setBackgroundColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.15, 0.15, 0.22, 0.9).CGColor()) # #242438
            btn.layer().setBorderWidth_(1.0)
            btn.layer().setBorderColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.27, 0.28, 0.38, 0.85).CGColor()) # #45475a
            fg_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.80, 0.84, 0.96, 1.0) # #cdd6f4 Text
            font = AppKit.NSFont.systemFontOfSize_weight_(11.5, AppKit.NSFontWeightMedium)

        pstyle = AppKit.NSMutableParagraphStyle.alloc().init()
        pstyle.setAlignment_(AppKit.NSTextAlignmentCenter)
        attrs = {
            AppKit.NSFontAttributeName: font,
            AppKit.NSForegroundColorAttributeName: fg_color,
            AppKit.NSParagraphStyleAttributeName: pstyle
        }
        title_str = btn.title()
        attr_str = AppKit.NSAttributedString.alloc().initWithString_attributes_(title_str, attrs)
        btn.setAttributedTitle_(attr_str)

    @objc.python_method
    def _build_timing_section(self, card, w, h):
        self._add_section_header(
            card,
            "Notification Lead Times & Staged Reminders",
            "Select reminder alert windows to receive progressive notifications ahead of time.",
            h, w,
            icon_emoji="⏱️",
            badge_rgba=(0.96, 0.62, 0.04, 0.15),
            border_rgba=(0.0, 0.0, 0.0, 0.0)
        )

        # 0. Quick Preset Bar
        r0_y = h - 84.0
        self._add_row_label(card, "⚡ Quick Presets", "Apply curated reminder stage setups in 1 click", r0_y, 220)

        presets = [
            ("🧘 Relaxed", "onApplyPresetRelaxed:", 96.0),
            ("⚡ Standard", "onApplyPresetStandard:", 106.0),
            ("🚨 Intensive", "onApplyPresetIntensive:", 112.0)
        ]
        x_pre = 250.0
        for p_title, p_action, p_w in presets:
            p_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_pre, r0_y - 10, p_w, 26))
            p_btn.setButtonType_(AppKit.NSButtonTypeMomentaryPushIn)
            p_btn.setBordered_(False)
            p_btn.setWantsLayer_(True)
            p_btn.layer().setCornerRadius_(7.0)
            p_btn.layer().setBackgroundColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.18, 0.19, 0.28, 0.9).CGColor())
            p_btn.layer().setBorderWidth_(1.0)
            p_btn.layer().setBorderColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.35, 0.38, 0.52, 0.9).CGColor())
            p_btn.setTarget_(self)
            p_btn.setAction_(p_action)

            pstyle = AppKit.NSMutableParagraphStyle.alloc().init()
            pstyle.setAlignment_(AppKit.NSTextAlignmentCenter)
            attrs = {
                AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(11.5),
                AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.85, 0.88, 0.98, 1.0),
                AppKit.NSParagraphStyleAttributeName: pstyle
            }
            attr_str = AppKit.NSAttributedString.alloc().initWithString_attributes_(p_title, attrs)
            p_btn.setAttributedTitle_(attr_str)
            card.addSubview_(p_btn)
            x_pre += (p_w + 8.0)

        self._add_row_divider(card, h - 110.0, w)

        # 1. Video Meeting Stages
        r1_y = h - 142.0
        self._add_row_label(card, "📹 Video Meetings", "Alert ahead of meeting start (0m is always on)", r1_y, 220)

        curr_meeting_stages = set(self.config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        meeting_opts = [(30, "30m"), (20, "20m"), (15, "15m"), (10, "10m"), (5, "5m"), (2, "2m")]

        x_btn = 250.0
        for val, label in meeting_opts:
            btn_w = 58.0
            is_chk = val in curr_meeting_stages
            self._create_pill_chip(card, label, val, is_chk, "onToggleMeetingStage:", x_btn, r1_y - 10, btn_w, 26, "mauve")
            x_btn += (btn_w + 6.0)

        self._add_row_divider(card, h - 168.0, w)

        # 2. General Event Stages
        r2_y = h - 200.0
        self._add_row_label(card, "📅 General Events", "Alert ahead of start time (0m is always on)", r2_y, 220)

        curr_general_stages = set(self.config.get("general_reminder_stages", [20, 10, 5, 2, 0]))

        x_btn = 250.0
        for val, label in meeting_opts:
            btn_w = 58.0
            is_chk = val in curr_general_stages
            self._create_pill_chip(card, label, val, is_chk, "onToggleGeneralStage:", x_btn, r2_y - 10, btn_w, 26, "blue")
            x_btn += (btn_w + 6.0)

        self._add_row_divider(card, h - 226.0, w)

        # 3. Travel Stages (Before Departure Time)
        r3_y = h - 258.0
        self._add_row_label(card, "🚗 Travel & Trips", "Alert ahead of leave time (0m is always on)", r3_y, 220)

        curr_travel_stages = set(self.config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        travel_opts = [(60, "60m"), (45, "45m"), (30, "30m"), (15, "15m"), (5, "5m"), (2, "2m")]

        x_btn = 250.0
        for val, label in travel_opts:
            btn_w = 58.0
            is_chk = val in curr_travel_stages
            self._create_pill_chip(card, label, val, is_chk, "onToggleTravelStage:", x_btn, r3_y - 10, btn_w, 26, "peach")
            x_btn += (btn_w + 6.0)

        self._add_row_divider(card, h - 284.0, w)

        # 4. Snooze
        r4_y = h - 316.0
        snooze_val = self.config.get("default_snooze_seconds", 120) // 60
        self._add_row_label(card, "💤 Snooze Duration", "Interval delay when clicking Snooze on a banner", r4_y, 220)

        snooze_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(250, r4_y - 12, 260, 28), False)
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

    @objc.python_method
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

        curr_addr = str(self.config.get("home_address", "") or "")
        self.home_addr_field = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(265, r1_y - 10, 370, 26))
        self.home_addr_field.setStringValue_(curr_addr)
        self.home_addr_field.setPlaceholderString_("e.g. 24 Oxford Street, London or Piazza Castello, Torino")
        self.home_addr_field.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.home_addr_field.setTextColor_(Theme.TEXT)
        self.home_addr_field.setTarget_(self)
        self.home_addr_field.setAction_("onSaveHomeAddress:")
        self.home_addr_field.setWantsLayer_(True)
        self.home_addr_field.layer().setCornerRadius_(9.0)
        self.home_addr_field.setBackgroundColor_(Theme.MANTLE)
        self.home_addr_field.setDrawsBackground_(True)
        self.home_addr_field.layer().setBorderWidth_(1.0)
        self.home_addr_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        self.home_addr_field.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        card.addSubview_(self.home_addr_field)

        self.home_save_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(645, r1_y - 12, 85, 30))
        self.home_save_btn.setTitle_("💾 Save")
        self.home_save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        self.home_save_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        self.home_save_btn.setTarget_(self)
        self.home_save_btn.setAction_("onSaveHomeAddress:")
        if hasattr(self.home_save_btn, "setContentTintColor_"):
            self.home_save_btn.setContentTintColor_(Theme.SAPPHIRE)
        card.addSubview_(self.home_save_btn)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Preferred Transport Mode
        r2_y = h - 136.0
        self._add_row_label(card, "🚦 Transport Mode", "Default vehicle mode for route calculation", r2_y, 220)

        modes = ["transit", "automobile", "walking", "bicycling"]
        curr_mode = self.config.get("transport_mode", "transit")
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
        if hasattr(self.mode_segmented, "setSelectedSegmentBezelColor_"):
            self.mode_segmented.setSelectedSegmentBezelColor_(Theme.SAPPHIRE)
        card.addSubview_(self.mode_segmented)

        self._add_row_divider(card, h - 160.0, w)

        # 3. Departure Buffer
        r3_y = h - 188.0
        buf_val = self.config.get("eta_buffer_minutes", 10)
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

    @objc.python_method
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
        curr_mb_mode = self.config.get("menubar_status_mode", "countdown")
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
        if hasattr(mb_segmented, "setSelectedSegmentBezelColor_"):
            mb_segmented.setSelectedSegmentBezelColor_(Theme.MAUVE)
        card.addSubview_(mb_segmented)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Banner Position
        r2_y = h - 136.0
        self._add_row_label(card, "📍 Banner Position", "HUD screen location for taking off banner", r2_y, 220)

        pos_segmented = AppKit.NSSegmentedControl.alloc().initWithFrame_(AppKit.NSMakeRect(245, r2_y - 12, 260, 28))
        pos_segmented.setSegmentCount_(2)
        pos_segmented.setLabel_forSegment_("⬆️ Top (HUD)", 0)
        pos_segmented.setLabel_forSegment_("⬇️ Bottom", 1)
        curr_pos = self.config.get("banner_position", "top")
        pos_segmented.setSelectedSegment_(0 if curr_pos == "top" else 1)
        pos_segmented.setTarget_(self)
        pos_segmented.setAction_("onSelectBannerPosition:")
        if hasattr(pos_segmented, "setSelectedSegmentBezelColor_"):
            pos_segmented.setSelectedSegmentBezelColor_(Theme.BLUE)
        card.addSubview_(pos_segmented)

        self._add_row_divider(card, h - 160.0, w)

        # 3. Flight Speed
        r3_y = h - 188.0
        curr_spd = int(float(self.config.get("flight_speed", 3.2)) * 10)
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

    @objc.python_method
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
        sound_on = self.config.get("sound_enabled", True)
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
        curr_snd = self.config.get("sound_name", "Glass")

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
        if hasattr(play_btn, "setContentTintColor_"):
            play_btn.setContentTintColor_(Theme.SAPPHIRE)
        card.addSubview_(play_btn)

    @objc.python_method
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
            lbl.setTextColor_(Theme.SUBTEXT0)
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            card.addSubview_(lbl)
            return

        y_offset = h - 90.0
        x_offset = 18.0
        pill_h = 28.0

        for idx, cal in enumerate(cals):
            cal_name = cal.get("name", "Calendar")
            title = f"📅 {cal_name}"
            pill_w = max(120.0, min(240.0, len(cal_name) * 8.5 + 42.0))

            if x_offset + pill_w > w - 18.0:
                x_offset = 18.0
                y_offset -= (pill_h + 8.0)

            btn = self._create_pill_chip(
                card,
                title,
                idx,
                cal.get("enabled", True),
                "onToggleCalendarSource:",
                x_offset,
                y_offset,
                pill_w,
                pill_h,
                "green"
            )
            btn.setToolTip_(cal_name)
            x_offset += (pill_w + 8.0)

    @objc.python_method
    def _build_system_section(self, card, w, h):
        self._add_section_header(
            card,
            "System, Launch at Login & JSON Rules",
            "Manage macOS startup behavior, classification rules, and diagnostic logs.",
            h, w,
            icon_emoji="🛠️",
            badge_rgba=(0.1, 0.72, 0.85, 0.20),
            border_rgba=(0.1, 0.72, 0.85, 0.38)
        )

        # 1. Launch at macOS Login Switch
        r1_y = h - 84.0
        self.autostart_switch = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, r1_y - 10, 480, 24))
        self.autostart_switch.setButtonType_(AppKit.NSButtonTypeSwitch)
        self.autostart_switch.setTitle_("🚀 Launch QuakMeeting automatically at macOS login")
        self.autostart_switch.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        self.autostart_switch.setState_(AppKit.NSControlStateValueOn if is_autostart_enabled() else AppKit.NSControlStateValueOff)
        self.autostart_switch.setTarget_(self)
        self.autostart_switch.setAction_("onToggleAutostart:")
        card.addSubview_(self.autostart_switch)

        self._add_row_divider(card, h - 108.0, w)

        # 2. Action Buttons
        y = h - 150.0
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
        info_lbl.setTextColor_(Theme.SUBTEXT0)
        info_lbl.setBezeled_(False)
        info_lbl.setDrawsBackground_(False)
        info_lbl.setEditable_(False)
        card.addSubview_(info_lbl)

    @objc.python_method
    def _build_update_section(self, card, w, h):
        self._add_section_header(
            card,
            "Software Updates & Releases",
            "Keep QuakMeeting up to date with the latest features, mascottes, and security patches.",
            h, w,
            icon_emoji="🚀",
            badge_rgba=(0.02, 0.52, 0.78, 0.20),
            border_rgba=(0.02, 0.52, 0.78, 0.38)
        )

        y = h - 94.0
        btn_w = 180.0

        # Check for updates button
        check_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, btn_w, 32))
        check_btn.setTitle_("🔍 Check for Updates")
        check_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        check_btn.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        check_btn.setTarget_(self)
        check_btn.setAction_("onCheckForUpdatesMac:")
        card.addSubview_(check_btn)
        self.mac_check_update_btn = check_btn

        # Install update button (hidden by default unless update available)
        install_btn = AppKit.NSButton.alloc().initWithFrame_(AppKit.NSMakeRect(18 + btn_w + 14.0, y, 220, 32))
        install_btn.setTitle_("⚡ Install Update Now")
        install_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        install_btn.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        install_btn.setTarget_(self)
        install_btn.setAction_("onInstallUpdateMac:")
        install_btn.setHidden_(True)
        card.addSubview_(install_btn)
        self.mac_install_update_btn = install_btn

        # Status text field
        status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, 14, w - 36, 18))
        status_lbl.setStringValue_(f"QuakMeeting v{updater_service.current_version}  •  Ready")
        status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        status_lbl.setTextColor_(Theme.SUBTEXT0)
        status_lbl.setBezeled_(False)
        status_lbl.setDrawsBackground_(False)
        status_lbl.setEditable_(False)
        card.addSubview_(status_lbl)
        self.mac_update_status_lbl = status_lbl

        # Hook event_bus listeners to update labels/buttons on main thread
        def _on_mac_update_avail(tag_name=None, version=None, **k):
            v_name = tag_name or version or "New Version"
            def update_ui():
                if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                    self.mac_update_status_lbl.setStringValue_(f"🚀 Update Available: {v_name} (Current: v{updater_service.current_version})")
                    self.mac_update_status_lbl.setTextColor_(Theme.SAPPHIRE)
                if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
                    self.mac_install_update_btn.setTitle_(f"⚡ Install {v_name} Now")
                    self.mac_install_update_btn.setHidden_(False)
                if hasattr(self, 'mac_check_update_btn') and self.mac_check_update_btn:
                    self.mac_check_update_btn.setTitle_("🔍 Check for Updates")
                    self.mac_check_update_btn.setEnabled_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        def _on_mac_update_check_done(has_update=False, current_version=None, error=None, **k):
            def update_ui():
                if hasattr(self, 'mac_check_update_btn') and self.mac_check_update_btn:
                    self.mac_check_update_btn.setTitle_("🔍 Check for Updates")
                    self.mac_check_update_btn.setEnabled_(True)
                if not has_update:
                    if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                        if error:
                            self.mac_update_status_lbl.setStringValue_(f"⚠️ Update check error: {error[:60]}")
                            self.mac_update_status_lbl.setTextColor_(Theme.YELLOW)
                        else:
                            self.mac_update_status_lbl.setStringValue_(f"✨ You are up to date!  v{current_version or updater_service.current_version}")
                            self.mac_update_status_lbl.setTextColor_(Theme.GREEN)
                    if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
                        self.mac_install_update_btn.setHidden_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        def _on_mac_downloading(file_name=None, percent=None, **k):
            def update_ui():
                if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                    p_txt = f" ({percent}%)" if percent is not None else ""
                    self.mac_update_status_lbl.setStringValue_(f"📥 Downloading update package{p_txt}...")
                    self.mac_update_status_lbl.setTextColor_(Theme.PEACH)
                if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
                    self.mac_install_update_btn.setEnabled_(False)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        def _on_mac_downloaded(**k):
            def update_ui():
                if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                    self.mac_update_status_lbl.setStringValue_("⚙️ Installing update package & replacing /Applications/QuakMeeting.app...")
                    self.mac_update_status_lbl.setTextColor_(Theme.BLUE)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        def _on_mac_installed(**k):
            def update_ui():
                if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                    self.mac_update_status_lbl.setStringValue_("🎉 Update installed successfully! Relaunching QuakMeeting...")
                    self.mac_update_status_lbl.setTextColor_(Theme.GREEN)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        def _on_mac_failed(error=None, **k):
            def update_ui():
                if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                    self.mac_update_status_lbl.setStringValue_(f"❌ Update failed: {error or 'Unknown error'}")
                    self.mac_update_status_lbl.setTextColor_(Theme.RED)
                if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
                    self.mac_install_update_btn.setTitle_("🔄 Try Again")
                    self.mac_install_update_btn.setEnabled_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        event_bus.subscribe("UPDATE_AVAILABLE", _on_mac_update_avail)
        event_bus.subscribe("UPDATE_CHECK_COMPLETE", _on_mac_update_check_done)
        event_bus.subscribe("UPDATE_DOWNLOADING", _on_mac_downloading)
        event_bus.subscribe("UPDATE_DOWNLOAD_PROGRESS", _on_mac_downloading)
        event_bus.subscribe("UPDATE_DOWNLOADED", _on_mac_downloaded)
        event_bus.subscribe("UPDATE_INSTALLED", _on_mac_installed)
        event_bus.subscribe("UPDATE_FAILED", _on_mac_failed)

        # Check if already available on load
        if updater_service.latest_release_info and updater_service.latest_release_info.get("has_update"):
            _on_mac_update_avail(**updater_service.latest_release_info)

    def onCheckForUpdatesMac_(self, sender):
        if hasattr(self, 'mac_check_update_btn') and self.mac_check_update_btn:
            self.mac_check_update_btn.setTitle_("⏳ Checking...")
            self.mac_check_update_btn.setEnabled_(False)
        if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
            self.mac_update_status_lbl.setStringValue_("Checking for new releases on GitHub...")
        updater_service.check_for_updates(background=True)

    def onInstallUpdateMac_(self, sender):
        if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
            self.mac_install_update_btn.setTitle_("⏳ Preparing...")
            self.mac_install_update_btn.setEnabled_(False)
        updater_service.download_and_install_update(background=True)

    # Setting Handlers
    @objc.IBAction
    def onApplyPresetRelaxed_(self, sender):
        self.config.set("meeting_reminder_stages", [15, 5, 0])
        self.config.set("general_reminder_stages", [15, 5, 0])
        self.config.set("travel_reminder_stages", [30, 15, 0])
        self.refresh_data(force=True)

    @objc.IBAction
    def onApplyPresetStandard_(self, sender):
        self.config.set("meeting_reminder_stages", [20, 10, 5, 2, 0])
        self.config.set("general_reminder_stages", [20, 10, 5, 2, 0])
        self.config.set("travel_reminder_stages", [45, 30, 15, 5, 2, 0])
        self.refresh_data(force=True)

    @objc.IBAction
    def onApplyPresetIntensive_(self, sender):
        self.config.set("meeting_reminder_stages", [30, 20, 15, 10, 5, 2, 0])
        self.config.set("general_reminder_stages", [30, 20, 15, 10, 5, 2, 0])
        self.config.set("travel_reminder_stages", [60, 45, 30, 15, 5, 2, 0])
        self.refresh_data(force=True)

    @objc.IBAction
    def onToggleMeetingStage_(self, sender):
        val = sender.tag()
        curr = set(self.config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on:
            curr.add(val)
        else:
            curr.discard(val)
        curr.add(0)
        self.config.set("meeting_reminder_stages", sorted(list(curr), reverse=True))
        self._update_pill_chip_style(sender, is_on, "mauve")

    @objc.IBAction
    def onToggleGeneralStage_(self, sender):
        val = sender.tag()
        curr = set(self.config.get("general_reminder_stages", [20, 10, 5, 2, 0]))
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on:
            curr.add(val)
        else:
            curr.discard(val)
        curr.add(0)
        self.config.set("general_reminder_stages", sorted(list(curr), reverse=True))
        self._update_pill_chip_style(sender, is_on, "blue")

    @objc.IBAction
    def onToggleTravelStage_(self, sender):
        val = sender.tag()
        curr = set(self.config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on:
            curr.add(val)
        else:
            curr.discard(val)
        curr.add(0)
        self.config.set("travel_reminder_stages", sorted(list(curr), reverse=True))
        self._update_pill_chip_style(sender, is_on, "peach")

    @objc.IBAction
    def onSaveHomeAddress_(self, sender):
        if hasattr(self, 'home_addr_field') and self.home_addr_field:
            addr = str(self.home_addr_field.stringValue() or "").strip()
            self.config.set("home_address", addr)
            if hasattr(self, 'home_save_btn') and self.home_save_btn:
                self.home_save_btn.setTitle_("✓ Saved")
                def reset_btn():
                    time.sleep(1.5)
                    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(lambda: self.home_save_btn.setTitle_("💾 Save"))
                threading.Thread(target=reset_btn, daemon=True).start()
            self.refresh_data(force=True)

    @objc.IBAction
    def onSelectTransportMode_(self, sender):
        modes = ["transit", "automobile", "walking", "bicycling"]
        idx = sender.selectedSegment()
        if 0 <= idx < len(modes):
            self.config.set("transport_mode", modes[idx])
            try:
                event_bus.publish("CONFIG_CHANGED", key="transport_mode", value=modes[idx])
            except Exception:
                pass
            self.refresh_data(force=True)

    @objc.IBAction
    def onSelectETABuffer_(self, sender):
        val_buf = sender.selectedItem().representedObject()
        self.config.set("eta_buffer_minutes", int(val_buf))
        self.refresh_data(force=True)

    @objc.IBAction
    def onToggleCalendarSource_(self, sender):
        cal_name = sender.toolTip() or sender.title().replace("📅 ", "")
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        self._update_pill_chip_style(sender, is_on, "green")
        ignored = set(self.config.get("ignored_calendars", []))
        if is_on:
            ignored.discard(cal_name)
        else:
            ignored.add(cal_name)
        self.config.set("ignored_calendars", list(ignored))
        for cal in self.cached_calendars:
            if cal.get("name") == cal_name:
                cal["enabled"] = is_on
        self.refresh_data(force=True)

    @objc.IBAction
    def onSelectSnoozeDuration_(self, sender):
        val_min = sender.selectedItem().representedObject()
        self.config.set("default_snooze_seconds", int(val_min) * 60)

    @objc.IBAction
    def onSelectMenuBarMode_(self, sender):
        modes = ["countdown", "event_time", "time_only", "icon_only"]
        sel = sender.selectedSegment()
        if 0 <= sel < len(modes):
            self.config.set("menubar_status_mode", modes[sel])
            try:
                event_bus.publish("CONFIG_CHANGED", key="menubar_status_mode")
            except Exception:
                pass

    @objc.IBAction
    def onSelectBannerPosition_(self, sender):
        pos = "top" if sender.selectedSegment() == 0 else "bottom"
        self.config.set("banner_position", pos)

    @objc.IBAction
    def onSelectFlightSpeed_(self, sender):
        spd_tag = sender.selectedItem().representedObject()
        self.config.set("flight_speed", float(spd_tag) / 10.0)

    @objc.IBAction
    def onToggleSoundEnabled_(self, sender):
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        self.config.set("sound_enabled", is_on)

    @objc.IBAction
    def onSelectSound_(self, sender):
        snd_name = sender.selectedItem().representedObject()
        self.config.set("sound_name", str(snd_name))
        self.config.set("sound_enabled", True)
        if hasattr(self, 'sound_switch') and self.sound_switch:
            self.sound_switch.setState_(AppKit.NSControlStateValueOn)
        self.onPlaySoundPreview_(None)

    @objc.IBAction
    def onPlaySoundPreview_(self, sender):
        snd_name = self.config.get("sound_name", "Glass")
        try:
            import subprocess
            subprocess.Popen(["afplay", f"/System/Library/Sounds/{snd_name}.aiff"])
        except Exception:
            pass

    @objc.IBAction
    def onOpenConfigEditor_(self, sender):
        self.config.open_config_in_editor()

    @objc.IBAction
    def onReloadConfig_(self, sender):
        self.config.reload()
        self.refresh_data(force=True)

    @objc.IBAction
    def onOpenLogs_(self, sender):
        open_log_file()

    @objc.IBAction
    def onOpenLogFolder_(self, sender):
        open_log_folder()

    @objc.IBAction
    def onToggleAutostart_(self, sender):
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on:
            success = enable_autostart()
            if not success:
                sender.setState_(AppKit.NSControlStateValueOff)
        else:
            success = disable_autostart()
            if not success:
                sender.setState_(AppKit.NSControlStateValueOn)

