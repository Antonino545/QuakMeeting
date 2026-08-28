import unittest
from datetime import datetime, timedelta, timezone
from core.domain.models import Meeting
from core.services.reminder_engine import ReminderEngine

class TestDSTTransitions(unittest.TestCase):
    def setUp(self):
        self.engine = ReminderEngine()
        self.engine.config.set("general_reminder_stages", [20, 10, 5, 2, 0])
        self.engine.reset_state()

    def test_spring_forward_absolute_timing(self):
        # A meeting scheduled right after a spring-forward transition (e.g., 03:00 local time).
        # We test that the reminder engine evaluates using exact UTC diffs.
        
        # Suppose a meeting starts at 07:00 UTC
        start_time_utc = datetime(2026, 3, 29, 7, 0, tzinfo=timezone.utc)
        meeting = Meeting(
            title="Post-DST Meeting",
            start_time=start_time_utc
        )

        # Evaluating 10 minutes before exact absolute time (06:50 UTC)
        now_utc = datetime(2026, 3, 29, 6, 50, tzinfo=timezone.utc)
        results = self.engine.evaluate_meetings([meeting], current_time=now_utc)
        
        # Should trigger exactly 10m ahead regardless of what DST did to local hour
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 10)

if __name__ == "__main__":
    unittest.main()
