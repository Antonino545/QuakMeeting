import os
import json
import subprocess

CONFIG_DIR = os.path.expanduser("~/.quakmeeting")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "lead_time_meeting_minutes": 6,
    "lead_time_travel_minutes": 35,
    "default_snooze_seconds": 120,
    "flight_speed": 3.2,
    "banner_position": "top", # "top" or "bottom"
    "sound_enabled": True,
    "sound_name": "Glass",    # "Glass", "Hero", "Ping", "Pop", "Submarine"
    "ignored_calendars": [
        "Festività in Italia",
        "Birthdays",
        "Scheduled Reminders",
        "Siri Suggestions"
    ],
    "custom_keywords": {
        "chef": ["cena", "pranzo", "dinner", "lunch", "ristorante", "pizza", "pizzeria", "sushi", "aperitivo", "apericena", "osteria", "trattoria", "cibo", "food", "mangiare", "pub", "burger"],
        "captain": ["flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "pullman", "ryanair", "easyjet", "wizz", "ita airways", "treno", "frecciarossa", "italo", "stazione", "viaggio", "partenza", "gate", "terminal", "imbarco", "boarding", "taxi", "uber"],
        "owl": ["universit", "uni", "esame", "esami", "lezione", "lezioni", "politecnico", "tesi", "smartgrid", "building", "ict", "satellite", "ricerca operativa", "corso", "aula"],
        "driver": ["palestra", "dentista", "dottore", "visita", "medico", "allenamento", "terapia", "yoga", "studio", "ufficio"],
        "zen_duck": ["serenis", "terapia", "yoga", "meditazione", "benessere", "relax"]
    }
}

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = cls._instance._load_or_create()
        return cls._instance

    def _load_or_create(self):
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
            print(f"⚠️ Errore caricamento config.json, uso default: {e}")
            return dict(DEFAULT_CONFIG)

    def _save_raw(self, cfg_data):
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Errore salvataggio config.json: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self._save_raw(self.config)

    def reload(self):
        self.config = self._load_or_create()
        return self.config

    def open_config_in_editor(self):
        """Apre il file JSON nell'editor predefinito o TextEdit per personalizzazione manuale."""
        if not os.path.exists(CONFIG_PATH):
            self._save_raw(self.config)
        try:
            subprocess.Popen(["open", CONFIG_PATH])
        except Exception as e:
            print(f"Errore apertura editor: {e}")

# Helper singleton per accesso globale
config = ConfigManager()

if __name__ == "__main__":
    print(f"Config path: {CONFIG_PATH}")
    print(f"Lead time meeting: {config.get('lead_time_meeting_minutes')} min")
    print(f"Lead time travel: {config.get('lead_time_travel_minutes')} min")
    print(f"Flight speed: {config.get('flight_speed')}")
    print(f"Banner position: {config.get('banner_position')}")
