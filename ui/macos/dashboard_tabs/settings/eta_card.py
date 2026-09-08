import AppKit
import objc
from core.services.calendar_service import calendar_service
from core.services.event_bus import event_bus
from core.services.language_service import t
from ui.macos.components import (
    AddressAutocompleteView,
    ModernButton,
)
from ui.macos.dashboard_tabs.settings.helpers import add_section_header
from ui.macos.theme import Theme


class ETACardController(AppKit.NSObject):
    """Card 2: Departure Address & Multi-Modal Route ETA."""

    def initWithParent_(self, parent):
        self = objc.super(ETACardController, self).init()
        self.parent = parent
        self.home_addr_auto = None
        self.exam_addr_auto = None
        self.mode_buttons = {}
        self.buf_popup = None
        self.buf_hint_label = None
        self.seg_container = None
        return self

    @property
    def config(self):
        return self.parent.config

    @objc.python_method
    def _get_buffer_hint(self, mode):
        hints = {
            "transit": t("settings_buffer_hint_transit"),
            "automobile": t("settings_buffer_hint_driving"),
            "bicycling": t("settings_buffer_hint_cycling"),
            "walking": t("settings_buffer_hint_walking"),
        }
        return hints.get(mode, t("settings_buffer_hint_transit"))

    @objc.python_method
    def build_card(self, card, w, h):
        add_section_header(
            card,
            t("settings_eta_title"),
            t("settings_eta_subtitle"),
            h, w
        )

        card_padding = 18.0
        route_w = w - (card_padding * 2)
        route_h = 168.0
        route_y = h - 232.0

        # =========================================================================
        # 1. UNIFIED ROUTE CONTAINER (Origin + Destination with Transit Graphic)
        # =========================================================================
        route_box = AppKit.NSView.alloc().initWithFrame_(
            AppKit.NSMakeRect(card_padding, route_y, route_w, route_h)
        )
        route_box.setWantsLayer_(True)
        route_box.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        route_box.layer().setCornerRadius_(10.0)
        route_box.layer().setBorderWidth_(1.0)
        route_box.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        card.addSubview_(route_box)

        # 1A. Transit Line Connector Graphic (Left Track)
        # Dot centers: Origin y = 114.0, Destination y = 32.0
        conn_line = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(15.0, 37.0, 2.0, 72.0))
        conn_line.setWantsLayer_(True)
        conn_line.layer().setBackgroundColor_(Theme.SURFACE1.CGColor())
        conn_line.layer().setCornerRadius_(1.0)
        route_box.addSubview_(conn_line)

        # Blue dot for Origin
        origin_dot = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(11.0, 109.0, 10.0, 10.0))
        origin_dot.setWantsLayer_(True)
        origin_dot.layer().setBackgroundColor_(Theme.SAPPHIRE.CGColor())
        origin_dot.layer().setCornerRadius_(5.0)
        route_box.addSubview_(origin_dot)

        # Purple dot for Destination
        dest_dot = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(11.0, 27.0, 10.0, 10.0))
        dest_dot.setWantsLayer_(True)
        dest_dot.layer().setBackgroundColor_(Theme.MAUVE.CGColor())
        dest_dot.layer().setCornerRadius_(5.0)
        route_box.addSubview_(dest_dot)

        # 1B. Origin Address Section
        t1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(34.0, 138.0, route_w - 46.0, 16.0))
        t1.setStringValue_(t("settings_starting_address"))
        t1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t1.setTextColor_(Theme.TEXT)
        t1.setBezeled_(False)
        t1.setDrawsBackground_(False)
        t1.setEditable_(False)
        t1.setSelectable_(False)
        route_box.addSubview_(t1)

        curr_addr = str(self.config.get("home_address", "") or "")

        def _on_home_saved(addr_str, candidate):
            self.config.set("home_address", addr_str)
            if candidate and candidate.city:
                self.config.set("home_city", candidate.city)
            from core.services.eta_service import eta_service
            eta_service.clear_cache()
            try:
                event_bus.publish("CONFIG_CHANGED", key="home_address", value=addr_str)
            except Exception:
                pass

        self.home_addr_auto = AddressAutocompleteView.alloc().initWithFrame_placeholder_initialValue_onSave_btnColor_(
            AppKit.NSMakeRect(34.0, 92.0, route_w - 46.0, 44.0),
            t("settings_address_placeholder"),
            curr_addr,
            _on_home_saved,
            Theme.GREEN,
            Theme.TEAL
        )
        route_box.addSubview_(self.home_addr_auto)

        # 1C. Destination Campus Section
        t_exam = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(34.0, 56.0, route_w - 46.0, 16.0))
        t_exam.setStringValue_(t("settings_exam_location"))
        t_exam.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t_exam.setTextColor_(Theme.TEXT)
        t_exam.setBezeled_(False)
        t_exam.setDrawsBackground_(False)
        t_exam.setEditable_(False)
        t_exam.setSelectable_(False)
        route_box.addSubview_(t_exam)

        curr_exam_addr = str(self.config.get("exam_location", "") or "")

        def _on_exam_saved(addr_str, candidate):
            self.config.set("exam_location", addr_str)
            from core.services.eta_service import eta_service
            eta_service.clear_cache()
            try:
                event_bus.publish("CONFIG_CHANGED", key="exam_location", value=addr_str)
            except Exception:
                pass

        self.exam_addr_auto = AddressAutocompleteView.alloc().initWithFrame_placeholder_initialValue_onSave_btnColor_(
            AppKit.NSMakeRect(34.0, 10.0, route_w - 46.0, 44.0),
            t("settings_exam_location_placeholder"),
            curr_exam_addr,
            _on_exam_saved,
            Theme.MAUVE,
            Theme.LAVENDER
        )
        route_box.addSubview_(self.exam_addr_auto)

        # =========================================================================
        # 2. CARD-LEVEL DIVIDER (Exactly ONE hairline divider on the card)
        # =========================================================================
        sep = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(card_padding, h - 248.0, route_w, 1.0))
        sep.setWantsLayer_(True)
        sep.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        card.addSubview_(sep)

        # =========================================================================
        # 3. TRANSPORT MODE (Connected Segmented Control with shared background)
        # =========================================================================
        t2 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(card_padding, h - 274.0, route_w, 18.0))
        t2.setStringValue_(t("settings_transport_calc"))
        t2.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t2.setTextColor_(Theme.TEXT)
        t2.setBezeled_(False)
        t2.setDrawsBackground_(False)
        t2.setEditable_(False)
        t2.setSelectable_(False)
        card.addSubview_(t2)

        modes = [
            ("transit", t("settings_public_transit")),
            ("automobile", t("settings_driving_mode")),
            ("bicycling", t("settings_cycling_mode")),
            ("walking", t("settings_walking_mode"))
        ]
        curr_mode = self.config.get("transport_mode", "transit")

        self.seg_container = AppKit.NSView.alloc().initWithFrame_(
            AppKit.NSMakeRect(card_padding, h - 314.0, route_w, 34.0)
        )
        self.seg_container.setWantsLayer_(True)
        self.seg_container.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        self.seg_container.layer().setCornerRadius_(8.0)
        self.seg_container.layer().setBorderWidth_(1.0)
        self.seg_container.layer().setBorderColor_(Theme.SURFACE1.CGColor())
        card.addSubview_(self.seg_container)

        self.mode_buttons = {}
        seg_w = (route_w - 4.0) / 4.0

        for i, (m_key, m_label) in enumerate(modes):
            m_btn = ModernButton.alloc().initWithFrame_(
                AppKit.NSMakeRect(2.0 + i * seg_w, 2.0, seg_w, 30.0)
            )
            m_btn.setTitle_(m_label)
            m_btn.setWantsLayer_(True)
            m_btn.setBordered_(False)
            m_btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
            m_btn.setButtonType_(AppKit.NSButtonTypeMomentaryPushIn)
            m_btn.layer().setCornerRadius_(6.0)
            m_btn.layer().setMasksToBounds_(True)
            m_btn.setTarget_(self)
            m_btn.setAction_("onSelectModeBtn:")
            self.mode_buttons[m_key] = m_btn
            self.seg_container.addSubview_(m_btn)

        self._update_transport_mode_buttons_ui(curr_mode)

        # =========================================================================
        # 4. DEPARTURE BUFFER MARGIN (Directly beneath Transport Mode, no divider)
        # =========================================================================
        t3 = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(card_padding, h - 348.0, route_w - 230.0, 16.0)
        )
        t3.setStringValue_(t("settings_departure_buffer"))
        t3.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t3.setTextColor_(Theme.TEXT)
        t3.setBezeled_(False)
        t3.setDrawsBackground_(False)
        t3.setEditable_(False)
        t3.setSelectable_(False)
        card.addSubview_(t3)

        self.buf_hint_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(card_padding, h - 366.0, route_w - 230.0, 15.0)
        )
        self.buf_hint_label.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        self.buf_hint_label.setTextColor_(Theme.SUBTEXT0)
        self.buf_hint_label.setBezeled_(False)
        self.buf_hint_label.setDrawsBackground_(False)
        self.buf_hint_label.setEditable_(False)
        self.buf_hint_label.setSelectable_(False)
        self.buf_hint_label.setStringValue_(self._get_buffer_hint(curr_mode))
        card.addSubview_(self.buf_hint_label)

        buf_val = self.config.get("eta_buffer_minutes", 10)

        self.buf_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            AppKit.NSMakeRect(w - card_padding - 214.0, h - 364.0, 214.0, 26.0), False
        )
        self.buf_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.buf_popup.setTarget_(self)
        self.buf_popup.setAction_("onSelectETABuffer:")

        for opt_title, opt_val in [
            (t("buffer_0m"), 0),
            (t("buffer_5m"), 5),
            (t("buffer_10m_rec"), 10),
            (t("buffer_15m"), 15),
            (t("buffer_20m"), 20),
            (t("buffer_30m"), 30),
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
                fg = Theme.CRUST
                fnt = AppKit.NSFont.boldSystemFontOfSize_(12.0)
            else:
                btn.layer().setBackgroundColor_(AppKit.NSColor.clearColor().CGColor())
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

    @objc.IBAction
    def onSelectModeBtn_(self, sender):
        for k, btn in getattr(self, "mode_buttons", {}).items():
            if btn == sender:
                self.config.set("transport_mode", k)
                self._update_transport_mode_buttons_ui(k)
                if self.buf_hint_label:
                    self.buf_hint_label.setStringValue_(self._get_buffer_hint(k))
                from core.services.eta_service import eta_service
                eta_service.clear_cache()
                calendar_service.update_transport_mode()
                try:
                    event_bus.publish("CONFIG_CHANGED", key="transport_mode", value=k)
                except Exception:
                    pass
                break

    @objc.IBAction
    def onSaveHomeAddress_(self, sender):
        if hasattr(self, 'home_addr_auto') and self.home_addr_auto:
            self.home_addr_auto.onSaveClicked_(sender)

    @objc.IBAction
    def onSaveExamAddress_(self, sender):
        if hasattr(self, 'exam_addr_auto') and self.exam_addr_auto:
            self.exam_addr_auto.onSaveClicked_(sender)

    @objc.IBAction
    def onSelectETABuffer_(self, sender):
        item = sender.selectedItem()
        if not item:
            return
        val_buf = item.representedObject()
        if val_buf is not None:
            self.config.set("eta_buffer_minutes", int(val_buf))
            try:
                event_bus.publish("CONFIG_CHANGED", key="eta_buffer_minutes", value=int(val_buf))
            except Exception:
                pass

    @objc.python_method
    def close_suggestions(self):
        if hasattr(self, "home_addr_auto") and self.home_addr_auto:
            self.home_addr_auto.close_suggestions()
        if hasattr(self, "exam_addr_auto") and self.exam_addr_auto:
            self.exam_addr_auto.close_suggestions()

