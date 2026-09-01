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

    @staticmethod
    def _normalize_event_subject(title: str) -> str:
        """
        Normalizes course / exam / meeting titles for duplicate detection.
        Strips academic prefixes (Exam:, Esame:, Lezione:), classrooms (- Aula ...),
        teacher names ((Prof. ...)), and punctuation to extract the canonical subject.
        """
        if not title:
            return ""
        import re
        t = title.strip().lower()
        # Strip common prefixes e.g. "Exam:", "Esame:", "Lezione:", "Class:", "Course:", "Appello:", "Parziale:"
        t = re.sub(r'^(?:exam|esame|lezione|lezioni|class|course|corso|appello|parziale|esonero|seminario|workshop)[:\s\-\–\—\|]+', '', t, flags=re.IGNORECASE)
        # Strip teacher/extra in parentheses e.g. "(VASSIO LUCA)"
        t = re.sub(r'\([^\)]*\)', '', t)
        # Strip classroom suffix e.g. "- Aula 5M", "- Room 101"
        t = re.sub(r'[\-\–\—\|]\s*(?:aula|room|lab|edificio).*$', '', t, flags=re.IGNORECASE)
        # Strip non-alphanumeric except whitespace
        t = re.sub(r'[^a-z0-9\s]', ' ', t)
        return ' '.join(t.split())

    def _enrich_with_eta(self, meetings: List[Meeting]) -> None:
        """Enriches physical/travel meetings with ETA travel time and departure deadlines."""
        if not self.config.get("enable_eta_service", True):
            return

        home_address = self.config.get("home_address", "").strip()
        exam_location = self.config.get("exam_location", "").strip()
        transport_mode = self.config.get("transport_mode", "transit")
        buffer_minutes = int(self.config.get("eta_buffer_minutes", 10))

        for m in meetings:
            if m.is_all_day:
                continue

            # Fallback to user-configured exam_location for exams without a physical campus or where user set a default
            if m.event_type == "exam" and exam_location:
                if not m.location or m.location == "missing value" or m.location.strip() == "":
                    m.location = exam_location
                elif any(c in m.location.lower() for c in ["aula", "room", "lab"]) and not any(univ in m.location.lower() for univ in ["politecnico", "universit", "corso", "via", "piazza", "strada"]):
                    m.location = f"{exam_location}, {m.location}"
                m.is_travel = True

            if m.is_travel and m.start_time:
                dest = m.location if (m.location and m.location != "missing value") else m.title
                mode = transport_mode
                m.transport_mode = mode

                # 1. Native EventKit travel time already extracted from Apple Calendar
                if m.travel_time_minutes and m.travel_time_minutes > 0 and getattr(m, "_is_native_travel_time", True) and not getattr(m, "_is_calculated_eta", False):
                    dur_str = format_duration(m.travel_time_minutes)
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

                # 2. Dynamic calculated ETA via ETAService if home_address is configured
                elif home_address and dest:
                    eta_res = eta_service.calculate_eta(home_address, dest, mode)
                    if eta_res:
                        m.travel_time_minutes = eta_res["duration_minutes"]
                        m.travel_distance_km = eta_res["distance_km"]
                        m.origin_address = home_address
                        m.departure_time = eta_service.get_departure_time(m.start_time, m.travel_time_minutes, buffer_minutes)
                        m._is_calculated_eta = True

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
        """Filters events to only include those happening Today and deduplicates overlapping duplicates."""
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

        # 1. Deduplicate events based on exact UID
        seen_uids = set()
        unique_list: List[Meeting] = []
        for m in filtered:
            key = m.uid if m.uid else (m.title, m.start_time.timestamp())
            if key not in seen_uids:
                seen_uids.add(key)
                unique_list.append(m)

        # 2. Smart Deduplication for Duplicate Exams & Overlapping Entries
        # Groups events with matching normalized subjects and overlapping/near times
        merged_list: List[Meeting] = []
        skip_indices = set()

        for i, m1 in enumerate(unique_list):
            if i in skip_indices:
                continue

            norm1 = self._normalize_event_subject(m1.title)
            chosen = m1

            for j in range(i + 1, len(unique_list)):
                if j in skip_indices:
                    continue

                m2 = unique_list[j]
                norm2 = self._normalize_event_subject(m2.title)

                # Check if subjects match
                if norm1 and norm2 and len(norm1) >= 3 and norm1 == norm2:
                    # Check time overlap or start times within 90 minutes (5400s)
                    s1 = chosen.start_time
                    e1 = chosen.end_time or chosen.start_time
                    s2 = m2.start_time
                    e2 = m2.end_time or m2.start_time

                    time_overlaps = (s1 < e2 and s2 < e1) or (abs((s1 - s2).total_seconds()) <= 5400)
                    if time_overlaps:
                        # Decide which event to keep:
                        # Priority A: If one is an exam and the other is a regular class/event, ALWAYS KEEP EXAM!
                        is_exam_1 = chosen.event_type == "exam" or "exam" in chosen.title.lower() or "esame" in chosen.title.lower()
                        is_exam_2 = m2.event_type == "exam" or "exam" in m2.title.lower() or "esame" in m2.title.lower()

                        if is_exam_2 and not is_exam_1:
                            # Prefer m2 (the exam event)
                            survivor = m2
                            discarded = chosen
                        elif is_exam_1 and not is_exam_2:
                            # Prefer chosen (already the exam event)
                            survivor = chosen
                            discarded = m2
                        else:
                            # Both exams or both classes: prefer the one with earlier start time or more info
                            if m2.start_time < chosen.start_time:
                                survivor = m2
                                discarded = chosen
                            else:
                                survivor = chosen
                                discarded = m2

                        # Merge rich metadata from discarded event if survivor is missing it
                        if not survivor.classroom and discarded.classroom:
                            survivor.classroom = discarded.classroom
                        if not survivor.teacher and discarded.teacher:
                            survivor.teacher = discarded.teacher
                        if (not survivor.location or survivor.location == "missing value") and discarded.location and discarded.location != "missing value":
                            survivor.location = discarded.location
                        if not survivor.description and discarded.description:
                            survivor.description = discarded.description
                        if not survivor.meeting_url and discarded.meeting_url:
                            survivor.meeting_url = discarded.meeting_url

                        chosen = survivor
                        skip_indices.add(j)

            merged_list.append(chosen)

        merged_list.sort(key=lambda m: m.start_time)
        return merged_list

    def _apply_current_transport_mode(self, meetings: List[Meeting]) -> None:
        """Re-applies the current config transport_mode to all travel meetings.

        When meetings are loaded from disk cache or when the user changes the
        preferred transport mode in settings, the cached Meeting objects still
        carry the old mode.  This method patches them in-place so the UI
        immediately reflects the new preference without waiting for a full
        calendar sync.
        """
        current_mode = self.config.get("transport_mode", "transit")
        for m in meetings:
            if m.is_travel and m.transport_mode and m.transport_mode != current_mode:
                old_mode = m.transport_mode
                m.transport_mode = current_mode

                # Update the mode icon in eta_text  (e.g.  "🚆 ~30m • Leave at 08:15")
                if m.eta_text:
                    old_icon = MODE_ICONS.get(old_mode, "🚆")
                    new_icon = MODE_ICONS.get(current_mode, "🚆")
                    m.eta_text = m.eta_text.replace(old_icon, new_icon, 1)

                # Update action button text  (e.g.  "🗺️ PUBLIC TRANSIT (~30m)")
                if m.action_btn_text:
                    _BTN_LABELS = {
                        "transit": "PUBLIC TRANSIT",
                        "automobile": "DRIVE WITH MAPS",
                        "walking": "WALKING ROUTE",
                        "bicycling": "CYCLING ROUTE",
                    }
                    old_label = _BTN_LABELS.get(old_mode)
                    new_label = _BTN_LABELS.get(current_mode)
                    if old_label and new_label:
                        m.action_btn_text = m.action_btn_text.replace(old_label, new_label)

                # Rebuild the maps action URL with the new mode
                if m.action_url:
                    dest = m.location if (m.location and m.location != "missing value") else m.title
                    home = self.config.get("home_address", "").strip() or None
                    m.action_url = eta_service.build_maps_url(home, dest, current_mode)

    def _load_cache_from_disk(self) -> List[Meeting]:
        loaded = self.repository.load()
        if loaded:
            filtered = self._filter_within_window(loaded)
            self._apply_current_transport_mode(filtered)
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

    def update_transport_mode(self) -> None:
        """Immediately re-applies the current config transport_mode to all cached meetings.

        Call this after config.set("transport_mode", ...) so that the in-memory
        cache (and subsequent get_upcoming_meetings() calls) reflect the new
        preference without waiting for a full calendar sync.
        """
        if self._in_memory_cache:
            self._apply_current_transport_mode(self._in_memory_cache)

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
        """Checks if the user is currently attending an active university lecture/lesson."""
        from datetime import timezone
        now = (current_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
        meetings = self.get_upcoming_meetings()
        for m in meetings:
            if m.is_all_day:
                continue
            # Self-study sessions should not mute banner sounds
            if m.event_type == "study" or m.category == "study":
                continue

            is_class = (
                m.event_type == "class" or
                m.category == "class" or
                bool(m.classroom) or
                bool(m.teacher)
            )
            if not is_class:
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
