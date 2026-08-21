# ⚙️ QuakMeeting — Configuration & Custom Rules Guide

QuakMeeting stores all user preferences, timing thresholds, ignored calendars, and custom keyword rules in:
`~/.quakmeeting/config.json`

---

## 📝 Configuration File Reference

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lead_time_meeting_minutes` | `int` | `6` | Minutes before an online video meeting to launch the flying banner. |
| `lead_time_travel_minutes` | `int` | `35` | Minutes before an in-person event/flight to launch the transit banner. |
| `default_snooze_seconds` | `int` | `120` | Duration (in seconds) for the Snooze button (e.g. 120 = 2 min). |
| `flight_speed` | `float` | `3.2` | Flying airplane speed multiplier (2.0 = Relaxed, 3.2 = Standard, 4.8 = Turbo). |
| `sound_enabled` | `bool` | `true` | Whether to play a macOS chime sound when the banner appears. |
| `sound_name` | `string` | `"Glass"` | System sound name (`Glass`, `Hero`, `Ping`, `Pop`, `Submarine`). |
| `ignored_calendars` | `list` | `[...]` | Calendar names to exclude from scanning (e.g. Birthdays, Holidays). |
| `custom_keywords` | `dict` | `{...}` | Custom keyword mappings for each pilot category. |

---

## 🏷️ Custom Keyword Rules (`custom_keywords`)

You can add any custom keywords to trigger specific pilots:

```json
{
  "custom_keywords": {
    "chef": [
      "cena", "pranzo", "dinner", "lunch", "ristorante", "pizza", "pizzeria", "sushi", "aperitivo", "apericena"
    ],
    "captain": [
      "flight", "volo", "airport", "aeroporto", "bus", "navetta", "shuttle", "treno", "frecciarossa", "italo"
    ],
    "owl": [
      "universit", "uni", "esame", "esami", "lezione", "lezioni", "politecnico", "tesi", "studio"
    ],
    "zen_duck": [
      "serenis", "terapia", "yoga", "meditazione", "benessere", "relax"
    ],
    "driver": [
      "palestra", "dentista", "dottore", "visita", "medico", "allenamento"
    ]
  }
}
```
