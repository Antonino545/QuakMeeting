"""
Calendar Service for QuakMeeting.
Coordinates in-memory and disk caching, provider querying, background sync, and ETA route enrichment.
Strictly retrieves only current and upcoming events for Today and Tomorrow.
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
from core.providers.base import BaseCalendarProvider
from core.providers.eventkit_provider import EventKitCalendarProvider

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
        
        # Select best available provider (EventKit if available, else AppleScript)
        if provider:
            self._provider = provider
        else:
            self._provider = EventKitCalendarProvider(self.config)

        self._in_memory_cache: List[Meeting] = []
        self._last_fetch_time: float = 0.0
        self._is_fetching: bool = False
        self._cached_calendars: List[Dict[str, Any]] = []
        self._last_calendars_fetch_time: float = 0.0
        self._fetch_lock = threading.Lock()
        self._initialized = True

    def set_provider(self, provider: BaseCalendarProvider) -> None:
        self._provider = provider

    def _enrich_with_eta(self, meetings: List[Meeting]) -> None:
        """Enriches physical/travel meetings with ETA travel time and departure deadlines."""
        if not self.config.get("enable_eta_service", True):
            return

        home_address = self.config.get("home_address", "").strip()
        transport_mode = self.config.get("transport_mode", "transit")
        buffer_minutes = int(self.config.get("eta_buffer_minutes", 10))

        for m in meetings:
            if m.is_travel and m.start_time:
                dest = m.location if (m.location and m.location != "missing value") else m.title
                
                dur_str = format_duration(m.travel_time_minutes)
                
                # 1. Native EventKit travel time already extracted from Apple Calendar
                if m.travel_time_minutes and m.travel_time_minutes > 0:
                    m.departure_time = eta_service.get_departure_time(m.start_time, m.travel_time_minutes, buffer_minutes)
                    icon = MODE_ICONS.get(m.transport_mode or transport_mode, "🚗")
                    dep_str = m.departure_time.strftime("%H:%M")
                    m.eta_text = f"{icon} ~{dur_str} • Leave at {dep_str}"
                    if not m.action_url or "maps.apple.com" not in m.action_url:
                        m.action_url = eta_service.build_apple_maps_url(home_address or None, dest, m.transport_mode or transport_mode)
                    
                    mode = m.transport_mode or transport_mode
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
                    eta_res = eta_service.calculate_eta(home_address, dest, transport_mode)
                    if eta_res:
                        m.travel_time_minutes = eta_res["duration_minutes"]
                        m.travel_distance_km = eta_res["distance_km"]
                        m.transport_mode = transport_mode
                        m.origin_address = home_address
                        m.departure_time = eta_service.get_departure_time(m.start_time, m.travel_time_minutes, buffer_minutes)
                        
                        dur_str = format_duration(m.travel_time_minutes)
                        icon = MODE_ICONS.get(transport_mode, "🚆")
                        dep_str = m.departure_time.strftime("%H:%M")
                        m.eta_text = f"{icon} ~{dur_str} • Leave at {dep_str}"
                        m.action_url = eta_res["maps_url"]
                        
                        if transport_mode == "transit":
                            m.action_btn_text = f"🗺️ PUBLIC TRANSIT (~{dur_str})"
                        elif transport_mode == "automobile":
                            m.action_btn_text = f"🗺️ DRIVE WITH MAPS (~{dur_str})"
                        elif transport_mode == "walking":
                            m.action_btn_text = f"🗺️ WALKING ROUTE (~{dur_str})"
                        elif transport_mode == "bicycling":
                            m.action_btn_text = f"🗺️ CYCLING ROUTE (~{dur_str})"

    def _save_cache_to_disk(self, meetings: List[Meeting]) -> None:
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            serializable = [m.to_serializable_dict() for m in meetings]
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error saving calendar cache to disk: {e}")

    def _filter_today_and_tomorrow(self, meetings: List[Meeting]) -> List[Meeting]:
        """Filters events so only events starting between today (00:00) and tomorrow (23:59:59) are kept."""
        now = datetime.now()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=2)
        end_of_tomorrow = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

        filtered = [
            m for m in meetings 
            if m.start_time and start_of_today <= m.start_time <= end_of_tomorrow
        ]
        filtered.sort(key=lambda m: m.start_time)
        return filtered

    def _load_cache_from_disk(self) -> List[Meeting]:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                loaded = [Meeting.from_dict(item) for item in data]
                filtered = self._filter_today_and_tomorrow(loaded)
                self._in_memory_cache = filtered
                self._last_fetch_time = os.path.getmtime(CACHE_FILE)
                return filtered
            except Exception as e:
                logger.warning(f"Error loading calendar cache from disk: {e}")
        return []

    def sync_now(self) -> List[Meeting]:
        """Force synchronous fetch from calendar provider, updating cache and publishing event."""
        with self._fetch_lock:
            self._is_fetching = True
            try:
                raw_meetings = self._provider.fetch_events()
                filtered = self._filter_today_and_tomorrow(raw_meetings)
                self._enrich_with_eta(filtered)
                self._in_memory_cache = filtered
                self._last_fetch_time = time.time()
                self._save_cache_to_disk(filtered)
                logger.info(f"Synchronized {len(filtered)} events scheduled for today and tomorrow.")
                self.bus.publish("CALENDAR_SYNCED", meetings=filtered)
                return filtered
            except Exception as e:
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

# Global singleton instance
calendar_service = CalendarService()
