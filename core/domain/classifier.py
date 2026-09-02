"""
Event Classification and URL Extraction Engine for QuakMeeting.
Pure Python matching logic for video meeting providers, keyword pilots, and travel detection.
"""
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List, Union
from .models import Meeting, PilotType, EventCategory

_KW_REGEX_CACHE: Dict[str, re.Pattern] = {}

MEETING_PATTERNS = [
    (r"https://meet\.google\.com/[a-z0-9-]+", "Google Meet 🟢", "duck", "🚀 JOIN GOOGLE MEET"),
    (r"https://[a-zA-Z0-9-]+\.zoom\.us/[jsw]/[0-9a-zA-Z?=&_-]+", "Zoom Meeting 🔷", "duck", "🚀 JOIN ZOOM MEETING"),
    (r"https://teams\.microsoft\.com/l/meetup-join/[0-9a-zA-Z%?=&_-]+", "Microsoft Teams 🟣", "duck", "🚀 JOIN TEAMS MEETING"),
    (r"https://teams\.live\.com/meet/[0-9a-zA-Z?=&_-]+", "Microsoft Teams 🟣", "duck", "🚀 JOIN TEAMS MEETING"),
    (r"https://app\.serenis\.it/join/[0-9a-zA-Z_-]+", "Serenis 🛋️", "zen_duck", "🚀 JOIN SESSION")
]

DEFAULT_KEYWORDS = {
    "chef": [
        "dinner", "lunch", "breakfast", "brunch", "restaurant", "pizza", "pizzeria", "sushi",
        "barbecue", "bbq", "burger", "food", "eat", "dining", "cocktail", "drinks", "pub",
        "bistro", "cafe", "coffee", "snack", "tasting", "cooking", "supper",
        "cena", "pranzo", "colazione", "ristorante", "trattoria", "osteria", "aperitivo",
        "apericena", "cibo", "mangiare", "pasticceria", "bar", "degustazione", "focaccia",
        "panino", "spuntino", "mensa"
    ],
    "captain": [
        "flight", "airplane", "airport", "boarding", "gate", "terminal", "takeoff", "landing",
        "train", "railway", "station", "subway", "metro", "bus", "shuttle", "pullman", "ferry",
        "cruise", "travel", "trip", "journey", "departure", "transit", "commute", "roadtrip",
        "cab", "taxi", "uber", "lyft", "airline", "ryanair", "easyjet", "wizz", "delta",
        "lufthansa", "british airways", "volo", "aereo", "aeroporto", "imbarco", "partenza",
        "treno", "stazione", "ferrovia", "frecciarossa", "italo", "regionale", "metropolitana",
        "navetta", "traghetto", "viaggio", "gita", "trasferta", "spostamento", "ita airways"
    ],
    "exam": [
        "exam", "exams", "esame", "esami", "appello", "parziale", "midterm", "final exam",
        "oral exam", "written exam", "esonero", "prova scritta", "prova orale", "colloquio",
        "test d'esame", "exam prep", "preparazione esame"
    ],
    "class": [
        "lecture", "classes", "course", "classroom", "seminar", "workshop", "tutorial",
        "lab", "laboratory", "university", "college", "professor", "prof", "academic",
        "lezione", "lezioni", "corso", "aula", "seminario", "laboratorio", "universit",
        "politecnico", "professore", "docente", "smartgrid", "building", "ict", "satellite",
        "operations research", "ricerca operativa"
    ],
    "owl": [
        "study", "studying", "homework", "assignment", "revision", "self-study", "self study", "selfstudy",
        "or study", "quiz", "thesis", "dissertation", "library", "research", "paper", "reading", "textbook",
        "studio", "studiare", "studio individuale", "studio autonomo", "compiti", "ripasso",
        "tesi", "tesina", "laurea", "biblioteca", "ricerca", "dispense", "esercitazione", "appunti"
    ],
    "gym": [
        "gym", "workout", "fitness", "training", "exercise", "crossfit", "bodybuilding",
        "weights", "cardio", "running", "jogging", "swimming", "pool", "cycling", "bike ride",
        "yoga", "pilates", "football", "soccer", "basketball", "tennis", "padel", "volleyball",
        "boxing", "martial arts", "climbing", "hiking", "treadmill", "stretching", "match",
        "palestra", "allenamento", "pesi", "corsa", "camminata", "nuoto", "piscina", "bici",
        "bicicletta", "calcio", "calcetto", "partita", "partitella", "basket", "pallavolo",
        "tennis", "atletica", "boxe", "maratona", "scalata", "arrampicata", "ginnastica"
    ],
    "driver": [
        "doctor", "dr.", "physician", "dentist", "medical", "clinic", "hospital",
        "therapy", "checkup", "appointment", "consultation", "optician", "eye doctor",
        "vet", "veterinarian", "mechanic", "garage", "car inspection", "car wash", "driving",
        "drive", "post office", "bank", "barber", "haircut", "errand", "office",
        "dottore", "medico", "visita", "dentista", "ortodontista", "clinica", "ospedale",
        "controllo", "appuntamento", "consulenza", "oculista", "veterinario", "meccanico",
        "tagliando", "revisione auto", "posta", "banca", "barbiere", "parrucchiere",
        "commissione", "ufficio", "studio"
    ],
    "zen_duck": [
        "meditation", "mindfulness", "wellness", "relax", "spa", "massage", "thermal",
        "sauna", "breathing", "mental health", "counseling", "serenis", "therapy",
        "therapy session", "calm", "retreat", "chill", "meditazione", "benessere",
        "terme", "massaggio", "respirazione", "salute mentale", "terapia", "seduta", "riposo"
    ],
    "platypus": [
        "secret", "segreto", "mission", "missione", "spy", "spia", "agent", "agente",
        "undercover", "in incognito", "confidential", "confidenziale", "top secret",
        "perry", "doofenshmirtz", "classified", "riservato"
    ],
    "squirrel": [
        "brainstorm", "brainstorming", "idea", "quick", "sync", "flash", "agile",
        "standup", "sprint", "retro", "retrospettiva", "hackathon", "nut", "squirrel",
        "speed", "allineamento", "confronto", "chiacchierata", "touchpoint", "huddle"
    ]
}

