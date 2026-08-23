"""
Unit tests for Universal CalDAV & iCalendar Provider (Linux / Cross-platform).
"""
import unittest
from datetime import datetime, timedelta
from core.providers.caldav_provider import CalDAVCalendarProvider
from core.services.config_service import ConfigService

SAMPLE_ICS_DATA = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//QuakMeeting Test//EN
X-WR-CALNAME:Work Calendar
BEGIN:VEVENT
UID:meet-12345
SUMMARY:Weekly Engineering Sync (Google Meet)
DESCRIPTION:Join meeting at https://meet.google.com/abc-defg-hij
LOCATION:Online
DTSTART:{DTSTART}
DTEND:{DTEND}
URL:https://meet.google.com/abc-defg-hij
END:VEVENT
BEGIN:VEVENT
UID:dinner-67890
SUMMARY:Team Dinner at Pizzeria Napoli
DESCRIPTION:Delicious dinner
LOCATION:Pizzeria Da Michele, London
DTSTART:{DTSTART_DINNER}
DTEND:{DTEND_DINNER}
END:VEVENT
END:VCALENDAR
"""

class TestCalDAVProvider(unittest.TestCase):
    def setUp(self):
        self.provider = CalDAVCalendarProvider()

    def test_parse_ics_events_today(self):
        now = datetime.now()
        dt_start_str = now.strftime("%Y%m%dT%H%M%S")
        dt_end_str = (now + timedelta(hours=1)).strftime("%Y%m%dT%H%M%S")
        
        dinner_time = now.replace(hour=20, minute=0, second=0)
        dt_start_dinner = dinner_time.strftime("%Y%m%dT%H%M%S")
        dt_end_dinner = (dinner_time + timedelta(hours=2)).strftime("%Y%m%dT%H%M%S")

        ics_payload = SAMPLE_ICS_DATA.format(
            DTSTART=dt_start_str,
            DTEND=dt_end_str,
            DTSTART_DINNER=dt_start_dinner,
            DTEND_DINNER=dt_end_dinner
        )

        events = self.provider._parse_ics_events(ics_payload)
        self.assertEqual(len(events), 2)
        
        ev1 = events[0]
        self.assertEqual(ev1["title"], "Weekly Engineering Sync (Google Meet)")
        self.assertEqual(ev1["url"], "https://meet.google.com/abc-defg-hij")
        self.assertIsNotNone(ev1["start_time"])

    def test_calendar_name_extraction(self):
        name = self.provider._extract_calendar_name(SAMPLE_ICS_DATA, "default.ics")
        self.assertEqual(name, "Work Calendar")

    def test_unescape_ics(self):
        escaped = r"Hello\, World\; This is a line\nwith backslash\\"
        unescaped = self.provider._unescape_ics(escaped)
        self.assertEqual(unescaped, "Hello, World; This is a line\nwith backslash\\")

if __name__ == "__main__":
    unittest.main()
