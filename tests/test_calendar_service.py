import unittest
from datetime import datetime, timedelta
from core.domain.models import Meeting
from core.services.calendar_service import CalendarService
from core.services.config_service import ConfigService

class TestCalendarServiceTravelTime(unittest.TestCase):
    def setUp(self):
        self.service = CalendarService()
        self.service.config.set("enable_eta_service", True)
        self.service.config.set("eta_buffer_minutes", 10)
        self.service.config.set("transport_mode", "automobile")

    def test_native_eventkit_travel_time_enrichment(self):
        now = datetime.now()
        start = now + timedelta(hours=2)
        m = Meeting(
            title="Dinner in Center",
            start_time=start,
            location="Piazza Castello, Torino",
            is_travel=True,
            travel_time_minutes=30
        )
        self.service._enrich_with_eta([m])
        self.assertEqual(m.travel_time_minutes, 30)
        self.assertIsNotNone(m.departure_time)
        self.assertIn("30m", m.eta_text)
        self.assertTrue("maps.apple.com" in m.action_url or "maps.google.com" in m.action_url or "google.com/maps" in m.action_url)

if __name__ == "__main__":
    unittest.main()
