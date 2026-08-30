# ⚙️ QuakMeeting — Configuration & Custom Rules Guide

QuakMeeting stores all user preferences, timing thresholds, routing configurations, and custom keyword rules in:
`~/.quakmeeting/config.json`

---

## 📝 Configuration File Reference

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `language` | `string` | `"system"` | Active UI language (`"system"` for OS auto-detection, `"en"` for English, `"it"` for Italian). |
| `meeting_reminder_stages` | `list[int]` | `[20, 10, 5, 2, 0]` | Minutes before an online meeting to trigger the banner notification sequence. |
| `general_reminder_stages` | `list[int]` | `[20, 10, 5, 2, 0]` | Minutes before a general non-travel event to trigger the banner notification sequence. |
| `travel_reminder_stages` | `list[int]` | `[45, 30, 15, 5, 0]` | Minutes before departure to trigger the travel/transit banner notification sequence. |
| `lead_time_meeting_minutes` | `int` | `6` | Legacy trigger threshold (used for fallback compatibility). |
| `lead_time_travel_minutes` | `int` | `35` | Legacy trigger threshold (used for fallback compatibility). |
| `default_snooze_seconds` | `int` | `120` | Duration (in seconds) for the Snooze button (e.g. 120 = 2 min). |
| `flight_speed` | `float` | `3.2` | Flying airplane speed multiplier (2.0 = Relaxed, 3.2 = Standard, 4.8 = Turbo). |
| `banner_position` | `string` | `"top"` | Screen position for the banner (`"top"` or `"bottom"`). |
| `menubar_status_mode` | `string` | `"countdown"` | Default tray display mode (`"countdown"`, `"event_time"`, `"time_only"`, `"icon_only"`). |
| `max_countdown_lookahead_hours`| `int` | `3` | Maximum hours ahead to show live countdown in the menu bar. Events further out show a clean start time. |
| `sound_enabled` | `bool` | `true` | Whether to play a system sound when the banner appears. |
| `sound_name` | `string` | `"Glass"` | System sound name to play (`"Glass"`, `"Hero"`, `"Ping"`, `"Pop"`, `"Submarine"`). |
| `mute_during_lessons` | `bool` | `true` | Automatically mute banner chime when attending a university lecture/lesson or when the event is a class. |
| `ignored_calendars` | `list[str]` | `[...]` | Exact names of calendars to exclude from scanning (e.g., `"Birthdays"`, `"Holidays"`). |
| `calendar_urls` | `list[str]` | `[]` | URLs for remote ICS / CalDAV feeds, primarily used on Linux. |
| `home_address` | `string` | `""` | Origin address for ETA calculations (e.g., `"Corso Duca degli Abruzzi 24, Torino"`). |
| `transport_mode` | `string` | `"transit"` | Default travel mode (`"transit"`, `"automobile"`, `"walking"`, `"bicycling"`). |
| `enable_eta_service` | `bool` | `true` | Whether to calculate departure times and routing links via Apple Maps / Google Maps. |
| `eta_buffer_minutes` | `int` | `10` | Buffer minutes added before departure to account for reaching transit stop/parking. |
| `custom_keywords` | `dict` | `{...}` | Custom keyword mappings to trigger specific pilots based on event titles. |

---

## 🏷️ Custom Keyword Rules (`custom_keywords`)

You can add any custom keywords to trigger specific pilots and categorize events.

```json
{
  "custom_keywords": {
    "chef": [
      "cena", "pranzo", "dinner", "lunch", "ristorante", "pizza", "pizzeria", "sushi", "aperitivo", "apericena", "osteria", "trattoria", "cibo", "food", "mangiare", "pub", "burger"
    ],
    "captain": [
      "flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "pullman", "ryanair", "easyjet", "wizz", "ita airways", "treno", "frecciarossa", "italo", "stazione", "viaggio", "partenza", "gate", "terminal", "imbarco", "boarding", "taxi", "uber"
    ],
    "owl": [
      "universit", "uni", "esame", "esami", "lezione", "lezioni", "politecnico", "tesi", "smartgrid", "building", "ict", "satellite", "ricerca operativa", "corso", "aula"
    ],
    "gym": [
      "palestra", "gym", "workout", "allenamento", "crossfit", "fitness", "sport", "padel", "tennis", "calcio", "calcetto", "partita", "match", "nuoto", "swimming", "running", "corsa", "boxe", "boxing", "basket", "pallavolo", "pesi", "cardio", "training", "maratona", "pilates", "atletica"
    ],
    "driver": [
      "dentista", "dottore", "visita", "medico", "studio", "ufficio", "appuntamento"
    ],
    "zen_duck": [
      "serenis", "terapia", "yoga", "meditazione", "benessere", "relax"
    ]
  }
}
```
