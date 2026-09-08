import AppKit
import objc
from core.services.arrival_service import arrival_service
from core.services.event_bus import event_bus
from core.services.language_service import t
from ui.macos.components import (
    ModernButton,
    ModernToggleSwitch,
    style_button,
)

from ui.macos.dashboard_tabs.settings.helpers import add_section_header
from ui.macos.theme import Theme


class ArrivalCardController(AppKit.NSObject):
    """Card: Smart Presence & Arrival Detection for macOS Flight Deck."""

    def initWithParent_(self, parent):
        self = objc.super(ArrivalCardController, self).init()
        self.parent = parent
        self.master_sw = None
        self.calls_sw = None
        self.wifi_sw = None
        self.ssid_field = None
        self.diag_wifi_lbl = None
        self.diag_call_lbl = None
        self.save_btn = None
        return self

    @property
    def config(self):
        return self.parent.config

    @objc.python_method
    def build_card(self, card, w, h):
        add_section_header(
            card,
            t("settings_arrival_title"),
            t("settings_arrival_subtitle"),
            h, w
        )

        addr_w = w - 36.0

        # 1. Master Toggle Row
        t1 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 86, addr_w - 60, 18))
        t1.setStringValue_(t("settings_arrival_enable"))
        t1.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.5))
        t1.setTextColor_(Theme.TEXT)
        t1.setBezeled_(False)
        t1.setDrawsBackground_(False)
        t1.setEditable_(False)
        card.addSubview_(t1)

        t1_sub = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 102, addr_w - 60, 14))
        t1_sub.setStringValue_(t("settings_arrival_enable_sub"))
        t1_sub.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
        t1_sub.setTextColor_(Theme.SUBTEXT0)
        t1_sub.setBezeled_(False)
        t1_sub.setDrawsBackground_(False)
        t1_sub.setEditable_(False)
        card.addSubview_(t1_sub)

        self.master_sw = ModernToggleSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(w - 62, h - 97, 44, 24))
        self.master_sw.setChecked_(bool(self.config.get("enable_arrival_detection", True)))
        self.master_sw.setCallback_(self.onToggleMasterSwitch)
        card.addSubview_(self.master_sw)

        # 2. Calls Detection Toggle Row
        t2 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(36, h - 130, addr_w - 78, 16))
        t2.setStringValue_(t("settings_arrival_calls"))
        t2.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        t2.setTextColor_(Theme.TEXT)
        t2.setBezeled_(False)
        t2.setDrawsBackground_(False)
        t2.setEditable_(False)
        card.addSubview_(t2)

        t2_sub = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(36, h - 146, addr_w - 78, 14))
        t2_sub.setStringValue_(t("settings_arrival_calls_sub"))
        t2_sub.setFont_(AppKit.NSFont.systemFontOfSize_(10.0))
        t2_sub.setTextColor_(Theme.SUBTEXT0)
        t2_sub.setBezeled_(False)
        t2_sub.setDrawsBackground_(False)
        t2_sub.setEditable_(False)
        card.addSubview_(t2_sub)

        self.calls_sw = ModernToggleSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(w - 62, h - 142, 44, 24))
        self.calls_sw.setChecked_(bool(self.config.get("arrival_detect_active_calls", True)))
        self.calls_sw.setCallback_(self.onToggleCallsSwitch)
        card.addSubview_(self.calls_sw)

        # 3. Wi-Fi Detection Toggle Row
        t3 = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(36, h - 172, addr_w - 78, 16))
        t3.setStringValue_(t("settings_arrival_wifi"))
        t3.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        t3.setTextColor_(Theme.TEXT)
        t3.setBezeled_(False)
        t3.setDrawsBackground_(False)
        t3.setEditable_(False)
        card.addSubview_(t3)

        t3_sub = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(36, h - 188, addr_w - 78, 14))
        t3_sub.setStringValue_(t("settings_arrival_wifi_sub"))
        t3_sub.setFont_(AppKit.NSFont.systemFontOfSize_(10.0))
        t3_sub.setTextColor_(Theme.SUBTEXT0)
        t3_sub.setBezeled_(False)
        t3_sub.setDrawsBackground_(False)
        t3_sub.setEditable_(False)
        card.addSubview_(t3_sub)

        self.wifi_sw = ModernToggleSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(w - 62, h - 184, 44, 24))
        self.wifi_sw.setChecked_(bool(self.config.get("arrival_detect_venue_wifi", True)))
        self.wifi_sw.setCallback_(self.onToggleWifiSwitch)
        card.addSubview_(self.wifi_sw)

        # 4. Live Diagnostics Box
        diag_bg = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 292, addr_w, 90))
        diag_bg.setWantsLayer_(True)
        diag_bg.layer().setBackgroundColor_(Theme.CRUST.CGColor())
        diag_bg.layer().setCornerRadius_(8.0)
        diag_bg.layer().setBorderWidth_(1.0)
        diag_bg.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        card.addSubview_(diag_bg)

        diag_hdr = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(10, 66, addr_w - 120, 18))
        diag_hdr.setStringValue_(t("settings_arrival_diagnostics_title"))
        diag_hdr.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        diag_hdr.setTextColor_(Theme.LAVENDER)
        diag_hdr.setBezeled_(False)
        diag_hdr.setDrawsBackground_(False)
        diag_hdr.setEditable_(False)
        diag_bg.addSubview_(diag_hdr)

        refresh_btn = Theme.create_button(
            AppKit.NSMakeRect(addr_w - 96, 64, 86, 22),
            title=t("settings_arrival_refresh_btn"),
            bg_color=Theme.SURFACE1,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE2,
            corner_radius=5.0,
            font_size=11.0,
        )
        refresh_btn.setTarget_(self)
        refresh_btn.setAction_("onRefreshDiagnostics:")
        diag_bg.addSubview_(refresh_btn)

        self.diag_wifi_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(10, 44, addr_w - 180, 16))
        self.diag_wifi_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        self.diag_wifi_lbl.setTextColor_(Theme.TEXT)
        self.diag_wifi_lbl.setBezeled_(False)
        self.diag_wifi_lbl.setDrawsBackground_(False)
        self.diag_wifi_lbl.setEditable_(False)
        diag_bg.addSubview_(self.diag_wifi_lbl)

        self.add_wifi_btn = Theme.create_button(
            AppKit.NSMakeRect(addr_w - 160, 42, 150, 20),
            title="",
            bg_color=Theme.GREEN,
            text_color=Theme.CRUST,
            corner_radius=4.0,
            font_size=10.5,
            bold=True,
        )
        self.add_wifi_btn.setTarget_(self)
        self.add_wifi_btn.setAction_("onAddCurrentWiFi:")
        self.add_wifi_btn.setHidden_(True)
        diag_bg.addSubview_(self.add_wifi_btn)

        self.diag_call_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(10, 24, addr_w - 20, 16))
        self.diag_call_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        self.diag_call_lbl.setTextColor_(Theme.TEXT)
        self.diag_call_lbl.setBezeled_(False)
        self.diag_call_lbl.setDrawsBackground_(False)
        self.diag_call_lbl.setEditable_(False)
        diag_bg.addSubview_(self.diag_call_lbl)

        self.diag_summary_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(10, 4, addr_w - 20, 16))
        self.diag_summary_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.0))
        self.diag_summary_lbl.setTextColor_(Theme.SUBTEXT1)
        self.diag_summary_lbl.setBezeled_(False)
        self.diag_summary_lbl.setDrawsBackground_(False)
        self.diag_summary_lbl.setEditable_(False)
        diag_bg.addSubview_(self.diag_summary_lbl)

        # 5. Monitored SSIDs Editor
        t_ssid = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 322, addr_w, 18))
        t_ssid.setStringValue_(t("settings_arrival_ssids_label"))
        t_ssid.setFont_(AppKit.NSFont.boldSystemFontOfSize_(12.0))
        t_ssid.setTextColor_(Theme.TEXT)
        t_ssid.setBezeled_(False)
        t_ssid.setDrawsBackground_(False)
        t_ssid.setEditable_(False)
        card.addSubview_(t_ssid)

        t_hint = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 340, addr_w, 15))
        t_hint.setStringValue_(t("settings_arrival_ssids_hint"))
        t_hint.setFont_(AppKit.NSFont.systemFontOfSize_(10.5))
        t_hint.setTextColor_(Theme.SUBTEXT1)
        t_hint.setBezeled_(False)
        t_hint.setDrawsBackground_(False)
        t_hint.setEditable_(False)
        card.addSubview_(t_hint)

        curr_ssids = self.config.get("arrival_wifi_ssids", ["eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"])
        self.ssid_field = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 372, addr_w, 26))
        self.ssid_field.setWantsLayer_(True)
        self.ssid_field.setStringValue_(", ".join(curr_ssids))
        self.ssid_field.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.ssid_field.setTextColor_(Theme.TEXT)
        self.ssid_field.setBackgroundColor_(Theme.MANTLE)
        self.ssid_field.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        self.ssid_field.layer().setCornerRadius_(6.0)
        self.ssid_field.layer().setBorderWidth_(1.0)
        self.ssid_field.layer().setBorderColor_(Theme.SURFACE1.CGColor())
        card.addSubview_(self.ssid_field)

        # Buttons Row
        self.save_btn = Theme.create_button(
            AppKit.NSMakeRect(18, h - 410, 110, 28),
            title=t("settings_arrival_save_btn"),
            bg_color=Theme.SAPPHIRE,
            text_color=Theme.CRUST,
            corner_radius=7.0,
            font_size=11.5,
            bold=True,
        )
        self.save_btn.setTarget_(self)
        self.save_btn.setAction_("onSaveSSIDs:")
        card.addSubview_(self.save_btn)

        reset_btn = Theme.create_button(
            AppKit.NSMakeRect(136, h - 410, 140, 28),
            title=t("settings_arrival_reset_btn"),
            bg_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            border_color=Theme.SURFACE1,
            corner_radius=7.0,
            font_size=11.5,
        )
        reset_btn.setTarget_(self)
        reset_btn.setAction_("onResetSSIDs:")
        card.addSubview_(reset_btn)

        master_enabled = bool(self.config.get("enable_arrival_detection", True))
        if self.calls_sw:
            self.calls_sw.setEnabled_(master_enabled)
        if self.wifi_sw:
            self.wifi_sw.setEnabled_(master_enabled)

        self.update_diagnostics()

    @objc.python_method
    def onToggleMasterSwitch(self, checked):
        is_on = bool(checked)
        self.config.set("enable_arrival_detection", is_on)
        if self.calls_sw:
            self.calls_sw.setEnabled_(is_on)
            self.calls_sw.setNeedsDisplay_(True)
        if self.wifi_sw:
            self.wifi_sw.setEnabled_(is_on)
            self.wifi_sw.setNeedsDisplay_(True)
        try:
            event_bus.publish("CONFIG_CHANGED", key="enable_arrival_detection", value=is_on)
        except Exception:

            pass
        self.update_diagnostics()

    @objc.python_method
    def onToggleCallsSwitch(self, checked):
        self.config.set("arrival_detect_active_calls", bool(checked))
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_detect_active_calls", value=bool(checked))
        except Exception:
            pass
        self.update_diagnostics()

    @objc.python_method
    def onToggleWifiSwitch(self, checked):
        self.config.set("arrival_detect_venue_wifi", bool(checked))
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_detect_venue_wifi", value=bool(checked))
        except Exception:
            pass
        self.update_diagnostics()

    @objc.IBAction
    def onRefreshDiagnostics_(self, sender):
        self.update_diagnostics()

    @objc.IBAction
    def onSaveSSIDs_(self, sender):
        if self.ssid_field:
            raw = str(self.ssid_field.stringValue() or "")
            tokens = [s.strip().lower() for s in raw.split(",") if s.strip()]
            self.config.set("arrival_wifi_ssids", tokens)
            try:
                event_bus.publish("CONFIG_CHANGED", key="arrival_wifi_ssids", value=tokens)
            except Exception:
                pass
            if self.save_btn:
                self.save_btn.setTitle_("✓ " + t("saved"))
                style_button(
                    self.save_btn,
                    bg_color=Theme.GREEN,
                    text_color=Theme.CRUST,
                    corner_radius=7.0,
                    font_size=11.5,
                    bold=True,
                )
                AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    1.5, self, "restoreSaveBtnTitle:", None, False
                )
            self.update_diagnostics()

    @objc.IBAction
    def restoreSaveBtnTitle_(self, timer):
        if self.save_btn:
            self.save_btn.setTitle_(t("settings_arrival_save_btn"))
            style_button(
                self.save_btn,
                bg_color=Theme.SAPPHIRE,
                text_color=Theme.CRUST,
                corner_radius=7.0,
                font_size=11.5,
                bold=True,
            )


    @objc.IBAction
    def onResetSSIDs_(self, sender):
        defaults = ["eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"]
        self.config.set("arrival_wifi_ssids", defaults)
        if self.ssid_field:
            self.ssid_field.setStringValue_(", ".join(defaults))
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_wifi_ssids", value=defaults)
        except Exception:
            pass
        self.update_diagnostics()

    @objc.IBAction
    def onAddCurrentWiFi_(self, sender):
        diag = arrival_service.get_presence_diagnostics()
        ssid = diag.get("current_wifi")
        if not ssid:
            return
        curr_tokens = [s.strip().lower() for s in (str(self.ssid_field.stringValue() or "")).split(",") if s.strip()]
        if ssid.lower() not in curr_tokens:
            curr_tokens.append(ssid.lower())
        self.config.set("arrival_wifi_ssids", curr_tokens)
        if self.ssid_field:
            self.ssid_field.setStringValue_(", ".join(curr_tokens))
        try:
            event_bus.publish("CONFIG_CHANGED", key="arrival_wifi_ssids", value=curr_tokens)
        except Exception:
            pass
        if self.add_wifi_btn:
            self.add_wifi_btn.setTitle_(t("settings_arrival_added_wifi", default="✓ Added!").format(ssid=ssid))
        AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.5, self, "restoreAfterAddWiFi:", None, False
        )

    @objc.IBAction
    def restoreAfterAddWiFi_(self, timer):
        self.update_diagnostics()

    @objc.python_method
    def update_diagnostics(self):
        diag = arrival_service.get_presence_diagnostics()
        wifi_ssid = diag.get("current_wifi")
        is_venue = diag.get("is_venue_wifi", False)
        call_app = diag.get("detected_call_app")
        is_enabled = bool(self.config.get("enable_arrival_detection", True))

        if self.diag_wifi_lbl:
            if wifi_ssid:
                tag = t("settings_arrival_status_matched") if is_venue else t("settings_arrival_status_unmatched")
                self.diag_wifi_lbl.setStringValue_(f"📶 {t('settings_arrival_current_wifi')} {wifi_ssid}  •  {tag}")
            else:
                self.diag_wifi_lbl.setStringValue_(f"📶 {t('settings_arrival_current_wifi')} {t('settings_arrival_status_disconnected')}")

        if self.diag_call_lbl:
            if call_app:
                self.diag_call_lbl.setStringValue_(f"📞 {t('settings_arrival_active_call')} {call_app} (Running 🟢)")
            else:
                self.diag_call_lbl.setStringValue_(f"📞 {t('settings_arrival_active_call')} {t('settings_arrival_no_call')}")

        if self.diag_summary_lbl:
            if not is_enabled:
                self.diag_summary_lbl.setStringValue_(t("settings_arrival_summary_disabled"))
                if self.add_wifi_btn:
                    self.add_wifi_btn.setHidden_(True)
            elif call_app:
                self.diag_summary_lbl.setStringValue_(t("settings_arrival_summary_call").format(app=call_app))
                if self.add_wifi_btn:
                    self.add_wifi_btn.setHidden_(True)
            elif is_venue and wifi_ssid:
                self.diag_summary_lbl.setStringValue_(t("settings_arrival_summary_venue").format(ssid=wifi_ssid))
                if self.add_wifi_btn:
                    self.add_wifi_btn.setHidden_(True)
            else:
                self.diag_summary_lbl.setStringValue_(t("settings_arrival_summary_normal"))
                if wifi_ssid and self.add_wifi_btn:
                    self.add_wifi_btn.setTitle_(t("settings_arrival_add_current_wifi").format(ssid=wifi_ssid))
                    self.add_wifi_btn.setHidden_(False)
                elif self.add_wifi_btn:
                    self.add_wifi_btn.setHidden_(True)
