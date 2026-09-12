"""
Tests for core/diagnostics.py system health & diagnostics reporting.
"""
import unittest
from unittest.mock import patch, MagicMock

from core.diagnostics import run_system_diagnostics_check, format_diagnostics_report


class TestSystemDiagnostics(unittest.TestCase):

    def test_run_system_diagnostics_structure(self):
        diag = run_system_diagnostics_check()
        self.assertIn("status", diag)
        self.assertIn("python", diag)
        self.assertIn("gui", diag)
        self.assertIn("calendar", diag)
        self.assertIn("presence", diag)
        self.assertIn("audio", diag)
        self.assertIn("storage", diag)

        self.assertIn("version", diag["python"])
        self.assertIn("executable", diag["python"])
        self.assertIn("display_server", diag["gui"])

    def test_format_diagnostics_report(self):
        report = format_diagnostics_report()
        self.assertIsInstance(report, str)
        self.assertIn("FlightDeck System Health & Diagnostics Check", report)
        self.assertIn("Python & Runtime Environment", report)
        self.assertIn("Calendar Integration", report)
        self.assertIn("Smart Presence & Arrival Detection", report)
        self.assertIn("Storage & Configuration", report)

    def test_operational_modes_reporting(self):
        mock_diag = {
            "status": "OK",
            "warnings": [],
            "errors": [],
            "python": {"version": "3.13.0", "executable": "/usr/bin/python3", "platform": "Linux"},
            "gui": {"backend": "PyQt6 6.8.0", "display_server": "X11"},
            "calendar": {"active_provider": "CalDAV", "configured_feeds_count": 2},
            "presence": {
                "enabled": True,
                "current_wifi": "eduroam",
                "is_venue_wifi": True,
                "detected_call_app": None,
                "operational_mode": "🟢 Venue Mode (Connected to eduroam — Lecture alerts suppressed)",
                "venue_ssids": ["eduroam", "polito"],
            },
            "audio": {"sound_enabled": True, "sound_name": "Glass", "mute_during_lessons": True},
            "storage": {"config_file": "/tmp/config.json", "config_exists": True, "log_file": "/tmp/log"},
        }
        report = format_diagnostics_report(mock_diag)
        self.assertIn("Venue Mode", report)
        self.assertIn("eduroam (Recognized Venue ✅)", report)
        self.assertIn("All systems operational. FlightDeck is ready to fly! 🦆", report)


if __name__ == "__main__":
    unittest.main()
