"""
Evolution Data Server (EDS) Calendar Provider for Ubuntu/Linux.
Integrates directly with GNOME Calendar and system-wide CalDAV/Exchange setups.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from core.domain.models import Meeting
from core.domain.classifier import EventClassifier
from core.services.config_service import config_service, ConfigService
from .base import BaseCalendarProvider

logger = logging.getLogger("QuakMeeting.EDSProvider")

class EDSCalendarProvider(BaseCalendarProvider):
    """Calendar provider using GNOME Evolution Data Server (EDS)."""

    def __init__(self, config: Optional[ConfigService] = None):
        self.config = config or config_service
        self._registry = None
        self._is_available = None

    def _get_registry(self):
        if self._registry is None:
            try:
                import os
                gi_path = "/usr/lib/x86_64-linux-gnu/girepository-1.0"
                if gi_path not in os.environ.get("GI_TYPELIB_PATH", ""):
                    os.environ["GI_TYPELIB_PATH"] = f"{gi_path}:{os.environ.get('GI_TYPELIB_PATH', '')}".strip(":")
                    
                import gi
                gi.require_version('EDataServer', '1.2')
                gi.require_version('ECal', '2.0')
                from gi.repository import EDataServer
                self._registry = EDataServer.SourceRegistry.new_sync(None)
            except Exception as e:
                logger.debug(f"Evolution Data Server not available: {e}")
                self._registry = False
        return self._registry if self._registry is not False else None

    def is_available(self) -> bool:
        if self._is_available is None:
            self._is_available = (self._get_registry() is not None)
        return self._is_available

    def fetch_events(self, start_offset_hours: int = 2, end_offset_hours: int = 24) -> List[Meeting]:
        registry = self._get_registry()
        if not registry:
            return []

        import gi
        gi.require_version('ECal', '2.0')
        from gi.repository import EDataServer, ECal

        now = datetime.now().astimezone()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=start_offset_hours)
        end_of_tomorrow = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

        # Convert to ISO8601 for ECal query (UTC)
        start_iso = start_of_today.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        end_iso = end_of_tomorrow.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        ignored = set(self.config.get("ignored_calendars", []))
        custom_kw = self.config.get("custom_keywords", {})

        sources = registry.list_sources(EDataServer.SOURCE_EXTENSION_CALENDAR)

        meetings: List[Meeting] = []

        from core.providers.caldav_provider import CalDAVCalendarProvider
        caldav_parser = CalDAVCalendarProvider(self.config)

        for source in sources:
            name = source.get_display_name()
            if name in ignored or not source.get_enabled():
                continue

            try:
                client = ECal.Client.connect_sync(source, ECal.ClientSourceType.EVENTS, 3, None)
                if not client:
                    continue

                # Query time range
                query = f'(occur-in-time-range? (make-time "{start_iso}") (make-time "{end_iso}"))'

                success, events = client.get_object_list_as_comps_sync(query, None)
                if not success or not events:
                    continue

                for comp in events:
                    try:
                        # Extract the raw ICS string and reuse the CalDAV parser logic for robustness
                        if hasattr(comp, "get_as_string"):
                            ics_text = comp.get_as_string()
                        elif hasattr(comp, "get_icalcomponent"):
                            ics_text = comp.get_icalcomponent().as_ical_string()
                        elif hasattr(comp, "as_ical_string"):
                            ics_text = comp.as_ical_string()
                        else:
                            continue

                        parsed_events = caldav_parser._parse_ics_events(ics_text)

                        for ev in parsed_events:
                            s_dt = ev.get("start_time")
                            e_dt = ev.get("end_time")
                            if not s_dt:
                                continue

                            title = ev.get("title", "Untitled Event")
                            loc = ev.get("location", "")
                            desc = ev.get("description", "")
                            url_val = ev.get("url", "")

                            meeting_url = (
                                EventClassifier.extract_meeting_url(url_val) or
                                EventClassifier.extract_meeting_url(loc) or
                                EventClassifier.extract_meeting_url(desc)
                            )

                            meeting = EventClassifier.classify(
                                title=title,
                                location=loc,
                                description=desc,
                                meeting_url=meeting_url,
                                custom_keywords=custom_kw,
                                start_time=s_dt,
                                end_time=e_dt or (s_dt + timedelta(hours=1))
                            )
                            meeting.provider = name
                            meetings.append(meeting)
                    except Exception as parse_e:
                        logger.debug(f"Failed to parse EDS event in '{name}': {parse_e}")

            except Exception as e:
                logger.debug(f"Failed to fetch events from EDS source '{name}': {e}")

        meetings.sort(key=lambda m: m.start_time if m.start_time else datetime.min)
        return meetings

    def get_available_calendars(self) -> List[Dict[str, Any]]:
        registry = self._get_registry()
        if not registry:
            return []

        from gi.repository import EDataServer
        ignored = set(self.config.get("ignored_calendars", []))
        sources = registry.list_sources(EDataServer.SOURCE_EXTENSION_CALENDAR)

        cals = []
        for source in sources:
            name = source.get_display_name()
            is_enabled = source.get_enabled() and (name not in ignored)
            cals.append({
                "name": name,
                "enabled": is_enabled,
                "source": "eds://" + name
            })
        return cals
