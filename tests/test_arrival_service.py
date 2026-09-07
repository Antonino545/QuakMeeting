import unittest
from datetime import datetime, timedelta
from core.domain.models import Meeting
from core.services.arrival_service import ArrivalService

class TestArrivalService(unittest.TestCase):
    def setUp(self):
        self.service = ArrivalService()

    def test_manual_mark_arrived(self):
        m = Meeting(
            title="Design Sync",
            start_time=datetime.now() + timedelta(minutes=10),
            meeting_url="https://meet.google.com/test"
        )
        self.assertFalse(self.service.is_meeting_arrived(m))

        self.service.mark_arrived(m.id, reason="manual")
        self.assertTrue(self.service.is_meeting_arrived(m))
        self.assertEqual(self.service.get_arrival_reason(m.id), "manual")
        self.assertEqual(m.arrival_reason, "manual")

    def test_meeting_with_is_arrived_flag(self):
        m = Meeting(
            title="Lecture in Aula 5M",
            start_time=datetime.now() + timedelta(minutes=5),
            classroom="Aula 5M",
            is_arrived=True,
            arrival_reason="wifi:eduroam"
        )
        self.assertTrue(self.service.is_meeting_arrived(m))
        self.assertEqual(m.arrival_reason, "wifi:eduroam")

    def test_master_enable_toggle(self):
        m = Meeting(
            title="Online Sync",
            start_time=datetime.now() + timedelta(minutes=5),
            meeting_url="https://zoom.us/j/12345"
        )
        # Mock active call running
        with unittest.mock.patch.object(self.service, "is_active_video_call_running", return_value=True):
            # When enabled:
            self.service.config.set("enable_arrival_detection", True)
            self.assertTrue(self.service.is_meeting_arrived(m))

            # Reset meeting
            m.is_arrived = False
            m.arrival_reason = None
            if m.id in self.service._manually_arrived_ids:
                self.service._manually_arrived_ids.remove(m.id)

            # When disabled:
            self.service.config.set("enable_arrival_detection", False)
            self.assertFalse(self.service.is_meeting_arrived(m))

            # Restore default
            self.service.config.set("enable_arrival_detection", True)

    def test_active_call_toggle(self):
        m = Meeting(
            title="Zoom Strategy Meeting",
            start_time=datetime.now() + timedelta(minutes=5),
            meeting_url="https://zoom.us/j/999888"
        )
        with unittest.mock.patch.object(self.service, "_is_process_running_posix", return_value=True):
            with unittest.mock.patch.object(self.service, "_is_process_running_windows", return_value=True):
                self.service.config.set("arrival_detect_active_calls", True)
                self.assertTrue(self.service.is_active_video_call_running(m))

                self.service.config.set("arrival_detect_active_calls", False)
                self.assertFalse(self.service.is_active_video_call_running(m))

                # Restore
                self.service.config.set("arrival_detect_active_calls", True)

    def test_venue_wifi_toggle_and_matching(self):
        m = Meeting(
            title="Calculus I Lecture",
            start_time=datetime.now() + timedelta(minutes=5),
            pilot_type="owl",
            classroom="Aula Magna"
        )
        with unittest.mock.patch.object(self.service, "get_current_wifi_ssid", return_value="eduroam-PoliTO"):
            # Should match default 'eduroam' / 'polito'
            self.service.config.set("arrival_detect_venue_wifi", True)
            self.assertTrue(self.service.is_connected_to_venue_wifi(m))

            # When disabled
            self.service.config.set("arrival_detect_venue_wifi", False)
            self.assertFalse(self.service.is_connected_to_venue_wifi(m))

            # Restore
            self.service.config.set("arrival_detect_venue_wifi", True)

    def test_custom_venue_wifi_ssids(self):
        m = Meeting(
            title="Company All Hands",
            start_time=datetime.now() + timedelta(minutes=10),
            is_travel=True
        )
        with unittest.mock.patch.object(self.service, "get_current_wifi_ssid", return_value="AcmeHQ-Guest"):
            self.service.config.set("arrival_wifi_ssids", ["myoffice", "campus"])
            self.assertFalse(self.service.is_connected_to_venue_wifi(m))

            self.service.config.set("arrival_wifi_ssids", ["myoffice", "acmehq"])
            self.assertTrue(self.service.is_connected_to_venue_wifi(m))

            # Reset
            self.service.config.set("arrival_wifi_ssids", ["eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"])

    def test_linux_wifi_extraction_nmcli(self):
        mock_stdout = "no:Home-Network\nyes:eduroam\nno:Other-WiFi\n"
        with unittest.mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = unittest.mock.Mock(stdout=mock_stdout, returncode=0)
            ssid = self.service._get_wifi_ssid_linux()
            self.assertEqual(ssid, "eduroam")

    def test_linux_wifi_extraction_iwgetid_fallback(self):
        with unittest.mock.patch("subprocess.run") as mock_run:
            # 1st call nmcli fails, 2nd call iwgetid succeeds
            mock_run.side_effect = [
                Exception("nmcli not found"),
                unittest.mock.Mock(stdout="CampusGuest\n", returncode=0)
            ]
            ssid = self.service._get_wifi_ssid_linux()
            self.assertEqual(ssid, "CampusGuest")

    def test_presence_diagnostics_structure(self):
        with unittest.mock.patch.object(self.service, "get_current_wifi_ssid", return_value="iliadbox-5G"):
            with unittest.mock.patch.object(self.service, "_detect_any_active_call_app", return_value="Zoom"):
                diag = self.service.get_presence_diagnostics()
                self.assertIn("enabled", diag)
                self.assertIn("detect_calls", diag)
                self.assertIn("detect_wifi", diag)
                self.assertEqual(diag["current_wifi"], "iliadbox-5G")
                self.assertFalse(diag["is_venue_wifi"])
                self.assertTrue(diag["active_call_detected"])
                self.assertEqual(diag["detected_call_app"], "Zoom")
                self.assertIsInstance(diag["monitored_ssids"], list)

    def test_meeting_arrival_reason_serialization(self):
        m = Meeting(
            title="Team Huddle",
            start_time=datetime.now(),
            is_arrived=True,
            arrival_reason="call:Microsoft Teams"
        )
        d = m.to_dict()
        self.assertEqual(d["arrival_reason"], "call:Microsoft Teams")

        deserialized = Meeting.from_dict(d)
        self.assertTrue(deserialized.is_arrived)
        self.assertEqual(deserialized.arrival_reason, "call:Microsoft Teams")
