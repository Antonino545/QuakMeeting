import unittest
from datetime import datetime, timezone
from ui.common.tray_viewmodel import TrayViewModel, MODE_ICONS_TRAY

class TestTrayViewModelTransportMode(unittest.TestCase):
    def test_format_next_event_label_modes(self):
        dep = datetime(2026, 8, 30, 8, 30, tzinfo=timezone.utc)

        # Transit
        lbl_transit = TrayViewModel.format_next_event_label(
            "🦆", "09:00", "Team Sync", travel_minutes=25, departure_time=dep, transport_mode="transit", lang="en"
        )
        self.assertIn("🚆", lbl_transit)
        self.assertNotIn("🚗", lbl_transit)

        # Automobile
        lbl_auto = TrayViewModel.format_next_event_label(
            "🦆", "09:00", "Client Visit", travel_minutes=35, departure_time=dep, transport_mode="automobile", lang="en"
        )
        self.assertIn("🚗", lbl_auto)

        # Walking
        lbl_walk = TrayViewModel.format_next_event_label(
            "🦆", "09:00", "Lunch", travel_minutes=10, departure_time=dep, transport_mode="walking", lang="en"
        )
        self.assertIn("🚶", lbl_walk)

        # Bicycling
        lbl_bike = TrayViewModel.format_next_event_label(
            "🦆", "09:00", "Gym", travel_minutes=15, departure_time=dep, transport_mode="bicycling", lang="en"
        )
        self.assertIn("🚲", lbl_bike)

    def test_format_travel_info_modes(self):
        dep = datetime(2026, 8, 30, 8, 30, tzinfo=timezone.utc)
        info_transit = TrayViewModel.format_travel_info(20, dep, transport_mode="transit", lang="en")
        self.assertIn("🚆", info_transit)

        info_auto = TrayViewModel.format_travel_info(20, dep, transport_mode="automobile", lang="en")
        self.assertIn("🚗", info_auto)

        info_walk = TrayViewModel.format_travel_info(15, dep, transport_mode="walking", lang="en")
        self.assertIn("🚶", info_walk)

        info_bike = TrayViewModel.format_travel_info(10, dep, transport_mode="bicycling", lang="en")
        self.assertIn("🚲", info_bike)

if __name__ == "__main__":
    unittest.main()
