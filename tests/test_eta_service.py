import unittest
from datetime import datetime, timedelta
from core.services.eta_service import ETAService, APPLE_MAPS_FLAGS, MODE_ICONS
from core.services.config_service import ConfigService

class TestETAService(unittest.TestCase):
    def setUp(self):
        self.eta_service = ETAService()

    def test_apple_maps_url_generation_all_modes(self):
        # 1. Transit (Mezzi Pubblici) -> dirflg=r
        url_transit = self.eta_service._build_apple_maps_url("Corso Francia 10, Torino", "Politecnico di Torino", mode="transit")
        self.assertIn("dirflg=r", url_transit)
        self.assertIn("saddr=", url_transit)
        self.assertIn("daddr=", url_transit)

        # 2. Automobile (Driving) -> dirflg=d
        url_auto = self.eta_service._build_apple_maps_url("Corso Francia 10, Torino", "Politecnico di Torino", mode="automobile")
        self.assertIn("dirflg=d", url_auto)

        # 3. Walking (A Piedi) -> dirflg=w
        url_walk = self.eta_service._build_apple_maps_url("Piazza Castello, Torino", "Mole Antonelliana", mode="walking")
        self.assertIn("dirflg=w", url_walk)

        # 4. Bicycling (In Bici) -> dirflg=b
        url_bike = self.eta_service._build_apple_maps_url("Piazza Castello, Torino", "Parco del Valentino", mode="bicycling")
        self.assertIn("dirflg=b", url_bike)

    def test_departure_time_calculation(self):
        start = datetime(2026, 8, 22, 15, 0, 0)
        travel_minutes = 25
        buffer_minutes = 10

        dep_time = self.eta_service.get_departure_time(start, travel_minutes, buffer_minutes=buffer_minutes)
        expected = datetime(2026, 8, 22, 14, 25, 0)
        self.assertEqual(dep_time, expected)

    def test_mode_icons_mapping(self):
        self.assertEqual(MODE_ICONS["transit"], "🚆")
        self.assertEqual(MODE_ICONS["automobile"], "🚗")
        self.assertEqual(MODE_ICONS["walking"], "🚶")
        self.assertEqual(MODE_ICONS["bicycling"], "🚲")

if __name__ == "__main__":
    unittest.main()
