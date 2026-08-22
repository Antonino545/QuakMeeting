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
        
        self.service.mark_arrived(m.id)
        self.assertTrue(self.service.is_meeting_arrived(m))

    def test_meeting_with_is_arrived_flag(self):
        m = Meeting(
            title="Lecture in Aula 5M",
            start_time=datetime.now() + timedelta(minutes=5),
            classroom="Aula 5M",
            is_arrived=True
        )
        self.assertTrue(self.service.is_meeting_arrived(m))
