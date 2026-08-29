import unittest
from unittest.mock import MagicMock
import sys

# Only run macOS UI tests on macOS
class TestDashboardUI(unittest.TestCase):
    @unittest.skipIf(sys.platform != "darwin", "macOS specific UI tests")
    def test_instantiate_and_render_tabs(self):
        # Avoid showing actual windows during test
        try:
            from ui.macos.dashboard_tabs.agenda_tab import AgendaTabController
            from ui.macos.dashboard_tabs.hangar_tab import HangarTabController
            from ui.macos.dashboard_tabs.settings_tab import SettingsTabController

            agenda = AgendaTabController.alloc().init()
            hangar = HangarTabController.alloc().init()
            settings = SettingsTabController.alloc().init()

            self.assertIsNotNone(agenda)
            self.assertIsNotNone(hangar)
            self.assertIsNotNone(settings)

            # Mock container and config
            mock_container = MagicMock()
            mock_config = MagicMock()
            mock_config.get.side_effect = lambda k, d=None: d if d is not None else "transit"

            # Test Agenda render
            meetings = []
            agenda_view = agenda.render(mock_container, 800, 600, meetings, False, mock_config)
            self.assertIsNotNone(agenda_view)

            # Test Hangar render
            hangar_view = hangar.render(mock_container, 800, 600)
            self.assertIsNotNone(hangar_view)

            # Test Settings render
            cached_calendars = [{"name": "Work", "enabled": True}, {"name": "Personal", "enabled": False}]
            settings_view = settings.render(mock_container, 800, 600, mock_config, cached_calendars)
            self.assertIsNotNone(settings_view)

        except ImportError as e:
            self.fail(f"Failed to import UI controllers: {e}")

    @unittest.skipIf(sys.platform != "darwin", "macOS specific UI tests")
    def test_menu_bar_build_with_upcoming_events(self):
        from ui.macos.menu_bar_app import QuakMeetingMenuBar
        from datetime import datetime, timedelta
        now = datetime.now().astimezone()
        menu_bar = QuakMeetingMenuBar.alloc().init()
        self.assertIsNotNone(menu_bar)

        # Set upcoming meeting for today
        m = {
            "title": "Upcoming Lecture",
            "start_time": now + timedelta(minutes=30),
            "end_time": now + timedelta(minutes=90),
            "pilot_type": "owl",
            "travel_time_minutes": 15,
            "departure_time": now + timedelta(minutes=15)
        }
        menu_bar.meetings = [m]
        # Must build menu without raising AttributeError
        menu_bar.build_menu()
        self.assertGreater(menu_bar.menu.numberOfItems(), 0)

    @unittest.skipIf(sys.platform != "darwin", "macOS specific UI tests")
    def test_reminder_event_payload_shows_banner(self):
        """The EventBus payload includes event_dict as well as meeting/stage."""
        from ui.macos.menu_bar_app import QuakMeetingMenuBar
        from unittest.mock import patch

        payload = {"title": "Banner regression test", "reminder_stage": 0}

        with patch("ui.macos.menu_bar_app.show_banner_async") as show_banner:
            QuakMeetingMenuBar._on_reminder_triggered(
                object(), meeting=None, stage=0, event_dict=payload
            )

        show_banner.assert_called_once_with(payload)

    @unittest.skipIf(sys.platform != "darwin", "macOS specific UI tests")
    def test_show_dashboard_accepts_tab_index(self):
        from ui.macos.dashboard_window import show_dashboard
        # Ensure show_dashboard accepts positional tab_index parameters (0, 1, 2, None)
        try:
            show_dashboard()
            show_dashboard(0)
            show_dashboard(2)
        except TypeError as e:
            self.fail(f"show_dashboard raised TypeError with positional tab_index: {e}")

    def test_app_launcher_respects_qt_flag(self):
        from unittest.mock import patch
        from ui.app_launcher import launch_application

        with patch("sys.argv", ["main.py", "--qt"]), \
             patch("ui.linux.qt_tray_app.run_qt_tray_app") as mock_qt_tray:
            launch_application()
            mock_qt_tray.assert_called_once()

if __name__ == '__main__':
    unittest.main()
