import unittest
from unittest.mock import MagicMock
import sys

# Only run macOS UI tests on macOS
class TestDashboardUI(unittest.TestCase):
    @unittest.skipIf(sys.platform != "darwin", "macOS specific UI tests")
    def test_instantiate_and_render_tabs(self):
        # Avoid showing actual windows during test
        try:
            from ui.dashboard_tabs.agenda_tab import AgendaTabController
            from ui.dashboard_tabs.hangar_tab import HangarTabController
            from ui.dashboard_tabs.settings_tab import SettingsTabController
            
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

if __name__ == '__main__':
    unittest.main()
