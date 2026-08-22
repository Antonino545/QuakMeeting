"""
Backward-compatibility facade for calendar scanning.
Delegates to core.domain.classifier and core.services.calendar_service.
"""
from typing import List, Dict, Any
from core.domain.classifier import EventClassifier, MEETING_PATTERNS
from core.domain.models import Meeting
from core.services.calendar_service import calendar_service, CACHE_DIR, CACHE_FILE, CACHE_TTL_SECONDS
from core.services.config_service import config

extract_meeting_url = EventClassifier.extract_meeting_url
classify_event = EventClassifier.classify

def get_upcoming_meetings(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Retrieve upcoming meetings as dictionary list for full backward compatibility."""
    meetings = calendar_service.get_upcoming_meetings(force_refresh=force_refresh)
    return [m.to_dict() if isinstance(m, Meeting) else m for m in meetings]

def sync_calendar_now() -> List[Dict[str, Any]]:
    """Force sync calendar now and return dictionary list."""
    meetings = calendar_service.sync_now()
    return [m.to_dict() if isinstance(m, Meeting) else m for m in meetings]

def get_available_calendars() -> List[Dict[str, Any]]:
    return calendar_service.get_available_calendars()

__all__ = [
    "extract_meeting_url",
    "classify_event",
    "get_upcoming_meetings",
    "sync_calendar_now",
    "get_available_calendars",
    "MEETING_PATTERNS",
    "CACHE_DIR",
    "CACHE_FILE",
    "CACHE_TTL_SECONDS",
]
