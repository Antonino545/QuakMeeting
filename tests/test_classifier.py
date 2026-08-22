import unittest
from datetime import datetime
from core.domain.classifier import EventClassifier
from core.domain.models import PilotType, EventCategory

class TestEventClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = EventClassifier()

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
        meeting = self.classifier.classify(
            title="Flight to London (BA 257)",
            location="Terminal 5 - Gate B12",
            description=""
        )
        self.assertEqual(meeting.pilot_type, PilotType.CAPTAIN.value)
        self.assertEqual(meeting.event_type, EventCategory.TRAVEL.value)
        self.assertTrue(meeting.is_travel)
        self.assertIn("maps.apple.com", meeting.action_url)

    def test_classify_food_dinner(self):
        meeting = self.classifier.classify(
            title="Dinner with team",
            location="Mario Pizzeria",
            description=""
        )
        self.assertEqual(meeting.pilot_type, PilotType.CHEF.value)
        self.assertEqual(meeting.event_type, EventCategory.FOOD.value)
        self.assertTrue(meeting.is_travel)

    def test_classify_video_meetings(self):
        meeting = self.classifier.classify(
            title="Sprint Planning",
            location="",
            description="https://meet.google.com/xyz-uvw-rst"
        )
        self.assertEqual(meeting.pilot_type, PilotType.DUCK.value)
        self.assertEqual(meeting.event_type, EventCategory.VIDEO_MEETING.value)
        self.assertFalse(meeting.is_travel)
        self.assertEqual(meeting.action_url, "https://meet.google.com/xyz-uvw-rst")

    def test_classify_study_owl(self):
        meeting = self.classifier.classify(
            title="Neural Networks University Lecture",
            location="Room 3B",
            description=""
        )
        self.assertEqual(meeting.pilot_type, PilotType.OWL.value)
        self.assertEqual(meeting.event_type, EventCategory.STUDY.value)

    def test_classroom_and_teacher_extraction(self):
        title = "ICT for smart mobility (VASSIO LUCA) - Aula 5M"
        meeting = self.classifier.classify(title=title, location="Politecnico")
        self.assertEqual(meeting.pilot_type, PilotType.OWL.value)
        self.assertEqual(meeting.classroom, "Aula 5M")
        self.assertEqual(meeting.teacher, "VASSIO LUCA")
        self.assertIn("Aula 5M", meeting.provider)

    def test_classify_zen_duck(self):
        meeting = self.classifier.classify(
            title="Serenis Online Therapy Session",
            location="",
            description="https://app.serenis.it/join/test123"
        )
        self.assertEqual(meeting.pilot_type, PilotType.ZEN_DUCK.value)
        self.assertEqual(meeting.provider, "Serenis 🛋️")

