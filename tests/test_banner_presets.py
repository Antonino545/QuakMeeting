"""
Unit tests for shared banner presets and platform decoupling.
"""
import unittest
import sys
from ui.common.banner_presets import get_test_preset, get_update_preset, get_up_to_date_preset, get_update_error_preset

class TestBannerPresets(unittest.TestCase):
    def test_all_pilot_presets_exist(self):
        pilots = ["duck", "chef", "captain", "owl", "gym", "driver", "zen_duck", "platypus", "squirrel"]
        for p in pilots:
            preset = get_test_preset(p)
            self.assertIsInstance(preset, dict)
            self.assertEqual(preset.get("pilot_type"), p)
            self.assertIn("title", preset)
            self.assertIn("action_btn_text", preset)
            self.assertIn("start_time", preset)

    def test_fallback_pilot_preset(self):
        preset = get_test_preset("unknown_mascot")
        self.assertEqual(preset.get("pilot_type"), "duck")

    def test_update_preset(self):
        up = get_update_preset("v2.0.0", "https://github.com/Antonino545/QuakMeeting/releases/tag/v2.0.0")
        self.assertIsInstance(up, dict)
        self.assertTrue(up.get("is_update_banner"))
        self.assertFalse(up.get("is_up_to_date", False))
        self.assertIn("v2.0.0", up.get("title", ""))
        self.assertEqual(up.get("action_url"), "https://github.com/Antonino545/QuakMeeting/releases/tag/v2.0.0")

    def test_up_to_date_preset(self):
        utd = get_up_to_date_preset("1.0.49")
        self.assertIsInstance(utd, dict)
        self.assertTrue(utd.get("is_update_banner"))
        self.assertTrue(utd.get("is_up_to_date"))
        self.assertIn("1.0.49", utd.get("subtitle", ""))
        self.assertIn("title", utd)
        self.assertIn("action_btn_text", utd)

    def test_update_error_preset(self):
        err = get_update_error_preset("Network connection lost")
        self.assertIsInstance(err, dict)
        self.assertTrue(err.get("is_update_banner"))
        self.assertTrue(err.get("is_update_error"))
        self.assertIn("Network connection lost", err.get("subtitle", ""))

    def test_common_presets_do_not_import_platform_ui(self):
        # Ensure ui.common.banner_presets does not require ui.linux or ui.macos
        import ui.common.banner_presets as bp
        self.assertIsNotNone(bp.get_test_preset)
        self.assertIsNotNone(bp.get_update_preset)
        self.assertIsNotNone(bp.get_up_to_date_preset)
        self.assertIsNotNone(bp.get_update_error_preset)
        self.assertFalse(hasattr(bp, "Qt"))
        self.assertFalse(hasattr(bp, "NSView"))

if __name__ == "__main__":
    unittest.main()
