"""
End-to-End Scenario-Based Tests for FlightDeck.
Simulates day-in-the-life user journeys across time using FakeClock,
EventState lifecycle transitions, and adaptive ReminderPolicy suppression.
"""
import unittest
from datetime import datetime, timedelta, timezone

from core.domain.clock import FakeClock
from core.domain.models import CalendarEvent, Meeting, EventCategory
from core.domain.state_machine import EventState, resolve_event_state
from core.domain.reminder_policy import ReminderPolicyRegistry
from core.services.reminder_engine import ReminderEngine
from core.services.event_bus import EventBus
from core.services.config_service import ConfigService


class TestScenarios(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.bus.clear()
        self.config = ConfigService()
        self.engine = ReminderEngine(config=self.config, bus=self.bus)
        self.engine.reset_state()

    def test_student_morning_journey(self):
        """
        Scenario 1: Student Morning Journey
        - 08:30: User wakes up. Exam is at 10:00 at Politecnico.
                 Travel is 20m transit + 10m buffer -> departure at 09:30.
        - 09:00: Advance flyby reminder triggers (30m before departure).
        - 09:25: Imminent departure alert triggers (5m before departure).
        - 09:30: "Time to leave" alert triggers (0m departure).
        - 09:50: Student arrives on campus, connects to Eduroam.
                 System marks event arrived -> suppress remaining pre-event reminders.
        - 10:00: Exam becomes ACTIVE.
        - 12:00: Exam COMPLETED.
        """
        start_time = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
        departure_time = datetime(2026, 9, 10, 9, 30, 0, tzinfo=timezone.utc)

        exam = CalendarEvent(
            uid="exam-polito-001",
            title="Operational Research Exam",
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            departure_time=departure_time,
            travel_time_minutes=20,
            location="Politecnico di Torino",
            classroom="Aula 5M",
            category=EventCategory.EXAM.value,
            is_travel=True,
            pilot_type="owl"
        )

        clock = FakeClock(datetime(2026, 9, 10, 8, 30, 0, tzinfo=timezone.utc))

        # 1. At 08:30 - Event is UPCOMING, no reminder triggered
        state_830 = resolve_event_state(exam, clock=clock)
        self.assertEqual(state_830, EventState.UPCOMING)
        reminders_830 = self.engine.evaluate_meetings([exam], current_time=clock.now())
        self.assertEqual(len(reminders_830), 0)

        # 2. At 09:00 - 30 minutes before departure -> stage 30 triggers!
        clock.set_time(datetime(2026, 9, 10, 9, 0, 0, tzinfo=timezone.utc))
        state_900 = resolve_event_state(exam, clock=clock)
        self.assertEqual(state_900, EventState.PREPARE)
        reminders_900 = self.engine.evaluate_meetings([exam], current_time=clock.now())
        self.assertEqual(len(reminders_900), 1)
        self.assertEqual(reminders_900[0][1], 30)

        # 3. At 09:25 - 5 minutes before departure -> stage 5 triggers!
        clock.set_time(datetime(2026, 9, 10, 9, 25, 0, tzinfo=timezone.utc))
        state_925 = resolve_event_state(exam, clock=clock)
        self.assertEqual(state_925, EventState.TIME_TO_LEAVE)
        reminders_925 = self.engine.evaluate_meetings([exam], current_time=clock.now())
        self.assertEqual(len(reminders_925), 1)
        self.assertEqual(reminders_925[0][1], 5)

        # 4. At 09:30 - Departure time -> stage 0 departure alert!
        clock.set_time(datetime(2026, 9, 10, 9, 30, 0, tzinfo=timezone.utc))
        reminders_930 = self.engine.evaluate_meetings([exam], current_time=clock.now())
        self.assertEqual(len(reminders_930), 1)
        self.assertEqual(reminders_930[0][1], 0)

        # 5. At 09:50 - Student arrives on campus, connects to Eduroam!
        clock.set_time(datetime(2026, 9, 10, 9, 50, 0, tzinfo=timezone.utc))
        exam.is_arrived = True
        exam.arrival_reason = "wifi:eduroam"
        self.engine.mark_arrived(exam.id)

        state_950 = resolve_event_state(exam, clock=clock)
        self.assertEqual(state_950, EventState.ARRIVED)

        # 10:00 (Event start) -> reminders must be suppressed because student already arrived!
        clock.set_time(datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc))
        reminders_1000 = self.engine.evaluate_meetings([exam], current_time=clock.now())
        self.assertEqual(len(reminders_1000), 0)

        # Event in progress -> ACTIVE
        state_1000 = resolve_event_state(exam, clock=clock)
        self.assertEqual(state_1000, EventState.ACTIVE)

        # 12:05 -> Exam finished -> COMPLETED
        clock.set_time(datetime(2026, 9, 10, 12, 5, 0, tzinfo=timezone.utc))
        state_1205 = resolve_event_state(exam, clock=clock)
        self.assertEqual(state_1205, EventState.COMPLETED)

    def test_remote_work_video_meeting_journey(self):
        """
        Scenario 2: Remote Work Sync
        - 13:30: Video call at 14:00 (stages: 20m, 10m, 5m, 2m, 0m).
        - 13:40: 20m stage triggers.
        - 13:50: 10m stage triggers.
        - 13:54: User clicks "Join" or launches Zoom early.
                 Process is detected, marked arrived with "call:Zoom".
        - 13:58 & 14:00: Stage 2m and 0m are suppressed because user is already in call!
        """
        call_time = datetime(2026, 9, 10, 14, 0, 0, tzinfo=timezone.utc)
        meeting = CalendarEvent(
            uid="zoom-call-42",
            title="Team Architecture Review",
            start_time=call_time,
            end_time=call_time + timedelta(hours=1),
            meeting_url="https://zoom.us/j/123456789",
            category=EventCategory.VIDEO_MEETING.value,
            pilot_type="duck"
        )

        clock = FakeClock(datetime(2026, 9, 10, 13, 30, 0, tzinfo=timezone.utc))

        # 13:40 -> stage 20 triggers
        clock.set_time(datetime(2026, 9, 10, 13, 40, 0, tzinfo=timezone.utc))
        res_20 = self.engine.evaluate_meetings([meeting], current_time=clock.now())
        self.assertEqual(len(res_20), 1)
        self.assertEqual(res_20[0][1], 20)

        # 13:50 -> stage 10 triggers
        clock.set_time(datetime(2026, 9, 10, 13, 50, 0, tzinfo=timezone.utc))
        res_10 = self.engine.evaluate_meetings([meeting], current_time=clock.now())
        self.assertEqual(len(res_10), 1)
        self.assertEqual(res_10[0][1], 10)

        # 13:54 -> User enters Zoom meeting early!
        meeting.is_arrived = True
        meeting.arrival_reason = "call:Zoom"
        self.engine.mark_arrived(meeting.id)

        # 13:58 (2 minutes before start) -> Stage 2 MUST be suppressed
        clock.set_time(datetime(2026, 9, 10, 13, 58, 0, tzinfo=timezone.utc))
        res_2 = self.engine.evaluate_meetings([meeting], current_time=clock.now())
        self.assertEqual(len(res_2), 0)

        # 14:00 (Start time) -> Stage 0 MUST be suppressed
        clock.set_time(datetime(2026, 9, 10, 14, 0, 0, tzinfo=timezone.utc))
        res_0 = self.engine.evaluate_meetings([meeting], current_time=clock.now())
        self.assertEqual(len(res_0), 0)

        # State should be ACTIVE
        self.assertEqual(resolve_event_state(meeting, clock=clock), EventState.ACTIVE)


if __name__ == "__main__":
    unittest.main()
