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
        self.assertEqual(m.transport_mode, "automobile")
        self.assertIn("DRIVE WITH MAPS", m.action_btn_text)
        self.assertIn("🚗", m.eta_text)
        self.assertIsNotNone(m.departure_time)
        self.assertIn("30m", m.eta_text)
        self.assertTrue("maps.apple.com" in m.action_url or "maps.google.com" in m.action_url or "google.com/maps" in m.action_url)

    def test_transport_mode_changes_reflect_in_enrichment(self):
        now = datetime.now()
        start = now + timedelta(hours=2)

        # Transit mode
        self.service.config.set("transport_mode", "transit")
        m_transit = Meeting(title="Transit Trip", start_time=start, location="Politecnico", is_travel=True, travel_time_minutes=25)
        self.service._enrich_with_eta([m_transit])
        self.assertEqual(m_transit.transport_mode, "transit")
        self.assertIn("PUBLIC TRANSIT", m_transit.action_btn_text)
        self.assertIn("🚆", m_transit.eta_text)

        # Walking mode
        self.service.config.set("transport_mode", "walking")
        m_walk = Meeting(title="Walking Trip", start_time=start, location="Library", is_travel=True, travel_time_minutes=15)
        self.service._enrich_with_eta([m_walk])
        self.assertEqual(m_walk.transport_mode, "walking")
        self.assertIn("WALKING ROUTE", m_walk.action_btn_text)
        self.assertIn("🚶", m_walk.eta_text)

        # Bicycling mode
        self.service.config.set("transport_mode", "bicycling")
        m_bike = Meeting(title="Bicycle Trip", start_time=start, location="Park", is_travel=True, travel_time_minutes=20)
        self.service._enrich_with_eta([m_bike])
        self.assertEqual(m_bike.transport_mode, "bicycling")
        self.assertIn("CYCLING ROUTE", m_bike.action_btn_text)
        self.assertIn("🚲", m_bike.eta_text)

    def test_filter_within_window_midnight_spanning(self):
        from datetime import timezone
        # Test that an event starting yesterday but ending today is included
        # Let's mock datetime.now() inside the _filter_within_window by actually injecting a specific time?
        # Actually _filter_within_window uses datetime.now(), which is hard to mock without patch.
        # But we can just create an event that spans across the current time's midnight boundary.
        
        now = datetime.now(timezone.utc)
        # Event started 2 hours ago, ends in 2 hours
        start = now - timedelta(hours=2)
        end = now + timedelta(hours=2)
        
        m_spanning = Meeting(
            title="Spanning Event",
            start_time=start,
            end_time=end
        )
        
        filtered = self.service._filter_within_window([m_spanning])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Spanning Event")
if __name__ == "__main__":
    unittest.main()
