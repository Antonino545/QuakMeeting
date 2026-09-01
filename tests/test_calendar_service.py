import unittest
from datetime import datetime, timedelta
from core.domain.models import Meeting
from core.services.calendar_service import CalendarService
from core.services.config_service import ConfigService

class TestCalendarServiceTravelTime(unittest.TestCase):
    def setUp(self):
        self.service = CalendarService()
        self._orig_enable = self.service.config.get("enable_eta_service")
        self._orig_buf = self.service.config.get("eta_buffer_minutes")
        self._orig_mode = self.service.config.get("transport_mode")
        self._orig_home = self.service.config.get("home_address")
        self._orig_exam = self.service.config.get("exam_location")

        self.service.config.set("enable_eta_service", True)
        self.service.config.set("eta_buffer_minutes", 10)
        self.service.config.set("transport_mode", "automobile")

    def tearDown(self):
        self.service.config.set("enable_eta_service", self._orig_enable)
        self.service.config.set("eta_buffer_minutes", self._orig_buf)
        self.service.config.set("transport_mode", self._orig_mode)
        self.service.config.set("home_address", self._orig_home)
        self.service.config.set("exam_location", self._orig_exam)

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

    def test_apply_current_transport_mode_updates_cached_meetings(self):
        now = datetime.now()
        start = now + timedelta(hours=2)
        m = Meeting(
            title="Meeting with Travel",
            start_time=start,
            location="Politecnico",
            is_travel=True,
            travel_time_minutes=30,
            transport_mode="transit",
            eta_text="🚆 ~30m • Leave at 10:00",
            action_btn_text="🗺️ PUBLIC TRANSIT (~30m)"
        )
        self.service._in_memory_cache = [m]

        # Change config to walking and update
        self.service.config.set("transport_mode", "walking")
        self.service.update_transport_mode()

        self.assertEqual(m.transport_mode, "walking")
        self.assertIn("🚶", m.eta_text)
        self.assertIn("WALKING ROUTE", m.action_btn_text)

        # Change config to automobile and update
        self.service.config.set("transport_mode", "automobile")
        self.service.update_transport_mode()

        self.assertEqual(m.transport_mode, "automobile")
        self.assertIn("🚗", m.eta_text)
        self.assertIn("DRIVE WITH MAPS", m.action_btn_text)

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

    def test_exam_location_fallback_and_enrichment(self):
        from unittest.mock import patch
        self.service.config.set("home_address", "Corso Francia 10, Torino")
        self.service.config.set("exam_location", "Politecnico di Torino, Corso Duca degli Abruzzi 24")
        self.service.config.set("transport_mode", "transit")

        now = datetime.now()
        start = now + timedelta(hours=3)

        # Exam event without explicit location
        m_exam = Meeting(
            title="Exam:Satellite Systems for Positioning and Maps",
            start_time=start,
            location="",
            classroom="Aula 5M",
            event_type="exam",
            is_travel=True
        )

        with patch("core.services.calendar_service.eta_service.calculate_eta") as mock_eta:
            mock_eta.return_value = {
                "duration_minutes": 28,
                "distance_km": 3.9,
                "maps_url": "https://maps.apple.com/test",
                "mode_icon": "🚆"
            }
            self.service._enrich_with_eta([m_exam])

            self.assertEqual(m_exam.location, "Politecnico di Torino, Corso Duca degli Abruzzi 24")
            self.assertEqual(m_exam.travel_time_minutes, 28)
            self.assertIn("28m", m_exam.eta_text)
            self.assertIsNotNone(m_exam.departure_time)

    def test_deduplicate_duplicate_exam_and_lecture(self):
        now = datetime.now()
        start_exam = now + timedelta(hours=2) # e.g. 07:40
        end_exam = start_exam + timedelta(hours=2, minutes=15) # 09:55
        start_class = start_exam + timedelta(minutes=20) # e.g. 08:00
        end_class = start_class + timedelta(hours=2, minutes=30) # 10:30

        # Duplicate situation from user prompt:
        # Event 1: 07:40 - 09:55 • Exam:Satellite Systems for Positioning and Maps (Politecnico di Torino, Aula 5M)
        # Event 2: 08:00 - 10:30 • Satellite Systems for Positioning and Maps (Class / Lecture)
        m_exam = Meeting(
            title="Exam:Satellite Systems for Positioning and Maps",
            start_time=start_exam,
            end_time=end_exam,
            location="Politecnico di Torino",
            classroom="Aula 5M",
            event_type="exam"
        )
        m_class = Meeting(
            title="Satellite Systems for Positioning and Maps",
            start_time=start_class,
            end_time=end_class,
            location="Politecnico",
            event_type="class"
        )

        deduped = self.service._filter_within_window([m_exam, m_class])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].event_type, "exam")
        self.assertEqual(deduped[0].title, "Exam:Satellite Systems for Positioning and Maps")
        self.assertEqual(deduped[0].classroom, "Aula 5M")

if __name__ == "__main__":
    unittest.main()
