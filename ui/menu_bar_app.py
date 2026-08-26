"""
Menu Bar Application for QuakMeeting.
Displays dynamic status bar item, full macOS top menu bar, quick-action context menu, and background scanning.
"""
import AppKit
import objc
import webbrowser
import threading
import time
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.domain.models import Meeting, format_duration
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.event_bus import event_bus
from core.services.config_service import config
from core.services.updater_service import updater_service
from core.logger import setup_logging, logger, open_log_file, open_log_folder
from ui.banner import show_banner_async, _run_banner
from ui.dashboard_window import show_dashboard
from ui.viewmodels.tray_viewmodel import TrayViewModel

class QuakMeetingAppDelegate(AppKit.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        logger.info("QuakMeeting running in macOS menu bar & system status bar!")
        import sys
        if "--silent" not in sys.argv:
            show_dashboard()

    def applicationShouldHandleReopen_hasVisibleWindows_(self, sender, flag):
        show_dashboard()
        return True

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
        return False

    @objc.IBAction
    def showBannerOnMainThread_(self, meeting_data):
        _run_banner(meeting_data)

class QuakMeetingMenuBar(AppKit.NSObject):
    def init(self):
        self = objc.super(QuakMeetingMenuBar, self).init()
        if self is None:
            return None

        self.app = AppKit.NSApplication.sharedApplication()

        # Force macOS to (re-)register this process as a GUI app with menu bar.
        # When launched from a .app bundle via execv, the WindowServer may not
        # recognise the Python process as the bundle's application. Toggling
        # Accessory → Regular forces a re-registration so the top menu bar and
        # keyboard shortcuts work correctly.
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

        self.delegate = QuakMeetingAppDelegate.alloc().init()
        self.app.setDelegate_(self.delegate)

        # Application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon_img = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
            self.app.setApplicationIconImage_(icon_img)

        # 1. macOS Top Menu Bar (App Menu, Edit, Window, Help)
        self._setup_main_menubar()

        # 2. macOS System Status Bar Item (Top Right tray icon & dropdown)
        self.status_bar = AppKit.NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(AppKit.NSVariableStatusItemLength)
        self.status_item.setVisible_(True)

        btn = self.status_item.button()
        if btn:
            btn.setTitle_("🦆")
            btn.setToolTip_("QuakMeeting — Smart Meeting & Travel Reminders")

        self.menu = AppKit.NSMenu.alloc().init()
        self.status_item.setMenu_(self.menu)

        self._last_menu_signature = None
        self.meetings: List[Dict[str, Any]] = []

        # Subscribe to EventBus
        event_bus.subscribe("REMINDER_TRIGGERED", self._on_reminder_triggered)
        event_bus.subscribe("CALENDAR_SYNCED", self._on_calendar_synced)
        event_bus.subscribe("CONFIG_CHANGED", self._on_config_changed)
        event_bus.subscribe("AGENDA_UPDATED", self._on_agenda_updated)
        event_bus.subscribe("UPDATE_AVAILABLE", self._on_update_event)
        event_bus.subscribe("UPDATE_CHECK_COMPLETE", self._on_update_event)
        event_bus.subscribe("UPDATE_INSTALLED", self._on_update_event)

        self.build_menu()
        return self

    def _setup_main_menubar(self):
        """Builds standard macOS Top Menu Bar so menus & shortcuts (Cmd+C, Cmd+V, Cmd+Q) work globally."""
        main_menu = AppKit.NSMenu.alloc().init()

        # --- APP MENU ---
        app_menu_item = AppKit.NSMenuItem.alloc().init()
        app_menu = AppKit.NSMenu.alloc().initWithTitle_("QuakMeeting")

        about_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About QuakMeeting", "openAbout:", ""
        )
        about_item.setTarget_(self)
        app_menu.addItem_(about_item)
        app_menu.addItem_(AppKit.NSMenuItem.separatorItem())

        pref_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Preferences (Flight Deck)...", "openDashboard:", ","
        )
        pref_item.setTarget_(self)
        app_menu.addItem_(pref_item)

        sync_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Sync Calendars Now", "refreshCalendar:", "r"
        )
        sync_item.setTarget_(self)
        app_menu.addItem_(sync_item)
        app_menu.addItem_(AppKit.NSMenuItem.separatorItem())

        hide_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hide QuakMeeting", "hide:", "h"
        )
        app_menu.addItem_(hide_item)

        hide_others = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hide Others", "hideOtherApplications:", "h"
        )
        hide_others.setKeyEquivalentModifierMask_(AppKit.NSEventModifierFlagCommand | AppKit.NSEventModifierFlagOption)
        app_menu.addItem_(hide_others)

        show_all = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show All", "unhideAllApplications:", ""
        )
        app_menu.addItem_(show_all)
        app_menu.addItem_(AppKit.NSMenuItem.separatorItem())

        quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit QuakMeeting", "terminate:", "q"
        )
        app_menu.addItem_(quit_item)
        app_menu_item.setSubmenu_(app_menu)
        main_menu.addItem_(app_menu_item)

        # --- EDIT MENU (Enables standard cut, copy, paste, select all) ---
        edit_menu_item = AppKit.NSMenuItem.alloc().init()
        edit_menu = AppKit.NSMenu.alloc().initWithTitle_("Edit")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Undo", "undo:", "z")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Redo", "redo:", "Z")
        edit_menu.addItem_(AppKit.NSMenuItem.separatorItem())
        edit_menu.addItemWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Copy", "copy:", "c")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Select All", "selectAll:", "a")
        edit_menu_item.setSubmenu_(edit_menu)
        main_menu.addItem_(edit_menu_item)

        # --- WINDOW MENU ---
        win_menu_item = AppKit.NSMenuItem.alloc().init()
        win_menu = AppKit.NSMenu.alloc().initWithTitle_("Window")

        dash_win_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Flight Deck", "openDashboard:", "o"
        )
        dash_win_item.setTarget_(self)
        win_menu.addItem_(dash_win_item)
        win_menu.addItemWithTitle_action_keyEquivalent_("Minimize", "performMiniaturize:", "m")
        win_menu.addItemWithTitle_action_keyEquivalent_("Close Window", "performClose:", "w")
        win_menu_item.setSubmenu_(win_menu)
        main_menu.addItem_(win_menu_item)

        # --- HELP MENU ---
        help_menu_item = AppKit.NSMenuItem.alloc().init()
        help_menu = AppKit.NSMenu.alloc().initWithTitle_("Help")

        help_log = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "View Log File (quakmeeting.log)", "openLogFileAction:", "l"
        )
        help_log.setTarget_(self)
        help_menu.addItem_(help_log)
        help_menu.addItem_(AppKit.NSMenuItem.separatorItem())

        help_doc = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "QuakMeeting Guide & GitHub", "openHelp:", ""
        )
        help_doc.setTarget_(self)
        help_menu.addItem_(help_doc)
        help_menu_item.setSubmenu_(help_menu)
        main_menu.addItem_(help_menu_item)

        self.app.setMainMenu_(main_menu)

    @objc.IBAction
    def openAbout_(self, sender):
        show_dashboard(0)

    @objc.IBAction
    def openHelp_(self, sender):
        webbrowser.open("https://github.com/Antonino545/QuakMeeting")

    def _on_reminder_triggered(self, meeting: Meeting, stage: int) -> None:
        m_dict = meeting.to_dict() if isinstance(meeting, Meeting) else meeting
        show_banner_async(m_dict)

    def _on_calendar_synced(self, meetings: List[Any]) -> None:
        self.meetings = [m.to_dict() if isinstance(m, Meeting) else m for m in meetings]
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "refreshMenuOnMainThread:",
            None,
            False
        )

    def _on_config_changed(self, key: Optional[str] = None, **kwargs) -> None:
        self._last_menu_signature = None
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "refreshMenuOnMainThread:",
            None,
            False
        )

    @objc.IBAction
    def refreshMenuOnMainThread_(self, sender):
        self.build_menu()

    # _format_status_title is now handled by TrayViewModel

    def build_menu(self):
        now = datetime.now().astimezone()
        from datetime import timedelta
        today_upcoming = [
            m for m in self.meetings
            if m.get("start_time") and m["start_time"].astimezone().date() == now.date()
            and ((m.get("end_time") and m["end_time"] > now) or m["start_time"] > now)
        ]

        tomorrow_date = now.date() + timedelta(days=1)
        tomorrow_upcoming = [
            m for m in self.meetings
            if m.get("start_time") and m["start_time"].astimezone().date() == tomorrow_date
        ]

        status_mode = config.get("menubar_status_mode", "countdown")
        max_lookahead_min = int(config.get("max_countdown_lookahead_hours", 3)) * 60

        # State signature diffing to avoid unnecessary menu rebuilding
        m_sigs = tuple((m.get("title"), str(m.get("start_time")), m.get("pilot_type")) for m in today_upcoming[:6] + tomorrow_upcoming[:6])
        minute_str = now.strftime("%H:%M")
        new_signature = (minute_str, len(today_upcoming), len(tomorrow_upcoming), status_mode, m_sigs)

        if self._last_menu_signature == new_signature:
            return
        self._last_menu_signature = new_signature

        primary_m = today_upcoming[0] if today_upcoming else None
        title_str = TrayViewModel.get_status_bar_title(primary_m, now, status_mode, max_lookahead_min)

        # Must execute AppKit UI updates on Main Thread
        def _update_ui():
            self.status_item.button().setTitle_(title_str)
        if self.status_item.button():
            self.status_item.button().performSelectorOnMainThread_withObject_waitUntilDone_("setTitle:", title_str, False)

        self.menu.removeAllItems()

        # 1. Open Flight Deck
        item_dash = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🦆 Open Flight Deck", "openDashboard:", "o"
        )
        item_dash.setTarget_(self)
        self.menu.addItem_(item_dash)
        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # 2. Next Event & Quick Join (Only for today!)
        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}

        if today_upcoming:
            next_m = today_upcoming[0]
            start_str = next_m["start_time"].astimezone().strftime("%H:%M") if next_m.get("start_time") else "--:--"
            m_title = (next_m.get("title") or "Event").strip()

            p_type = next_m.get("pilot_type", "duck")
            icon_prefix = icon_map.get(p_type, "🦆")

            travel_min = next_m.get("travel_time_minutes")
            dep_dt = next_m.get("departure_time")

            # Track the most immediate relevant event (could be currently active or next future)
            if travel_min and isinstance(dep_dt, datetime):
                dur_str = format_duration(travel_min)
                next_label = f"{icon_prefix} Next: {start_str} — {m_title} (🚗 ~{dur_str} • Leave at {dep_dt.astimezone().strftime('%H:%M')})"
            elif travel_min:
                dur_str = format_duration(travel_min)
                next_label = f"{icon_prefix} Next: {start_str} — {m_title} (🚗 ~{dur_str})"
            else:
                next_label = f"{icon_prefix} Next: {start_str} — {m_title}"

            item_next = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                next_label, None, ""
            )
            item_next.setEnabled_(False)
            self.menu.addItem_(item_next)

            action_url = next_m.get("action_url") or next_m.get("meeting_url")
            if action_url:
                btn_title = f"   {next_m.get('action_btn_text', '🚀 Join Now')}"
                item_join = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    btn_title, "openNextMeeting:", "j"
                )
                item_join.setTarget_(self)
                self.menu.addItem_(item_join)

            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        else:
            if self.status_item.button():
                fallback_title = TrayViewModel.get_status_bar_title(None, now, status_mode, max_lookahead_min)
                self.status_item.button().setTitle_(fallback_title)

            item_none = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "✨ No remaining events today", None, ""
            )
            item_none.setEnabled_(False)
            self.menu.addItem_(item_none)
            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        all_upcoming = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]

        # 3. Upcoming Today List
        if len(today_upcoming) > 1:
            item_header = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("📅 Today's Events:", None, "")
            item_header.setEnabled_(False)
            self.menu.addItem_(item_header)

            for m in today_upcoming[1:6]:
                try:
                    idx = all_upcoming.index(m)
                except ValueError:
                    continue
                start_str = m["start_time"].astimezone().strftime("%H:%M") if m.get("start_time") else "--:--"
                p_type = m.get("pilot_type", "duck")
                icon = icon_map.get(p_type, "🦆")
                m_title = (m.get("title") or "Event").strip()
                title_short = m_title[:24] + "…" if len(m_title) > 24 else m_title

                tr_min = m.get("travel_time_minutes")
                sub_text = f"  {icon} {start_str} - {title_short}"
                if tr_min:
                    sub_text += f" (~{format_duration(tr_min)})"

                sub_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    sub_text, "openMeetingItem:", ""
                )
                sub_item.setTarget_(self)
                sub_item.setTag_(idx)
                self.menu.addItem_(sub_item)

            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        if tomorrow_upcoming:
            item_header_tmrw = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🗓️ Tomorrow:", None, "")
            item_header_tmrw.setEnabled_(False)
            self.menu.addItem_(item_header_tmrw)

            for m in tomorrow_upcoming[:5]:
                try:
                    idx = all_upcoming.index(m)
                except ValueError:
                    continue
                start_str = m["start_time"].astimezone().strftime("%H:%M") if m.get("start_time") else "--:--"
                p_type = m.get("pilot_type", "duck")
                icon = icon_map.get(p_type, "🦆")
                m_title = (m.get("title") or "Event").strip()
                title_short = m_title[:24] + "…" if len(m_title) > 24 else m_title

                tr_min = m.get("travel_time_minutes")
                sub_text = f"  {icon} {start_str} - {title_short}"
                if tr_min:
                    sub_text += f" (~{format_duration(tr_min)})"

                sub_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    sub_text, "openMeetingItem:", ""
                )
                sub_item.setTarget_(self)
                sub_item.setTag_(idx)
                self.menu.addItem_(sub_item)

            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # 4. Updates & Utilities (Sync, Preferences, Quit)
        if updater_service.latest_release_info and updater_service.latest_release_info.get("has_update"):
            v_tag = updater_service.latest_release_info.get("tag_name") or "New Version"
            item_up = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"🚀 Update Available ({v_tag}) - Install...", "onInstallUpdateAction:", "u"
            )
            item_up.setTarget_(self)
            self.menu.addItem_(item_up)
            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        item_sync = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔄 Sync Calendars", "refreshCalendar:", "r"
        )
        item_sync.setTarget_(self)
        self.menu.addItem_(item_sync)

        item_settings = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Settings & Preferences...", "openSettings:", ","
        )
        item_settings.setTarget_(self)
        self.menu.addItem_(item_settings)

        item_check = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔍 Check for Updates...", "onCheckUpdatesAction:", ""
        )
        item_check.setTarget_(self)
        self.menu.addItem_(item_check)

        # Status Bar Display Mode Quick Switcher
        item_display_mode = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "📊 Status Bar Mode", None, ""
        )
        mode_menu = AppKit.NSMenu.alloc().initWithTitle_("📊 Status Bar Mode")

        curr_mode = config.get("menubar_status_mode", "countdown")
        modes_def = [
            ("countdown", "⏳ Live Countdown (e.g. In 25m / Leave in 10m)"),
            ("event_time", "🕐 Start Time & Title (e.g. 20:00 Dinner)"),
            ("time_only", "⏱️ Time & Countdown (e.g. 20:00 in 25m)"),
            ("icon_only", "🦆 Icon Only (Minimal)")
        ]
        for idx, (mode_key, mode_label) in enumerate(modes_def):
            m_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                mode_label, "onSelectStatusMode:", ""
            )
            m_item.setTarget_(self)
            m_item.setTag_(idx)
            if mode_key == curr_mode:
                m_item.setState_(AppKit.NSControlStateValueOn)
            else:
                m_item.setState_(AppKit.NSControlStateValueOff)
            mode_menu.addItem_(m_item)

        item_display_mode.setSubmenu_(mode_menu)
        self.menu.addItem_(item_display_mode)

        item_logs = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "📄 View Logs & Diagnostics...", "openLogFileAction:", "l"
        )
        item_logs.setTarget_(self)
        self.menu.addItem_(item_logs)

        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # 5. Quit
        item_quit = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "❌ Quit QuakMeeting", "quitApp:", "q"
        )
        item_quit.setTarget_(self)
        self.menu.addItem_(item_quit)

    @objc.IBAction
    def onSelectStatusMode_(self, sender):
        tag = sender.tag()
        modes = ["countdown", "event_time", "time_only", "icon_only"]
        if 0 <= tag < len(modes):
            config.set("menubar_status_mode", modes[tag])
            event_bus.publish("CONFIG_CHANGED", key="menubar_status_mode")
            self._last_menu_signature = None
            self.build_menu()

    @objc.IBAction
    def openDashboard_(self, sender):
        show_dashboard(0)

    @objc.IBAction
    def openSettings_(self, sender):
        show_dashboard(2)

    @objc.IBAction
    def onCheckUpdatesAction_(self, sender):
        show_dashboard(2)
        updater_service.check_for_updates(background=True)

    @objc.IBAction
    def onInstallUpdateAction_(self, sender):
        show_dashboard(2)
        updater_service.download_and_install_update(background=True)

    @objc.IBAction
    def openLogFileAction_(self, sender):
        open_log_file()

    def _on_update_event(self, **kwargs):
        def refresh_ui():
            self._last_menu_signature = None
            self.build_menu()
        AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(refresh_ui)

    @objc.IBAction
    def openNextMeeting_(self, sender):
        now = datetime.now().astimezone()
        upcoming = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]
        if upcoming:
            url = upcoming[0].get("action_url") or upcoming[0].get("meeting_url")
            if url and url != "https://calendar.apple.com":
                webbrowser.open(url)

    @objc.IBAction
    def openMeetingItem_(self, sender):
        idx = sender.tag()
        now = datetime.now().astimezone()
        upcoming = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]
        if 0 <= idx < len(upcoming):
            m = upcoming[idx]
            url = m.get("action_url") or m.get("meeting_url")
            if url and url != "https://calendar.apple.com":
                webbrowser.open(url)

    @objc.IBAction
    def refreshCalendar_(self, sender):
        logger.info("Manual calendar synchronization triggered")
        raw_meetings = calendar_service.sync_now()
        self.meetings = [m.to_dict() if isinstance(m, Meeting) else m for m in raw_meetings]
        self.build_menu()

    @objc.IBAction
    def quitApp_(self, sender):
        self.is_scanning = False
        AppKit.NSApplication.sharedApplication().terminate_(self)

    def _on_agenda_updated(self, meeting_objects=None, **kwargs):
        if meeting_objects is None:
            return
        from core.domain.models import Meeting
        self.meetings = [m.to_dict() if isinstance(m, Meeting) else m for m in meeting_objects]
        self.performSelectorOnMainThread_withObject_waitUntilDone_("refreshMenuOnMainThread:", None, False)

    @objc.IBAction
    def triggerBannerOnMainThread_(self, meeting_data):
        _run_banner(meeting_data)

    def run(self):
        self.app.run()

if __name__ == "__main__":
    menu_app = QuakMeetingMenuBar.alloc().init()
    menu_app.run()
