"""
Unit Tests for Sound and Volume Service.
Tests system volume detection, mute detection, and chime playback conditions on macOS and Linux.
"""
import unittest
from unittest.mock import patch, MagicMock
import subprocess

from core.services.config_service import config
from core.services.sound_service import is_system_volume_on, play_chime


class TestSoundService(unittest.TestCase):

    def setUp(self):
        self.original_sound_enabled = config.get("sound_enabled")
        self.original_mute_during_lessons = config.get("mute_during_lessons")

    def tearDown(self):
        config.set("sound_enabled", self.original_sound_enabled)
        config.set("mute_during_lessons", self.original_mute_during_lessons)

    @patch("core.services.sound_service.sys")
    @patch("core.services.sound_service.subprocess.run")
    def test_macos_volume_on(self, mock_run, mock_sys):
        mock_sys.platform = "darwin"
        # 1st call for mute check: "false" (not muted)
        # 2nd call for volume check: "75"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="false\n"),
            MagicMock(returncode=0, stdout="75\n")
        ]
        self.assertTrue(is_system_volume_on())

    @patch("core.services.sound_service.sys")
    @patch("core.services.sound_service.subprocess.run")
    def test_macos_volume_muted(self, mock_run, mock_sys):
        mock_sys.platform = "darwin"
        mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
        self.assertFalse(is_system_volume_on())

    @patch("core.services.sound_service.sys")
    @patch("core.services.sound_service.subprocess.run")
    def test_macos_volume_zero(self, mock_run, mock_sys):
        mock_sys.platform = "darwin"
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="false\n"),
            MagicMock(returncode=0, stdout="0\n")
        ]
        self.assertFalse(is_system_volume_on())

    @patch("core.services.sound_service.sys")
    @patch("core.services.sound_service.shutil.which")
    @patch("core.services.sound_service.subprocess.run")
    def test_linux_wpctl_volume_on(self, mock_run, mock_which, mock_sys):
        mock_sys.platform = "linux"
        mock_which.side_effect = lambda cmd: "/usr/bin/wpctl" if cmd == "wpctl" else None
        mock_run.return_value = MagicMock(returncode=0, stdout="Volume: 0.88\n")
        self.assertTrue(is_system_volume_on())

    @patch("core.services.sound_service.sys")
    @patch("core.services.sound_service.shutil.which")
    @patch("core.services.sound_service.subprocess.run")
    def test_linux_wpctl_volume_muted(self, mock_run, mock_which, mock_sys):
        mock_sys.platform = "linux"
        mock_which.side_effect = lambda cmd: "/usr/bin/wpctl" if cmd == "wpctl" else None
        mock_run.return_value = MagicMock(returncode=0, stdout="Volume: 0.88 [MUTED]\n")
        self.assertFalse(is_system_volume_on())

    @patch("core.services.sound_service.sys")
    @patch("core.services.sound_service.shutil.which")
    @patch("core.services.sound_service.subprocess.run")
    def test_linux_pactl_muted(self, mock_run, mock_which, mock_sys):
        mock_sys.platform = "linux"
        mock_which.side_effect = lambda cmd: "/usr/bin/pactl" if cmd == "pactl" else None
        mock_run.return_value = MagicMock(returncode=0, stdout="Mute: yes\n")
        self.assertFalse(is_system_volume_on())

    @patch("core.services.calendar_service.calendar_service.is_in_lesson", return_value=False)
    @patch("core.services.sound_service.is_system_volume_on")
    @patch("core.services.sound_service.subprocess.run")
    def test_play_chime_disabled_in_config(self, mock_run, mock_vol, mock_in_lesson):
        config.set("sound_enabled", False)
        play_chime(sync=True)
        mock_vol.assert_not_called()
        mock_run.assert_not_called()

    @patch("core.services.calendar_service.calendar_service.is_in_lesson", return_value=False)
    @patch("core.services.sound_service.is_system_volume_on", return_value=False)
    @patch("core.services.sound_service.subprocess.run")
    def test_play_chime_skips_when_volume_off(self, mock_run, mock_vol, mock_in_lesson):
        config.set("sound_enabled", True)
        config.set("mute_during_lessons", False)
        play_chime(sync=True)
        mock_vol.assert_called_once()
        mock_run.assert_not_called()

    @patch("core.services.sound_service.is_system_volume_on", return_value=True)
    @patch("core.services.sound_service.subprocess.run")
    def test_play_chime_muted_when_event_is_lesson(self, mock_run, mock_vol):
        config.set("sound_enabled", True)
        config.set("mute_during_lessons", True)
        lesson_event = {
            "title": "Sistemi Operativi",
            "event_type": "class",
            "classroom": "Aula 3B"
        }
        play_chime(sync=True, event_dict=lesson_event)
        mock_run.assert_not_called()

    @patch("core.services.calendar_service.calendar_service.is_in_lesson", return_value=True)
    @patch("core.services.sound_service.is_system_volume_on", return_value=True)
    @patch("core.services.sound_service.subprocess.run")
    def test_play_chime_muted_when_user_is_in_lesson(self, mock_run, mock_vol, mock_in_lesson):
        config.set("sound_enabled", True)
        config.set("mute_during_lessons", True)
        normal_event = {
            "title": "General Sync",
            "event_type": "general"
        }
        play_chime(sync=True, event_dict=normal_event)
        mock_run.assert_not_called()

    @patch("core.services.calendar_service.calendar_service.is_in_lesson", return_value=False)
    @patch("core.services.sound_service.is_system_volume_on", return_value=True)
    @patch("core.services.sound_service.subprocess.run")
    def test_play_chime_plays_when_mute_during_lessons_disabled(self, mock_run, mock_vol, mock_in_lesson):
        config.set("sound_enabled", True)
        config.set("mute_during_lessons", False)
        lesson_event = {
            "title": "Sistemi Operativi",
            "event_type": "class",
            "classroom": "Aula 3B"
        }
        play_chime(sync=True, event_dict=lesson_event)
        mock_vol.assert_called_once()

    @patch("core.services.sound_service.is_system_volume_on", return_value=True)
    @patch("core.services.sound_service.subprocess.run")
    def test_play_chime_muted_when_quiet_reminder(self, mock_run, mock_vol):
        config.set("sound_enabled", True)
        quiet_event = {
            "title": "Meeting",
            "event_type": "video_meeting",
            "is_quiet_reminder": True
        }
        play_chime(sync=True, event_dict=quiet_event)
        mock_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
