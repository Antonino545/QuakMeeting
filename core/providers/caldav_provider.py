"""
Universal CalDAV / iCalendar (.ics / webcal) Calendar Provider for QuakMeeting.
Pure Python calendar provider for Ubuntu/Linux and cross-platform feed sync.
"""
import os
import re
import html
import urllib.request
import logging
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any, Optional
from core.domain.models import Meeting
from core.domain.classifier import EventClassifier
from core.services.config_service import config_service, ConfigService
from .base import BaseCalendarProvider

logger = logging.getLogger("QuakMeeting.CalDAVProvider")

class CalDAVCalendarProvider(BaseCalendarProvider):
    """Calendar provider supporting CalDAV endpoints, webcal feeds, and local .ics files."""

    def __init__(self, config: Optional[ConfigService] = None):
        self.config = config or config_service

    def fetch_events(self, start_offset_hours: int = 2, end_offset_hours: int = 24) -> List[Meeting]:
        """Fetch today's events from configured remote calendar feeds or local .ics files."""
        calendar_sources = list(self.config.get("calendar_urls", []))
        if not calendar_sources:
            # Check default local calendars directory or test ICS
            local_cal_dir = os.path.expanduser("~/.quakmeeting/calendars")
            if os.path.exists(local_cal_dir):
                for fname in os.listdir(local_cal_dir):
                    if fname.endswith(".ics"):
                        calendar_sources.append(os.path.join(local_cal_dir, fname))

        if not calendar_sources:
            return []

        meetings: List[Meeting] = []
        ignored = set(self.config.get("ignored_calendars", []))
        custom_kw = self.config.get("custom_keywords", {})
        now = datetime.now()
        today_date = now.date()

        for source in calendar_sources:
            source_str = str(source).strip()
            if not source_str or source_str in ignored:
                continue

            ics_text = self._load_ics_content(source_str)
            if not ics_text:
                continue

            cal_name = self._extract_calendar_name(ics_text, source_str)
            if cal_name in ignored:
                continue

            events = self._parse_ics_events(ics_text)
            for ev in events:
                s_dt = ev.get("start_time")
                e_dt = ev.get("end_time")
                if not s_dt:
                    continue

                title = ev.get("title", "Untitled Event")
                loc = ev.get("location", "")
                desc = ev.get("description", "")
                url_val = ev.get("url", "")
                is_all_day = ev.get("is_all_day", False)
                uid_base = ev.get("uid", "")
                rec_id = ev.get("recurrence_id", "")
                uid = f"{uid_base}_{rec_id}" if rec_id else uid_base

                meeting = EventClassifier.classify(
                    title=title,
                    location=loc,
                    description=desc,
                    meeting_url=(
                        EventClassifier.extract_meeting_url(url_val) or
                        EventClassifier.extract_meeting_url(loc) or
                        EventClassifier.extract_meeting_url(desc)
                    ),
                    custom_keywords=custom_kw,
                    start_time=s_dt,
                    end_time=e_dt or (s_dt + timedelta(hours=1))
                )
                meeting.provider = cal_name
                if uid:
                    meeting.uid = uid
                meeting.is_all_day = is_all_day
                if is_all_day and not e_dt:
                    meeting.end_time = s_dt.replace(hour=23, minute=59, second=59)
                meetings.append(meeting)

        meetings.sort(key=lambda m: m.start_time)
        return meetings

    def get_available_calendars(self) -> List[Dict[str, Any]]:
        """List configured calendar URLs and local sources."""
        sources = self.config.get("calendar_urls", [])
        ignored = set(self.config.get("ignored_calendars", []))
        cals: List[Dict[str, Any]] = []

        for src in sources:
            name = src.split("/")[-1].replace(".ics", "") or src
            cals.append({
                "name": name,
                "enabled": name not in ignored and src not in ignored,
                "source": src
            })
        return cals

    def _load_ics_content(self, source: str) -> Optional[str]:
        try:
            if source.startswith("webcal://"):
                source = "https://" + source[len("webcal://"):]

            if source.startswith("http://") or source.startswith("https://"):
                req = urllib.request.Request(source, headers={"User-Agent": "QuakMeeting/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read().decode("utf-8", errors="ignore")
            elif os.path.exists(source):
                with open(source, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Failed to load calendar source {source}: {e}")
        return None

    def _extract_calendar_name(self, ics_text: str, default_source: str) -> str:
        for line in ics_text.splitlines():
            if line.startswith("X-WR-CALNAME:"):
                return line.split(":", 1)[1].strip()
        base = os.path.basename(default_source).replace(".ics", "")
        return base or "Linux Calendar"

    def _parse_ics_events(self, ics_text: str) -> List[Dict[str, Any]]:
        """Parses VEVENT components from raw iCalendar text."""
        events = []
        in_event = False
        current_event: Dict[str, Any] = {}

        # Unfold lines according to RFC 5545
        unfolded_lines = []
        for line in ics_text.splitlines():
            if line.startswith(" ") or line.startswith("\t"):
                if unfolded_lines:
                    unfolded_lines[-1] += line[1:]
            else:
                unfolded_lines.append(line)

        for line in unfolded_lines:
            line = line.strip()
            if line == "BEGIN:VALARM":
                in_alarm = True
                continue
            if line == "END:VALARM":
                in_alarm = False
                continue
            if line == "BEGIN:VEVENT":
                in_event = True
                in_alarm = False
                current_event = {}
            elif line == "END:VEVENT":
                if in_event and "title" in current_event and "start_time" in current_event:
                    events.append(current_event)
                in_event = False
            elif in_event and not in_alarm:
                if ":" in line:
                    raw_key, val = line.split(":", 1)
                    key = raw_key.split(";")[0].upper()

                    if key == "SUMMARY":
                        current_event["title"] = self._unescape_ics(val)
                    elif key == "LOCATION":
                        current_event["location"] = self._unescape_ics(val)
                    elif key == "DESCRIPTION":
                        current_event["description"] = self._unescape_ics(val)
                    elif key == "X-ALT-DESC":
                        alt_description = self._unescape_ics(html.unescape(val))
                        if not current_event.get("description") or current_event["description"] == "This is an event reminder":
                            current_event["description"] = alt_description
                        elif alt_description not in current_event["description"]:
                            current_event["description"] += "\n" + alt_description
                    elif key == "URL":
                        current_event["url"] = val.strip()
                    elif key == "UID":
                        current_event["uid"] = val.strip()
                    elif key == "RECURRENCE-ID":
                        current_event["recurrence_id"] = val.strip()
                    elif key == "DTSTART":
                        dt, is_all_day = self._parse_ics_datetime(val)
                        current_event["start_time"] = dt
                        if is_all_day:
                            current_event["is_all_day"] = True
                    elif key == "DTEND":
                        dt, _ = self._parse_ics_datetime(val)
                        current_event["end_time"] = dt

        return events

    def _parse_ics_datetime(self, val: str):
        val = val.strip()
        try:
            if val.endswith("Z"):
                dt = datetime.strptime(val, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                return dt, False
            elif "T" in val:
                dt = datetime.strptime(val[:15], "%Y%m%dT%H%M%S").astimezone(timezone.utc)
                return dt, False
            elif len(val) == 8:
                dt = datetime.strptime(val, "%Y%m%d").replace(hour=0, minute=0, second=0).astimezone(timezone.utc)
                return dt, True
        except Exception:
            pass
        return None, False

    def _unescape_ics(self, text: str) -> str:
        text = text.replace(r"\,", ",").replace(r"\;", ";").replace(r"\n", "\n").replace(r"\\", "\\")
        text = re.sub(r"https:\s*//", "https://", text)
        return text.strip()
