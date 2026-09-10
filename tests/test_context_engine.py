"""
Unit tests for ContextEngine and 'Why?' Transparency Guidance.
"""
import unittest
from datetime import datetime, timedelta, timezone

from core.domain.clock import FakeClock
from core.domain.models import CalendarEvent, EventCategory
from core.domain.context_engine import ContextEngine, ActionType, UserContextState


class TestContextEngine(unittest.TestCase):
    def setUp(self):
        self.base_time = datetime(2026, 9, 10, 8, 30, 0, tzinfo=timezone.utc)
        self.clock = FakeClock(self.base_time)

    def test_idle_when_no_events_today(self):
        guidance = ContextEngine.evaluate([], clock=self.clock)
        self.assertEqual(guidance.action_type, ActionType.RELAX)
        self.assertEqual(guidance.context_state, UserContextState.IDLE)
        self.assertEqual(guidance.headline, "All Clear for Today")

    def test_transit_event_leave_now_rationale(self):
        # Event at 09:00 with departure at 08:35 (25m travel)
        # Clock is at 08:36 (past departure deadline)
        self.clock.set_time(datetime(2026, 9, 10, 8, 36, 0, tzinfo=timezone.utc))

        event = CalendarEvent(
            uid="evt-doc",
            title="Dentist Appointment",
            start_time=datetime(2026, 9, 10, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            departure_time=datetime(2026, 9, 10, 8, 35, 0, tzinfo=timezone.utc),
            travel_time_minutes=25,
            is_travel=True,
            location="Corso Francia 102, Torino"
        )

        guidance = ContextEngine.evaluate([event], clock=self.clock)
        self.assertEqual(guidance.action_type, ActionType.LEAVE_NOW)
        self.assertEqual(guidance.context_state, UserContextState.TIME_TO_LEAVE)
        self.assertIn("Departure deadline reached", guidance.rationale)
        self.assertIn("25m travel", guidance.rationale)
        self.assertTrue(guidance.is_urgent)

    def test_online_meeting_ready_to_join(self):
        # Meeting at 09:00, clock at 08:58 (2 mins to start)
        self.clock.set_time(datetime(2026, 9, 10, 8, 58, 0, tzinfo=timezone.utc))

        event = CalendarEvent(
            uid="evt-zoom",
            title="Sprint Planning",
            start_time=datetime(2026, 9, 10, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            meeting_url="https://zoom.us/j/123456789",
            category=EventCategory.VIDEO_MEETING.value
        )

        guidance = ContextEngine.evaluate([event], clock=self.clock)
        self.assertEqual(guidance.action_type, ActionType.JOIN_CALL)
        self.assertIn("begins in 2m", guidance.rationale)
        self.assertEqual(guidance.action_url, "https://zoom.us/j/123456789")

    def test_active_in_call_presence_suppression(self):
        # Meeting underway, user detected in Zoom
        self.clock.set_time(datetime(2026, 9, 10, 9, 15, 0, tzinfo=timezone.utc))

        event = CalendarEvent(
            uid="evt-zoom",
            title="Sprint Planning",
            start_time=datetime(2026, 9, 10, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            meeting_url="https://zoom.us/j/123456789",
            is_arrived=True,
            arrival_reason="call:Zoom"
        )

        guidance = ContextEngine.evaluate([event], clock=self.clock)
        self.assertEqual(guidance.action_type, ActionType.ACTIVE_SESSION)
        self.assertEqual(guidance.context_state, UserContextState.IN_CALL)
        self.assertIn("Banners suppressed", guidance.rationale)


if __name__ == "__main__":
    unittest.main()
