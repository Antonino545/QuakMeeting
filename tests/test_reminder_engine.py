import unittest
from datetime import datetime, timedelta
from core.domain.models import Meeting, PilotType
from core.services.reminder_engine import ReminderEngine
from core.services.event_bus import EventBus
from core.services.config_service import ConfigService

class TestReminderEngine(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.bus.clear()
        self.engine = ReminderEngine(bus=self.bus)
        self.engine.config.set("general_reminder_stages", [20, 10, 5, 2, 0])
        self.engine.config.set("meeting_reminder_stages", [20, 10, 5, 2, 0])
        self.engine.config.set("travel_reminder_stages", [45, 30, 15, 5, 2, 0])
        self.engine.reset_state()

    def test_reminder_stage_evaluation(self):
        now = datetime(2026, 8, 22, 12, 0, 0)
        # Meeting in 10 minutes (should match stage 10)
        meeting_10m = Meeting(
            title="Team Sync",
            start_time=now + timedelta(minutes=10),
            pilot_type=PilotType.DUCK.value,
            is_travel=False
        )

        triggered_events = []
        def handler(meeting, stage):
            triggered_events.append((meeting.title, stage))

        self.bus.subscribe("REMINDER_TRIGGERED", handler)

        results = self.engine.evaluate_meetings([meeting_10m], current_time=now)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 10)
        self.assertEqual(len(triggered_events), 1)
        self.assertEqual(triggered_events[0], ("Team Sync", 10))

    def test_duplicate_suppression_on_same_stage(self):
        now = datetime(2026, 8, 22, 12, 0, 0)
        meeting = Meeting(
            title="Design Review",
            start_time=now + timedelta(minutes=5),
            pilot_type=PilotType.DUCK.value
        )

        # First evaluation: triggers stage 5
        res1 = self.engine.evaluate_meetings([meeting], current_time=now)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0][1], 5)

        # Second evaluation 10 seconds later: should NOT trigger stage 5 again
        now_plus_10s = now + timedelta(seconds=10)
        res2 = self.engine.evaluate_meetings([meeting], current_time=now_plus_10s)
        self.assertEqual(len(res2), 0)

    def test_travel_stages(self):
        now = datetime(2026, 8, 22, 12, 0, 0)
        meeting_travel = Meeting(
            title="Flight Departure",
            start_time=now + timedelta(minutes=45),
            is_travel=True
        )
        self.engine.config.set("travel_reminder_stages", [45, 30, 15, 5, 0])

        stages = self.engine.get_stages_for_meeting(meeting_travel)
        self.assertEqual(stages, [45, 30, 15, 5, 0])

        res = self.engine.evaluate_meetings([meeting_travel], current_time=now)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1], 45)

    def test_travel_departure_time_stages(self):
        now = datetime(2026, 8, 22, 12, 0, 0)
        # Event is in 2 hours (14:00), but departure time is in 15 minutes (12:15)
        meeting_transit = Meeting(
            title="Dinner at Restaurant",
            start_time=now + timedelta(hours=2),
            departure_time=now + timedelta(minutes=15),
            travel_time_minutes=35,
            is_travel=True
        )

        # Evaluating at 12:00: departure is in 15 mins -> triggers stage 15 (15m before leave time!)
        res = self.engine.evaluate_meetings([meeting_transit], current_time=now)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1], 15)

    def test_mark_arrived_suppression(self):
        now = datetime(2026, 8, 22, 12, 0, 0)
        meeting = Meeting(
            title="ICT for smart mobility (VASSIO LUCA) - Aula 5M",
            start_time=now + timedelta(minutes=5),
            classroom="Aula 5M"
        )

        # Mark arrived
        self.engine.mark_arrived(meeting.id)

        # Should not trigger any reminder
        results = self.engine.evaluate_meetings([meeting], current_time=now)
        self.assertEqual(len(results), 0)

    def test_event_time_stage_zero_and_pre_event_stages(self):
        now = datetime(2026, 8, 22, 12, 0, 0)
        # Event exactly starting at 12:00 (stage 0)
        meeting_stage_0 = Meeting(
            title="Now Starting Meeting",
            start_time=now,
            pilot_type=PilotType.DUCK.value
        )
        results = self.engine.evaluate_meetings([meeting_stage_0], current_time=now)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 0)
        self.assertEqual(results[0][0].reminder_stage, 0)

    def test_check_and_notify_convenience_method(self):
        res = self.engine.check_and_notify()
        self.assertIsInstance(res, list)

if __name__ == "__main__":
    unittest.main()
