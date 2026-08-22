import unittest
from datetime import datetime, timedelta
from core.domain.models import Meeting, PilotType, EventCategory

class TestMeetingModel(unittest.TestCase):
    def test_meeting_creation_and_id(self):
        start = datetime(2026, 8, 22, 14, 30)
        meeting = Meeting(
            title="Design Review",
            start_time=start,
            pilot_type=PilotType.DUCK.value,
            category=EventCategory.VIDEO_MEETING.value
        )
        self.assertEqual(meeting.id, "Design Review_202608221430")
        self.assertEqual(meeting.title, "Design Review")

    def test_serialization_and_deserialization(self):
        start = datetime(2026, 8, 22, 10, 0, 0)
        end = datetime(2026, 8, 22, 11, 0, 0)
        original = Meeting(
            title="Flight to Rome",
            start_time=start,
            end_time=end,
            location="Terminal 1",
            pilot_type=PilotType.CAPTAIN.value,
            is_travel=True,
            action_btn_text="🗺️ INDICAZIONI MAPPE",
            action_url="https://maps.apple.com/?q=FCO"
        )

        d = original.to_serializable_dict()
        self.assertEqual(d["start_time"], "2026-08-22T10:00:00")
        self.assertEqual(d["end_time"], "2026-08-22T11:00:00")
        self.assertTrue(d["is_travel"])

        reconstituted = Meeting.from_dict(d)
        self.assertEqual(reconstituted.title, original.title)
        self.assertEqual(reconstituted.start_time, original.start_time)
        self.assertEqual(reconstituted.end_time, original.end_time)
        self.assertEqual(reconstituted.pilot_type, PilotType.CAPTAIN.value)
        self.assertTrue(reconstituted.is_travel)

    def test_upcoming_and_past_checks(self):
        future_meeting = Meeting(
            title="Future Call",
            start_time=datetime.now() + timedelta(hours=2)
        )
        self.assertTrue(future_meeting.is_upcoming)
        self.assertFalse(future_meeting.is_past)

        past_meeting = Meeting(
            title="Past Call",
            start_time=datetime.now() - timedelta(hours=3),
            end_time=datetime.now() - timedelta(hours=2)
        )
        self.assertFalse(past_meeting.is_upcoming)
        self.assertTrue(past_meeting.is_past)

if __name__ == "__main__":
    unittest.main()
