"""
Unit tests for shared banner presets and platform decoupling.
"""
import unittest
import sys
from ui.common.banner_presets import get_test_preset, get_update_preset

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
        self.assertIn("v2.0.0", up.get("title", ""))
        self.assertEqual(up.get("action_url"), "https://github.com/Antonino545/QuakMeeting/releases/tag/v2.0.0")

    def test_common_presets_do_not_import_platform_ui(self):
        # Ensure ui.common.banner_presets does not require ui.linux or ui.macos
        import ui.common.banner_presets as bp
        self.assertIsNotNone(bp.get_test_preset)
        self.assertIsNotNone(bp.get_update_preset)
        self.assertFalse(hasattr(bp, "Qt"))
        self.assertFalse(hasattr(bp, "NSView"))

if __name__ == "__main__":
    unittest.main()
