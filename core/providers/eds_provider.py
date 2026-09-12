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

logger = logging.getLogger("FlightDeck.EDSProvider")

class EDSCalendarProvider(BaseCalendarProvider):
    """Calendar provider using GNOME Evolution Data Server (EDS)."""

    def __init__(self, config: Optional[ConfigService] = None):
        self.config = config or config_service
        self._registry = None
        self._is_available = None
        self._clients: Dict[str, Any] = {}

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
            logger.debug("EDS availability check: %s.", self._is_available)
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
        logger.debug("EDS returned %d calendar sources.", len(sources))

        active_sources = []
        for source in sources:
            name = source.get_display_name()
            if name not in ignored and source.get_enabled():
                active_sources.append(source)

        # Connect to uncached sources concurrently to eliminate sequential timeout stalls
        sources_to_connect = [s for s in active_sources if s.get_uid() not in self._clients]
        if sources_to_connect:
            from concurrent.futures import ThreadPoolExecutor

            def _connect_worker(src):
                try:
                    # 1.5s timeout prevents blocking on dormant or unreachable webcal/CalDAV endpoints
                    c = ECal.Client.connect_sync(src, ECal.ClientSourceType.EVENTS, 1.5, None)
                    return src.get_uid(), c
                except Exception as exc:
                    logger.debug("Failed to connect to EDS source '%s': %s", src.get_display_name(), exc)
                    return src.get_uid(), None

            max_workers = min(16, len(sources_to_connect))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for uid, client in pool.map(_connect_worker, sources_to_connect):
                    if client:
                        self._clients[uid] = client

        meetings: List[Meeting] = []

        from core.providers.caldav_provider import CalDAVCalendarProvider
        caldav_parser = CalDAVCalendarProvider(self.config)

        for source in active_sources:
            name = source.get_display_name()
            uid = source.get_uid()
            client = self._clients.get(uid)
            if not client:
                continue

            try:
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
                                end_time=e_dt or (s_dt + timedelta(hours=1)),
                                calendar_name=name
                            )
                            meeting.provider = name
                            meetings.append(meeting)
                    except Exception as parse_e:
                        logger.debug(f"Failed to parse EDS event in '{name}': {parse_e}")

            except Exception as e:
                logger.debug(f"Failed to fetch events from EDS source '{name}': {e}")
                self._clients.pop(uid, None)

        meetings.sort(key=lambda m: m.start_time if m.start_time else datetime.min)
        logger.debug("Parsed %d meetings from EDS.", len(meetings))
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
