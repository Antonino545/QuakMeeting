import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from core.domain.models import Meeting, PilotType
from core.services.event_bus import EventBus
from core.services.config_service import ConfigService, config_service
from core.services.notification_service import (
    ReminderNotification,
    MascotBannerProvider,
    SystemNotificationProvider,
    SoundNotificationProvider,
    CompositeNotificationProvider,
    NotificationService,
)


class TestNotificationService(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.bus.clear()
        self.config = config_service
        self.config.set("banner_enabled", True)
        self.config.set("system_notifications_enabled", False)
        self.config.set("sound_enabled", True)

    def test_reminder_notification_from_meeting(self):
        now = datetime.now(timezone.utc)
        meeting = Meeting(
            id="sync-123",
            title="Design Review",
            location="Room 404",
            meeting_link="https://meet.google.com/abc-defg-hij",
            start_time=now,
            pilot_type=PilotType.DUCK.value,
        )

        notification = ReminderNotification.from_meeting(meeting, stage=10)
        self.assertEqual(notification.meeting_id, "sync-123")
        self.assertEqual(notification.title, "Design Review")
        self.assertEqual(notification.stage, 10)
        self.assertEqual(notification.body, "Starts in 10 minutes")
        self.assertEqual(notification.action_url, "https://meet.google.com/abc-defg-hij")
        self.assertEqual(notification.action_label, "📋 OPEN EVENT")

        # Stage 0
        notif_0 = ReminderNotification.from_meeting(meeting, stage=0)
        self.assertEqual(notif_0.body, "Starting right now!")

    def test_mascot_banner_provider_publishes_event(self):
        provider = MascotBannerProvider(bus=self.bus)
        received = []
        self.bus.subscribe("REMINDER_TRIGGERED", lambda **kwargs: received.append(kwargs))

        notification = ReminderNotification(
            id="notif-1",
            title="Standup",
            body="Starts in 5 minutes",
            stage=5,
            meeting_dict={"title": "Standup", "id": "meet-1"},
        )

        success = provider.send(notification)
        self.assertTrue(success)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["stage"], 5)
        self.assertEqual(received[0]["event_dict"]["title"], "Standup")

    @patch("subprocess.run")
    def test_system_notification_provider_macos(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        provider = SystemNotificationProvider()

        notification = ReminderNotification(
            id="notif-sys-1",
            title="Lecture",
            subtitle="Aula Magna",
            body="Starts in 15 minutes",
            stage=15,
        )

        with patch("sys.platform", "darwin"), patch("shutil.which", return_value="/usr/bin/osascript"):
            self.assertTrue(provider.is_available())
            success = provider.send(notification)
            self.assertTrue(success)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "osascript")
            self.assertIn("display notification", args[2])

    @patch("subprocess.run")
    def test_system_notification_provider_linux(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        provider = SystemNotificationProvider()

        notification = ReminderNotification(
            id="notif-sys-2",
            title="Team Huddle",
            body="Starting right now!",
            stage=0,
        )

        with patch("sys.platform", "linux"), patch("shutil.which", return_value="/usr/bin/notify-send"):
            self.assertTrue(provider.is_available())
            success = provider.send(notification)
            self.assertTrue(success)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "notify-send")
            self.assertEqual(args[1], "Team Huddle")

    def test_composite_notification_provider_fallback(self):
        failing_primary = MagicMock()
        failing_primary.is_available.return_value = False
        failing_primary.send.return_value = False

        successful_fallback = MagicMock()
        successful_fallback.name = "fallback_sys"
        successful_fallback.is_available.return_value = True
        successful_fallback.send.return_value = True

        composite = CompositeNotificationProvider(
            providers=[failing_primary],
            fallback_provider=successful_fallback,
        )

        notification = ReminderNotification(id="test-1", title="Test", body="Body")
        success = composite.send(notification)

        self.assertTrue(success)
        successful_fallback.send.assert_called_once_with(notification)

    def test_notification_service_integration(self):
        service = NotificationService(config=self.config, bus=self.bus)
        received_events = []
        self.bus.subscribe("REMINDER_TRIGGERED", lambda **kwargs: received_events.append(kwargs))

        meeting = Meeting(id="test-meet", title="All Hands", start_time=datetime.now(timezone.utc))
        sent = service.notify_meeting(meeting, stage=5)

        self.assertTrue(sent)
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0]["stage"], 5)


if __name__ == "__main__":
    unittest.main()
