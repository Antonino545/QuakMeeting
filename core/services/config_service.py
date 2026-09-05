"""
Configuration Service for QuakMeeting.
Handles loading, saving, defaults merging, and disk persistence.
"""
import os
import json
import subprocess
import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger("QuakMeeting.ConfigService")

CONFIG_DIR = os.path.expanduser("~/.quakmeeting")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "language": "system",              # "system" (Auto OS Language), "en" (English), "it" (Italiano)
    "meeting_reminder_stages": [20, 10, 5, 2, 0],
    "general_reminder_stages": [20, 10, 5, 2, 0],
    "travel_reminder_stages": [45, 30, 15, 5, 0],
    "lead_time_meeting_minutes": 6,
    "lead_time_travel_minutes": 35,
    "default_snooze_seconds": 120,
    "flight_speed": 3.2,
    "banner_position": "top", # "top" or "bottom"
    "menubar_status_mode": "countdown", # "countdown", "event_time", "time_only", "icon_only"
    "max_countdown_lookahead_hours": 3, # Maximum hours ahead to show live countdown (caps at 3h instead of 24h)
    "sound_enabled": True,
    "sound_name": "Glass",    # "Glass", "Hero", "Ping", "Pop", "Submarine"
    "mute_during_lessons": True,       # Mute chime when in a university lecture or class
    "ignored_calendars": [
        "Festività in Italia",
        "Birthdays",
        "Scheduled Reminders",
        "Siri Suggestions"
    ],
    "calendar_urls": [],               # Remote ICS / CalDAV feeds for Linux (Google, iCloud, Outlook, Nextcloud)
    # Smart Travel & ETA Settings (Mezzi Pubblici, Auto, Piedi, Bici)
    "home_address": "",               # e.g. "Corso Duca degli Abruzzi 24, Torino"
    "home_city": "",                  # e.g. "Torino"
    "exam_location": "",              # Default campus/hall location for exams e.g. "Politecnico di Torino"
    "transport_mode": "transit",       # "transit" (Mezzi Pubblici), "automobile" (Auto), "walking" (A Piedi), "bicycling" (Bici)
    "enable_eta_service": True,
    "eta_buffer_minutes": 10,          # Margine di anticipo per raggiungere la fermata/parcheggio
    "debug_mode": False,               # Show developer & diagnostics test banners and tools
    "default_pilot": "duck",           # Active default mascot ("duck", "owl", "bunny")
    "force_default_pilot": False,      # If True, always uses default_pilot for all notifications instead of auto-categorization
    "mascot_customization": {
        "exam": {"animal": "owl", "outfit": "student"},
        "study": {"animal": "owl", "outfit": "student"},
        "class": {"animal": "owl", "outfit": "student"},
        "food": {"animal": "duck", "outfit": "chef"},
        "travel": {"animal": "duck", "outfit": "captain"},
        "sport": {"animal": "bunny", "outfit": "gym"},
        "in_person": {"animal": "squirrel", "outfit": "racer"},
        "health": {"animal": "bunny", "outfit": "zen"},
        "general": {"animal": "duck", "outfit": "aviator"}
    },
    "custom_keywords": {
        "study": [
            "study", "studying", "homework", "assignment", "revision", "self-study", "exam",
            "test", "thesis", "library", "research", "lecture", "class", "course", "classroom",
            "studio", "studiare", "compiti", "ripasso", "esame", "esami", "tesi", "laurea",
            "lezione", "lezioni", "corso", "aula", "universit", "politecnico", "biblioteca"
        ],
        "food": [
            "dinner", "lunch", "breakfast", "brunch", "restaurant", "pizza", "pizzeria", "sushi",
            "barbecue", "bbq", "burger", "food", "eat", "dining", "cocktail", "drinks", "pub",
            "cena", "pranzo", "colazione", "ristorante", "trattoria", "osteria", "aperitivo",
            "apericena", "cibo", "mangiare", "pasticceria", "bar", "degustazione", "focaccia"
        ],
        "travel": [
            "flight", "airplane", "airport", "boarding", "gate", "terminal", "train", "station",
            "subway", "metro", "bus", "shuttle", "pullman", "ferry", "travel", "trip", "departure",
            "volo", "aereo", "aeroporto", "imbarco", "partenza", "treno", "stazione", "ferrovia",
            "frecciarossa", "italo", "regionale", "metropolitana", "navetta", "viaggio", "gita"
        ],
        "sport": [
            "gym", "workout", "fitness", "training", "exercise", "crossfit", "weights", "cardio",
            "running", "swimming", "cycling", "yoga", "pilates", "football", "soccer", "tennis", "padel",
            "palestra", "allenamento", "pesi", "corsa", "nuoto", "piscina", "bici", "bicicletta",
            "calcio", "calcetto", "partita", "basket", "pallavolo", "tennis", "boxe", "atletica"
        ],
        "in_person": [
            "doctor", "dr.", "dentist", "medical", "clinic", "hospital", "therapy", "checkup",
            "appointment", "consultation", "optician", "vet", "mechanic", "garage", "driving",
            "dottore", "medico", "visita", "dentista", "clinica", "ospedale", "controllo",
            "appuntamento", "consulenza", "oculista", "veterinario", "meccanico", "tagliando"
        ],
        "health": [
            "meditation", "mindfulness", "wellness", "relax", "spa", "massage", "sauna",
            "mental health", "serenis", "therapy", "calm", "meditazione", "benessere", "terme"
        ],
        "general": [
            "meeting", "sync", "catchup", "call", "riunione", "allineamento", "confronto"
        ]
    }
}

