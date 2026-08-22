<div align="center">

# 🦆 QuakMeeting
### macOS Native Flight Deck & Smart Meeting Reminder Assistant
*Inspired by [QuakPit](https://github.com/Ooble-Studio/QuakPit) — Designed for Timing Precision, Travel Readiness, & 1-Click Meeting Joins.*

[![macOS](https://img.shields.io/badge/macOS-12.0%2B-blue?logo=apple&style=flat-square)](https://apple.com)
[![Python](https://img.shields.io/badge/Python-3.9%2B-yellow?logo=python&style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<img src="assets/icon.png" width="160" alt="QuakMeeting Icon" />

</div>

---

## 📖 Overview & Philosophy

**QuakMeeting** is a native macOS companion application built to solve one of the biggest challenges for busy professionals, neurodivergent users, and university students: **forgetting upcoming meetings, missing transit departures, or getting lost in endless notification banners.**

Instead of subtle notification center alerts that disappear after 5 seconds, QuakMeeting animates a **playful cartoon airplane towing an interactive HUD banner** across your screen. The banner provides a clear countdown, intelligent context-aware action buttons (1-click Google Meet / Zoom / Serenis join, 1-click Apple Maps navigation), and gentle snooze loops that keep you on track.

---

## ✨ Key Features

- 🖥️ **Flight Deck Control Center (`ui/dashboard_window.py`)**: Modern macOS Frosted Glass UI with 3 dedicated tabs:
  - **📅 Agenda di Oggi**: Visual timeline of all today's events, pilot badges, locations, and instant join buttons.
  - **🦆 Hangar Piloti**: Interactive playground to test flight animations for all 6 pilots.
  - **⚙️ Impostazioni & Timing**: Live controls for lead times, snooze intervals, banner screen position, flight speeds, chime audio, and autostart.
- ⚡ **Stale-While-Revalidate Instant Sync**: Displays today's schedule in **0.000013s** from persistent local disk cache while silently updating in the background without UI lag.
- ✈️ **6 Specialized Pilot Themes**: Dynamic Mascot and HUD themes automatically assigned based on event keywords.
- 🚀 **1-Click Smart Action Buttons**: Automatically launches meeting URLs in browser or sets Apple Maps GPS navigation with travel times.
- 💤 **Smart Timing Snooze Loops**: Custom snooze intervals (1 min, 2 min, 5 min, 10 min) ensuring critical events are never forgotten.
- 🍎 **Menu Bar Companion**: Lightweight menu bar status item displaying your next upcoming meeting countdown.
- 🔒 **Privacy-First & Local**: No external cloud accounts or servers. Runs entirely on your Mac through local Apple Calendar sync.

---

## 🦆 Pilot Themes & Smart Classification

QuakMeeting automatically parses your calendar event titles, locations, and URLs to assign the ideal pilot mascot and action:

| Pilot Mascot | Theme | Trigger Keywords / URLs | 1-Click Action |
| :--- | :--- | :--- | :--- |
| 🦆 **Papero Aviatore** | Google Green / Zoom Blue | Google Meet, Zoom, MS Teams, Webex, Online calls | `[🚀 PARTECIPA ORA]` (Browser) |
| 👨‍🍳 **Papero Chef** | Coral Food | Cena, Pranzo, Dinner, Ristorante, Pizzeria, Sushi, Aperitivo | `[🗺️ INDICAZIONI MAPPE]` |
| 🧑‍✈️ **Capitano Jet** | Sky Blue | Volo, Flight, Airport, WizzAir, Ryanair, Frecciarossa, Italo, Treno | `[🗺️ AEROPORTO / STAZIONE]` |
| 🦉 **Gufo Accademico** | Amber Academic | Lezione, Politecnico, Università, Esame, Tesi, SmartGrid, Studio | `[📚 AULA / APPUNTI]` |
| 🏎️ **Speed Racer** | Emerald Travel | In presenza, Palestra, Dottore, Dentista, Appuntamento con indirizzo | `[🗺️ VAI CON MAPPE]` |
| 🦆🌸 **Papero Zen** | Teal Zen | Serenis, Terapia, Meditazione, Yoga, Benessere, Relax | `[🚀 PARTECIPA AL MEETING]` |

---

## 🏗️ Architecture & Project Structure

The project follows a clean modular structure:

```
QuakMeeting/
├── QuakMeeting.app/            # Native standalone macOS Application Bundle
├── main.py                     # Primary Application Entrypoint (CLI / GUI)
├── build_macos_app.py          # Automated macOS Bundle & ICNS Generator
├── generate_app_icon.py        # Vector App Icon Generator (AppKit/Quartz)
├── core/                       # Core Logic & Services
│   ├── __init__.py
│   ├── calendar_scanner.py     # Calendar queries, classifier & disk cache store
│   ├── config_manager.py       # Configuration singleton (~/.quakmeeting/config.json)
│   └── autostart.py            # macOS LaunchAgent login manager
├── ui/                         # Native macOS User Interface
│   ├── __init__.py
│   ├── banner_window.py        # Quartz 2D animated flying banner HUD
│   ├── dashboard_window.py     # Frosted glass Flight Deck window
│   └── menu_bar_app.py         # NSStatusBar item & background daemon loop
├── assets/                     # Graphic Assets (PNG, ICNS)
└── docs/                       # Technical Documentation
    ├── ARCHITECTURE.md         # Detailed lifecycle, threading & IPC design
    └── CONFIGURATION.md        # Custom keywords & configuration guide
```

---

## 🚀 Installation & Getting Started

### Option 1: Standalone macOS App (`QuakMeeting.app`)
1. Double-click **`QuakMeeting.app`** on your **Desktop** or inside **`/Applications/`**.
2. When prompted by macOS, click **"Consenti" (Allow)** to grant Calendar access.
3. The app will launch in your Menu Bar and open the **Flight Deck Control Center**.

### Option 2: Test Flying Banner over Full Screen Apps
You can test the banner immediately (including over any full screen application like Safari, Chrome, YouTube, or Keynote):
- Double-click **`test_banner.command`** in the project folder, OR
- Run via terminal:
```bash
./test_banner.command
# Or with Python directly:
python3 main.py --test --delay 3 --pilot duck
```

### Option 3: Run via Terminal / Python
Ensure Python 3 with PyObjC is installed:
```bash
# Launch Menu Bar App + Flight Deck Dashboard
python3 main.py --dashboard
```

### Option 4: Rebuild the `.app` Bundle
If you customize the code or add new pilots:
```bash
python3 build_macos_app.py
```

---

## ⚙️ Configuration & Customization

QuakMeeting stores all user preferences in `~/.quakmeeting/config.json`. You can edit it through the **Flight Deck UI**, the **Menu Bar**, or directly in your text editor:

```json
{
  "lead_time_meeting_minutes": 6,
  "lead_time_travel_minutes": 35,
  "default_snooze_seconds": 120,
  "flight_speed": 3.2,
  "sound_enabled": true,
  "sound_name": "Glass",
  "ignored_calendars": [
    "Festività in Italia",
    "Birthdays",
    "Scheduled Reminders",
    "Siri Suggestions"
  ],
  "custom_keywords": {
    "chef": ["cena", "pranzo", "pizzeria", "aperitivo"],
    "captain": ["volo", "flight", "aeroporto", "treno", "frecciarossa"],
    "owl": ["politecnico", "universit", "esame", "lezione"],
    "zen_duck": ["serenis", "terapia", "yoga", "meditazione"],
    "driver": ["palestra", "dentista", "visita"]
  }
}
```

---

## 📜 Technical Documentation

- 📐 **[Technical Architecture & Lifecycle (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md)**
- 🏷️ **[Configuration & Rules Reference (docs/CONFIGURATION.md)](docs/CONFIGURATION.md)**

---

## 🤝 Credits & Acknowledgments
- Inspired by the open-source concept of [QuakPit](https://github.com/Ooble-Studio/QuakPit).
- Built with **Python 3**, **macOS PyObjC**, and native Apple **AppKit/Quartz 2D** rendering.
