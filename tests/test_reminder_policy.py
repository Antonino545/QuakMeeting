import unittest
from datetime import datetime, timezone

from core.domain.models import CalendarEvent, EventCategory
from core.domain.reminder_policy import (
    ReminderPolicyRegistry,
    ExamReminderPolicy,
    LectureReminderPolicy,
    VideoMeetingReminderPolicy,
    TransitReminderPolicy,
    GeneralReminderPolicy
)
from core.domain.state_machine import EventState


class TestReminderPolicies(unittest.TestCase):
    def test_policy_resolution(self):
        # Exam event
        exam = CalendarEvent(title="Physics Exam", category=EventCategory.EXAM.value)
        self.assertIsInstance(ReminderPolicyRegistry.get_policy(exam), ExamReminderPolicy)

        # Lecture event
        lecture = CalendarEvent(title="Neural Networks", category=EventCategory.CLASS.value)
        self.assertIsInstance(ReminderPolicyRegistry.get_policy(lecture), LectureReminderPolicy)

        # Video call event
        call = CalendarEvent(title="Design Review", meeting_url="https://meet.google.com/abc-xyz")
        self.assertIsInstance(ReminderPolicyRegistry.get_policy(call), VideoMeetingReminderPolicy)

        # Transit event
        transit = CalendarEvent(title="Flight to Paris", is_travel=True, departure_time=datetime.now(timezone.utc))
        self.assertIsInstance(ReminderPolicyRegistry.get_policy(transit), TransitReminderPolicy)

        # General event
        general = CalendarEvent(title="Lunch with Alex", category=EventCategory.GENERAL.value)
        self.assertIsInstance(ReminderPolicyRegistry.get_policy(general), GeneralReminderPolicy)

    def test_exam_policy_stages_and_suppression(self):
        policy = ExamReminderPolicy()
        event = CalendarEvent(title="Math Exam", category=EventCategory.EXAM.value)
        stages = policy.get_stages(event, config=None)
        self.assertIn(60, stages)
        self.assertIn(30, stages)
        self.assertIn(0, stages)

        # Should suppress when arrived on campus
        self.assertTrue(policy.should_suppress(event, EventState.ARRIVED, diff_min=20.0))
        # Should not suppress when upcoming
        self.assertFalse(policy.should_suppress(event, EventState.UPCOMING, diff_min=30.0))

    def test_video_meeting_call_suppression(self):
        policy = VideoMeetingReminderPolicy()
        event = CalendarEvent(
            title="Team Standup",
            meeting_url="https://zoom.us/j/123",
            arrival_reason="call:Zoom",
            is_arrived=True
        )
        # Suppresses when user is actively in call
        self.assertTrue(policy.should_suppress(event, EventState.ACTIVE, diff_min=2.0))


if __name__ == "__main__":
    unittest.main()
