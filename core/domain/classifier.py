"""
Event Classification and URL Extraction Engine for QuakMeeting.
Pure Python matching logic for video meeting providers, keyword pilots, and travel detection.
"""
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List, Union
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
    "gym": ["gym", "palestra", "workout", "allenamento", "crossfit", "fitness", "sport", "padel", "tennis", "calcio", "calcetto", "partita", "match", "nuoto", "swimming", "running", "corsa", "boxe", "boxing", "basket", "pallavolo", "pesi", "cardio", "training", "maratona", "pilates", "atletica"],
    "driver": ["dentist", "dentista", "doctor", "dottore", "visit", "visita", "medical", "medico", "office", "ufficio", "drive", "driving", "appuntamento", "studio"],
    "zen_duck": ["serenis", "therapy", "terapia", "yoga", "meditation", "meditazione", "mindfulness", "wellness", "benessere", "relax", "spa", "chill"]
}


class EventClassifier:
    """Classifies raw calendar events into enriched domain Meeting objects."""

    def __init__(self, custom_keywords: Optional[Dict[str, List[str]]] = None):
        self.keywords = custom_keywords or DEFAULT_KEYWORDS

    @staticmethod
    def extract_meeting_url(text: Optional[str]) -> Optional[str]:
        """Extract first known video meeting URL from text (notes, description, location)."""
        if not text or not isinstance(text, str) or text == "missing value":
            return None
        for pattern, _, _, _ in MEETING_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def extract_classroom_and_teacher(title: str, location: str = "", description: str = "") -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts university/academic classroom and professor from strings such as:
        'ICT for smart mobility (VASSIO LUCA) - Aula 5M'
        'Sistemi Operativi - Aula 3B (Prof. Rossi)'
        'Room 201', 'Lab 4', 'Edificio B'
        """
        full_text = f"{title} {location} {description}"
        classroom = None
        teacher = None

        # 1. Match Teacher in parentheses e.g. (VASSIO LUCA), (Prof. Mario Rossi)
        teacher_match = re.search(r'\(([A-Z\s\.,\'-]{3,35}|Prof[^\)]+)\)', title)
        if teacher_match:
            cand = teacher_match.group(1).strip()
            if cand.lower() not in ["online", "zoom", "meet", "teams", "remoto", "exam", "oral", "written"]:
                teacher = cand

        # 2. Match Classroom patterns: "Aula 5M", "Aula Magna", "Room 101", "Lab 3", "Edificio 2"
        room_match = re.search(r'\b(Aula\s+[0-9A-Za-z]+|Room\s+[0-9A-Za-z]+|Lab(?:oratorio|\.)?\s+[0-9A-Za-z]+|Edificio\s+[0-9A-Za-z]+|Auditorium\s+[0-9A-Za-z]+)', full_text, re.IGNORECASE)
        if room_match:
            classroom = room_match.group(1).strip()
            classroom = re.sub(r'[\-\(\)\]].*$', '', classroom).strip()

        if not classroom and location and location != "missing value":
            if any(term in location.lower() for term in ["aula", "room", "lab", "campus", "edificio"]):
                classroom = location.strip()

        return classroom, teacher

    @classmethod
    def classify(cls, title: str, location: str = "", description: str = "",
                 meeting_url: Optional[str] = None,
                 custom_keywords: Optional[Dict[str, List[str]]] = None,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None) -> Meeting:
        """Classifies an event by inspecting URLs, keywords, and location metadata."""
        keywords_dict = DEFAULT_KEYWORDS.copy()
        if isinstance(cls, EventClassifier) and hasattr(cls, 'keywords') and cls.keywords:
            keywords_dict.update(cls.keywords)
        if custom_keywords and isinstance(custom_keywords, dict):
            for k, v in custom_keywords.items():
                if k in keywords_dict and isinstance(v, list):
                    keywords_dict[k] = list(set(keywords_dict[k] + v))
                elif isinstance(v, list):
                    keywords_dict[k] = v

        classroom, teacher = cls.extract_classroom_and_teacher(title, location, description)
        search_blob = f"{title} {location} {description} {meeting_url or ''}".lower()

        # 1. Match Video Meeting Patterns
        active_url = meeting_url or cls.extract_meeting_url(search_blob)
        if active_url:
            for pattern, provider_name, p_type, btn_text in MEETING_PATTERNS:
                if re.search(pattern, active_url, re.IGNORECASE):
                    return Meeting(
                        title=title,
                        start_time=start_time or datetime.now(),
                        end_time=end_time,
                        meeting_url=active_url,
                        location=location,
                        description=description,
                        event_type=EventCategory.VIDEO_MEETING.value,
                        pilot_type=p_type,
                        provider=provider_name,
                        action_btn_text=btn_text,
                        action_url=active_url,
                        theme_name="Teal Modern" if p_type == "zen_duck" else "Sunset Orange",
                        is_travel=False,
                        classroom=classroom,
                        teacher=teacher
                    )

        # 2. Check Physical Food / Dinner keywords
        for kw in keywords_dict.get("chef", []):
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
                    action_btn_text="🗺️ RESTAURANT DIRECTIONS",
                    action_url=maps_url,
                    theme_name="Coral Food",
                    is_travel=True,
                    classroom=classroom,
                    teacher=teacher
                )

        # 3. Check Travel / Flights / Airport / Trains
        for kw in keywords_dict.get("captain", []):
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
                    action_btn_text="🗺️ TRAVEL DIRECTIONS",
                    action_url=maps_url,
                    theme_name="Sky Captain Blue",
                    is_travel=True,
                    classroom=classroom,
                    teacher=teacher
                )

        # 4. Check University / Academic Owl or Classroom presence
        is_academic = bool(classroom) or any(kw in search_blob for kw in keywords_dict.get("owl", []))
        if is_academic:
            is_trav = bool(location and location != "missing value" and "online" not in search_blob)
            maps_dest = location if is_trav else (f"{title} {classroom or ''}".strip())
            maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}" if is_trav else "https://calendar.apple.com"
            provider_label = f"Study / Class 🎓 {classroom}" if classroom else "Study / University 🎓"
            return Meeting(
                title=title,
                start_time=start_time or datetime.now(),
                end_time=end_time,
                location=location,
                description=description,
                event_type=EventCategory.STUDY.value,
                pilot_type=PilotType.OWL.value,
                provider=provider_label,
                action_btn_text=f"🗺️ {classroom or 'CAMPUS'}" if is_trav else "📚 CLASSROOM & NOTES",
                action_url=maps_url,
                theme_name="Academic Purple",
                is_travel=is_trav,
                classroom=classroom,
                teacher=teacher
            )

        # 5. Check Gym / Palestra / Sport / Workout
        for kw in keywords_dict.get("gym", []):
            if kw in search_blob:
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?daddr={urllib.parse.quote(maps_dest)}"
                return Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.SPORT.value,
                    pilot_type=PilotType.GYM.value,
                    provider="Gym & Sport 🏋️‍♂️💪",
                    action_btn_text="🗺️ GYM DIRECTIONS",
                    action_url=maps_url,
                    theme_name="Athletic Crimson",
                    is_travel=True,
                    classroom=classroom,
                    teacher=teacher
                )

        # 6. Check In-Person Appointments / Driver
        for kw in keywords_dict.get("driver", []):
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
                    action_btn_text="🗺️ NAVIGATE IN MAPS",
                    action_url=maps_url,
                    theme_name="Racing Green",
                    is_travel=True
                )

        # 6. Check Therapy / Zen Duck
        for kw in keywords_dict.get("zen_duck", []):
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
                action_btn_text="🗺️ OPEN MAPS",
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

