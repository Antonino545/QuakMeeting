"""
Unit tests for Universal CalDAV & iCalendar Provider (Linux / Cross-platform).
"""
import unittest
from unittest.mock import MagicMock
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

    def test_parse_html_alt_description_with_serenis_link(self):
        ics_payload = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:serenis-html-123
SUMMARY:Serenis Session
DESCRIPTION:This is an event reminder
X-ALT-DESC;FMTTYPE=text/html:<p>Join your session <a href="https://app.serenis.it/join/html123">here</a></p>
DTSTART:20260902T150000Z
DTEND:20260902T160000Z
END:VEVENT
END:VCALENDAR
"""

        event = self.provider._parse_ics_events(ics_payload)[0]

        self.assertIn("https://app.serenis.it/join/html123", event["description"])

    def test_parse_event_description_not_alarm_description(self):
        ics_payload = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:serenis-alarm-123
SUMMARY:Serenis Session
DESCRIPTION:Join Serenis at https:\n //app.serenis.it/join/alarm123
DTSTART:20260902T150000Z
DTEND:20260902T160000Z
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:This is an event reminder
TRIGGER:PT0S
END:VALARM
END:VEVENT
END:VCALENDAR
"""

        event = self.provider._parse_ics_events(ics_payload)[0]

        self.assertIn("https://app.serenis.it/join/alarm123", event["description"])

    def test_fetch_events_uses_serenis_url_from_description(self):
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "calendar_urls": ["test.ics"],
            "ignored_calendars": [],
            "custom_keywords": {},
        }.get(key, default)
        provider = CalDAVCalendarProvider(config)
        now = datetime.now()
        ics_payload = f"""BEGIN:VCALENDAR
X-WR-CALNAME:Therapy
BEGIN:VEVENT
UID:serenis-123
SUMMARY:Serenis Online Therapy Session
DESCRIPTION:Join your session at https://app.serenis.it/join/test123
URL:https://calendar.example.test/event/serenis-123
DTSTART:{now.strftime('%Y%m%dT%H%M%S')}
DTEND:{(now + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}
END:VEVENT
END:VCALENDAR
"""
        provider._load_ics_content = MagicMock(return_value=ics_payload)

        meetings = provider.fetch_events()

        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_url, "https://app.serenis.it/join/test123")
        self.assertEqual(meetings[0].action_url, "https://app.serenis.it/join/test123")

if __name__ == "__main__":
    unittest.main()
