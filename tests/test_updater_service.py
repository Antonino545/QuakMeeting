"""
Unit tests for Auto-Updater Service and SemVer comparison.
"""
import unittest
from core.services.updater_service import UpdaterService

class TestUpdaterService(unittest.TestCase):
    def setUp(self):
        self.updater = UpdaterService()

    def test_parse_semver(self):
        self.assertEqual(self.updater.parse_semver("v1.2.3"), (1, 2, 3))
        self.assertEqual(self.updater.parse_semver("1.0.0"), (1, 0, 0))
        self.assertEqual(self.updater.parse_semver("2.5"), (2, 5, 0))
        self.assertEqual(self.updater.parse_semver("v0.9.1-beta"), (0, 9, 1))

    def test_is_newer_version(self):
        self.assertTrue(self.updater.is_newer_version("v1.1.0", "1.0.0"))
        self.assertTrue(self.updater.is_newer_version("2.0.0", "1.9.9"))
        self.assertTrue(self.updater.is_newer_version("1.0.1", "1.0.0"))
        self.assertFalse(self.updater.is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(self.updater.is_newer_version("0.9.0", "1.0.0"))

    def test_platform_asset_resolution(self):
        mock_assets = [
            {"name": "quakmeeting_1.1.0_amd64.deb", "browser_download_url": "https://example.com/quak.deb"},
            {"name": "QuakMeeting-macOS.dmg", "browser_download_url": "https://example.com/quak.dmg"}
        ]
        asset = self.updater.get_platform_asset(mock_assets)
        self.assertIsNotNone(asset)
        self.assertTrue(asset["name"].endswith(".dmg") or asset["name"].endswith(".deb"))

if __name__ == "__main__":
    unittest.main()
