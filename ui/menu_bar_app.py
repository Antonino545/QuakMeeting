"""
Menu Bar Application for QuakMeeting.
Displays dynamic status bar item, quick-action context menu, and orchestrates background scanning.
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
from ui.banner import show_banner_async, _run_banner
from ui.dashboard_window import show_dashboard

logger = logging.getLogger("QuakMeeting.MenuBarApp")

class QuakMeetingAppDelegate(AppKit.NSObject):
    def applicationDidFinishLaunching_(self, notification):
        logger.info("QuakMeeting running in macOS menu bar!")
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
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        
        # Application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon_img = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
            self.app.setApplicationIconImage_(icon_img)
            
        self.status_bar = AppKit.NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(AppKit.NSVariableStatusItemLength)
        self.status_item.button().setTitle_("🦆 QuakMeeting")
        
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
            "🦆 Apri Flight Deck", "openDashboard:", "o"
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
            m_title = (next_m.get("title") or "Evento").strip()
            title_short = m_title[:18] + "…" if len(m_title) > 18 else m_title
            
            p_type = next_m.get("pilot_type", "duck")
            icon_prefix = icon_map.get(p_type, "🦆")
            
            self.status_item.button().setTitle_(f"{icon_prefix} {start_str} {title_short}")
            
            item_next = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{icon_prefix} Prossimo: {start_str} — {m_title}", None, ""
            )
            item_next.setEnabled_(False)
            self.menu.addItem_(item_next)
            
            action_url = next_m.get("action_url") or next_m.get("meeting_url")
            if action_url:
                btn_title = f"   {next_m.get('action_btn_text', '🚀 Partecipa Subito')}"
                item_join = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    btn_title, "openNextMeeting:", "j"
                )
                item_join.setTarget_(self)
                self.menu.addItem_(item_join)
        else:
            self.status_item.button().setTitle_("🦆 QuakMeeting")
            item_none = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "🧘‍♂️ Nessun evento imminente per oggi", None, ""
            )
            item_none.setEnabled_(False)
            self.menu.addItem_(item_none)
            
        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        # 3. Today's Agenda List
        if self.meetings:
            lbl_header = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"📅 Agenda di Oggi ({len(self.meetings)} eventi)", None, ""
            )
            lbl_header.setEnabled_(False)
            self.menu.addItem_(lbl_header)

            for idx, m in enumerate(self.meetings):
                s_time = m["start_time"].strftime("%H:%M") if m.get("start_time") else "--:--"
                p_type = m.get("pilot_type", "duck")
                icon = icon_map.get(p_type, "🦆")
                m_title = (m.get("title") or "Senza Titolo").strip()
                item_title = f"   {icon} {s_time}  {m_title}"
                
                menu_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    item_title, "openMeetingItem:", ""
                )
                menu_item.setTarget_(self)
                menu_item.setTag_(idx)
                self.menu.addItem_(menu_item)
                
            self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        # 4. Actions & Preferences
        item_refresh = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🔄 Sincronizza Calendario", "refreshCalendar:", "r"
        )
        item_refresh.setTarget_(self)
        self.menu.addItem_(item_refresh)

        item_settings = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Preferenze & Timing...", "openSettings:", ","
        )
        item_settings.setTarget_(self)
        self.menu.addItem_(item_settings)

        self.menu.addItem_(AppKit.NSMenuItem.separatorItem())
        
        # 5. Quit
        item_quit = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "❌ Esci da QuakMeeting", "quitApp:", "q"
        )
        item_quit.setTarget_(self)
        self.menu.addItem_(item_quit)

    @objc.IBAction
    def openDashboard_(self, sender):
        show_dashboard(tab_index=0)

    @objc.IBAction
    def openSettings_(self, sender):
        show_dashboard(tab_index=2)

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
        if 0 <= idx < len(self.meetings):
            m = self.meetings[idx]
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
