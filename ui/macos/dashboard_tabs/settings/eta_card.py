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
        return self

    @property
    def config(self):
        return self.parent.config

    @objc.python_method
    def build_card(self, card, w, h):
        add_section_header(
            card,
            t("settings_eta_title"),
            t("settings_eta_subtitle"),
            h, w
        )

        addr_w = w - 36.0

        # 1. Starting Address (Origin) - Google Maps Style
        t1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 74, addr_w, 18))
        t1.setStringValue_(t("settings_starting_address"))
        t1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t1.setTextColor_(Theme.TEXT)
        t1.setBezeled_(False)
        t1.setDrawsBackground_(False)
        t1.setEditable_(False)
        card.addSubview_(t1)

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
            AppKit.NSMakeRect(18, h - 140, addr_w, 62.0),
            t("settings_address_placeholder"),
            curr_addr,
            _on_home_saved,
            Theme.GREEN,
            Theme.TEAL
        )
        card.addSubview_(self.home_addr_auto)

        # Subtle divider between Home and Exam
        sep1 = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 152, addr_w, 1.0))
        sep1.setWantsLayer_(True)
        sep1.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        card.addSubview_(sep1)

        # 2. General University & Exam Campus
        t_exam = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 176, addr_w, 18))
        t_exam.setStringValue_(t("settings_exam_location"))
        t_exam.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t_exam.setTextColor_(Theme.TEXT)
        t_exam.setBezeled_(False)
        t_exam.setDrawsBackground_(False)
        t_exam.setEditable_(False)
        card.addSubview_(t_exam)

        t_exam_hint = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 194, addr_w, 15))
        t_exam_hint.setStringValue_(t("settings_exam_location_hint"))
        t_exam_hint.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        t_exam_hint.setTextColor_(Theme.SUBTEXT1)
        t_exam_hint.setBezeled_(False)
        t_exam_hint.setDrawsBackground_(False)
        t_exam_hint.setEditable_(False)
        card.addSubview_(t_exam_hint)

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
            AppKit.NSMakeRect(18, h - 262, addr_w, 62.0),
            t("settings_exam_location_placeholder"),
            curr_exam_addr,
            _on_exam_saved,
            Theme.MAUVE,
            Theme.LAVENDER
        )
        card.addSubview_(self.exam_addr_auto)

        # Subtle divider between Exam and Transport
        sep2 = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 274, addr_w, 1.0))
        sep2.setWantsLayer_(True)
        sep2.layer().setBackgroundColor_(Theme.SURFACE0.CGColor())
        card.addSubview_(sep2)

        # 3. Transport Mode for Route Calculation
        t2 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 298, w - 36, 18))
        t2.setStringValue_(t("settings_transport_calc"))
        t2.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t2.setTextColor_(Theme.TEXT)
        t2.setBezeled_(False)
        t2.setDrawsBackground_(False)
        t2.setEditable_(False)
        card.addSubview_(t2)

        modes = [
            ("transit", t("settings_public_transit")),
            ("automobile", t("settings_driving_mode")),
            ("bicycling", t("settings_cycling_mode")),
            ("walking", t("settings_walking_mode"))
        ]
        curr_mode = self.config.get("transport_mode", "transit")
        self.mode_buttons = {}
        x_m = 18.0
        btn_m_w = (w - 36.0 - 24.0) / 4.0

        for m_key, m_label in modes:
            m_btn = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(x_m, h - 336, btn_m_w, 30))
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

        # 4. Departure Buffer Margin
        t3 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 384, w - 240, 18))
        t3.setStringValue_(t("settings_departure_buffer"))
        t3.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t3.setTextColor_(Theme.TEXT)
        t3.setBezeled_(False)
        t3.setDrawsBackground_(False)
        t3.setEditable_(False)
        card.addSubview_(t3)

        buf_val = self.config.get("eta_buffer_minutes", 10)

        self.buf_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(AppKit.NSMakeRect(w - 240, h - 388, 222, 26), False)
        self.buf_popup.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.buf_popup.setTarget_(self)
        self.buf_popup.setAction_("onSelectETABuffer:")
        
        for opt_title, opt_val in [
            (t("buffer_5m"), 5), (t("buffer_10m_rec"), 10), (t("buffer_15m"), 15), (t("buffer_20m"), 20)
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

    @objc.IBAction
    def onSelectModeBtn_(self, sender):
        for k, btn in getattr(self, "mode_buttons", {}).items():
            if btn == sender:
                self.config.set("transport_mode", k)
                self._update_transport_mode_buttons_ui(k)
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

