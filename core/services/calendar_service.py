"""
Calendar Service for QuakMeeting.
Coordinates in-memory and disk caching, provider querying, and background sync.
"""
import os
import json
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.domain.models import Meeting
from core.domain.classifier import EventClassifier
from core.services.config_service import config_service, ConfigService
from core.services.event_bus import event_bus, EventBus
from core.providers.base import BaseCalendarProvider
from core.providers.applescript_provider import AppleScriptCalendarProvider
from core.providers.eventkit_provider import EventKitCalendarProvider

logger = logging.getLogger("QuakMeeting.CalendarService")

CACHE_DIR = os.path.expanduser("~/.quakmeeting")
CACHE_FILE = os.path.join(CACHE_DIR, "calendar_cache.json")
CACHE_TTL_SECONDS = 90.0

class CalendarService:
    """Manages meeting fetching, caching, and calendar synchronization."""
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
        self._provider = provider or AppleScriptCalendarProvider(self.config)
        self._in_memory_cache: List[Meeting] = []
        self._last_fetch_time: float = 0.0
        self._is_fetching: bool = False
        self._fetch_lock = threading.Lock()
        self._initialized = True

    def set_provider(self, provider: BaseCalendarProvider) -> None:
        self._provider = provider

    def _save_cache_to_disk(self, meetings: List[Meeting]) -> None:
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            serializable = [m.to_serializable_dict() for m in meetings]
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error saving calendar cache to disk: {e}")

    def _load_cache_from_disk(self) -> List[Meeting]:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                loaded = [Meeting.from_dict(item) for item in data]
                self._in_memory_cache = loaded
                self._last_fetch_time = os.path.getmtime(CACHE_FILE)
                return loaded
            except Exception as e:
                logger.warning(f"Error loading calendar cache from disk: {e}")
        return []

    def sync_now(self) -> List[Meeting]:
        """Force synchronous fetch from calendar provider, updating cache and publishing event."""
        with self._fetch_lock:
            self._is_fetching = True
            try:
                meetings = self._provider.fetch_events()
                self._in_memory_cache = meetings
                self._last_fetch_time = time.time()
                self._save_cache_to_disk(meetings)
                self.bus.publish("CALENDAR_SYNCED", meetings=meetings)
                return meetings
            except Exception as e:
                logger.error(f"Error during calendar synchronization: {e}")
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

    def get_available_calendars(self) -> List[Dict[str, Any]]:
        return self._provider.get_available_calendars()

# Global singleton instance
calendar_service = CalendarService()
