import unittest
from core.services.config_service import ConfigService, DEFAULT_CONFIG
from core.domain.classifier import EventClassifier
from core.domain.models import EventCategory

class TestKeywordManager(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigService()
        self.original_custom_keywords = {
            k: list(v) for k, v in self.cfg.get_custom_keywords().items()
        }
        # Provide clean isolated state for keyword tests
        self.cfg.set("custom_keywords", {
            "food": ["dinner", "pizza", "cooking"],
            "sport": ["workout", "padel"],
            "study": ["exam", "thesis"],
        })

    def tearDown(self):
        # Restore initial configuration
        self.cfg.set("custom_keywords", self.original_custom_keywords)

    def test_get_custom_keywords(self):
        all_kw = self.cfg.get_custom_keywords()
        self.assertIn("food", all_kw)
        self.assertEqual(all_kw["food"], ["dinner", "pizza", "cooking"])

        # Category key
        sport_kw = self.cfg.get_custom_keywords("sport")
        self.assertEqual(sport_kw, ["workout", "padel"])

        # Backward compatibility with pilot aliases (gym -> sport, chef -> food)
        gym_kw = self.cfg.get_custom_keywords("gym")
        self.assertEqual(gym_kw, ["workout", "padel"])
        chef_kw = self.cfg.get_custom_keywords("chef")
        self.assertEqual(chef_kw, ["dinner", "pizza", "cooking"])

        empty_kw = self.cfg.get_custom_keywords("unknown_category")
        self.assertEqual(empty_kw, [])

    def test_add_custom_keyword(self):
        # Add to standard category
        success = self.cfg.add_custom_keyword("sport", "Crossfit")
        self.assertTrue(success)
        self.assertIn("crossfit", self.cfg.get_custom_keywords("sport"))

        # Deduplication & case-insensitive check
        success_dup = self.cfg.add_custom_keyword("sport", "CROSSFIT")
        self.assertFalse(success_dup)
        self.assertEqual(self.cfg.get_custom_keywords("sport").count("crossfit"), 1)

        # Adding via alias (captain -> travel)
        success_alias = self.cfg.add_custom_keyword("captain", "Flight 101")
        self.assertTrue(success_alias)
        self.assertIn("flight 101", self.cfg.get_custom_keywords("travel"))

    def test_remove_custom_keyword(self):
        success = self.cfg.remove_custom_keyword("food", "pizza")
        self.assertTrue(success)
        self.assertNotIn("pizza", self.cfg.get_custom_keywords("food"))

        # Removing non-existent
        success_absent = self.cfg.remove_custom_keyword("food", "nonexistent_sushi")
        self.assertFalse(success_absent)

    def test_reset_custom_keywords(self):
        self.cfg.add_custom_keyword("food", "custom_tacos")
        self.assertIn("custom_tacos", self.cfg.get_custom_keywords("food"))

        self.cfg.reset_custom_keywords("food")
        default_food = DEFAULT_CONFIG["custom_keywords"]["food"]
        self.assertEqual(self.cfg.get_custom_keywords("food"), default_food)

        # Reset all
        self.cfg.add_custom_keyword("sport", "pilates")
        self.cfg.reset_custom_keywords()
        self.assertEqual(self.cfg.get_custom_keywords(), DEFAULT_CONFIG["custom_keywords"])

    def test_classifier_with_category_custom_keywords(self):
        classifier = EventClassifier()
        # Pass standard category keywords
        custom_kw = {
            "study": ["laurea celebration"],
            "sport": ["bouldering session"],
            "food": ["poke bowl lunch"]
        }
        meeting_sport = classifier.classify(
            title="Bouldering session with Marco",
            location="Climbing Gym",
            custom_keywords=custom_kw
        )
        self.assertEqual(meeting_sport.event_type, EventCategory.SPORT.value)
        self.assertEqual(meeting_sport.outfit, "gym")

        meeting_study = classifier.classify(
            title="Final Laurea Celebration",
            location="Room 3B",
            custom_keywords=custom_kw
        )
        self.assertEqual(meeting_study.event_type, EventCategory.STUDY.value)
        self.assertEqual(meeting_study.outfit, "student")

        meeting_food = classifier.classify(
            title="Poke bowl lunch with team",
            custom_keywords=custom_kw
        )
        self.assertEqual(meeting_food.event_type, EventCategory.FOOD.value)
        self.assertEqual(meeting_food.outfit, "chef")

if __name__ == "__main__":
    unittest.main()