PILOT_TO_CATEGORY_MAP = {
    "owl": "study",
    "class": "study",
    "exam": "study",
    "chef": "food",
    "captain": "travel",
    "gym": "sport",
    "driver": "in_person",
    "zen_duck": "health",
    "general": "general"
}

class ConfigService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance.config = cls._instance._load_or_create()
        return cls._instance

    def _load_or_create(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR, exist_ok=True)

            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                # Merge with defaults for any missing keys
                merged = dict(DEFAULT_CONFIG)
                for k, v in user_cfg.items():
                    if isinstance(v, dict) and isinstance(merged.get(k), dict):
                        merged[k] = {**merged[k], **v}
                    else:
                        merged[k] = v
                return merged
            else:
                self._save_raw(DEFAULT_CONFIG)
                return dict(DEFAULT_CONFIG)
        except Exception as e:
            logger.warning(f"Error loading config.json, using default: {e}")
            return dict(DEFAULT_CONFIG)

    def _save_raw(self, cfg_data: Dict[str, Any]) -> None:
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config.json: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self._save_raw(self.config)

    def reload(self) -> Dict[str, Any]:
        self.config = self._load_or_create()
        return self.config

    def open_config_in_editor(self) -> None:
        """Opens the JSON configuration file in the default editor."""
        if not os.path.exists(CONFIG_PATH):
            self._save_raw(self.config)
        try:
            import sys
            cmd = ["open", CONFIG_PATH] if sys.platform == "darwin" else ["xdg-open", CONFIG_PATH]
            subprocess.Popen(cmd)
        except Exception as e:
            logger.error(f"Error opening config editor: {e}")

    def _normalize_category_key(self, key: Optional[str]) -> Optional[str]:
        if not key:
            return None
        k = str(key).strip().lower()
        return PILOT_TO_CATEGORY_MAP.get(k, k)

    def get_custom_keywords(self, category_key: Optional[str] = None) -> Any:
        """Returns the dictionary of custom keywords or the list for a specific category/pilot."""
        kw_dict = self.get("custom_keywords", {})
        if not isinstance(kw_dict, dict) or not kw_dict:
            kw_dict = DEFAULT_CONFIG.get("custom_keywords", {})
        if category_key:
            norm_k = self._normalize_category_key(category_key)
            if norm_k in kw_dict:
                return list(kw_dict[norm_k])
            if category_key in kw_dict:
                return list(kw_dict[category_key])
            defaults = DEFAULT_CONFIG.get("custom_keywords", {})
            return list(defaults.get(norm_k, defaults.get(category_key, [])))
        return {k: list(v) for k, v in kw_dict.items()}

    def add_custom_keyword(self, category_key: str, keyword: str) -> bool:
        """Adds a new keyword to a category/pilot, preventing duplicates."""
        clean_kw = (keyword or "").strip().lower()
        if not clean_kw:
            return False
        norm_k = self._normalize_category_key(category_key) or category_key
        kw_dict = dict(self.get("custom_keywords", {}))
        cat_list = list(kw_dict.get(norm_k, kw_dict.get(category_key, [])))
        if clean_kw in [k.lower() for k in cat_list]:
            return False
        cat_list.append(clean_kw)
        kw_dict[norm_k] = cat_list
        if category_key != norm_k and category_key in kw_dict:
            del kw_dict[category_key]
        self.set("custom_keywords", kw_dict)
        return True

    def remove_custom_keyword(self, category_key: str, keyword: str) -> bool:
        """Removes a keyword from a category/pilot."""
        clean_kw = (keyword or "").strip().lower()
        norm_k = self._normalize_category_key(category_key) or category_key
        kw_dict = dict(self.get("custom_keywords", {}))
        target_k = norm_k if norm_k in kw_dict else category_key
        cat_list = list(kw_dict.get(target_k, []))
        initial_len = len(cat_list)
        cat_list = [k for k in cat_list if k.lower() != clean_kw]
        if len(cat_list) == initial_len:
            return False
        kw_dict[target_k] = cat_list
        self.set("custom_keywords", kw_dict)
        return True

    def reset_custom_keywords(self, category_key: Optional[str] = None) -> None:
        """Resets custom keywords to default values."""
        defaults = DEFAULT_CONFIG.get("custom_keywords", {})
        if category_key:
            norm_k = self._normalize_category_key(category_key) or category_key
            kw_dict = dict(self.get("custom_keywords", {}))
            kw_dict[norm_k] = list(defaults.get(norm_k, []))
            if category_key != norm_k and category_key in kw_dict:
                del kw_dict[category_key]
            self.set("custom_keywords", kw_dict)
        else:
            self.set("custom_keywords", {k: list(v) for k, v in defaults.items()})

    # Category-centric aliases
    get_category_keywords = get_custom_keywords
    add_category_keyword = add_custom_keyword
    remove_category_keyword = remove_custom_keyword
    reset_category_keywords = reset_custom_keywords

def is_debug_mode() -> bool:
    """Returns True if debug mode is active via CLI flag, environment variable, or configuration."""
    import sys
    if "--debug" in sys.argv:
        return True
    if os.environ.get("QUAKMEETING_DEBUG", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    if os.environ.get("DEBUG", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    return bool(config_service.get("debug_mode", False))

# Global singleton instance
config_service = ConfigService()
ConfigManager = ConfigService
config = config_service

