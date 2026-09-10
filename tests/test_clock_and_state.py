import unittest
from datetime import datetime, timedelta, timezone

from core.domain.clock import SystemClock, FakeClock
from core.domain.models import CalendarEvent, Meeting, EventCategory
from core.domain.state_machine import EventState, resolve_event_state


class TestClockAndStateMachine(unittest.TestCase):
    def test_system_clock(self):
        clock = SystemClock()
        now = clock.now()
        self.assertIsNotNone(now.tzinfo)
        self.assertGreater(clock.time(), 0)

    def test_fake_clock_advance(self):
        start = datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc)
        clock = FakeClock(start)
        self.assertEqual(clock.now(), start)

        clock.advance(minutes=30)
        self.assertEqual(clock.now(), start + timedelta(minutes=30))

        clock.advance(hours=2)
        self.assertEqual(clock.now(), start + timedelta(hours=2, minutes=30))

    def test_state_machine_lifecycle_transitions(self):
        clock = FakeClock(datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc))

        # Event from 10:00 to 11:30, departure at 09:30 (30m travel)
        event = CalendarEvent(
            title="Operational Research Exam",
            start_time=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 10, 11, 30, 0, tzinfo=timezone.utc),
            departure_time=datetime(2026, 9, 10, 9, 30, 0, tzinfo=timezone.utc),
            is_travel=True,
            category=EventCategory.EXAM.value
        )

        # 08:00 -> UPCOMING
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.UPCOMING)

        # 09:00 -> PREPARE (30m before departure)
        clock.set_time(datetime(2026, 9, 10, 9, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.PREPARE)

        # 09:20 -> TIME_TO_LEAVE (10m before departure)
        clock.set_time(datetime(2026, 9, 10, 9, 20, 0, tzinfo=timezone.utc))
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.TIME_TO_LEAVE)

        # 09:40 -> ARRIVING (en route, between departure 09:30 and start 10:00)
        clock.set_time(datetime(2026, 9, 10, 9, 40, 0, tzinfo=timezone.utc))
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.ARRIVING)

        # 09:50 -> User connects to campus Wi-Fi -> ARRIVED
        event.is_arrived = True
        event.arrival_reason = "wifi:eduroam"
        clock.set_time(datetime(2026, 9, 10, 9, 50, 0, tzinfo=timezone.utc))
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.ARRIVED)

        # 10:15 -> ACTIVE (exam in session)
        clock.set_time(datetime(2026, 9, 10, 10, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.ACTIVE)

        # 11:35 -> COMPLETED
        clock.set_time(datetime(2026, 9, 10, 11, 35, 0, tzinfo=timezone.utc))
        self.assertEqual(resolve_event_state(event, clock=clock), EventState.COMPLETED)


if __name__ == "__main__":
    unittest.main()
