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

from core.domain.models import Meeting
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.event_bus import event_bus
from core.services.config_service import config
from core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from core.logger import setup_logging, logger, open_log_file, open_log_folder
from ui.banner import show_banner_async, _run_banner
from ui.dashboard_window import show_dashboard

class QuakMeetingAppDelegate(AppKit.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        logger.info("QuakMeeting running in macOS menu bar & system status bar!")
        import sys
        if "--silent" not in sys.argv and "--autostart" not in sys.argv:
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
        self.delegate = QuakMeetingAppDelegate.alloc().init()
        self.app.setDelegate_(self.delegate)
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        
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
            btn.setTitle_("🦆 QuakMeeting")
            btn.setToolTip_("QuakMeeting — Smart Meeting & Travel Reminders")
        
        self.menu = AppKit.NSMenu.alloc().init()
        self.status_item.setMenu_(self.menu)
        
        self.meetings: List[Dict[str, Any]] = []
        
        # Subscribe to EventBus
        event_bus.subscribe("REMINDER_TRIGGERED", self._on_reminder_triggered)
        event_bus.subscribe("CALENDAR_SYNCED", self._on_calendar_synced)
        
        # Periodic background scanner loop
        self.is_scanning = True
        self.scanner_thread = threading.Thread(target=self._background_scanner_loop, daemon=True)
        self.scanner_thread.start()
        
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
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "triggerBannerOnMainThread:",
            m_dict,
            False
        )

    def _on_calendar_synced(self, meetings: List[Any]) -> None:
        self.meetings = [m.to_dict() if isinstance(m, Meeting) else m for m in meetings]
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            "refreshMenuOnMainThread:",
            None,
            False
        )

    @objc.IBAction
    def refreshMenuOnMainThread_(self, sender):
        self.build_menu()

    def build_menu(self):
        self.menu.removeAllItems()

        # 1. Open Flight Deck
        item_dash = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🦆 Open Flight Deck", "openDashboard:", "o"
        )
        item_dash.setTarget_(self)
        self.menu.addItem_(item_dash)
        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        now = datetime.now()
        upcoming = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]
        
        # 2. Next Event & Quick Join
        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}
        
        if upcoming:
            next_m = upcoming[0]
            start_str = next_m["start_time"].strftime("%H:%M") if next_m.get("start_time") else "--:--"
            m_title = (next_m.get("title") or "Event").strip()
            title_short = m_title[:18] + "…" if len(m_title) > 18 else m_title
            
            p_type = next_m.get("pilot_type", "duck")
            icon_prefix = icon_map.get(p_type, "🦆")
            
            if self.status_item.button():
                self.status_item.button().setTitle_(f"{icon_prefix} {start_str} {title_short}")
            
            item_next = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{icon_prefix} Next: {start_str} — {m_title}", None, ""
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
                self.status_item.button().setTitle_(f"🦆 QuakMeeting")
            
            item_none = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "No further events today", None, ""
            )
            item_none.setEnabled_(False)
            self.menu.addItem_(item_none)
            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # 3. Upcoming Today List
        if len(upcoming) > 1:
            item_header = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Today's Events:", None, "")
            item_header.setEnabled_(False)
            self.menu.addItem_(item_header)
            
            for idx, m in enumerate(upcoming[1:6], start=1):
                start_str = m["start_time"].strftime("%H:%M") if m.get("start_time") else "--:--"
                p_type = m.get("pilot_type", "duck")
                icon = icon_map.get(p_type, "🦆")
                m_title = (m.get("title") or "Event").strip()
                title_short = m_title[:24] + "…" if len(m_title) > 24 else m_title
                
                sub_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    f"  {icon} {start_str} - {title_short}", "openMeetingItem:", ""
                )
                sub_item.setTarget_(self)
                sub_item.setTag_(idx)
                self.menu.addItem_(sub_item)
                
            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())

        # 4. Utilities (Sync, Preferences, Quit)
        item_sync = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔄 Sync Calendars", "refreshCalendar:", "r"
        )
        item_sync.setTarget_(self)
        self.menu.addItem_(item_sync)

        item_test = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🧪 Test Flight Banner...", "testFlightBanner:", "t"
        )
        item_test.setTarget_(self)
        self.menu.addItem_(item_test)

        item_settings = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Settings & Preferences...", "openSettings:", ","
        )
        item_settings.setTarget_(self)
        self.menu.addItem_(item_settings)

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
    def openDashboard_(self, sender):
        show_dashboard(0)

    @objc.IBAction
    def openSettings_(self, sender):
        show_dashboard(2)

    @objc.IBAction
    def openLogFileAction_(self, sender):
        open_log_file()

    @objc.IBAction
    def testFlightBanner_(self, sender):
        _run_banner({
            "title": "QuakMeeting Flight Test",
            "provider": "Manual Test 🚀",
            "pilot_type": "duck",
            "action_btn_text": "🚀 OPEN GOOGLE MEET",
            "action_url": "https://meet.google.com/test",
            "start_time": datetime.now(),
            "is_travel": False
        })

    @objc.IBAction
    def openNextMeeting_(self, sender):
        now = datetime.now()
        upcoming = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]
        if upcoming:
            url = upcoming[0].get("action_url") or upcoming[0].get("meeting_url")
            if url:
                webbrowser.open(url)

    @objc.IBAction
    def openMeetingItem_(self, sender):
        idx = sender.tag()
        now = datetime.now()
        upcoming = [m for m in self.meetings if (m.get("end_time") and m["end_time"] > now) or (m.get("start_time") and m["start_time"] > now)]
        if 0 <= idx < len(upcoming):
            m = upcoming[idx]
            url = m.get("action_url") or m.get("meeting_url")
            if url:
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

    def _background_scanner_loop(self):
        """Scans upcoming meetings and triggers multi-stage reminders via ReminderEngine."""
        while self.is_scanning:
            try:
                meeting_objects = calendar_service.get_upcoming_meetings()
                self.meetings = [m.to_dict() if isinstance(m, Meeting) else m for m in meeting_objects]
                
                # Evaluate multi-stage reminders cleanly in domain service
                reminder_engine.evaluate_meetings(meeting_objects)
                
                self.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "refreshMenuOnMainThread:",
                    None,
                    False
                )
            except Exception as e:
                logger.error(f"Error in background scanner loop: {e}", exc_info=True)
                
            time.sleep(15)

    @objc.IBAction
    def triggerBannerOnMainThread_(self, meeting_data):
        _run_banner(meeting_data)

    def run(self):
        self.app.run()

if __name__ == "__main__":
    menu_app = QuakMeetingMenuBar.alloc().init()
    menu_app.run()
