# 🦆 QuakMeeting — Developer & Agent Guide

> **IMPORTANT FOR AI AGENTS & DEVELOPERS:**
> Read this document first before making changes. It contains the project architecture, operational rules, and the **mandatory 4-step development workflow** to follow after every code modification.

---

## ⚡ Mandatory 4-Step Development Workflow (Execute on Every Change)

Whenever you make any change to code or configuration in this project, **always execute this complete workflow**:

```bash
# 1. Run Unit Test Suite
/opt/miniconda3/bin/python3 -m unittest discover -s tests -v

# 2. Rebuild the macOS Native .app Bundle
/opt/miniconda3/bin/python3 build_macos_app.py

# 3. Close the running instance and reopen the freshly built .app
pkill -f "QuakMeeting" 2>/dev/null; sleep 1; open /Applications/QuakMeeting.app

# 4. Verify running process and inspect live logs
sleep 2 && ps aux | grep -i "[Q]uakMeeting" && echo "---" && tail -15 ~/.quakmeeting/quakmeeting.log
```

> ⚠️ **IMPORTANT COMMIT RULE**:
> **DO NOT automatically commit changes.** Only commit to Git when explicitly requested by the user.

---

## 🏗️ Architecture & Core Components

```
QuakMeeting/
├── main.py                        # App entry point (initializes logging, status bar, and Flight Deck)
├── build_macos_app.py             # Custom build script compiling C launcher Mach-O & bundling app
├── assets/                        # App icons (PNG & ICNS), audio files
├── core/
│   ├── domain/
│   │   ├── models.py              # Meeting dataclass, PilotType, TransportMode, format_duration()
│   │   └── classifier.py          # Smart keyword matching & categorization
│   ├── providers/
│   │   ├── base.py                # BaseCalendarProvider abstract class
│   │   └── eventkit_provider.py   # Native Apple EventKit bridge (extracts travelTime & coordinates)
│   ├── services/
│   │   ├── calendar_service.py    # Synchronizes & caches Today-only events (00:00 to 23:59:59)
│   │   ├── reminder_engine.py     # Multi-stage notification triggers (evaluates leave vs start time)
│   │   ├── eta_service.py         # Apple Maps URL builder & departure time calculator
│   │   ├── arrival_service.py     # Automatic/manual arrival detection and suppression
│   │   ├── config_service.py      # Configuration manager (~/.quakmeeting/config.json)
│   │   └── event_bus.py           # Decoupled pub/sub event system
│   └── logger.py                  # Dual console & file logger (~/.quakmeeting/quakmeeting.log)
├── ui/
│   ├── menu_bar_app.py            # macOS Status Bar Item (NSStatusItem) & top menu bar
│   ├── dashboard_window.py        # Flight Deck HUD window (Today's Agenda, Pilots, Preferences)
│   └── banner/
│       ├── banner_view.py         # Quartz 2D animated banner component
│       ├── banner_controller.py   # NSWindow floating banner controller
│       └── renderers/             # Specialized pilot themes (Duck, Captain, Chef, Owl, Driver, Zen)
└── tests/                         # Full automated unit test suite (27+ tests)
```

---

## 📌 Critical Design Decisions & Rules

### 1. In-Process Mach-O Python Embedding
- **Rule**: When building `QuakMeeting.app`, the launcher stub in `build_macos_app.py` compiles a native C Mach-O binary that loads `libpython3.13.dylib` via `dlopen`/`dlsym` and invokes `Py_Main` in-process.
- **Why**: Calling `execv` to a shell script or external interpreter breaks macOS bundle association and causes the top macOS menu bar (`QuakMeeting`, `Edit`, `Window`, `Help`) to disappear.

### 2. Strict Today-Only Calendar Filter
- **Rule**: `CalendarService` only fetches and evaluates events scheduled for **Today** (`00:00:00` to `23:59:59`).
- **Why**: Events for tomorrow must **never** appear in Today's Agenda, must not be picked as "Next Event" 24 hours in advance, and must not trigger premature notifications.

### 3. Transit / Travel Events vs Video Calls
- **Travel / Transit Events (`is_travel=True`, `departure_time` set)**:
  - Notification stages (e.g. 45m, 30m, 15m, 5m, 0m) evaluate relative to the **Leave / Departure Time** (`departure_time`), not the event start time.
  - Stage 0m = *"🚨 Time to Leave! 🚗"*.
- **Online Meetings & Regular Events (`is_travel=False`)**:
  - Notification stages evaluate relative to the **Event Start Time** (`start_time`).

### 4. Duration & Time Formatting
- **Rule**: Always use `format_duration(minutes, long_form=False)` from `core.domain.models`:
  - `120 min` → `2h` (or `2 hours`)
  - `90 min` → `1h 30m`
  - `60 min` → `1h`
  - `45 min` → `45m`

### 5. Menu Bar Live Status Modes & 3-Hour Lookahead Cap
- **Modes**:
  - `countdown` (Default): Dynamic countdown (`Leave in 18m (Dinner)` / `in 25m: Sync` / `🟢 Sync (15m left)`).
  - `event_time`: Start time and title (`20:00 Dinner (~25m)`).
  - `time_only`: Time with countdown (`20:00 in 25m`).
  - `icon_only`: Minimal icon (`🦆` or pilot emoji).
- **Lookahead Cap (`max_countdown_lookahead_hours: 3`)**:
  - If the next event is more than 3 hours away, the menu bar displays a clean event start time (`20:00 [Title]`) instead of long countdowns (`in 11h15m`).
  - Once within 3 hours, it automatically transitions to active live countdown.
- **Immediate EventBus Sync**:
  - Changing mode in dropdown or Flight Deck Preferences fires `event_bus.publish("CONFIG_CHANGED")` to immediately update the tray title without delay.

---

## 🧪 Testing Guidelines

Always run unit tests before building or committing:
```bash
/opt/miniconda3/bin/python3 -m unittest discover -s tests -v
```

Existing test suites:
- `tests/test_models.py` (Meeting model, serialization, `format_duration`)
- `tests/test_reminder_engine.py` (Stage evaluation, travel departure stages, arrival suppression)
- `tests/test_calendar_service.py` (EventKit extraction, ETA enrichment)
- `tests/test_classifier.py` (Keyword matching, pilot categories, URL extraction)
- `tests/test_eta_service.py` (Apple Maps route URLs, departure calculation)
- `tests/test_event_bus.py` (Publish/subscribe event isolation)
- `tests/test_config_service.py` (Default configuration, fallback handling)
- `tests/test_arrival_service.py` (Manual & presence arrival state)
