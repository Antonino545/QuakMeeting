"""
Domain models and Enums for QuakMeeting.
Pure Python representations decoupled from PyObjC and external frameworks.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class PilotType(str, Enum):
    DUCK = "duck"
    CAPTAIN = "captain"
    CHEF = "chef"
    OWL = "owl"
    DRIVER = "driver"
    ZEN_DUCK = "zen_duck"

class EventCategory(str, Enum):
    VIDEO_MEETING = "video_meeting"
    TRAVEL = "travel"
    FOOD = "food"
    STUDY = "study"
    HEALTH = "health"
    IN_PERSON = "in_person"
    GENERAL = "general"

class TransportMode(str, Enum):
    TRANSIT = "transit"           # Mezzi Pubblici (Bus, Tram, Metro, Treno) 🚆🚌
    AUTOMOBILE = "automobile"     # Auto / Moto 🚗
    WALKING = "walking"           # A Piedi 🚶‍♂️
    BICYCLING = "bicycling"       # Bicicletta 🚲

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
    provider: str = "Promemoria ⏰"
    action_btn_text: str = "📋 APRI EVENTO"
    action_url: Optional[str] = None
    theme_name: str = "Sunset Orange"
    is_travel: bool = False
    reminder_stage: Optional[int] = None
    category: Optional[str] = None
    
    # Travel & ETA Metadata
    travel_time_minutes: Optional[int] = None
    travel_distance_km: Optional[float] = None
    transport_mode: str = "transit"
    departure_time: Optional[datetime] = None
    origin_address: Optional[str] = None
    eta_text: Optional[str] = None

    def __post_init__(self):
        if self.category and not self.event_type:
            self.event_type = self.category
        elif self.event_type and not self.category:
            self.category = self.event_type

    @property
    def id(self) -> str:
        """Unique deterministic identifier for an event based on title and start time."""
        time_str = self.start_time.strftime("%Y%m%d%H%M") if self.start_time else "000000000000"
        return f"{self.title}_{time_str}"

    @property
    def is_upcoming(self) -> bool:
        now = datetime.now()
        if self.end_time:
            return self.end_time > now
        if self.start_time:
            return self.start_time > now
        return False

    @property
    def is_past(self) -> bool:
        return not self.is_upcoming

    def to_dict(self) -> Dict[str, Any]:
        """Convert Meeting to dictionary format for backward compatibility and JSON serialization."""
        return {
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
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
            "eta_text": self.eta_text
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
            title=d.get("title", ""),
            start_time=start_dt,
            end_time=end_dt,
            meeting_url=d.get("meeting_url"),
            location=d.get("location", ""),
            description=d.get("description", ""),
            event_type=d.get("event_type", d.get("category", "general")),
            pilot_type=d.get("pilot_type", "duck"),
            provider=d.get("provider", "Promemoria ⏰"),
            action_btn_text=d.get("action_btn_text", "📋 APRI EVENTO"),
            action_url=d.get("action_url"),
            theme_name=d.get("theme_name", "Sunset Orange"),
            is_travel=bool(d.get("is_travel", False)),
            reminder_stage=d.get("reminder_stage"),
            category=d.get("category"),
            travel_time_minutes=d.get("travel_time_minutes"),
            travel_distance_km=d.get("travel_distance_km"),
            transport_mode=d.get("transport_mode", "transit"),
            departure_time=dep_dt,
            origin_address=d.get("origin_address"),
            eta_text=d.get("eta_text")
        )
