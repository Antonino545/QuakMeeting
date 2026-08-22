import unittest
from datetime import datetime
from core.domain.classifier import EventClassifier
from core.domain.models import PilotType, EventCategory

class TestEventClassifier(unittest.TestCase):
    def test_extract_meeting_url(self):
        meet_text = "Join us at https://meet.google.com/abc-defg-hij please!"
        self.assertEqual(EventClassifier.extract_meeting_url(meet_text), "https://meet.google.com/abc-defg-hij")

        zoom_text = "Click here: https://company.zoom.us/j/123456789?pwd=xyz"
        self.assertEqual(EventClassifier.extract_meeting_url(zoom_text), "https://company.zoom.us/j/123456789?pwd=xyz")

        serenis_text = "Link: https://app.serenis.it/join/abc_123"
        self.assertEqual(EventClassifier.extract_meeting_url(serenis_text), "https://app.serenis.it/join/abc_123")

        self.assertIsNone(EventClassifier.extract_meeting_url(None))
        self.assertIsNone(EventClassifier.extract_meeting_url("missing value"))
        self.assertIsNone(EventClassifier.extract_meeting_url("No link here at all"))

    def test_classify_flight_travel(self):
        meta = EventClassifier.classify(
            title="Flight to Catania (W4 6555)",
            location="Terminal 1 - Gate 12",
            description="",
            meeting_url=None
        )
        self.assertEqual(meta["pilot_type"], PilotType.CAPTAIN.value)
        self.assertEqual(meta["event_type"], EventCategory.TRAVEL.value)
        self.assertTrue(meta["is_travel"])
        self.assertIn("maps.apple.com", meta["action_url"])

    def test_classify_food_dinner(self):
        meta = EventClassifier.classify(
            title="Cena con colleghi",
            location="Pizzeria da Mario",
            description="",
            meeting_url=None
        )
        self.assertEqual(meta["pilot_type"], PilotType.CHEF.value)
        self.assertEqual(meta["event_type"], EventCategory.FOOD.value)
        self.assertTrue(meta["is_travel"])

    def test_classify_video_meetings(self):
        meta = EventClassifier.classify(
            title="Sprint Planning",
            location="",
            description="",
            meeting_url="https://meet.google.com/xyz-uvw-rst"
        )
        self.assertEqual(meta["pilot_type"], PilotType.DUCK.value)
        self.assertEqual(meta["event_type"], EventCategory.VIDEO_MEETING.value)
        self.assertFalse(meta["is_travel"])
        self.assertEqual(meta["action_url"], "https://meet.google.com/xyz-uvw-rst")

    def test_classify_study_owl(self):
        meta = EventClassifier.classify(
            title="Lezione Reti Neurali Politecnico",
            location="Aula 3B",
            description="",
            meeting_url=None
        )
        self.assertEqual(meta["pilot_type"], PilotType.OWL.value)
        self.assertEqual(meta["event_type"], EventCategory.STUDY.value)

    def test_classify_zen_duck(self):
        meta = EventClassifier.classify(
            title="Seduta Serenis Online",
            location="",
            description="",
            meeting_url="https://app.serenis.it/join/test123"
        )
        self.assertEqual(meta["pilot_type"], PilotType.ZEN_DUCK.value)
        self.assertEqual(meta["event_type"], EventCategory.HEALTH.value)

    def test_parse_applescript_date(self):
        dt = EventClassifier.parse_applescript_date("2026-08-22T15:30:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 8)
        self.assertEqual(dt.day, 22)
        self.assertEqual(dt.hour, 15)
        self.assertEqual(dt.minute, 30)

if __name__ == "__main__":
    unittest.main()
