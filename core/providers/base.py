"""
Base Calendar Provider abstract interface for QuakMeeting.
Defines standard contract for querying calendar events across different data sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.domain.models import Meeting

class BaseCalendarProvider(ABC):
    """Abstract interface for calendar data retrieval."""

    @abstractmethod
    def fetch_events(self, start_offset_hours: int = 2, end_offset_hours: int = 24) -> List[Meeting]:
        """Fetch events within [now - start_offset_hours, now + end_offset_hours]."""
        pass

    @abstractmethod
    def get_available_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars on the system and their enabled status."""
        pass
