"""
Unit tests for Evolution Data Server (EDS) Calendar Provider (Linux / GNOME).
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from core.providers.eds_provider import EDSCalendarProvider

SAMPLE_ICS = """BEGIN:VEVENT
UID:sample-1234
SUMMARY:Doctor Appointment
LOCATION:Corso Francia 10, Torino
DTSTART:{DTSTART}
DTEND:{DTEND}
END:VEVENT"""

class TestEDSProvider(unittest.TestCase):
    def setUp(self):
        self.provider = EDSCalendarProvider()

    def test_is_available(self):
        avail = self.provider.is_available()
        self.assertIsInstance(avail, bool)

    def test_mocked_fetch_events(self):
        if not self.provider.is_available():
            self.skipTest("EDS not available on this platform (macOS or missing EDS)")

        import gi
        gi.require_version('ECal', '2.0')
        from gi.repository import ECal

        now = datetime.now().astimezone()
        dt_start = now.strftime('%Y%m%dT%H%M%S')
        dt_end = (now + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')
        ics_data = SAMPLE_ICS.format(DTSTART=dt_start, DTEND=dt_end)

        mock_source = MagicMock()
        mock_source.get_display_name.return_value = 'Test EDS Cal'
        mock_source.get_enabled.return_value = True

        mock_comp = MagicMock()
        mock_comp.get_as_string.return_value = ics_data

        mock_client = MagicMock()
        mock_client.get_object_list_as_comps_sync.return_value = (True, [mock_comp])

        mock_registry = MagicMock()
        mock_registry.list_sources.return_value = [mock_source]

        with patch.object(self.provider, '_get_registry', return_value=mock_registry):
            with patch.object(ECal.Client, 'connect_sync', return_value=mock_client) as mock_connect:
                meetings = self.provider.fetch_events()
                self.assertEqual(len(meetings), 1)
                self.assertEqual(meetings[0].title, 'Doctor Appointment')
                self.assertEqual(meetings[0].provider, 'Test EDS Cal')
                self.assertEqual(mock_connect.call_count, 1)

                # Subsequent call must use cached client and not call connect_sync again
                meetings2 = self.provider.fetch_events()
                self.assertEqual(len(meetings2), 1)
                self.assertEqual(mock_connect.call_count, 1)

    def test_eviction_on_query_error(self):
        if not self.provider.is_available():
            self.skipTest("EDS not available on this platform")

        mock_source = MagicMock()
        mock_source.get_uid.return_value = "uid-fail"
        mock_source.get_display_name.return_value = "Failing Cal"
        mock_source.get_enabled.return_value = True

        mock_client = MagicMock()
        mock_client.get_object_list_as_comps_sync.side_effect = RuntimeError("D-Bus disconnect")

        mock_registry = MagicMock()
        mock_registry.list_sources.return_value = [mock_source]

        import gi
        gi.require_version('ECal', '2.0')
        from gi.repository import ECal

        with patch.object(self.provider, '_get_registry', return_value=mock_registry):
            with patch.object(ECal.Client, 'connect_sync', return_value=mock_client):
                meetings = self.provider.fetch_events()
                self.assertEqual(len(meetings), 0)
                # Failed client must have been evicted from _clients
                self.assertNotIn("uid-fail", self.provider._clients)

if __name__ == '__main__':
    unittest.main()
