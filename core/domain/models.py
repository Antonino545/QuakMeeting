"""
Domain models and Enums for QuakMeeting.
Pure Python representations decoupled from PyObjC and external frameworks.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

__version__ = "1.0.5"

class PilotType(str, Enum):
    DUCK = "duck"
    CAPTAIN = "captain"
    CHEF = "chef"
    OWL = "owl"
    DRIVER = "driver"
    ZEN_DUCK = "zen_duck"
    GYM = "gym"
    PLATYPUS = "platypus"
    SQUIRREL = "squirrel"

class EventCategory(str, Enum):
    VIDEO_MEETING = "video_meeting"
    TRAVEL = "travel"
    FOOD = "food"
    CLASS = "class"
    STUDY = "study"
    HEALTH = "health"
    IN_PERSON = "in_person"
    SPORT = "sport"
    GENERAL = "general"


class TransportMode(str, Enum):
    TRANSIT = "transit"           # Public Transit (Bus, Tram, Subway, Train) 🚆🚌
    AUTOMOBILE = "automobile"     # Car / Motorcycle 🚗
    WALKING = "walking"           # Walking 🚶‍♂️
    BICYCLING = "bicycling"       # Cycling 🚲

def format_duration(minutes: Optional[int], long_form: bool = False) -> str:
    """
    Converts a duration in minutes into a human-readable string with hours and minutes.
    Examples:
    - 30 min -> "30m" (short) or "30 min" (long)
    - 60 min -> "1h" (short) or "1 hour" (long)
    - 90 min -> "1h 30m" (short) or "1h 30m" (long)
    - 120 min -> "2h" (short) or "2 hours" (long)
    - 145 min -> "2h 25m" (short) or "2h 25m" (long)
    """
    if minutes is None or minutes <= 0:
        return "0m" if not long_form else "0 min"

    hours = int(minutes // 60)
    rem_min = int(minutes % 60)

    if hours > 0 and rem_min > 0:
        return f"{hours}h {rem_min}m"
    elif hours > 0:
        if long_form:
            return f"{hours} hour" if hours == 1 else f"{hours} hours"
        return f"{hours}h"
    else:
        return f"{rem_min}m" if not long_form else f"{rem_min} min"

@dataclass
class Meeting:
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    meeting_url: Optional[str] = None
    location: str = ""
    description: str = ""
    event_type: str = "general"
    pilot_type: str = "duck"
    provider: str = "Reminder ⏰"
    action_btn_text: str = "📋 OPEN EVENT"
    action_url: Optional[str] = None
    theme_name: str = "Sunset Orange"
    is_travel: bool = False
    reminder_stage: Optional[int] = None
    category: Optional[str] = None

    # Identity and All-day flags
    uid: Optional[str] = None
    is_all_day: bool = False

    # Travel & ETA Metadata
    travel_time_minutes: Optional[int] = None
    travel_distance_km: Optional[float] = None
    transport_mode: Optional[str] = None
    departure_time: Optional[datetime] = None
    origin_address: Optional[str] = None
    eta_text: Optional[str] = None

    # Academic & Presence Metadata
    classroom: Optional[str] = None
    teacher: Optional[str] = None
    is_arrived: bool = False
    is_quiet_reminder: bool = False

    # Modular Animal & Outfit
    animal: Optional[str] = None
    outfit: Optional[str] = None

    def __post_init__(self):
        if self.category and not self.event_type:
            self.event_type = self.category
        elif self.event_type and not self.category:
            self.category = self.event_type

        from datetime import timezone
        import logging
        import uuid
        
        # Enforce all datetimes to be UTC aware
        if self.start_time:
            self.start_time = self.start_time.astimezone(timezone.utc)
        if self.end_time:
            self.end_time = self.end_time.astimezone(timezone.utc)
        if self.departure_time:
            self.departure_time = self.departure_time.astimezone(timezone.utc)

        # Generate a deterministic UUID if none is provided to avoid merging different events at the same time
        if not self.uid:
            time_str = self.start_time.strftime("%Y%m%dT%H%M") if self.start_time else "unknown_time"
            unique_str = f"{self.title}_{time_str}_{self.provider}_{self.location}_{self.description}"
            self.uid = str(uuid.uuid5(uuid.NAMESPACE_URL, unique_str))

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    @property
    def id(self) -> str:
        """Unique deterministic identifier for an event."""
        if self.uid:
            return self.uid
        time_str = self.start_time.strftime("%Y%m%d%H%M") if self.start_time else "000000000000"
        return f"{self.title}_{time_str}"

    @property
    def is_upcoming(self) -> bool:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.end_time:
            return self.end_time > now
        if self.start_time:
            return self.start_time > now
        return False

    @property
    def duration_minutes(self) -> Optional[int]:
        """Total scheduled duration in minutes."""
        if self.start_time and self.end_time:
            diff = (self.end_time - self.start_time).total_seconds() / 60.0
            return max(0, int(round(diff)))
        return None

    @property
    def is_past(self) -> bool:
        return not self.is_upcoming

    def to_dict(self) -> Dict[str, Any]:
        """Convert Meeting to dictionary format for backward compatibility and JSON serialization."""
        return {
            "uid": self.uid,
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_all_day": self.is_all_day,
            "meeting_url": self.meeting_url,
            "location": self.location,
            "description": self.description,
            "event_type": self.event_type,
            "pilot_type": self.pilot_type,
            "provider": self.provider,
            "action_btn_text": self.action_btn_text,
            "action_url": self.action_url,
            "theme_name": self.theme_name,
            "is_travel": self.is_travel,
            "reminder_stage": self.reminder_stage,
            "category": self.category,
            "travel_time_minutes": self.travel_time_minutes,
            "travel_distance_km": self.travel_distance_km,
            "transport_mode": self.transport_mode,
            "departure_time": self.departure_time,
            "origin_address": self.origin_address,
            "eta_text": self.eta_text,
            "classroom": self.classroom,
            "teacher": self.teacher,
            "is_arrived": self.is_arrived,
            "is_quiet_reminder": self.is_quiet_reminder,
            "animal": self.animal,
            "outfit": self.outfit
        }

    def to_serializable_dict(self) -> Dict[str, Any]:
        """Convert Meeting to JSON-serializable dictionary with ISO-formatted dates."""
        d = self.to_dict()
        d["start_time"] = self.start_time.isoformat() if self.start_time else None
        d["end_time"] = self.end_time.isoformat() if self.end_time else None
        d["departure_time"] = self.departure_time.isoformat() if self.departure_time else None
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Meeting":
        """Create Meeting object from a dictionary, handling both datetime and ISO string formats."""
        start_val = d.get("start_time")
        if isinstance(start_val, str):
            start_dt = datetime.fromisoformat(start_val)
        else:
            start_dt = start_val

        end_val = d.get("end_time")
        if isinstance(end_val, str):
            end_dt = datetime.fromisoformat(end_val)
        else:
            end_dt = end_val

        dep_val = d.get("departure_time")
        if isinstance(dep_val, str):
            dep_dt = datetime.fromisoformat(dep_val)
        else:
            dep_dt = dep_val

        return cls(
            uid=d.get("uid"),
            title=d.get("title", ""),
            start_time=start_dt,
            end_time=end_dt,
            is_all_day=bool(d.get("is_all_day", False)),
            meeting_url=d.get("meeting_url"),
            location=d.get("location", ""),
            description=d.get("description", ""),
            event_type=d.get("event_type", d.get("category", "general")),
            pilot_type=d.get("pilot_type", "duck"),
            provider=d.get("provider", "Reminder ⏰"),
            action_btn_text=d.get("action_btn_text", "📋 OPEN EVENT"),
            action_url=d.get("action_url"),
            theme_name=d.get("theme_name", "Sunset Orange"),
            is_travel=bool(d.get("is_travel", False)),
            reminder_stage=d.get("reminder_stage"),
            category=d.get("category"),
            travel_time_minutes=d.get("travel_time_minutes"),
            travel_distance_km=d.get("travel_distance_km"),
            transport_mode=d.get("transport_mode"),
            departure_time=dep_dt,
            origin_address=d.get("origin_address"),
            eta_text=d.get("eta_text"),
            classroom=d.get("classroom"),
            teacher=d.get("teacher"),
            is_arrived=bool(d.get("is_arrived", False)),
            is_quiet_reminder=bool(d.get("is_quiet_reminder", False)),
            animal=d.get("animal"),
            outfit=d.get("outfit")
        )
