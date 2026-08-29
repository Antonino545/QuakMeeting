import AppKit
import objc
import os
import time
import threading
from core.services.calendar_service import calendar_service
from core.services.event_bus import event_bus
from core.services.updater_service import updater_service
from core.services.config_service import is_debug_mode
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from core.logger import open_log_file, open_log_folder
from ui.macos.theme import Theme, ModernButton, ModernToggleSwitch

class SettingsTabController(AppKit.NSObject):
    def init(self):
        self = objc.super(SettingsTabController, self).init()
        self.dashboard_controller = None
        self.config = None
        self.cached_calendars = []
        self._cached_view = None
        self._cached_sig = None
        return self

    @objc.python_method
    def invalidate_cache(self):
        self._cached_view = None
        self._cached_sig = None

    @objc.python_method
    def refresh_data(self, force=False):
        if self.dashboard_controller and hasattr(self.dashboard_controller, 'refresh_data'):
            self.dashboard_controller.refresh_data(force=force)

    @objc.python_method
    def render(self, container, w, h, config, cached_calendars):
        self.dashboard_controller = container
        self.config = config
        self.cached_calendars = cached_calendars
        
        cals_count = len(cached_calendars or [])
        sig = (round(w), round(h), cals_count)
        if self._cached_view is not None and self._cached_sig == sig:
            return self._cached_view

        view = self._render_settings_tab(w, h)
        self._cached_view = view
        self._cached_sig = sig
        return view

    # -------------------------------------------------------------
    # TAB 3: PREFERENCES & TIMING SETTINGS (Exact Qt Design Match)
    # -------------------------------------------------------------
    @objc.python_method
    def _render_settings_tab(self, w, h):
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setAutohidesScrollers_(True)

        card_w = w - 16.0
        gap = 14.0

        c1_h = 362.0  # Notification Lead Times & Staged Reminders
        c2_h = 246.0  # Home / Departure Address & Multi-Modal Route ETA

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
        c4_h = 246.0  # System & Diagnostics

        content_h = c1_h + c2_h + c3_h + c4_h + gap * 5 + 20.0
        doc_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, content_h))

        curr_y = content_h - gap

        # CARD 1: TIMING & MULTI-STAGE NOTIFICATIONS
        curr_y -= c1_h
        card1 = self._create_card_container(0, curr_y, card_w, c1_h)
        self._build_timing_card(card1, card_w, c1_h)
        doc_view.addSubview_(card1)

        # CARD 2: DEPARTURE ADDRESS & MULTI-MODAL ROUTE ETA
        curr_y -= (c2_h + gap)
        card2 = self._create_card_container(0, curr_y, card_w, c2_h)
        self._build_eta_card(card2, card_w, c2_h)
        doc_view.addSubview_(card2)

        # CARD 3: INCLUDED SYSTEM CALENDARS
        curr_y -= (c3_h + gap)
        card3 = self._create_card_container(0, curr_y, card_w, c3_h)
        self._build_calendars_card(card3, card_w, c3_h, cals)
        doc_view.addSubview_(card3)

        # CARD 4: SYSTEM & DIAGNOSTICS
        curr_y -= (c4_h + gap)
        card4 = self._create_card_container(0, curr_y, card_w, c4_h)
        self._build_system_card(card4, card_w, c4_h)
        doc_view.addSubview_(card4)

        scroll_view.setDocumentView_(doc_view)
        if scroll_view.contentView():
            scroll_view.contentView().scrollToPoint_(AppKit.NSMakePoint(0, content_h - h))
        return scroll_view

    @objc.python_method
    def _create_card_container(self, x, y, w, h):
        """Creates a solid card container with Catppuccin Mocha styling."""
        card = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, w, h))
        card.setWantsLayer_(True)
        card.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        card.layer().setCornerRadius_(12.0)
        card.layer().setMasksToBounds_(True)
        card.layer().setBorderWidth_(1.0)
        card.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        return card

    @objc.python_method
    def _add_section_header(self, parent, title, subtitle, h, w):
        """Qt-matching section header: clean bold title with emoji, subtitle underneath."""
        t_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 34, w - 36, 22))
        t_lbl.setStringValue_(title)
        t_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14.5))
        t_lbl.setTextColor_(Theme.TEXT)
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        if subtitle:
            s_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 52, w - 36, 16))
            s_lbl.setStringValue_(subtitle)
            s_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            s_lbl.setTextColor_(Theme.SUBTEXT0)
            s_lbl.setBezeled_(False)
            s_lbl.setDrawsBackground_(False)
            s_lbl.setEditable_(False)
            parent.addSubview_(s_lbl)

    @objc.python_method
    def _add_hairline_divider(self, parent, y, w):
        """Adds a subtle inner hairline divider matching Qt #313244."""
        div = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, y, w - 36, 1))
        div.setWantsLayer_(True)
        div.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        parent.addSubview_(div)

    @objc.python_method
    def _create_pill_chip(self, parent, title, tag, is_checked, action_name, x, y, width=52.0, height=26.0, accent_type="mauve"):
        """Creates a modern pill chip toggle button matching Qt."""
        btn = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, width, height))
        btn.setButtonType_(AppKit.NSButtonTypePushOnPushOff)
        btn.setBordered_(False)
        btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
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
        """Applies Catppuccin active/inactive styling matching Qt."""
        if accent_type == "blue":
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.706, 0.980, 1.0)  # #89b4fa
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.706, 0.980, 1.0).CGColor()
        elif accent_type == "peach":
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0)  # #fab387
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0).CGColor()
        elif accent_type == "green":
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0)  # #a6e3a1
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0).CGColor()
        else:
            active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0)  # #cba6f7
            border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0).CGColor()

        if is_checked:
            btn.layer().setBackgroundColor_(active_bg.CGColor())
            btn.layer().setBorderWidth_(1.0)
            btn.layer().setBorderColor_(border_col)
            fg_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.067, 0.067, 0.106, 1.0)  # #11111b Crust
            font = AppKit.NSFont.boldSystemFontOfSize_(11.5)
        else:
            btn.layer().setBackgroundColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.141, 0.141, 0.220, 1.0).CGColor())  # #242438
            btn.layer().setBorderWidth_(1.0)
            btn.layer().setBorderColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.271, 0.278, 0.353, 1.0).CGColor())  # #45475a
            fg_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.804, 0.839, 0.957, 1.0)  # #cdd6f4
            font = AppKit.NSFont.systemFontOfSize_weight_(11.5, AppKit.NSFontWeightMedium)

        pstyle = AppKit.NSMutableParagraphStyle.alloc().init()
        pstyle.setAlignment_(AppKit.NSTextAlignmentCenter)
        attrs = {
            AppKit.NSFontAttributeName: font,
            AppKit.NSForegroundColorAttributeName: fg_color,
            AppKit.NSParagraphStyleAttributeName: pstyle
        }
        title_str = btn.title() or ""
        attr_str = AppKit.NSAttributedString.alloc().initWithString_attributes_(title_str, attrs)
        btn.setAttributedTitle_(attr_str)

    # ── CARD 1: TIMING & STAGES ───────────────────────────────────────────
    @objc.python_method
    def _build_timing_card(self, card, w, h):
        self._add_section_header(
            card,
            "⏱️ Notification Lead Times & Staged Reminders",
            "Select reminder alert windows to receive progressive notifications ahead of time.",
            h, w
        )

        # Quick Presets Row
        pre_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 84, 110, 20))
        pre_lbl.setStringValue_("⚡ Quick Presets:")
        pre_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        pre_lbl.setTextColor_(Theme.SUBTEXT0)
        pre_lbl.setBezeled_(False)
        pre_lbl.setDrawsBackground_(False)
        pre_lbl.setEditable_(False)
        card.addSubview_(pre_lbl)

        presets = [
            ("🧘 Relaxed", "onApplyPresetRelaxed:", 92.0),
            ("⚡ Standard", "onApplyPresetStandard:", 98.0),
            ("🚨 Intensive", "onApplyPresetIntensive:", 104.0)
        ]
        x_pre = 135.0
        for p_title, p_action, p_w in presets:
            p_btn = Theme.create_button(
                AppKit.NSMakeRect(x_pre, h - 86, p_w, 24),
                title=p_title,
                bg_color=AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.141, 0.141, 0.220, 1.0),
                text_color=Theme.TEXT,
                border_color=Theme.SURFACE1,
                corner_radius=7.0,
                font_size=11.5,
                bold=True
            )
            p_btn.setTarget_(self)
            p_btn.setAction_(p_action)
            card.addSubview_(p_btn)
            x_pre += (p_w + 8.0)

        self._add_hairline_divider(card, h - 100, w)

        self.meeting_stage_chips = []
        self.general_stage_chips = []
        self.travel_stage_chips = []

        meeting_opts = [(30, "30m"), (20, "20m"), (15, "15m"), (10, "10m"), (5, "5m"), (2, "2m")]
        travel_opts = [(60, "60m"), (45, "45m"), (30, "30m"), (15, "15m"), (5, "5m"), (2, "2m")]

        # 1. Video Meetings
        def _add_sub_header(title, desc, y_t, y_d):
            t = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y_t, w - 36, 18))
            t.setStringValue_(title)
            t.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
            t.setTextColor_(Theme.TEXT)
            t.setBezeled_(False)
            t.setDrawsBackground_(False)
            t.setEditable_(False)
            card.addSubview_(t)

            d = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, y_d, w - 36, 16))
            d.setStringValue_(desc)
            d.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
            d.setTextColor_(Theme.SUBTEXT0)
            d.setBezeled_(False)
            d.setDrawsBackground_(False)
            d.setEditable_(False)
            card.addSubview_(d)

        # Video Meetings Row
        _add_sub_header("📹 Video Meetings", "Alert ahead of meeting start (0m is always on)", h - 124, h - 140)
        curr_meeting_stages = set(self.config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        x_chip = 18.0
        for val, label in meeting_opts:
            chip = self._create_pill_chip(card, label, val, val in curr_meeting_stages, "onToggleMeetingStage:", x_chip, h - 172, 54.0, 26.0, "mauve")
            self.meeting_stage_chips.append(chip)
            x_chip += 60.0

        self._add_hairline_divider(card, h - 184, w)

        # General Events Row
        _add_sub_header("📅 General Events", "Alert ahead of start time (0m is always on)", h - 208, h - 224)
        curr_general_stages = set(self.config.get("general_reminder_stages", [20, 10, 5, 2, 0]))
        x_chip = 18.0
        for val, label in meeting_opts:
            chip = self._create_pill_chip(card, label, val, val in curr_general_stages, "onToggleGeneralStage:", x_chip, h - 256, 54.0, 26.0, "blue")
            self.general_stage_chips.append(chip)
            x_chip += 60.0

        self._add_hairline_divider(card, h - 268, w)

        # Travel & Trips Row
        _add_sub_header("🚗 Travel & Trips", "Alert ahead of leave time (0m is always on)", h - 292, h - 308)
        curr_travel_stages = set(self.config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        x_chip = 18.0
        for val, label in travel_opts:
            chip = self._create_pill_chip(card, label, val, val in curr_travel_stages, "onToggleTravelStage:", x_chip, h - 340, 54.0, 26.0, "peach")
            self.travel_stage_chips.append(chip)
            x_chip += 60.0

    # ── CARD 2: DEPARTURE ADDRESS & MULTI-MODAL ROUTE ETA ─────────────────
    @objc.python_method
    def _build_eta_card(self, card, w, h):
        self._add_section_header(
            card,
            "📍 Home / Departure Address & Multi-Modal Route ETA",
            "Calculates real-time travel duration and departure times for Public Transit, Driving, Walking, or Cycling.",
            h, w
        )

        # 1. Starting Address (Origin)
        t1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 74, w - 36, 18))
        t1.setStringValue_("🏠 Starting Address (Origin)")
        t1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t1.setTextColor_(Theme.TEXT)
        t1.setBezeled_(False)
        t1.setDrawsBackground_(False)
        t1.setEditable_(False)
        card.addSubview_(t1)

        curr_addr = str(self.config.get("home_address", "") or "")
        field_w = w - 36.0 - 146.0
        self.home_addr_field = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 108, field_w, 28))
        self.home_addr_field.setStringValue_(curr_addr)
        self.home_addr_field.setPlaceholderString_("e.g. Piazza Castello, Torino or Via Roma, Torino")
        self.home_addr_field.setFont_(AppKit.NSFont.systemFontOfSize_(12))
        self.home_addr_field.setTextColor_(Theme.TEXT)
        self.home_addr_field.setTarget_(self)
        self.home_addr_field.setAction_("onSaveHomeAddress:")
        self.home_addr_field.setWantsLayer_(True)
        self.home_addr_field.layer().setCornerRadius_(8.0)
        self.home_addr_field.setBackgroundColor_(Theme.CRUST)
        self.home_addr_field.setDrawsBackground_(True)
        self.home_addr_field.layer().setBorderWidth_(1.0)
        self.home_addr_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        self.home_addr_field.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        card.addSubview_(self.home_addr_field)

        self.home_save_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(18 + field_w + 8.0, h - 108, 138.0, 28.0),
            title="💾 Save Location",
            start_color=Theme.GREEN,
            end_color=Theme.TEAL,
            text_color=Theme.CRUST,
            corner_radius=8.0,
            font_size=12.0,
            bold=True
        )
        self.home_save_btn.setTarget_(self)
        self.home_save_btn.setAction_("onSaveHomeAddress:")
        card.addSubview_(self.home_save_btn)

        # 2. Transport Mode for Route Calculation
        t2 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 138, w - 36, 18))
        t2.setStringValue_("🚦 Transport Mode for Route Calculation")
        t2.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t2.setTextColor_(Theme.TEXT)
        t2.setBezeled_(False)
        t2.setDrawsBackground_(False)
        t2.setEditable_(False)
        card.addSubview_(t2)

        modes = [
            ("transit", "🚆 Public Transit"),
            ("automobile", "🚗 Driving"),
            ("bicycling", "🚲 Cycling"),
            ("walking", "🚶 Walking")
        ]
        curr_mode = self.config.get("transport_mode", "transit")
        self.mode_buttons = {}
        x_m = 18.0
        btn_m_w = (w - 36.0 - 24.0) / 4.0

        for m_key, m_label in modes:
            m_btn = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_m, h - 176, btn_m_w, 30))
            m_btn.setTitle_(m_label)
            m_btn.setWantsLayer_(True)
            m_btn.setBordered_(False)
            m_btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
            m_btn.setButtonType_(AppKit.NSButtonTypeMomentaryPushIn)
            m_btn.layer().setCornerRadius_(8.0)
            m_btn.layer().setMasksToBounds_(True)
            m_btn.setTarget_(self)
            m_btn.setAction_("onSelectModeBtn:")
            self.mode_buttons[m_key] = m_btn
            card.addSubview_(m_btn)
            x_m += (btn_m_w + 8.0)

        self._update_transport_mode_buttons_ui(curr_mode)

        # 3. Departure Buffer Margin
        t3 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 216, w - 240, 18))
        t3.setStringValue_("⏳ Departure Buffer Margin (station transit / parking time):")
        t3.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t3.setTextColor_(Theme.TEXT)
        t3.setBezeled_(False)
        t3.setDrawsBackground_(False)
        t3.setEditable_(False)
        card.addSubview_(t3)

        buf_val = self.config.get("eta_buffer_minutes", 10)
        self.buf_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(w - 240, h - 220, 222, 26), False)
        self.buf_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.buf_popup.setTarget_(self)
        self.buf_popup.setAction_("onSelectETABuffer:")
        for opt_title, opt_val in [
            ("5 minutes", 5), ("10 minutes (Recommended)", 10), ("15 minutes", 15), ("20 minutes", 20)
        ]:
            item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(opt_title, None, "")
            item.setRepresentedObject_(opt_val)
            self.buf_popup.menu().addItem_(item)
            if opt_val == buf_val:
                self.buf_popup.selectItem_(item)
        card.addSubview_(self.buf_popup)

    @objc.python_method
    def _update_transport_mode_buttons_ui(self, active_mode):
        for k, btn in getattr(self, "mode_buttons", {}).items():
            is_active = (k == active_mode)
            if is_active:
                btn.layer().setBackgroundColor_(Theme.SAPPHIRE.CGColor())
                btn.layer().setBorderWidth_(1.0)
                btn.layer().setBorderColor_(Theme.SKY.CGColor())
                fg = Theme.CRUST
                fnt = AppKit.NSFont.boldSystemFontOfSize_(12.0)
            else:
                btn.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
                btn.layer().setBorderWidth_(1.0)
                btn.layer().setBorderColor_(Theme.SURFACE1.CGColor())
                fg = Theme.SUBTEXT1
                fnt = AppKit.NSFont.systemFontOfSize_weight_(12.0, AppKit.NSFontWeightMedium)

            pstyle = AppKit.NSMutableParagraphStyle.alloc().init()
            pstyle.setAlignment_(AppKit.NSTextAlignmentCenter)
            attrs = {
                AppKit.NSFontAttributeName: fnt,
                AppKit.NSForegroundColorAttributeName: fg,
                AppKit.NSParagraphStyleAttributeName: pstyle
            }
            attr_title = AppKit.NSAttributedString.alloc().initWithString_attributes_(btn.title() or "", attrs)
            btn.setAttributedTitle_(attr_title)

    # ── CARD 3: INCLUDED SYSTEM CALENDARS ─────────────────────────────────
    @objc.python_method
    def _build_calendars_card(self, card, w, h, cals=None):
        self._add_section_header(
            card,
            "📅 Included macOS Calendars",
            "Select which local, iCloud, or Google calendars to actively monitor for reminders.",
            h, w
        )

        if cals is None:
            cals = self.cached_calendars if self.cached_calendars else calendar_service.get_available_calendars()

        if not cals:
            lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 86, w - 36, 22))
            lbl.setStringValue_("All calendar sources are currently monitored.")
            lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12))
            lbl.setTextColor_(Theme.SUBTEXT0)
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            card.addSubview_(lbl)
            return

        pill_h = 28.0
        pill_gap = 8.0
        y_offset = h - 72.0 - pill_h
        x_offset = 18.0

        for idx, cal in enumerate(cals):
            cal_name = cal.get("name", "Calendar")
            title = f"📅 {cal_name}"
            pill_w = max(110.0, min(240.0, len(cal_name) * 8.5 + 42.0))

            if x_offset > 18.0 and x_offset + pill_w > w - 18.0:
                x_offset = 18.0
                y_offset -= (pill_h + pill_gap)

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
            x_offset += (pill_w + pill_gap)

    # ── CARD 4: SYSTEM & DIAGNOSTICS ──────────────────────────────────────
    @objc.python_method
    def _build_system_card(self, card, w, h):
        self._add_section_header(
            card,
            "⚙️ System & Diagnostics",
            "",
            h, w
        )

        # 1. Autostart toggle row
        auto_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 64, w - 80, 20))
        auto_lbl.setStringValue_("🚀 Launch QuakMeeting automatically at macOS login")
        auto_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13.0))
        auto_lbl.setTextColor_(Theme.TEXT)
        auto_lbl.setBezeled_(False)
        auto_lbl.setDrawsBackground_(False)
        auto_lbl.setEditable_(False)
        card.addSubview_(auto_lbl)

        self.autostart_sw = ModernToggleSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(w - 62, h - 66, 44, 24))
        self.autostart_sw.setChecked_(is_autostart_enabled())
        self.autostart_sw.setCallback_(self.onToggleAutostartSwitch)
        card.addSubview_(self.autostart_sw)

        # 2. Debug mode toggle row
        dbg_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 98, w - 80, 20))
        dbg_lbl.setStringValue_("🐛 Enable Developer & Debug Diagnostics Mode")
        dbg_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(13.0))
        dbg_lbl.setTextColor_(Theme.TEXT)
        dbg_lbl.setBezeled_(False)
        dbg_lbl.setDrawsBackground_(False)
        dbg_lbl.setEditable_(False)
        card.addSubview_(dbg_lbl)

        self.debug_sw = ModernToggleSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(w - 62, h - 100, 44, 24))
        self.debug_sw.setChecked_(is_debug_mode())
        self.debug_sw.setCallback_(self.onToggleDebugSwitch)
        card.addSubview_(self.debug_sw)

        # 3. Action Buttons Row
        y_btns = h - 146.0
        btn_w = (w - 36.0 - 24.0) / 4.0

        self.mac_check_update_btn = Theme.create_button(
            AppKit.NSMakeRect(18, y_btns, btn_w, 30),
            title="🔍 Check for Updates",
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=7.0,
            font_size=11.5,
            bold=True
        )
        self.mac_check_update_btn.setTarget_(self)
        self.mac_check_update_btn.setAction_("onCheckForUpdatesMac:")
        card.addSubview_(self.mac_check_update_btn)

        edit_btn = Theme.create_button(
            AppKit.NSMakeRect(18 + (btn_w + 8.0) * 1, y_btns, btn_w, 30),
            title="📝 Edit Config JSON",
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=7.0,
            font_size=11.5
        )
        edit_btn.setTarget_(self)
        edit_btn.setAction_("onOpenConfigEditor:")
        card.addSubview_(edit_btn)

        view_logs_btn = Theme.create_button(
            AppKit.NSMakeRect(18 + (btn_w + 8.0) * 2, y_btns, btn_w, 30),
            title="📄 View Live Log File",
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=7.0,
            font_size=11.5
        )
        view_logs_btn.setTarget_(self)
        view_logs_btn.setAction_("onOpenLogs:")
        card.addSubview_(view_logs_btn)

        folder_btn = Theme.create_button(
            AppKit.NSMakeRect(18 + (btn_w + 8.0) * 3, y_btns, btn_w, 30),
            title="📂 Log Folder",
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=7.0,
            font_size=11.5
        )
        folder_btn.setTarget_(self)
        folder_btn.setAction_("onOpenLogFolder:")
        card.addSubview_(folder_btn)

        # 4. Animated Update Card Status Container
        update_box = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, 14, w - 36, 48))
        update_box.setWantsLayer_(True)
        update_box.layer().setBackgroundColor_(Theme.BASE.CGColor())
        update_box.layer().setCornerRadius_(10.0)
        update_box.layer().setMasksToBounds_(True)
        update_box.layer().setBorderWidth_(1.0)
        update_box.layer().setBorderColor_(Theme.SURFACE0.CGColor())

        self.mac_update_icon = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(14, 12, 28, 24))
        self.mac_update_icon.setStringValue_("🦆")
        self.mac_update_icon.setFont_(AppKit.NSFont.systemFontOfSize_(18))
        self.mac_update_icon.setBezeled_(False)
        self.mac_update_icon.setDrawsBackground_(False)
        self.mac_update_icon.setEditable_(False)
        update_box.addSubview_(self.mac_update_icon)

        self.mac_update_status_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(46, 14, w - 240, 20))
        self.mac_update_status_lbl.setStringValue_(f"QuakMeeting v{updater_service.current_version}  •  Ready")
        self.mac_update_status_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12.5))
        self.mac_update_status_lbl.setTextColor_(Theme.TEXT)
        self.mac_update_status_lbl.setBezeled_(False)
        self.mac_update_status_lbl.setDrawsBackground_(False)
        self.mac_update_status_lbl.setEditable_(False)
        update_box.addSubview_(self.mac_update_status_lbl)

        self.mac_install_update_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(w - 36 - 190, 8, 176, 32),
            title="⚡ Install Update Now",
            start_color=Theme.SAPPHIRE,
            end_color=Theme.BLUE,
            text_color=Theme.CRUST,
            corner_radius=8.0,
            font_size=12.0,
            bold=True
        )
        self.mac_install_update_btn.setTarget_(self)
        self.mac_install_update_btn.setAction_("onInstallUpdateMac:")
        self.mac_install_update_btn.setHidden_(True)
        update_box.addSubview_(self.mac_install_update_btn)

        card.addSubview_(update_box)

        # Hook event_bus listeners
        self._subscribe_update_events()

    @objc.python_method
    def _subscribe_update_events(self):
        def _on_mac_update_avail(tag_name=None, version=None, **k):
            v_name = tag_name or version or "New Version"
            def update_ui():
                if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
                    self.mac_update_status_lbl.setStringValue_(f"Update Available: {v_name} (Current: v{updater_service.current_version})")
                    self.mac_update_status_lbl.setTextColor_(Theme.SAPPHIRE)
                if hasattr(self, 'mac_update_icon') and self.mac_update_icon:
                    self.mac_update_icon.setStringValue_("🚀")
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
                            self.mac_update_status_lbl.setStringValue_(f"Update check error: {error[:60]}")
                            self.mac_update_status_lbl.setTextColor_(Theme.RED)
                            if hasattr(self, 'mac_update_icon') and self.mac_update_icon:
                                self.mac_update_icon.setStringValue_("⚠️")
                        else:
                            self.mac_update_status_lbl.setStringValue_(f"You are on the latest version!  v{current_version or updater_service.current_version}")
                            self.mac_update_status_lbl.setTextColor_(Theme.GREEN)
                            if hasattr(self, 'mac_update_icon') and self.mac_update_icon:
                                self.mac_update_icon.setStringValue_("✨")
                    if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
                        self.mac_install_update_btn.setHidden_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(update_ui)

        event_bus.subscribe("UPDATE_AVAILABLE", _on_mac_update_avail)
        event_bus.subscribe("UPDATE_CHECK_COMPLETE", _on_mac_update_check_done)

    # ── ACTION HANDLERS ───────────────────────────────────────────────────
    @objc.python_method
    def onToggleAutostartSwitch(self, is_on):
        if is_on:
            success = enable_autostart()
            if not success and hasattr(self, 'autostart_sw'):
                self.autostart_sw.setChecked_(False)
        else:
            success = disable_autostart()
            if not success and hasattr(self, 'autostart_sw'):
                self.autostart_sw.setChecked_(True)

    @objc.python_method
    def onToggleDebugSwitch(self, is_on):
        self.config.set("debug_mode", is_on)

    @objc.IBAction
    def onSelectModeBtn_(self, sender):
        for k, btn in getattr(self, "mode_buttons", {}).items():
            if btn == sender:
                self.config.set("transport_mode", k)
                self._update_transport_mode_buttons_ui(k)
                try:
                    event_bus.publish("CONFIG_CHANGED", key="transport_mode", value=k)
                except Exception:
                    pass
                self.refresh_data(force=True)
                break

    @objc.python_method
    def _refresh_stage_chips_ui(self):
        meeting_stages = set(self.config.get("meeting_reminder_stages", []))
        for btn in getattr(self, "meeting_stage_chips", []):
            is_on = btn.tag() in meeting_stages
            btn.setState_(AppKit.NSControlStateValueOn if is_on else AppKit.NSControlStateValueOff)
            self._update_pill_chip_style(btn, is_on, "mauve")

        general_stages = set(self.config.get("general_reminder_stages", []))
        for btn in getattr(self, "general_stage_chips", []):
            is_on = btn.tag() in general_stages
            btn.setState_(AppKit.NSControlStateValueOn if is_on else AppKit.NSControlStateValueOff)
            self._update_pill_chip_style(btn, is_on, "blue")

        travel_stages = set(self.config.get("travel_reminder_stages", []))
        for btn in getattr(self, "travel_stage_chips", []):
            is_on = btn.tag() in travel_stages
            btn.setState_(AppKit.NSControlStateValueOn if is_on else AppKit.NSControlStateValueOff)
            self._update_pill_chip_style(btn, is_on, "peach")

    @objc.IBAction
    def onApplyPresetRelaxed_(self, sender):
        self.config.set("meeting_reminder_stages", [15, 5, 0])
        self.config.set("general_reminder_stages", [15, 5, 0])
        self.config.set("travel_reminder_stages", [45, 15, 0])
        self._refresh_stage_chips_ui()
        self.refresh_data(force=False)

    @objc.IBAction
    def onApplyPresetStandard_(self, sender):
        self.config.set("meeting_reminder_stages", [20, 10, 5, 2, 0])
        self.config.set("general_reminder_stages", [20, 10, 5, 2, 0])
        self.config.set("travel_reminder_stages", [45, 30, 15, 5, 2, 0])
        self._refresh_stage_chips_ui()
        self.refresh_data(force=False)

    @objc.IBAction
    def onApplyPresetIntensive_(self, sender):
        self.config.set("meeting_reminder_stages", [30, 20, 15, 10, 5, 2, 0])
        self.config.set("general_reminder_stages", [30, 20, 15, 10, 5, 2, 0])
        self.config.set("travel_reminder_stages", [60, 45, 30, 15, 5, 2, 0])
        self._refresh_stage_chips_ui()
        self.refresh_data(force=False)

    @objc.IBAction
    def onToggleMeetingStage_(self, sender):
        val = sender.tag()
        curr = set(self.config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on: curr.add(val)
        else: curr.discard(val)
        curr.add(0)
        self.config.set("meeting_reminder_stages", sorted(list(curr), reverse=True))
        self._update_pill_chip_style(sender, is_on, "mauve")

    @objc.IBAction
    def onToggleGeneralStage_(self, sender):
        val = sender.tag()
        curr = set(self.config.get("general_reminder_stages", [20, 10, 5, 2, 0]))
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on: curr.add(val)
        else: curr.discard(val)
        curr.add(0)
        self.config.set("general_reminder_stages", sorted(list(curr), reverse=True))
        self._update_pill_chip_style(sender, is_on, "blue")

    @objc.IBAction
    def onToggleTravelStage_(self, sender):
        val = sender.tag()
        curr = set(self.config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        if is_on: curr.add(val)
        else: curr.discard(val)
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
                    AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(lambda: self.home_save_btn.setTitle_("💾 Save Location"))
                threading.Thread(target=reset_btn, daemon=True).start()
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
        if is_on: ignored.discard(cal_name)
        else: ignored.add(cal_name)
        self.config.set("ignored_calendars", list(ignored))
        for cal in self.cached_calendars:
            if cal.get("name") == cal_name:
                cal["enabled"] = is_on
        self.refresh_data(force=True)

    @objc.IBAction
    def onCheckForUpdatesMac_(self, sender):
        if hasattr(self, 'mac_check_update_btn') and self.mac_check_update_btn:
            self.mac_check_update_btn.setTitle_("⏳ Checking...")
            self.mac_check_update_btn.setEnabled_(False)
        if hasattr(self, 'mac_update_status_lbl') and self.mac_update_status_lbl:
            self.mac_update_status_lbl.setStringValue_("Checking for new releases on GitHub...")
        updater_service.check_for_updates(background=True)

    @objc.IBAction
    def onInstallUpdateMac_(self, sender):
        if hasattr(self, 'mac_install_update_btn') and self.mac_install_update_btn:
            self.mac_install_update_btn.setTitle_("⏳ Preparing...")
            self.mac_install_update_btn.setEnabled_(False)
        updater_service.download_and_install_update(background=True)

    @objc.IBAction
    def onOpenConfigEditor_(self, sender):
        self.config.open_config_in_editor()

    @objc.IBAction
    def onOpenLogs_(self, sender):
        open_log_file()

    @objc.IBAction
    def onOpenLogFolder_(self, sender):
        open_log_folder()
