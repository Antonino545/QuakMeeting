"""
Unit Tests for QuakMeeting Autostart Subsystem.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
import xml.etree.ElementTree as ET

from core.autostart import (
    generate_launchagent_plist,
    _get_target_app_path,
    is_autostart_enabled,
    enable_autostart,
    disable_autostart,
    toggle_autostart,
    PLIST_LABEL,
    PLIST_PATH
)

class TestAutostartService(unittest.TestCase):
    def test_generate_launchagent_plist(self):
        plist_str = generate_launchagent_plist("/Applications/QuakMeeting.app")
        self.assertIn("<string>com.quakmeeting.app</string>", plist_str)
        self.assertIn("<string>/Applications/QuakMeeting.app</string>", plist_str)
        self.assertIn("<string>--silent</string>", plist_str)
        self.assertIn("<string>--autostart</string>", plist_str)
        self.assertIn("<key>LimitLoadToSessionType</key>", plist_str)
        self.assertIn("<string>Aqua</string>", plist_str)
        self.assertIn("<key>RunAtLoad</key>", plist_str)
        
        # Verify valid XML parsing
        root = ET.fromstring(plist_str)
        self.assertEqual(root.tag, "plist")

    def test_get_target_app_path(self):
        path = _get_target_app_path()
        self.assertTrue(isinstance(path, str))
        self.assertTrue(path.endswith(".app"))

    @patch("core.autostart._check_smappservice_status", return_value=None)
    @patch("os.path.exists")
    def test_is_autostart_enabled_plist(self, mock_exists, mock_sm):
        mock_exists.return_value = True
        self.assertTrue(isout := is_autostart_enabled())
        mock_exists.assert_called_with(PLIST_PATH)

        mock_exists.return_value = False
        self.assertFalse(is_autostart_enabled())

    @patch("core.autostart._check_smappservice_status", return_value=True)
    def test_is_autostart_enabled_smappservice(self, mock_sm):
        self.assertTrue(is_autostart_enabled())

    @patch("subprocess.run")
    @patch("builtins.open", create=True)
    @patch("os.makedirs")
    def test_enable_autostart(self, mock_mkdirs, mock_open, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = enable_autostart()
        self.assertTrue(res)
        mock_mkdirs.assert_called_once()
        mock_open.assert_called_once()

    @patch("subprocess.run")
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_disable_autostart(self, mock_remove, mock_exists, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = disable_autostart()
        self.assertTrue(res)
        mock_remove.assert_called_with(PLIST_PATH)

    @patch("core.autostart.is_autostart_enabled")
    @patch("core.autostart.disable_autostart", return_value=True)
    @patch("core.autostart.enable_autostart", return_value=True)
    def test_toggle_autostart(self, mock_enable, mock_disable, mock_is_enabled):
        mock_is_enabled.return_value = True
        state = toggle_autostart()
        self.assertFalse(state)
        mock_disable.assert_called_once()

        mock_is_enabled.return_value = False
        state = toggle_autostart()
        self.assertTrue(state)
        mock_enable.assert_called_once()

if __name__ == "__main__":
    unittest.main()
