import AppKit
import objc
from core.services.calendar_service import calendar_service
from core.services.event_bus import event_bus
from core.services.language_service import t
from ui.macos.dashboard_tabs.settings.helpers import (
    add_section_header,
    create_pill_chip,
    update_pill_chip_style,
)
from ui.macos.theme import Theme


class CalendarsCardController(AppKit.NSObject):
    """Card 3: Included System Calendars."""

    def initWithParent_(self, parent):
        self = objc.super(CalendarsCardController, self).init()
        self.parent = parent
        return self

    @property
    def config(self):
        return self.parent.config

    @objc.python_method
    def build_card(self, card, w, h, cals=None):
        add_section_header(
            card,
            t("settings_calendars_title"),
            t("settings_calendars_subtitle"),
            h, w
        )

        if cals is None:
            cals = self.parent.cached_calendars if self.parent.cached_calendars else calendar_service.get_available_calendars()

        if not cals:
            lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(18, h - 86, w - 36, 22))
            lbl.setStringValue_(t("settings_all_cals_monitored"))
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

            btn = create_pill_chip(
                card,
                title,
                idx,
                cal.get("enabled", True),
                "onToggleCalendarSource:",
                x_offset,
                y_offset,
                pill_w,
                pill_h,
                "green",
                target=self,
            )
            btn.setToolTip_(cal_name)
            x_offset += (pill_w + pill_gap)

    @objc.IBAction
    def onToggleCalendarSource_(self, sender):
        cal_name = sender.toolTip() or sender.title().replace("📅 ", "")
        is_on = (sender.state() == AppKit.NSControlStateValueOn)
        update_pill_chip_style(sender, is_on, "green")
        ignored = set(self.config.get("ignored_calendars", []))
        if is_on:
            ignored.discard(cal_name)
        else:
            ignored.add(cal_name)
        self.config.set("ignored_calendars", list(ignored))
        try:
            event_bus.publish("CONFIG_CHANGED", key="ignored_calendars", value=list(ignored))
        except Exception:
            pass
        self.parent.refresh_data(force=True)
