"""
Unit tests for StudyFocusGuardian (Focus vs Distraction Logic).
"""
import unittest
from datetime import datetime, timezone, timedelta
from core.domain.models import Meeting, DeviceActivity, PilotType
from core.services.study_focus_guardian import StudyFocusGuardian
from core.services.device_presence_service import DevicePresenceService
from core.services.event_bus import EventBus
from core.services.config_service import ConfigService


class TestStudyFocusGuardian(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.config = ConfigService()
        self.presence = DevicePresenceService()
        self.presence.registered_devices.clear()
        
        self.guardian = StudyFocusGuardian()
        self.guardian.bus = self.bus
        self.guardian.config = self.config
        self.guardian.last_distraction_banner_time = None
        self.guardian.cached_meetings = []

    def test_no_active_study_event_ignores_distraction(self):
        # Current time is 14:00, no meetings scheduled
        now = datetime(2026, 8, 30, 14, 0, 0, tzinfo=timezone.utc)
        activity = DeviceActivity(device_type="iphone", state="distracted", app_name="TikTok", timestamp=now)
        
        result = self.guardian.evaluate_activity(activity, current_time=now)
        self.assertIsNone(result)

    def test_active_study_event_triggers_distraction_banner(self):
        now = datetime(2026, 8, 30, 14, 30, 0, tzinfo=timezone.utc)
        study_meeting = Meeting(
            title="Studiare Sistemi Operativi",
            start_time=datetime(2026, 8, 30, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 30, 16, 0, 0, tzinfo=timezone.utc),
            event_type="study",
            pilot_type="owl"
        )
        self.guardian.cached_meetings = [study_meeting]

        banner_events = []
        self.bus.subscribe("REMINDER_TRIGGERED", lambda **kwargs: banner_events.append(kwargs))

        activity = DeviceActivity(device_type="iphone", state="distracted", app_name="Instagram", timestamp=now)
        result = self.guardian.evaluate_activity(activity, current_time=now)

        self.assertIsNotNone(result)
        self.assertIn("Stay Focused", result.get("title", ""))
        self.assertEqual(result.get("pilot_type"), PilotType.OWL.value)
        self.assertEqual(len(banner_events), 1)

    def test_active_study_with_ipad_studying_suppresses_phone_distraction(self):
        now = datetime(2026, 8, 30, 14, 30, 0, tzinfo=timezone.utc)
        study_meeting = Meeting(
            title="Homework & Exam Revision",
            start_time=datetime(2026, 8, 30, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 30, 16, 0, 0, tzinfo=timezone.utc),
            event_type="study",
            pilot_type="owl"
        )
        self.guardian.cached_meetings = [study_meeting]

        # iPad reported active studying 5 minutes ago
        ipad_time = now - timedelta(minutes=5)
        ipad_act = DeviceActivity(device_type="ipad", state="studying", app_name="GoodNotes", timestamp=ipad_time)
        self.presence.record_activity(ipad_act)

        # Phone reports distraction
        activity = DeviceActivity(device_type="iphone", state="distracted", app_name="WhatsApp", timestamp=now)
        result = self.guardian.evaluate_activity(activity, current_time=now)

        # Must be suppressed because iPad study session is active
        self.assertIsNone(result)

    def test_cooldown_rate_limiting(self):
        now = datetime(2026, 8, 30, 14, 30, 0, tzinfo=timezone.utc)
        study_meeting = Meeting(
            title="Self-Study Math",
            start_time=datetime(2026, 8, 30, 14, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 30, 16, 0, 0, tzinfo=timezone.utc),
            event_type="study",
            pilot_type="owl"
        )
        self.guardian.cached_meetings = [study_meeting]

        # First distraction triggers banner
        act1 = DeviceActivity(device_type="iphone", state="distracted", app_name="TikTok", timestamp=now)
        res1 = self.guardian.evaluate_activity(act1, current_time=now)
        self.assertIsNotNone(res1)

        # Second distraction 1 minute later is suppressed by cooldown
        later_1m = now + timedelta(minutes=1)
        act2 = DeviceActivity(device_type="iphone", state="distracted", app_name="TikTok", timestamp=later_1m)
        res2 = self.guardian.evaluate_activity(act2, current_time=later_1m)
        self.assertIsNone(res2)

        # Third distraction 6 minutes later triggers again
        later_6m = now + timedelta(minutes=6)
        act3 = DeviceActivity(device_type="iphone", state="distracted", app_name="TikTok", timestamp=later_6m)
        res3 = self.guardian.evaluate_activity(act3, current_time=later_6m)
        self.assertIsNotNone(res3)


if __name__ == "__main__":
    unittest.main()