LEGACY_PILOT_MAP = {
    ("duck", "aviator"): "duck",
    ("duck", "chef"): "chef",
    ("duck", "captain"): "captain",
    ("owl", "student"): "owl",
    ("duck", "gym"): "gym",
    ("duck", "racer"): "driver",
    ("duck", "zen"): "zen_duck",
    ("platypus", "agent"): "platypus",
    ("squirrel", "acorn"): "squirrel"
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

    @staticmethod
    def _matches_kw(kw: str, text: str) -> bool:
        """Match keyword using word-boundary regex with compiled pattern cache."""
        pattern = _KW_REGEX_CACHE.get(kw)
        if pattern is None:
            pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            _KW_REGEX_CACHE[kw] = pattern
        return bool(pattern.search(text))

    @staticmethod
    def _apply_meeting_url_if_found(meeting: Meeting, active_url: Optional[str]) -> Meeting:
        """If a video meeting URL was extracted, overlay it onto the Meeting's action button.

        The event keeps its category theme, pilot, and provider label — only the
        action button text/URL and meeting_url field are updated so the banner
        shows a clickable "Join" button instead of a generic calendar/maps link.
        """
        if not active_url:
            return meeting
        btn_text = "🚀 JOIN MEETING"
        for pat, _, _, pat_btn in MEETING_PATTERNS:
            if re.search(pat, active_url, re.IGNORECASE):
                btn_text = pat_btn
                break
        meeting.meeting_url = active_url
        meeting.action_url = active_url
        meeting.action_btn_text = btn_text
        return meeting

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
                    keywords_dict[k] = list(set(keywords_dict[k] + [kw.lower() for kw in v]))
                elif isinstance(v, list):
                    keywords_dict[k] = [kw.lower() for kw in v]

        classroom, teacher = cls.extract_classroom_and_teacher(title, location, description)
        # Keep original-case text for URL extraction to preserve case-sensitive tokens
        raw_blob = f"{title} {location} {description} {meeting_url or ''}"
        search_blob = raw_blob.lower()

        # 1. Match Video Meeting Patterns
        active_url = meeting_url or cls.extract_meeting_url(raw_blob)
        if active_url:
            for pattern, provider_name, p_type, btn_text in MEETING_PATTERNS:
                if re.search(pattern, active_url, re.IGNORECASE):
                    res_meeting = Meeting(
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
                    return cls._apply_forced_pilot_if_needed(res_meeting)

        # 2. Check Physical Food / Dinner keywords
        for kw in keywords_dict.get("chef", []):
            if cls._matches_kw(kw, search_blob):
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}"
                res_meeting = Meeting(
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
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 3. Check Travel / Flights / Airport / Trains
        for kw in keywords_dict.get("captain", []):
            if cls._matches_kw(kw, search_blob):
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}"
                res_meeting = Meeting(
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
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 4. Check Exam / Esame
        is_exam_event = (
            any(cls._matches_kw(kw, search_blob) for kw in keywords_dict.get("exam", []))
            or bool(re.search(r"^(?:exam|esame|appello|parziale|esonero)[:\s\-\–\—]+", title.strip(), re.IGNORECASE))
        )
        if is_exam_event:
            is_trav = "online" not in search_blob
            maps_dest = location if (location and location != "missing value") else (f"{title} {classroom or ''}".strip())
            maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}" if is_trav else "https://calendar.apple.com"
            provider_label = f"Exam 🎓 {classroom}" if classroom else "Exam 🎓"
            res_meeting = Meeting(
                title=title,
                start_time=start_time or datetime.now(),
                end_time=end_time,
                location=location,
                description=description,
                event_type=EventCategory.EXAM.value,
                pilot_type=PilotType.OWL.value,
                provider=provider_label,
                action_btn_text=f"🎓 {classroom or 'EXAM LOCATION'}" if is_trav else "🎓 EXAM NOTES",
                action_url=maps_url,
                theme_name="Academic Purple",
                is_travel=is_trav,
                classroom=classroom,
                teacher=teacher
            )
            return cls._apply_forced_pilot_if_needed(res_meeting)

        # 5. Check Self-Study Block vs Class / Lecture Attendance
        is_study_event = any(cls._matches_kw(kw, search_blob) for kw in keywords_dict.get("owl", []))
        is_class_event = bool(classroom) or bool(teacher) or any(cls._matches_kw(kw, search_blob) for kw in keywords_dict.get("class", []))

        if is_study_event:
            is_trav = bool(location and location != "missing value" and "online" not in search_blob)
            maps_dest = location if is_trav else title
            maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}" if is_trav else "https://calendar.apple.com"
            res_meeting = Meeting(
                title=title,
                start_time=start_time or datetime.now(),
                end_time=end_time,
                location=location,
                description=description,
                event_type=EventCategory.STUDY.value,
                pilot_type=PilotType.OWL.value,
                provider="Study Session 📖",
                action_btn_text=f"🗺️ {location}" if is_trav else "⚡ TIME TO STUDY! DO IT 📖",
                action_url=maps_url,
                theme_name="Academic Purple",
                is_travel=is_trav,
                classroom=classroom,
                teacher=teacher
            )
            cls._apply_meeting_url_if_found(res_meeting, active_url)
            return cls._apply_forced_pilot_if_needed(res_meeting)

        if is_class_event:
            is_trav = bool(location and location != "missing value" and "online" not in search_blob)
            maps_dest = location if is_trav else (f"{title} {classroom or ''}".strip())
            maps_url = f"https://maps.apple.com/?q={urllib.parse.quote(maps_dest)}" if is_trav else "https://calendar.apple.com"
            provider_label = f"Class / Lecture 🏫 {classroom}" if classroom else "Class / Lecture 🏫"
            res_meeting = Meeting(
                title=title,
                start_time=start_time or datetime.now(),
                end_time=end_time,
                location=location,
                description=description,
                event_type=EventCategory.CLASS.value,
                pilot_type=PilotType.OWL.value,
                provider=provider_label,
                action_btn_text=f"🗺️ {classroom or 'CAMPUS'}" if is_trav else "🏫 CLASSROOM & NOTES",
                action_url=maps_url,
                theme_name="Academic Purple",
                is_travel=is_trav,
                classroom=classroom,
                teacher=teacher
            )
            cls._apply_meeting_url_if_found(res_meeting, active_url)
            return cls._apply_forced_pilot_if_needed(res_meeting)
        # 5. Check Gym / Palestra / Sport / Workout
        for kw in keywords_dict.get("gym", []):
            if cls._matches_kw(kw, search_blob):
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?daddr={urllib.parse.quote(maps_dest)}"
                res_meeting = Meeting(
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
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 6. Check In-Person Appointments / Driver
        for kw in keywords_dict.get("driver", []):
            if cls._matches_kw(kw, search_blob):
                maps_dest = location if (location and location != "missing value") else title
                maps_url = f"https://maps.apple.com/?daddr={urllib.parse.quote(maps_dest)}"
                res_meeting = Meeting(
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
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 6. Check Therapy / Zen Duck
        for kw in keywords_dict.get("zen_duck", []):
            if cls._matches_kw(kw, search_blob):
                res_meeting = Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.HEALTH.value,
                    pilot_type=PilotType.ZEN_DUCK.value,
                    provider="Therapy & Wellness 🌸🛋️",
                    action_btn_text="🌸 WELLNESS TIME",
                    action_url="https://calendar.apple.com",
                    theme_name="Teal Modern",
                    is_travel=False
                )
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 7. Check Secret Mission / Platypus
        for kw in keywords_dict.get("platypus", []):
            if cls._matches_kw(kw, search_blob):
                res_meeting = Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.GENERAL.value,
                    pilot_type=PilotType.PLATYPUS.value,
                    provider="Top Secret Mission 🕵️‍♂️",
                    action_btn_text="🕵️ BRIEFING ACCESS",
                    action_url="https://calendar.apple.com",
                    theme_name="Midnight Slate",
                    is_travel=False
                )
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 8. Check Quick Sync / Squirrel
        for kw in keywords_dict.get("squirrel", []):
            if cls._matches_kw(kw, search_blob):
                res_meeting = Meeting(
                    title=title,
                    start_time=start_time or datetime.now(),
                    end_time=end_time,
                    location=location,
                    description=description,
                    event_type=EventCategory.GENERAL.value,
                    pilot_type=PilotType.SQUIRREL.value,
                    provider="Quick Sync & Brainstorm 🐿️⚡",
                    action_btn_text="🐿️ JOIN HUDDLE",
                    action_url="https://calendar.apple.com",
                    theme_name="Amber Glow",
                    is_travel=False
                )
                cls._apply_meeting_url_if_found(res_meeting, active_url)
                return cls._apply_forced_pilot_if_needed(res_meeting)

        # 9. Generic Physical Event (if non-empty location)
        if location and location != "missing value" and len(location.strip()) > 2:
            maps_url = f"https://maps.apple.com/?daddr={urllib.parse.quote(location)}"
            res_meeting = Meeting(
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
            cls._apply_meeting_url_if_found(res_meeting, active_url)
            return cls._apply_forced_pilot_if_needed(res_meeting)

        # 10. General Default Meeting / Reminder
        default_pilot_id = cls._get_default_pilot()
        res_meeting = Meeting(
            title=title,
            start_time=start_time or datetime.now(),
            end_time=end_time,
            location=location,
            description=description,
            event_type=EventCategory.GENERAL.value,
            pilot_type=default_pilot_id,
            provider="Reminder ⏰",
            action_btn_text="📋 OPEN IN CALENDAR",
            action_url="https://calendar.apple.com",
            theme_name="Sunset Orange",
            is_travel=False
        )
        cls._apply_meeting_url_if_found(res_meeting, active_url)
        return cls._apply_forced_pilot_if_needed(res_meeting)

    @classmethod
    def _get_default_pilot(cls) -> str:
        try:
            from core.services.config_service import config
            return str(config.get("default_pilot", "duck"))
        except Exception:
            return "duck"

    @classmethod
    def _apply_forced_pilot_if_needed(cls, meeting: Meeting) -> Meeting:
        try:
            from core.services.config_service import config
            customs = config.get("mascot_customization")
            if not isinstance(customs, dict):
                customs = {}

            is_specialized = meeting.pilot_type in (PilotType.PLATYPUS.value, PilotType.SQUIRREL.value)
            cat_key = meeting.event_type or "general"

            CATEGORY_DEFAULT_OUTFITS = {
                "exam": "student",
                "study": "student",
                "class": "student",
                "food": "chef",
                "travel": "captain",
                "sport": "gym",
                "in_person": "racer",
                "health": "zen",
                "general": "aviator"
            }

            if not is_specialized or cat_key != "general":
                custom_val = customs.get(cat_key)
                def_outfit = CATEGORY_DEFAULT_OUTFITS.get(cat_key, "aviator")
                if isinstance(custom_val, dict):
                    meeting.animal = custom_val.get("animal", "duck")
                    meeting.outfit = custom_val.get("outfit", def_outfit)
                    meeting.pilot_type = LEGACY_PILOT_MAP.get(
                        (meeting.animal, meeting.outfit),
                        f"{meeting.animal}_{meeting.outfit}"
                    )
                elif isinstance(custom_val, str) and custom_val:
                    meeting.animal = custom_val
                    meeting.outfit = def_outfit
                    meeting.pilot_type = LEGACY_PILOT_MAP.get(
                        (meeting.animal, meeting.outfit),
                        f"{meeting.animal}_{meeting.outfit}"
                    )
                elif not meeting.animal:
                    meeting.animal = meeting.pilot_type or "duck"
            elif not meeting.animal:
                meeting.animal = meeting.pilot_type or "duck"

            if config.get("force_default_pilot", False):
                def_pilot = str(config.get("default_pilot", "duck"))
                meeting.animal = def_pilot
                meeting.pilot_type = LEGACY_PILOT_MAP.get(
                    (def_pilot, meeting.outfit or "aviator"),
                    f"{def_pilot}_{meeting.outfit or 'aviator'}"
                )
        except Exception:
            pass
        return meeting

