"""
Calendar Service for QuakMeeting.
Coordinates in-memory and disk caching, provider querying, background sync, and ETA route enrichment.
Strictly retrieves only current and upcoming events for Today.
"""
import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from core.domain.models import Meeting, format_duration
from core.domain.classifier import EventClassifier
from core.services.config_service import config_service, ConfigService
from core.services.event_bus import event_bus, EventBus
from core.services.eta_service import eta_service, ETAService, MODE_ICONS
import sys
from core.providers.base import BaseCalendarProvider
from core.providers.eventkit_provider import EventKitCalendarProvider
from core.providers.caldav_provider import CalDAVCalendarProvider

from core.repositories.meeting_repository import MeetingRepository

logger = logging.getLogger("QuakMeeting.CalendarService")

CACHE_DIR = os.path.expanduser("~/.quakmeeting")
CACHE_FILE = os.path.join(CACHE_DIR, "calendar_cache.json")
CACHE_TTL_SECONDS = 90.0

class CalendarService:
    """Manages meeting fetching, caching, and calendar synchronization for Today and Tomorrow."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CalendarService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, provider: Optional[BaseCalendarProvider] = None, config: Optional[ConfigService] = None, bus: Optional[EventBus] = None):
        if self._initialized:
            return
        self.config = config or config_service
        self.bus = bus or event_bus
        self.repository = MeetingRepository(CACHE_FILE)

        self.last_sync_time = None
        self.last_sync_status = "Pending"
        self.last_error = None
        self.provider_name = "Unknown"

        # Select best available provider based on platform
        if provider:
            self._provider = provider
        elif sys.platform == "darwin":
            self._provider = EventKitCalendarProvider(self.config)
            self.provider_name = "macOS EventKit"
        else:
            from core.providers.eds_provider import EDSCalendarProvider
            eds = EDSCalendarProvider(self.config)
            if eds.is_available():
                logger.info("Evolution Data Server detected. Using EDSCalendarProvider.")
                self._provider = eds
                self.provider_name = "Evolution Data Server"
            else:
                logger.info("EDS not available. Falling back to CalDAVCalendarProvider.")
                self._provider = CalDAVCalendarProvider(self.config)
                self.provider_name = "CalDAV"

        self._in_memory_cache: List[Meeting] = []
        self._last_fetch_time: float = 0.0
        self._is_fetching: bool = False
        self._cached_calendars: List[Dict[str, Any]] = []
        self._last_calendars_fetch_time: float = 0.0
        self._fetch_lock = threading.Lock()
        self._initialized = True

    def set_provider(self, provider: BaseCalendarProvider) -> None:
        self._provider = provider
        self.provider_name = provider.__class__.__name__

    def _enrich_with_eta(self, meetings: List[Meeting]) -> None:
        """Enriches physical/travel meetings with ETA travel time and departure deadlines."""
        if not self.config.get("enable_eta_service", True):
            return

        home_address = self.config.get("home_address", "").strip()
        transport_mode = self.config.get("transport_mode", "transit")
        buffer_minutes = int(self.config.get("eta_buffer_minutes", 10))

        for m in meetings:
            if m.is_all_day:
                continue
            if m.is_travel and m.start_time:
                dest = m.location if (m.location and m.location != "missing value") else m.title

                dur_str = format_duration(m.travel_time_minutes)
                mode = m.transport_mode or transport_mode
                m.transport_mode = mode

                # 1. Native EventKit travel time already extracted from Apple Calendar
                if m.travel_time_minutes and m.travel_time_minutes > 0:
                    m.departure_time = eta_service.get_departure_time(m.start_time, m.travel_time_minutes, buffer_minutes)
                    icon = MODE_ICONS.get(mode, "🚆")
                    dep_str = m.departure_time.astimezone().strftime("%H:%M")
                    m.eta_text = f"{icon} ~{dur_str} • Leave at {dep_str}"
                    if not m.action_url or ("maps.apple.com" not in m.action_url and "maps.google.com" not in m.action_url):
                        m.action_url = eta_service.build_maps_url(home_address or None, dest, mode)

                    if mode == "transit":
                        m.action_btn_text = f"🗺️ PUBLIC TRANSIT (~{dur_str})"
                    elif mode == "automobile":
                        m.action_btn_text = f"🗺️ DRIVE WITH MAPS (~{dur_str})"
                    elif mode == "walking":
                        m.action_btn_text = f"🗺️ WALKING ROUTE (~{dur_str})"
                    elif mode == "bicycling":
                        m.action_btn_text = f"🗺️ CYCLING ROUTE (~{dur_str})"
                    else:
                        m.action_btn_text = f"🗺️ MAPS ROUTE (~{dur_str})"

                # 2. Fallback: calculate ETA via ETAService if home_address is configured
                elif home_address and dest:
                    eta_res = eta_service.calculate_eta(home_address, dest, mode)
                    if eta_res:
                        m.travel_time_minutes = eta_res["duration_minutes"]
                        m.travel_distance_km = eta_res["distance_km"]
                        m.transport_mode = mode
                        m.origin_address = home_address
                        m.departure_time = eta_service.get_departure_time(m.start_time, m.travel_time_minutes, buffer_minutes)

                        dur_str = format_duration(m.travel_time_minutes)
                        icon = MODE_ICONS.get(mode, "🚆")
                        dep_str = m.departure_time.astimezone().strftime("%H:%M")
                        m.eta_text = f"{icon} ~{dur_str} • Leave at {dep_str}"
                        m.action_url = eta_res["maps_url"]

                        if mode == "transit":
                            m.action_btn_text = f"🗺️ PUBLIC TRANSIT (~{dur_str})"
                        elif mode == "automobile":
                            m.action_btn_text = f"🗺️ DRIVE WITH MAPS (~{dur_str})"
                        elif mode == "walking":
                            m.action_btn_text = f"🗺️ WALKING ROUTE (~{dur_str})"
                        elif mode == "bicycling":
                            m.action_btn_text = f"🗺️ CYCLING ROUTE (~{dur_str})"

    def _save_cache_to_disk(self, meetings: List[Meeting]) -> None:
        self.repository.save(meetings)

    def _filter_within_window(self, meetings: List[Meeting]) -> List[Meeting]:
        """Filters events to only include those happening Today (00:00 to 23:59:59)."""
        from datetime import timezone
        # Determine local 'today' boundaries converted to UTC
        now = datetime.now().astimezone() 
        start_of_today_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_today_local = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        start_of_today = start_of_today_local.astimezone(timezone.utc)
        end_of_today = end_of_today_local.astimezone(timezone.utc)

        filtered = []
        for m in meetings:
            if not m.start_time:
                continue
                
            s = m.start_time
            e = m.end_time or m.start_time
            
            # Intersection logic: begins on or before end_of_today AND ends on or after start_of_today
            if s <= end_of_today and e >= start_of_today:
                filtered.append(m)

        # Deduplicate events based on uid if available, else title and start time
        seen = set()
        deduped = []
        for m in filtered:
            key = m.uid if m.uid else (m.title, m.start_time.timestamp())
            if key not in seen:
                seen.add(key)
                deduped.append(m)

        deduped.sort(key=lambda m: m.start_time)
        return deduped

    def _load_cache_from_disk(self) -> List[Meeting]:
        loaded = self.repository.load()
        if loaded:
            filtered = self._filter_within_window(loaded)
            self._in_memory_cache = filtered
            self._last_fetch_time = self.repository.get_last_modified_time()
            return filtered
        return []

    def sync_now(self) -> List[Meeting]:
        """Force synchronous fetch from calendar provider, updating cache and publishing event."""
        with self._fetch_lock:
            self._is_fetching = True
            try:
                raw_meetings = self._provider.fetch_events()
                filtered = self._filter_within_window(raw_meetings)
                self._enrich_with_eta(filtered)
                self._in_memory_cache = filtered
                self._last_fetch_time = time.time()
                self._save_cache_to_disk(filtered)
                
                self.last_sync_time = datetime.now()
                self.last_sync_status = "Success"
                self.last_error = None

                logger.info(f"Synchronized {len(filtered)} events scheduled for today.")
                self.bus.publish("CALENDAR_SYNCED", meetings=filtered)
                return filtered
            except Exception as e:
                self.last_sync_time = datetime.now()
                self.last_sync_status = "Error"
                self.last_error = str(e)
                logger.error(f"Error during calendar synchronization: {e}", exc_info=True)
                return self._in_memory_cache
            finally:
                self._is_fetching = False

    def get_upcoming_meetings(self, force_refresh: bool = False) -> List[Meeting]:
        """Return cached meetings immediately (< 0.001s), dispatching background sync if needed."""
        if not self._in_memory_cache:
            self._load_cache_from_disk()

        if force_refresh or (not self._in_memory_cache and self._last_fetch_time == 0.0):
            if not self._is_fetching:
                threading.Thread(target=self.sync_now, daemon=True).start()
        elif time.time() - self._last_fetch_time > CACHE_TTL_SECONDS and not self._is_fetching:
            threading.Thread(target=self.sync_now, daemon=True).start()

        return list(self._in_memory_cache)

    def get_available_calendars(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Return list of macOS calendars with 5-minute cache to prevent main-thread UI blocking."""
        if not force_refresh and self._cached_calendars and (time.time() - self._last_calendars_fetch_time < 300.0):
            return list(self._cached_calendars)

        try:
            cals = self._provider.get_available_calendars()
            self._cached_calendars = cals
            self._last_calendars_fetch_time = time.time()
            return list(cals)
        except Exception as e:
            logger.error(f"Error fetching calendars list: {e}")
            return list(self._cached_calendars)

    def is_in_lesson(self, current_time: Optional[datetime] = None) -> bool:
        """Checks if the user is currently attending an active lecture/lesson or study session."""
        from datetime import timezone
        now = (current_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
        meetings = self.get_upcoming_meetings()
        for m in meetings:
            if m.is_all_day:
                continue
            is_lesson = (
                m.event_type in ("class", "study") or
                m.category in ("class", "study") or
                bool(m.classroom) or
                bool(m.teacher)
            )
            if not is_lesson:
                continue

            if m.start_time and m.end_time:
                if m.start_time <= now <= m.end_time:
                    return True
            elif m.start_time:
                diff = (now - m.start_time).total_seconds() / 60.0
                if 0 <= diff <= 45:
                    return True
        return False

# Global singleton instance
calendar_service = CalendarService()
