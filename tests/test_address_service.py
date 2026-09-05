import unittest
from unittest.mock import patch, MagicMock
import json
import io
from core.services.address_service import AddressService, AddressCandidate


class TestAddressService(unittest.TestCase):
    def setUp(self):
        self.service = AddressService()
        self.service._suggestions_cache = {}
        self.service._verification_cache = {}

    def test_short_query_returns_empty(self):
        candidates = self.service.search_suggestions("a")
        self.assertEqual(candidates, [])
        candidates = self.service.search_suggestions("  ")
        self.assertEqual(candidates, [])

    @patch("urllib.request.urlopen")
    def test_nominatim_search_success(self, mock_urlopen):
        mock_response_data = [
            {
                "lat": "45.0625",
                "lon": "7.6621",
                "display_name": "Corso Duca degli Abruzzi, 24, Crocetta, Torino, Piemonte, 10129, Italia",
                "address": {
                    "road": "Corso Duca degli Abruzzi",
                    "house_number": "24",
                    "city": "Torino",
                    "postcode": "10129",
                    "state": "Piemonte",
                    "country": "Italia"
                }
            }
        ]
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        candidates = self.service.search_suggestions("Corso Duca", city_context="Torino", limit=5)
        self.assertEqual(len(candidates), 1)
        c = candidates[0]
        self.assertEqual(c.short_address, "Corso Duca degli Abruzzi 24")
        self.assertEqual(c.city, "Torino")
        self.assertEqual(c.postcode, "10129")
        self.assertAlmostEqual(c.lat, 45.0625)
        self.assertAlmostEqual(c.lon, 7.6621)
        self.assertIn("Corso Duca degli Abruzzi 24", c.display_name)

    @patch("urllib.request.urlopen")
    def test_photon_fallback_when_nominatim_empty(self, mock_urlopen):
        # First call (Nominatim) returns empty list []
        # Second call (Photon) returns GeoJSON features
        mock_nom_resp = MagicMock()
        mock_nom_resp.read.return_value = b"[]"
        mock_nom_resp.__enter__.return_value = mock_nom_resp

        mock_photon_data = {
            "features": [
                {
                    "geometry": {"coordinates": [7.6621, 45.0625]},
                    "properties": {
                        "name": "Politecnico di Torino",
                        "street": "Corso Duca degli Abruzzi",
                        "housenumber": "24",
                        "city": "Torino",
                        "postcode": "10129",
                        "state": "Piemonte",
                        "country": "Italy"
                    }
                }
            ]
        }
        mock_photon_resp = MagicMock()
        mock_photon_resp.read.return_value = json.dumps(mock_photon_data).encode("utf-8")
        mock_photon_resp.__enter__.return_value = mock_photon_resp

        mock_urlopen.side_effect = [mock_nom_resp, mock_photon_resp]

        candidates = self.service.search_suggestions("PoliTo", limit=3)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].city, "Torino")
        self.assertAlmostEqual(candidates[0].lat, 45.0625)

    def test_verify_address_empty_is_valid(self):
        is_valid, cand, err = self.service.verify_address("")
        self.assertTrue(is_valid)
        self.assertIsNone(cand)
        self.assertIsNone(err)

    def test_verify_address_too_short(self):
        is_valid, cand, err = self.service.verify_address("ab")
        self.assertFalse(is_valid)
        self.assertEqual(err, "too_short")

    @patch.object(AddressService, "search_suggestions")
    def test_verify_address_found(self, mock_search):
        mock_cand = AddressCandidate(
            display_name="Corso Duca degli Abruzzi 24, Torino",
            short_address="Corso Duca degli Abruzzi 24",
            city="Torino",
            lat=45.06,
            lon=7.66
        )
        mock_search.return_value = [mock_cand]

        is_valid, cand, err = self.service.verify_address("Corso Duca 24", city_context="Torino")
        self.assertTrue(is_valid)
        self.assertEqual(cand, mock_cand)
        self.assertIsNone(err)

    @patch.object(AddressService, "search_suggestions")
    def test_verify_address_not_found(self, mock_search):
        mock_search.return_value = []
        is_valid, cand, err = self.service.verify_address("NonExistentPlace 99999")
        self.assertFalse(is_valid)
        self.assertIsNone(cand)
        self.assertEqual(err, "not_found")

    @patch("sys.platform", "darwin")
    def test_get_map_url_macos(self):
        url = AddressService.get_map_url("Corso Duca 24, Torino", 45.06, 7.66)
        self.assertIn("maps.apple.com", url)
        self.assertIn("ll=45.060000,7.660000", url)

    @patch("sys.platform", "linux")
    def test_get_map_url_linux(self):
        url = AddressService.get_map_url("Corso Duca 24, Torino", 45.06, 7.66)
        self.assertIn("openstreetmap.org", url)
        self.assertIn("mlat=45.060000", url)


if __name__ == "__main__":
    unittest.main()
