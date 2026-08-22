"""
Domain event classifier for QuakMeeting.
Extracts video conference links, classifies meeting categories, and assigns pilot themes.
"""
import re
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any, List
from .models import PilotType, EventCategory

MEETING_PATTERNS = [
    r'https?://meet\.google\.com/[a-z0-9-]+',
    r'https?://[a-z0-9-]+\.zoom\.us/j/[0-9]+[^\s"\'<>]*',
    r'https?://teams\.microsoft\.com/[^\s"\'<>]+',
    r'https?://teams\.live\.com/[^\s"\'<>]+',
    r'https?://[a-z0-9-]+\.webex\.com/[^\s"\'<>]+',
    r'https?://meet\.jit\.si/[^\s"\'<>]+',
    r'https?://whereby\.com/[^\s"\'<>]+',
    r'https?://(?:app\.)?serenis\.it/join/[a-zA-Z0-9_-]+',
    r'https?://[^\s"\'<>]+(?:meeting|join|call|vc)[^\s"\'<>]*'
]

DEFAULT_KEYWORDS = {
    "chef": ["cena", "pranzo", "dinner", "lunch", "ristorante", "pizza", "pizzeria", "sushi", "aperitivo", "apericena", "osteria", "trattoria", "cibo", "food", "mangiare", "pub", "burger"],
    "captain": ["flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "pullman", "ryanair", "easyjet", "wizz", "ita airways", "treno", "frecciarossa", "italo", "stazione", "viaggio", "partenza", "gate", "terminal", "imbarco", "boarding", "taxi", "uber"],
    "owl": ["universit", "uni", "esame", "esami", "lezione", "lezioni", "politecnico", "tesi", "smartgrid", "building", "ict", "satellite", "ricerca operativa", "corso", "aula"],
    "driver": ["palestra", "dentista", "dottore", "visita", "medico", "allenamento", "terapia", "yoga", "studio", "ufficio"],
    "zen_duck": ["serenis", "terapia", "yoga", "meditazione", "benessere", "relax"]
}

class EventClassifier:
    """Classifies calendar events into domain types, pilots, themes and action URLs."""

    @staticmethod
    def extract_meeting_url(text: Optional[str]) -> Optional[str]:
        if not text or text == 'missing value':
            return None
        for pattern in MEETING_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).rstrip('.,;)')
        return None

    @staticmethod
    def parse_applescript_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str or date_str == 'missing value':
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%A, %d %B %Y at %H:%M:%S",
            "%A %d %B %Y %H:%M:%S",
            "%d %B %Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        clean_str = date_str.replace(" alle ", " ").replace(" at ", " ")
        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                pass

        try:
            time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', date_str)
            if time_match:
                h, m, s = map(int, time_match.groups())
                now = datetime.now()
                day_match = re.search(r'\b(\d{1,2})\b', date_str)
                day = int(day_match.group(1)) if day_match else now.day
                return datetime(now.year, now.month, day, h, m, s)
        except Exception:
            pass
            
        return None

    @classmethod
    def classify(cls, title: str, location: str = "", description: str = "", meeting_url: Optional[str] = None, custom_keywords: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """Classify event based on title, location, description and keywords."""
        full_text = f"{title or ''} {location or ''} {description or ''}".lower()
        kw = {**DEFAULT_KEYWORDS, **(custom_keywords or {})}

        # 1. Travel & Transport (Captain Jet)
        travel_keywords = kw.get("captain", DEFAULT_KEYWORDS["captain"])
        if any(re.search(r'\b' + re.escape(k) + r'\b', full_text) if len(k) <= 4 else (k in full_text) for k in travel_keywords):
            maps_query = location if (location and location != "missing value") else title
            encoded_query = urllib.parse.quote(maps_query or "Aeroporto")
            return {
                "event_type": EventCategory.TRAVEL.value,
                "pilot_type": PilotType.CAPTAIN.value,
                "provider": "Volo / Viaggio / Bus ✈️🚌",
                "action_btn_text": "🗺️ INDICAZIONI MAPPE",
                "action_url": meeting_url if meeting_url else f"https://maps.apple.com/?q={encoded_query}",
                "theme_name": "Sky Blue",
                "is_travel": True
            }

        # 2. Food & Dinners (Chef Duck)
        food_keywords = kw.get("chef", DEFAULT_KEYWORDS["chef"])
        if any(k in full_text for k in food_keywords):
            maps_query = location if (location and location != "missing value") else f"Ristorante {title}"
            encoded_query = urllib.parse.quote(maps_query)
            return {
                "event_type": EventCategory.FOOD.value,
                "pilot_type": PilotType.CHEF.value,
                "provider": "Cena / Cibo 🍕🍽️",
                "action_btn_text": "🗺️ INDICAZIONI RISTORANTE",
                "action_url": meeting_url if meeting_url else f"https://maps.apple.com/?q={encoded_query}",
                "theme_name": "Coral Food",
                "is_travel": True
            }

        # 3. Video Meetings
        if meeting_url:
            if "serenis.it" in meeting_url or "serenis" in full_text:
                return {
                    "event_type": EventCategory.HEALTH.value,
                    "pilot_type": PilotType.ZEN_DUCK.value,
                    "provider": "Serenis 🛋️",
                    "action_btn_text": "🚀 PARTECIPA AL MEETING",
                    "action_url": meeting_url,
                    "theme_name": "Teal Zen",
                    "is_travel": False
                }
            elif "meet.google.com" in meeting_url:
                return {
                    "event_type": EventCategory.VIDEO_MEETING.value,
                    "pilot_type": PilotType.DUCK.value,
                    "provider": "Google Meet 🟢",
                    "action_btn_text": "🚀 PARTECIPA ORA",
                    "action_url": meeting_url,
                    "theme_name": "Google Green",
                    "is_travel": False
                }
            elif "zoom.us" in meeting_url:
                return {
                    "event_type": EventCategory.VIDEO_MEETING.value,
                    "pilot_type": PilotType.DUCK.value,
                    "provider": "Zoom 🔷",
                    "action_btn_text": "🚀 ENTRA IN ZOOM",
                    "action_url": meeting_url,
                    "theme_name": "Zoom Blue",
                    "is_travel": False
                }
            elif "teams.microsoft.com" in meeting_url or "teams.live.com" in meeting_url:
                return {
                    "event_type": EventCategory.VIDEO_MEETING.value,
                    "pilot_type": PilotType.DUCK.value,
                    "provider": "MS Teams 🟣",
                    "action_btn_text": "🚀 PARTECIPA SU TEAMS",
                    "action_url": meeting_url,
                    "theme_name": "Teams Purple",
                    "is_travel": False
                }
            else:
                return {
                    "event_type": EventCategory.VIDEO_MEETING.value,
                    "pilot_type": PilotType.DUCK.value,
                    "provider": "Video Call 🌐",
                    "action_btn_text": "🚀 PARTECIPA ORA",
                    "action_url": meeting_url,
                    "theme_name": "Classic Blue",
                    "is_travel": False
                }

        # 4. Academic & Study (Academic Owl)
        study_keywords = kw.get("owl", DEFAULT_KEYWORDS["owl"])
        if any(re.search(r'\b' + re.escape(k) + r'\b', full_text) if len(k) <= 4 else (k in full_text) for k in study_keywords):
            has_loc = bool(location and location != "missing value")
            maps_query = location if has_loc else "Politecnico Università"
            encoded_query = urllib.parse.quote(maps_query)
            return {
                "event_type": EventCategory.STUDY.value,
                "pilot_type": PilotType.OWL.value,
                "provider": "Studio / Uni 🎓",
                "action_btn_text": "🗺️ INDICAZIONI AULA" if has_loc else "📚 DETTAGLI STUDIO",
                "action_url": f"https://maps.apple.com/?q={encoded_query}" if has_loc else "https://calendar.google.com",
                "theme_name": "Amber Academic",
                "is_travel": has_loc
            }

        # 5. Health & Wellbeing (Zen Duck)
        zen_keywords = kw.get("zen_duck", DEFAULT_KEYWORDS["zen_duck"])
        if any(k in full_text for k in zen_keywords):
            has_loc = bool(location and location != "missing value")
            return {
                "event_type": EventCategory.HEALTH.value,
                "pilot_type": PilotType.ZEN_DUCK.value,
                "provider": "Salute & Relax 🌿",
                "action_btn_text": "🗺️ APRI MAPPE" if has_loc else "🌸 DETTAGLI",
                "action_url": f"https://maps.apple.com/?q={urllib.parse.quote(location)}" if has_loc else "https://calendar.google.com",
                "theme_name": "Teal Zen",
                "is_travel": has_loc
            }

        # 6. In Person & Travel (Driver Racer)
        driver_keywords = kw.get("driver", DEFAULT_KEYWORDS["driver"])
        if any(k in full_text for k in driver_keywords) or (location and location != "missing value" and len(location.strip()) > 2):
            dest = location if (location and location != "missing value") else title
            encoded_dest = urllib.parse.quote(dest or "Destinazione")
            return {
                "event_type": EventCategory.IN_PERSON.value,
                "pilot_type": PilotType.DRIVER.value,
                "provider": "In Presenza 📍 Tempo di Spostamento!",
                "action_btn_text": "🗺️ VAI CON MAPPE (NAVIGA)",
                "action_url": f"https://maps.apple.com/?daddr={encoded_dest}",
                "theme_name": "Emerald Travel",
                "is_travel": True
            }

        # 7. General Reminder (Classic Aviator Duck)
        return {
            "event_type": EventCategory.GENERAL.value,
            "pilot_type": PilotType.DUCK.value,
            "provider": "Promemoria ⏰",
            "action_btn_text": "📋 APRI EVENTO",
            "action_url": "https://calendar.google.com",
            "theme_name": "Sunset Orange",
            "is_travel": False
        }
