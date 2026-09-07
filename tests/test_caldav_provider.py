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
    def test_rrule_weekly_matching_today(self):
        now = datetime.now().astimezone()
        day_code = self.provider.DAY_CODES[now.weekday()]
        past_start = now - timedelta(days=28) # 4 weeks ago
        dt_start_str = past_start.strftime("%Y%m%dT100000")
        dt_end_str = past_start.strftime("%Y%m%dT110000")

        ics_payload = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:weekly-class-123
SUMMARY:Weekly Algorithms Lecture
LOCATION:Campus Aula 3
DTSTART:{dt_start_str}
DTEND:{dt_end_str}
RRULE:FREQ=WEEKLY;BYDAY={day_code}
END:VEVENT
END:VCALENDAR
"""
        events = self.provider._parse_ics_events(ics_payload)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["title"], "Weekly Algorithms Lecture")
        self.assertTrue(ev.get("is_recurring"))
        self.assertEqual(ev["start_time"].astimezone().date(), now.date())
        self.assertEqual(ev["start_time"].astimezone().hour, 10)
        self.assertEqual(ev["end_time"].astimezone().hour, 11)

    def test_rrule_weekly_different_day(self):
        now = datetime.now().astimezone()
        # Pick a different day
        diff_day = self.provider.DAY_CODES[(now.weekday() + 2) % 7]
        past_start = now - timedelta(days=28)
        dt_start_str = past_start.strftime("%Y%m%dT100000")
        dt_end_str = past_start.strftime("%Y%m%dT110000")

        ics_payload = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:weekly-class-456
SUMMARY:Weekly Algorithms Lecture
DTSTART:{dt_start_str}
DTEND:{dt_end_str}
RRULE:FREQ=WEEKLY;BYDAY={diff_day}
END:VEVENT
END:VCALENDAR
"""
        events = self.provider._parse_ics_events(ics_payload)
        self.assertEqual(len(events), 0)

    def test_rrule_expired_until(self):
        now = datetime.now().astimezone()
        day_code = self.provider.DAY_CODES[now.weekday()]
        past_start = now - timedelta(days=60)
        until_date = now - timedelta(days=5) # Expired last week

        ics_payload = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:expired-class-789
SUMMARY:Past Semester Lecture
DTSTART:{past_start.strftime("%Y%m%dT100000")}
DTEND:{past_start.strftime("%Y%m%dT110000")}
RRULE:FREQ=WEEKLY;BYDAY={day_code};UNTIL={until_date.strftime("%Y%m%dT235959Z")}
END:VEVENT
END:VCALENDAR
"""
        events = self.provider._parse_ics_events(ics_payload)
        self.assertEqual(len(events), 0)

    def test_rrule_cancelled_in_exdate(self):
        now = datetime.now().astimezone()
        day_code = self.provider.DAY_CODES[now.weekday()]
        past_start = now - timedelta(days=14)
        today_str = now.strftime("%Y%m%d")

        ics_payload = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:cancelled-class-101
SUMMARY:Cancelled Lecture Today
DTSTART:{past_start.strftime("%Y%m%dT100000")}
DTEND:{past_start.strftime("%Y%m%dT110000")}
RRULE:FREQ=WEEKLY;BYDAY={day_code}
EXDATE:{today_str}
END:VEVENT
END:VCALENDAR
"""
        events = self.provider._parse_ics_events(ics_payload)
        self.assertEqual(len(events), 0)

    def test_tzid_timezone_parsing(self):
        ics_payload = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:tz-event-1
SUMMARY:Rome Meeting
DTSTART;TZID=Europe/Rome:20260907T143000
DTEND;TZID=Europe/Rome:20260907T153000
END:VEVENT
END:VCALENDAR
"""
        events = self.provider._parse_ics_events(ics_payload)
        self.assertEqual(len(events), 1)
        ev = events[0]
        # In summer (CEST), Rome is UTC+2: 14:30 Europe/Rome == 12:30 UTC
        # In winter (CET), Rome is UTC+1: 14:30 Europe/Rome == 13:30 UTC
        self.assertEqual(ev["start_time"].tzinfo.tzname(None), "UTC")
        self.assertIn(ev["start_time"].hour, (12, 13))

    def test_feed_cache_fallback_on_network_error(self):
        source = "https://example.com/calendar.ics"
        self.provider._feed_cache[source] = "CACHED_ICS_DATA"
        # Simulate network failure
        with unittest.mock.patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
            content = self.provider._load_ics_content(source)
            self.assertEqual(content, "CACHED_ICS_DATA")


if __name__ == "__main__":
    unittest.main()
