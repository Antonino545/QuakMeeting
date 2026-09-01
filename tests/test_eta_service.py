import unittest
from unittest.mock import patch, MagicMock
import json
import io
from datetime import datetime
from core.services.eta_service import ETAService, MODE_ICONS, MODE_LABELS
from core.services.config_service import ConfigService

class TestETAService(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=ConfigService)
        self.mock_config.get.side_effect = lambda key, default=None: {
            "transport_mode": "transit",
            "eta_buffer_minutes": 10
        }.get(key, default)
        self.eta_service = ETAService(config=self.mock_config)
        self.eta_service._memory_cache = {}

    def test_apple_maps_url_generation_all_modes(self):
        # 1. Transit (Public Transit) -> dirflg=r
        url_transit = self.eta_service._build_apple_maps_url("Corso Francia 10, Torino", "Politecnico di Torino", mode="transit")
        self.assertIn("dirflg=r", url_transit)
        self.assertIn("saddr=Corso%20Francia%2010%2C%20Torino", url_transit)
        self.assertIn("daddr=Politecnico%20di%20Torino", url_transit)

        # 2. Automobile (Driving) -> dirflg=d
        url_auto = self.eta_service._build_apple_maps_url("Corso Francia 10, Torino", "Politecnico di Torino", mode="automobile")
        self.assertIn("dirflg=d", url_auto)

        # 3. Walking -> dirflg=w
        url_walk = self.eta_service._build_apple_maps_url("Piazza Castello, Torino", "Mole Antonelliana", mode="walking")
        self.assertIn("dirflg=w", url_walk)

        # 4. Bicycling -> dirflg=b
        url_bike = self.eta_service._build_apple_maps_url("Piazza Castello, Torino", "Parco del Valentino", mode="bicycling")
        self.assertIn("dirflg=b", url_bike)

        # 5. Destination only (no origin)
        url_dest_only = self.eta_service._build_apple_maps_url(None, "Politecnico di Torino", mode="transit")
        self.assertNotIn("saddr=", url_dest_only)
        self.assertIn("daddr=Politecnico%20di%20Torino", url_dest_only)

    def test_google_maps_url_generation_all_modes(self):
        # 1. Transit
        url_transit = self.eta_service._build_google_maps_url("Corso Francia 10, Torino", "Politecnico di Torino", mode="transit")
        self.assertIn("travelmode=transit", url_transit)
        self.assertIn("origin=Corso%20Francia%2010%2C%20Torino", url_transit)
        self.assertIn("destination=Politecnico%20di%20Torino", url_transit)

        # 2. Automobile (driving)
        url_auto = self.eta_service._build_google_maps_url("Corso Francia 10, Torino", "Politecnico di Torino", mode="automobile")
        self.assertIn("travelmode=driving", url_auto)

        # 3. Walking
        url_walk = self.eta_service._build_google_maps_url("Piazza Castello", "Mole", mode="walking")
        self.assertIn("travelmode=walking", url_walk)

        # 4. Bicycling
        url_bike = self.eta_service._build_google_maps_url("Piazza Castello", "Mole", mode="bicycling")
        self.assertIn("travelmode=bicycling", url_bike)

        # 5. Destination only
        url_dest_only = self.eta_service._build_google_maps_url("", "Politecnico di Torino", mode="transit")
        self.assertNotIn("origin=", url_dest_only)
        self.assertIn("destination=Politecnico%20di%20Torino", url_dest_only)

    def test_build_maps_url_platform_dispatch(self):
        with patch("sys.platform", "darwin"):
            url_mac = self.eta_service.build_maps_url("Home", "Office", "automobile")
            self.assertTrue(url_mac.startswith("https://maps.apple.com/"))

        with patch("sys.platform", "linux"):
            url_linux = self.eta_service.build_maps_url("Home", "Office", "automobile")
            self.assertTrue(url_linux.startswith("https://www.google.com/maps/dir/"))

    def test_calculate_eta_empty_or_invalid_inputs(self):
        self.assertIsNone(self.eta_service.calculate_eta("", "Politecnico"))
        self.assertIsNone(self.eta_service.calculate_eta("Home", ""))
        self.assertIsNone(self.eta_service.calculate_eta("   ", "   "))
        self.assertIsNone(self.eta_service.calculate_eta(None, "Politecnico")) # type: ignore

    @patch("core.services.eta_service.ETAService._calculate_apple_maps_eta")
    @patch("urllib.request.urlopen")
    def test_calculate_eta_with_native_apple_maps(self, mock_urlopen, mock_apple_eta):
        mock_apple_eta.return_value = (28, 4.2)
        geo_resp_1 = io.BytesIO(json.dumps([{"lat": "45.0625", "lon": "7.6622"}]).encode("utf-8"))
        geo_resp_2 = io.BytesIO(json.dumps([{"lat": "45.0705", "lon": "7.6866"}]).encode("utf-8"))
        mock_urlopen.side_effect = [geo_resp_1, geo_resp_2]

        result = self.eta_service.calculate_eta("Corso Duca degli Abruzzi 24", "Piazza Castello", mode="transit")
        self.assertIsNotNone(result)
        self.assertEqual(result["duration_minutes"], 28)
        self.assertEqual(result["distance_km"], 4.2)
        self.assertEqual(result["transport_mode"], "transit")

    @patch("core.services.eta_service.ETAService._calculate_apple_maps_eta", return_value=None)
    @patch("urllib.request.urlopen")
    def test_calculate_eta_with_mocked_osrm(self, mock_urlopen, mock_apple_eta):
        # Mock Nominatim geocoding responses (Home: 45.06, 7.66; Dest: 45.07, 7.68)
        geo_resp_1 = io.BytesIO(json.dumps([{"lat": "45.0625", "lon": "7.6622"}]).encode("utf-8"))
        geo_resp_2 = io.BytesIO(json.dumps([{"lat": "45.0705", "lon": "7.6866"}]).encode("utf-8"))

        # Mock OSRM route (duration: 600 seconds = 10 min, distance: 3000 meters = 3.0 km)
        # Driving in urban traffic: 10 * 1.35 + 4 = 17.5 ~ 18 min
        osrm_resp = io.BytesIO(json.dumps({
            "routes": [{"duration": 600, "distance": 3000}]
        }).encode("utf-8"))

        mock_urlopen.side_effect = [geo_resp_1, geo_resp_2, osrm_resp]

        result = self.eta_service.calculate_eta("Corso Duca degli Abruzzi 24", "Piazza Castello", mode="automobile")

        self.assertIsNotNone(result)
        self.assertEqual(result["duration_minutes"], 18)
        self.assertEqual(result["distance_km"], 3.0)
        self.assertEqual(result["transport_mode"], "automobile")
        self.assertEqual(result["mode_icon"], "🚗")

    @patch("core.services.eta_service.ETAService._calculate_apple_maps_eta", return_value=None)
    @patch("urllib.request.urlopen")
    def test_calculate_eta_transit_mode_multiplier(self, mock_urlopen, mock_apple_eta):
        geo_resp_1 = io.BytesIO(json.dumps([{"lat": "45.06", "lon": "7.66"}]).encode("utf-8"))
        geo_resp_2 = io.BytesIO(json.dumps([{"lat": "45.07", "lon": "7.68"}]).encode("utf-8"))
        # 10 min drive (600 sec), 3.0 km -> realistic city transit includes walking & wait: 10 * 1.8 + 12 = 30 min
        osrm_resp = io.BytesIO(json.dumps({
            "routes": [{"duration": 600, "distance": 3000}]
        }).encode("utf-8"))

        mock_urlopen.side_effect = [geo_resp_1, geo_resp_2, osrm_resp]

        result = self.eta_service.calculate_eta("Home", "Campus", mode="transit")

        self.assertIsNotNone(result)
        self.assertEqual(result["duration_minutes"], 30)
        self.assertEqual(result["transport_mode"], "transit")
        self.assertEqual(result["mode_icon"], "🚆")

    @patch("core.services.eta_service.ETAService._calculate_apple_maps_eta", return_value=None)
    @patch("urllib.request.urlopen")
    def test_calculate_eta_walking_and_bicycling(self, mock_urlopen, mock_apple_eta):
        # 1. Walking: 5.0 km (5000m, 3600 sec) -> 60 min
        geo_resp_1 = io.BytesIO(json.dumps([{"lat": "45.0", "lon": "7.0"}]).encode("utf-8"))
        geo_resp_2 = io.BytesIO(json.dumps([{"lat": "45.1", "lon": "7.1"}]).encode("utf-8"))
        osrm_resp_walk = io.BytesIO(json.dumps({
            "routes": [{"duration": 3600, "distance": 5000}]
        }).encode("utf-8"))

        mock_urlopen.side_effect = [geo_resp_1, geo_resp_2, osrm_resp_walk]

        result_walk = self.eta_service.calculate_eta("Point A", "Point B", mode="walking")
        self.assertEqual(result_walk["duration_minutes"], 60)
        self.assertEqual(result_walk["mode_icon"], "🚶")

    def test_calculate_eta_memory_caching(self):
        cache_key = "route_home_office_transit"
        self.eta_service._memory_cache[cache_key] = {
            "duration_minutes": 30,
            "distance_km": 6.5,
            "transport_mode": "transit",
            "mode_icon": "🚆",
            "mode_label": "Public Transit",
            "maps_url": "https://maps.apple.com/",
            "origin": "Home",
            "destination": "Office"
        }

        # Should retrieve cached value instantly without urlopen
        cached_result = self.eta_service.calculate_eta("Home", "Office", mode="transit")
        self.assertEqual(cached_result["duration_minutes"], 30)
        self.assertEqual(cached_result["distance_km"], 6.5)

    def test_clear_cache(self):
        self.eta_service._memory_cache["test_key"] = {"duration_minutes": 25}
        self.eta_service.clear_cache()
        self.assertEqual(len(self.eta_service._memory_cache), 0)

    def test_departure_time_calculation(self):
        start = datetime(2026, 8, 22, 15, 0, 0)
        travel_minutes = 25
        buffer_minutes = 10

        dep_time = self.eta_service.get_departure_time(start, travel_minutes, buffer_minutes=buffer_minutes)
        expected = datetime(2026, 8, 22, 14, 25, 0)
        self.assertEqual(dep_time, expected)

    def test_departure_time_default_buffer_from_config(self):
        start = datetime(2026, 8, 22, 15, 0, 0)
        travel_minutes = 20
        # When buffer_minutes is omitted, use config default (10m) -> 15:00 - 30m = 14:30
        dep_time = self.eta_service.get_departure_time(start, travel_minutes)
        expected = datetime(2026, 8, 22, 14, 30, 0)
        self.assertEqual(dep_time, expected)

    def test_mode_icons_and_labels_mapping(self):
        self.assertEqual(MODE_ICONS["transit"], "🚆")
        self.assertEqual(MODE_ICONS["automobile"], "🚗")
        self.assertEqual(MODE_ICONS["walking"], "🚶")
        self.assertEqual(MODE_ICONS["bicycling"], "🚲")
        self.assertEqual(MODE_LABELS["transit"], "Public Transit")
        self.assertEqual(MODE_LABELS["automobile"], "Driving")

    def test_validate_address_formats(self):
        from core.services.eta_service import validate_address

        # Valid cases
        self.assertEqual(validate_address("")[0], True)
        self.assertEqual(validate_address("   ")[0], True)
        self.assertEqual(validate_address("Corso Duca degli Abruzzi 24, Torino")[0], True)
        self.assertEqual(validate_address("Via Roma 10, 10121 Torino, Italia")[0], True)
        self.assertEqual(validate_address("Baker Street 221B, London")[0], True)
        self.assertEqual(validate_address("Piazza San Carlo, Torino")[0], True)
        self.assertEqual(validate_address("Torino")[0], True)
        self.assertEqual(validate_address("Politecnico")[0], True)

        # Invalid cases
        self.assertEqual(validate_address("a")[0], False)

if __name__ == "__main__":
    unittest.main()
