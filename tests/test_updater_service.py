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

    def test_mocked_check_for_updates(self):
        from unittest.mock import patch, MagicMock
        from core.services.event_bus import event_bus
        import json

        mock_payload = json.dumps({
            "tag_name": "v9.9.9",
            "name": "QuakMeeting 9.9.9",
            "body": "Awesome new release",
            "html_url": "https://github.com/Antonino545/QuakMeeting/releases/tag/v9.9.9",
            "assets": [{"name": "quakmeeting_9.9.9_amd64.deb", "browser_download_url": "https://example.com/quak.deb"}],
            "published_at": "2026-08-25T12:00:00Z"
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_payload
        mock_resp.__enter__.return_value = mock_resp

        events_received = []
        event_bus.subscribe("UPDATE_AVAILABLE", lambda **k: events_received.append(k))

        with patch("urllib.request.urlopen", return_value=mock_resp):
            info = self.updater.check_for_updates(background=False)
            self.assertIsNotNone(info)
            self.assertTrue(info["has_update"])
            self.assertEqual(info["tag_name"], "v9.9.9")
    def test_mocked_install_linux_update(self):
        from unittest.mock import patch, MagicMock
        from core.services.event_bus import event_bus

        installed_events = []
        event_bus.subscribe("UPDATE_INSTALLED", lambda **k: installed_events.append(True))

        mock_run_res = MagicMock(returncode=0, stdout="Installed", stderr="")
        with patch("subprocess.run", return_value=mock_run_res), \
             patch("subprocess.Popen") as mock_popen, \
             patch("os._exit") as mock_exit, \
             patch("time.sleep"):
            success = self.updater._install_linux_update("/tmp/mock_package.deb")
            self.assertTrue(success)
            self.assertTrue(len(installed_events) >= 1)
            mock_popen.assert_called_once()
            mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    unittest.main()
