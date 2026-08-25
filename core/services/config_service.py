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
    "meeting_reminder_stages": [20, 10, 5, 2, 0],
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
    "ignored_calendars": [
        "Festività in Italia",
        "Birthdays",
        "Scheduled Reminders",
        "Siri Suggestions"
    ],
    "calendar_urls": [],               # Remote ICS / CalDAV feeds for Linux (Google, iCloud, Outlook, Nextcloud)
    # Smart Travel & ETA Settings (Mezzi Pubblici, Auto, Piedi, Bici)
    "home_address": "",               # e.g. "Corso Duca degli Abruzzi 24, Torino"
    "transport_mode": "transit",       # "transit" (Mezzi Pubblici), "automobile" (Auto), "walking" (A Piedi), "bicycling" (Bici)
    "enable_eta_service": True,
    "eta_buffer_minutes": 10,          # Margine di anticipo per raggiungere la fermata/parcheggio
    "custom_keywords": {
        "chef": ["cena", "pranzo", "dinner", "lunch", "ristorante", "pizza", "pizzeria", "sushi", "aperitivo", "apericena", "osteria", "trattoria", "cibo", "food", "mangiare", "pub", "burger"],
        "captain": ["flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "pullman", "ryanair", "easyjet", "wizz", "ita airways", "treno", "frecciarossa", "italo", "stazione", "viaggio", "partenza", "gate", "terminal", "imbarco", "boarding", "taxi", "uber"],
        "owl": ["universit", "uni", "esame", "esami", "lezione", "lezioni", "politecnico", "tesi", "smartgrid", "building", "ict", "satellite", "ricerca operativa", "corso", "aula"],
        "gym": ["palestra", "gym", "workout", "allenamento", "crossfit", "fitness", "sport", "padel", "tennis", "calcio", "calcetto", "partita", "match", "nuoto", "swimming", "running", "corsa", "boxe", "boxing", "basket", "pallavolo", "pesi", "cardio", "training", "maratona", "pilates", "atletica"],
        "driver": ["dentista", "dottore", "visita", "medico", "studio", "ufficio", "appuntamento"],
        "zen_duck": ["serenis", "terapia", "yoga", "meditazione", "benessere", "relax"]
    }
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

# Global singleton instance
config_service = ConfigService()
ConfigManager = ConfigService
config = config_service
