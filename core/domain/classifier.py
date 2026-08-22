"""
Event Classification and URL Extraction Engine for QuakMeeting.
Pure Python matching logic for video meeting providers, keyword pilots, and travel detection.
"""
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from .models import Meeting, PilotType, EventCategory

MEETING_PATTERNS = [
    (r"https://meet\.google\.com/[a-z0-9-]+", "Google Meet 🟢", "duck", "🚀 JOIN GOOGLE MEET"),
    (r"https://[a-zA-Z0-9-]+\.zoom\.us/[jsw]/[0-9a-zA-Z?=&_-]+", "Zoom Meeting 🔷", "duck", "🚀 JOIN ZOOM MEETING"),
    (r"https://teams\.microsoft\.com/l/meetup-join/[0-9a-zA-Z%?=&_-]+", "Microsoft Teams 🟣", "duck", "🚀 JOIN TEAMS MEETING"),
    (r"https://teams\.live\.com/meet/[0-9a-zA-Z?=&_-]+", "Microsoft Teams 🟣", "duck", "🚀 JOIN TEAMS MEETING"),
    (r"https://app\.serenis\.it/join/[0-9a-zA-Z_-]+", "Serenis 🛋️", "zen_duck", "🚀 JOIN SESSION")
]

DEFAULT_KEYWORDS = {
    "chef": ["dinner", "lunch", "cena", "pranzo", "restaurant", "ristorante", "pizza", "pizzeria", "sushi", "aperitivo", "apericena", "osteria", "trattoria", "food", "cibo", "eat", "mangiare", "pub", "burger", "barbecue", "bbq", "cocktail"],
    "captain": ["flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "pullman", "ryanair", "easyjet", "wizz", "ita airways", "train", "treno", "frecciarossa", "italo", "station", "stazione", "travel", "viaggio", "trip", "departure", "partenza", "gate", "terminal", "boarding", "imbarco", "taxi", "uber"],
    "owl": ["university", "universit", "uni", "exam", "esame", "esami", "lecture", "lezione", "lezioni", "study", "studio", "politecnico", "thesis", "tesi", "smartgrid", "building", "ict", "satellite", "operations research", "ricerca operativa", "course", "corso", "classroom", "aula"],
    "driver": ["gym", "palestra", "workout", "allenamento", "dentist", "dentista", "doctor", "dottore", "visit", "visita", "medical", "medico", "therapy", "terapia", "yoga", "office", "ufficio", "drive", "driving"],
    "zen_duck": ["serenis", "therapy", "terapia", "yoga", "meditation", "meditazione", "mindfulness", "wellness", "benessere", "relax", "spa", "chill"]
}

class EventClassifier:
    """Classifies raw calendar events into enriched domain Meeting objects."""

    def __init__(self, custom_keywords: Optional[Dict[str, List[str]]] = None):
        self.keywords = custom_keywords or DEFAULT_KEYWORDS

    @staticmethod
    def extract_meeting_url(text: str) -> Optional[str]:
        """Extract first known video meeting URL from text (notes, description, location)."""
        if not text or not isinstance(text, str):
            return None
        for pattern, _, _, _ in MEETING_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def classify(self, title: str, location: str = "", description: str = "",
                 start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Meeting:
        """Classifies an event by inspecting URLs, keywords, and location metadata."""
        search_blob = f"{title} {location} {description}".lower()
        
        # 1. Match Video Meeting Patterns
        for pattern, provider_name, p_type, btn_text in MEETING_PATTERNS:
            match = re.search(pattern, search_blob, re.IGNORECASE)
            if match:
                url = match.group(0)
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    meeting_url=url,
                    location=location,
                    description=description,
                    event_type=EventCategory.VIDEO_MEETING.value,
                    pilot_type=p_type,
                    provider=provider_name,
                    action_btn_text=btn_text,
                    action_url=url,
                    theme_name="Teal Modern" if p_type == "zen_duck" else "Sunset Orange",
                    is_travel=False
                )

        # 2. Check Physical Food / Dinner keywords
        for kw in self.keywords.get("chef", []):
            if kw in search_blob:
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}"
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.FOOD.value,
                    pilot_type=PilotType.CHEF.value,
                    provider="Dinner / Food 🍕🍽️",
                    action_btn_text="🗺️ RESTAURANT DIRECTIONS (MAPS)",
                    action_url=maps_url,
                    theme_name="Chef Orange",
                    is_travel=True
                )

        # 3. Check Travel / Flights / Airport / Trains
        for kw in self.keywords.get("captain", []):
            if kw in search_blob:
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}"
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.TRAVEL.value,
                    pilot_type=PilotType.CAPTAIN.value,
                    provider="Flight / Travel ✈️",
                    action_btn_text="🗺️ TRAVEL DIRECTIONS (MAPS)",
                    action_url=maps_url,
                    theme_name="Sky Captain Blue",
                    is_travel=True
                )

        # 4. Check University / Academic Owl
        for kw in self.keywords.get("owl", []):
            if kw in search_blob:
                is_trav = bool(location and location != "missing value" and "online" not in search_blob)
                maps_dest = location if is_trav else title
                maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}" if is_trav else "https://calendar.apple.com"
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.STUDY.value,
                    pilot_type=PilotType.OWL.value,
                    provider="Study / University 🎓",
                    action_btn_text="🗺️ CAMPUS & CLASSROOM" if is_trav else "📚 CLASSROOM & NOTES",
                    action_url=maps_url,
                    theme_name="Academic Purple",
                    is_travel=is_trav
                )

        # 5. Check Gym / Fitness / Driver
        for kw in self.keywords.get("driver", []):
            if kw in search_blob:
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?daddr={urllib.parse.quote(maps_dest)}"
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.IN_PERSON.value,
                    pilot_type=PilotType.DRIVER.value,
                    provider="In Person 📍 Travel Time!",
                    action_btn_text="🗺️ NAVIGATE WITH MAPS",
                    action_url=maps_url,
                    theme_name="Racing Green",
                    is_travel=True
                )

        # 6. Check Therapy / Zen Duck
        for kw in self.keywords.get("zen_duck", []):
            if kw in search_blob:
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.HEALTH.value,
                    pilot_type=PilotType.ZEN_DUCK.value,
                    provider="Serenis & Wellness 🛋️",
                    action_btn_text="🚀 JOIN SESSION",
                    action_url="https://app.serenis.it",
                    theme_name="Zen Teal",
                    is_travel=False
                )

        # 7. Generic Physical Event (if non-empty location)
        if location and location != "missing value" and len(location.strip()) > 2:
            maps_url = f"https://maps.apple.com/?daddr={urllib.parse.quote(location)}"
            return Meeting(
                title=title,
                start_time=start_time or datetime.now(),
                end_time=end_time,
                location=location,
                description=description,
                event_type=EventCategory.IN_PERSON.value,
                pilot_type=PilotType.DRIVER.value,
                provider="In Person 📍 Travel Time!",
                action_btn_text="🗺️ OPEN IN APPLE MAPS",
                action_url=maps_url,
                theme_name="Racing Green",
                is_travel=True
            )

        # 8. General Default Meeting / Reminder
        return Meeting(
            title=title,
            start_time=start_time or datetime.now(),
            end_time=end_time,
            location=location,
            description=description,
            event_type=EventCategory.GENERAL.value,
            pilot_type=PilotType.DUCK.value,
            provider="Reminder ⏰",
            action_btn_text="📋 OPEN IN CALENDAR",
            action_url="https://calendar.apple.com",
            theme_name="Sunset Orange",
            is_travel=False
        )

    @staticmethod
    def parse_applescript_date(date_str: str) -> Optional[datetime]:
        """Parses AppleScript localized dates into Python datetime objects."""
        if not date_str or date_str == "missing value":
            return None
        cleaned = date_str.replace("alle ", "").replace("at ", "").strip()
        formats = [
            "%d/%m/%Y, %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d %B %Y %H:%M:%S",
            "%d/%m/%Y, %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%A %d %B %Y %H:%M:%S",
            "%A, %d %B %Y %H:%M:%S",
            "%a %d %b %Y %H:%M:%S"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        return None
