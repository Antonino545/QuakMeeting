<div align="center">

# 🦆 QuakMeeting
### Multiplatform Native Flight Deck & Smart Meeting Reminder Assistant
*macOS (Sonoma / Sequoia) & Ubuntu Linux (Wayland / X11)*  
*Inspired by [QuakPit](https://github.com/Ooble-Studio/QuakPit) — Designed for Timing Precision, Travel Readiness, & 1-Click Meeting Joins.*

[![macOS](https://img.shields.io/badge/macOS-12.0%2B-blue?logo=apple&style=flat-square)](https://apple.com)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%20%7C%2024.04%20(Wayland)-orange?logo=ubuntu&style=flat-square)](https://ubuntu.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow?logo=python&style=flat-square)](https://python.org)
[![Release](https://img.shields.io/badge/Release-v1.0.5-success?style=flat-square)](https://github.com/Antonino545/QuakMeeting/releases)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<img src="assets/icon.png" width="150" alt="QuakMeeting Icon" />

</div>

---

## 📖 Overview & Philosophy

**QuakMeeting** is a lightweight multiplatform companion application built to solve one of the biggest daily productivity challenges: **forgetting upcoming video calls, missing transit departure times, or losing track of time during deep work.**

Instead of tiny, easily-missed system notification banners, QuakMeeting animates a **mascot aircraft towing an interactive HUD banner** across your display:
- **macOS**: Built with native **AppKit / Quartz 2D** with frosted glass cards, smooth 60fps animations, and in-process runtime.
- **Ubuntu Linux (Wayland & X11)**: Native **PyQt6** animated overlay banner with solid Catppuccin cards and **GNOME AppIndicator3** status item.

<div align="center">
  <img src="assets/animations/banner_flight.gif" width="85%" alt="QuakMeeting Interactive HUD Banner in Flight" />
</div>

---

## ✨ Key Features

- 🖥️ **Flight Deck Control Center (`ui/macos/dashboard_window.py` & `ui/linux/qt_dashboard.py`)**:
  - **📅 Today's Agenda**: Timeline of all today's events, departure countdowns, and 1-click launch / navigation actions.
  - **🦆 Pilot Hangar**: Interactive flight test playground for all 7 pilot personas and 5 animal species.
  - **⚙️ Preferences & Timing**: Customizable staged alert windows (e.g. 45m, 30m, 20m, 15m, 10m, 5m, 2m, 0m), starting location for Apple/Google Maps ETA, chimes, and calendar feeds.
- 🌐 **Bilingual Multi-Language Support (English & Italiano)**:
  - Automatically detects system language from macOS `NSLocale` or Linux `$LANG`.
  - Manual language switcher in Settings (`🌐 System (Auto)`, `🇬🇧 English`, `🇮🇹 Italiano`).
  - Bilingual animal speech bubbles, badges, countdown timers, and in-app license viewers.
- 🚗 **Real-Time Travel & Multi-Modal ETA Engine**:
  - Automatically calculates transit, driving, walking, or cycling duration with configurable departure buffers.
  - Triggers alerts relative to **Leave Time** instead of meeting start time.
  - 1-Click deep links to **Apple Maps** (macOS) or **Google Maps Directions** (Linux).
- ✈️ **7 Specialized Mascot Personas & 5 Animal Species**:
  - Custom vector graphics and speech vocalizations tailored to event context.
- 🔄 **In-App GitHub Releases Auto-Updater**:
  - Checks for updates automatically with live download/installation progress tracking.
- ⚡ **Multiplatform Calendar Sync**:
  - **macOS**: Native Apple EventKit API bridge (`EventKitProvider`).
  - **Ubuntu Linux**: Universal iCalendar / CalDAV engine (`CalDAVProvider`) syncing Google Calendar, iCloud, Nextcloud, and Outlook `.ics` feeds.
- 🔒 **Privacy-First & Local**: No telemetry, tracking, or cloud account requirements.

---

## 🦆 Mascot Animal Roster & Pilot Personas

QuakMeeting features a diverse crew of animal pilots automatically chosen based on event classification. Each pilot features dynamic flight physics including high-RPM spinning propellers, wingtip navigation strobe beacons, vertical wave bobbing, blinking expressions, and fluttering accessories in the slipstream:

<div align="center">
  <img src="assets/animations/mascot_squadron.gif" width="100%" alt="QuakMeeting Animated Mascot Squadron" />
  <p><em>From left to right: Mallard Duck, Wise Owl, Athletic Bunny, Zen Platypus, and Gourmet Squirrel in formation flight.</em></p>
</div>

| Live Animation | Mascot Animal | Persona | Accent Color | Triggers & Context | 1-Click Action |
| :---: | :--- | :--- | :--- | :--- | :--- |
| <img src="assets/animations/duck_flight.gif" width="110" alt="Mallard Duck" /> | 🦆 **Mallard Duck** | **Aviator Pilot** | Catppuccin Green | Google Meet, Zoom, MS Teams, Webex, Online calls | `[🚀 JOIN MEETING]` |
| <img src="assets/animations/owl_flight.gif" width="110" alt="Wise Owl" /> | 🦉 **Wise Owl** | **Academic Scholar** | Catppuccin Mauve | University lectures, exams, campus study, research | `[📚 CLASSROOM & NOTES]` |
| <img src="assets/animations/bunny_flight.gif" width="110" alt="Athletic Bunny" /> | 🐰 **Athletic Bunny** | **Gym & Sport Hero** | Catppuccin Red | Palestra, Gym, CrossFit, Padel, Tennis, Football, Running | `[🗺️ GYM DIRECTIONS]` |
| <img src="assets/animations/platypus_flight.gif" width="110" alt="Zen Platypus" /> | 🦔 **Zen Platypus** | **Mindfulness Guru** | Catppuccin Teal | Serenis, Therapy, Yoga, Wellness, Meditation | `[🛋️ JOIN SESSION]` |
| <img src="assets/animations/squirrel_flight.gif" width="110" alt="Gourmet Squirrel" /> | 🐿️ **Gourmet Squirrel** | **Chef & Foodie** | Catppuccin Peach | Dinner, Lunch, Restaurant, Pizzeria, Sushi, Cooking | `[🗺️ RESTAURANT MAPS]` |
| <img src="assets/animations/captain_flight.gif" width="110" alt="Captain Duck" /> | 🧑‍✈️ **Captain Duck** | **Airline & Train Pilot**| Catppuccin Sapphire | Flights, Airports, High-speed trains, Buses, Transit | `[🗺️ TRANSIT / AIRPORT]` |
| <img src="assets/animations/racer_flight.gif" width="110" alt="Speed Racer" /> | 🏎️ **Speed Racer** | **Driver** | Catppuccin Yellow | Appointments, Doctor, Dentist, Errands, Commutes | `[🗺️ NAVIGATE MAPS]` |

---

## 📸 Visual Showcase & Multiplatform Parity

QuakMeeting delivers a unified **Catppuccin Mocha** visual experience across macOS (AppKit) and Linux (PyQt6). For complete implementation specifications, see [📐 UI Architecture & Design Tokens](docs/ARCHITECTURE.md#ui-architecture--visual-parity).

### 🦆 Pilot Hangar Playground
*Interactive test flight simulator featuring dedicated Catppuccin accent buttons for all mascot pilots.*

| 🍎 macOS (Native AppKit) | 🐧 Ubuntu Linux (PyQt6 / Wayland) |
| :---: | :---: |
| ![macOS Pilot Hangar](assets/screenshots/macos_hangar.png) | ![Linux Qt Pilot Hangar](assets/screenshots/qt_hangar.png) |

### ⚙️ Preferences & Timing Flight Deck
*Customizable staged reminder lead times (quick presets & dynamic pill chips), language switcher, multi-modal routing, and calendar feeds.*

| 🍎 macOS (Native AppKit) | 🐧 Ubuntu Linux (PyQt6 / Wayland) |
| :---: | :---: |
| ![macOS Settings](assets/screenshots/macos_settings.png) | ![Linux Qt Settings](assets/screenshots/qt_settings.png) |

---

## 📦 Download & Installation

### 🍎 macOS (`.dmg` Installer)
1. Download **`QuakMeeting-macOS.dmg`** from [Latest Releases](https://github.com/Antonino545/QuakMeeting/releases/latest).
2. Open the DMG and drag **QuakMeeting** into `/Applications`.
3. Launch `QuakMeeting.app` from Launchpad or Spotlight.
   > **Note on Gatekeeper**: If macOS reports the app is unsigned from GitHub, simply run:
   > ```bash
   > xattr -cr /Applications/QuakMeeting.app
   > ```
   > *(Or right-click `QuakMeeting.app` in Finder and select **Open**).*

### 🐧 Ubuntu Linux (`.deb` Package)
1. Download **`quakmeeting_1.0.5_amd64.deb`** from [Latest Releases](https://github.com/Antonino545/QuakMeeting/releases/latest).
2. Install via terminal:
   ```bash
   sudo apt install ./quakmeeting_1.0.5_amd64.deb
   ```
3. Launch **QuakMeeting** from your Application Grid or run `quakmeeting`.

---

## 🏗️ Project Architecture

```text
QuakMeeting/
├── main.py                        # App entry point & CLI flag dispatcher (--debug, --qt, --pilot)
├── build_macos_app.py             # Bundles standalone macOS .app with embedded Python & codesign
├── scripts/
│   ├── build_ubuntu_deb.sh        # Debian/Ubuntu .deb package builder for Linux (Wayland/X11)
│   └── install_linux_deps.sh      # Installs system dependencies for Linux
├── assets/                        # App icons (PNG & ICNS), audio files
├── core/
│   ├── domain/
│   │   ├── models.py              # Meeting dataclass, PilotType, TransportMode, format_duration()
│   │   └── classifier.py          # Bilingual keyword taxonomy matching & smart categorization
│   ├── providers/
│   │   ├── base.py                # BaseCalendarProvider abstract class
│   │   ├── eventkit_provider.py   # Native Apple EventKit bridge (macOS)
│   │   └── caldav_provider.py     # CalDAV calendar provider (Linux)
│   ├── services/
│   │   ├── calendar_service.py    # Synchronizes & caches Today-only events (00:00 to 23:59:59)
│   │   ├── reminder_engine.py     # Multi-stage notification triggers (evaluates leave vs start time)
│   │   ├── eta_service.py         # Multi-modal routing & Apple/Google Maps URL builder
│   │   ├── language_service.py    # OS detection & centralized English/Italian dictionary
│   │   ├── updater_service.py     # GitHub Releases auto-updater
│   │   ├── arrival_service.py     # Automatic/manual arrival detection and suppression
│   │   ├── config_service.py      # Configuration manager (~/.quakmeeting/config.json)
│   │   └── event_bus.py           # Decoupled pub/sub event system
│   └── logger.py                  # Dual console & file logger (~/.quakmeeting/quakmeeting.log)
├── ui/
│   ├── app_launcher.py            # Platform-aware UI dispatcher
│   ├── common/                    # Shared UI helpers & viewmodels
│   │   ├── theme.py               # Catppuccin Mocha color tokens & pilot palettes
│   │   ├── tray_viewmodel.py      # Status formatting & countdown badge logic
│   │   ├── banner_speech.py       # Animal vocalization generator (duck, owl, bunny, squirrel, platypus)
│   │   ├── banner_formatting.py   # Time differentials & travel badges
│   │   ├── banner_particles.py    # Turbo afterburner & exhaust smoke physics engine
│   │   └── banner_queue.py        # Cross-platform banner sequencing queue
│   ├── macos/                     # macOS Native UI (PyObjC, AppKit, Quartz 2D)
│   │   ├── menu_bar_app.py        # NSStatusItem status bar controller & dropdown
│   │   ├── dashboard_window.py    # Native NSWindow Flight Deck HUD
│   │   ├── dashboard_tabs/        # Native AppKit Tab Views (Agenda, Hangar, Settings)
│   │   ├── banner_window.py       # NSWindow overlay wrapper
│   │   └── banner/                # Quartz 2D animated HUD banners & pilot renderers
│   └── linux/                     # Linux / Ubuntu UI (PyQt6, Wayland / X11)
│       ├── qt_tray_app.py         # PyQt6 QSystemTrayIcon menu & status
│       ├── qt_dashboard.py        # PyQt6 Flight Deck window
│       └── banner/                # PyQt6 animated banner overlay & pilot renderers
└── tests/                         # Full automated unit test suite (90+ tests)
```

---

## 🛠️ Development & Testing

### 1. Run Automated Unit Tests
```bash
/opt/miniconda3/bin/python3 -m unittest discover -s tests -v
```

### 2. Build macOS App
```bash
/opt/miniconda3/bin/python3 build_macos_app.py
```

### 3. Build Ubuntu Debian Package
```bash
bash scripts/build_ubuntu_deb.sh
```

---

## 🤝 Credits & Acknowledgments
- Inspired by the open-source concept of [QuakPit](https://github.com/Ooble-Studio/QuakPit).
- Visual design tokens based on [Catppuccin](https://github.com/catppuccin/catppuccin) Mocha palette.
- Built with **Python 3**, **Apple AppKit/Quartz 2D** (macOS), and **PyQt6** (Linux Wayland/X11).
