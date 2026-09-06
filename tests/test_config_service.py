import unittest
from core.services.config_service import ConfigService, DEFAULT_CONFIG

class TestConfigService(unittest.TestCase):
    def test_default_config_keys(self):
        cfg = ConfigService()
        self.assertIsNotNone(cfg.get("meeting_reminder_stages"))
        self.assertIsNotNone(cfg.get("travel_reminder_stages"))
        self.assertIsNotNone(cfg.get("flight_speed"))
        self.assertTrue(cfg.get("mute_during_lessons"))
        self.assertIn("food", cfg.get("custom_keywords"))
        self.assertIn("study", cfg.get("custom_keywords"))
        self.assertIn("class", cfg.get("custom_keywords"))
        self.assertIn("exam", cfg.get("custom_keywords"))
        self.assertEqual(cfg.get_custom_keywords("chef"), cfg.get_custom_keywords("food"))
        self.assertEqual(cfg.get_custom_keywords("owl"), cfg.get_custom_keywords("study"))
        self.assertEqual(cfg.get_custom_keywords("lesson"), cfg.get_custom_keywords("class"))
        self.assertEqual(cfg.get_custom_keywords("lecture"), cfg.get_custom_keywords("class"))

    def test_get_with_fallback(self):
        cfg = ConfigService()
        val = cfg.get("non_existent_key_xyz", default="fallback_val")
        self.assertEqual(val, "fallback_val")

if __name__ == "__main__":
    unittest.main()
