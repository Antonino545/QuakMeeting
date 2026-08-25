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
            if name in ignored:
                continue

            try:
                client = ECal.Client.new(source, ECal.ClientSourceType.EVENTS)
                client.open_sync(None)
                
                # Query time range
                query = f'(occur-in-time-range? (make-time "{start_iso}") (make-time "{end_iso}"))'
                
                success, events = client.get_object_list_as_comps_sync(query, None)
                if not success:
                    continue
                    
                for icalcomp in events:
                    try:
                        # Extract the raw ICS string and reuse the CalDAV parser logic for robustness
                        ics_text = icalcomp.as_ical_string()
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

                            classified = EventClassifier.classify(
                                title=title,
                                location=loc,
                                notes=desc,
                                url=meeting_url,
                                custom_keywords=custom_kw
                            )
                            
                            action_url = classified.action_url or meeting_url

                            meeting = Meeting(
                                id=f"{title}_{s_dt.strftime('%Y%m%d%H%M')}",
                                title=title,
                                start_time=s_dt,
                                end_time=e_dt or (s_dt + timedelta(hours=1)),
                                location=loc,
                                notes=desc,
                                url=url_val,
                                provider=name,
                                pilot_type=classified.pilot_type,
                                category=classified.category,
                                action_btn_text=classified.action_btn_text,
                                action_url=action_url,
                                is_travel=classified.is_travel,
                                travel_time_minutes=None,
                                departure_time=None,
                                classroom=classified.classroom,
                                teacher=classified.teacher
                            )
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
            cals.append({
                "name": name,
                "enabled": name not in ignored,
                "source": "eds://" + name
            })
        return cals
