import unittest
from datetime import datetime, timedelta, timezone
from core.domain.models import Meeting, PilotType, EventCategory

class TestMeetingModel(unittest.TestCase):
    def test_meeting_creation_and_id(self):
        start = datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc)
        meeting = Meeting(
            title="Design Review",
            start_time=start,
            pilot_type=PilotType.DUCK.value,
            category=EventCategory.VIDEO_MEETING.value
        )
        self.assertEqual(meeting.id, "Design Review_202608221430")
        self.assertEqual(meeting.title, "Design Review")
        
        # Test explicit uid
        meeting_with_uid = Meeting(
            uid="event-uid-123",
            title="Design Review 2",
            start_time=start
        )
        self.assertEqual(meeting_with_uid.id, "event-uid-123")

    def test_serialization_and_deserialization(self):
        start = datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 22, 11, 0, 0, tzinfo=timezone.utc)
        original = Meeting(
            uid="uid-999",
            title="Flight to Rome",
            start_time=start,
            end_time=end,
            location="Terminal 1",
            pilot_type=PilotType.CAPTAIN.value,
            is_travel=True,
            is_all_day=True,
            action_btn_text="🗺️ INDICAZIONI MAPPE",
            action_url="https://maps.apple.com/?q=FCO"
        )

        d = original.to_serializable_dict()
        self.assertEqual(d["start_time"], original.start_time.isoformat())
        self.assertEqual(d["end_time"], original.end_time.isoformat())
        self.assertTrue(d["is_travel"])
        self.assertTrue(d["is_all_day"])
        self.assertEqual(d["uid"], "uid-999")

        reconstituted = Meeting.from_dict(d)
        self.assertEqual(reconstituted.title, original.title)
        self.assertEqual(reconstituted.start_time, original.start_time)
        self.assertEqual(reconstituted.end_time, original.end_time)
        self.assertEqual(reconstituted.pilot_type, PilotType.CAPTAIN.value)
        self.assertTrue(reconstituted.is_travel)
        self.assertTrue(reconstituted.is_all_day)
        self.assertEqual(reconstituted.uid, "uid-999")

    def test_upcoming_and_past_checks(self):
        now_utc = datetime.now(timezone.utc)
        future_meeting = Meeting(
            title="Future Call",
            start_time=now_utc + timedelta(hours=2)
        )
        self.assertTrue(future_meeting.is_upcoming)
        self.assertFalse(future_meeting.is_past)

        past_meeting = Meeting(
            title="Past Call",
            start_time=now_utc - timedelta(hours=3),
            end_time=now_utc - timedelta(hours=2)
        )
        self.assertFalse(past_meeting.is_upcoming)
        self.assertTrue(past_meeting.is_past)

    def test_meeting_duration_minutes(self):
        m1 = Meeting(
            title="Short Call",
            start_time=datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 25, 10, 45, tzinfo=timezone.utc)
        )
        self.assertEqual(m1.duration_minutes, 45)

        m2 = Meeting(
            title="Two Hour Sync",
            start_time=datetime(2026, 8, 25, 14, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 25, 16, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(m2.duration_minutes, 120)

    def test_format_duration(self):
        from core.domain.models import format_duration
        self.assertEqual(format_duration(0), "0m")
        self.assertEqual(format_duration(25), "25m")
        self.assertEqual(format_duration(60), "1h")
        self.assertEqual(format_duration(90), "1h 30m")
        self.assertEqual(format_duration(120), "2h")
        self.assertEqual(format_duration(135), "2h 15m")
        self.assertEqual(format_duration(120, long_form=True), "2 hours")
        self.assertEqual(format_duration(60, long_form=True), "1 hour")
        self.assertEqual(format_duration(45, long_form=True), "45 min")

if __name__ == "__main__":
    unittest.main()
