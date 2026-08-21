# 📐 QuakMeeting — Technical Architecture & Lifecycle

This document outlines the internal architecture, threading model, memory lifecycle, and data flow of QuakMeeting.

---

## 🏗️ System Overview

```mermaid
flowchart TD
    subgraph macOS Environment
        CalApp[macOS Calendar / iCloud / Google / Exchange]
        Dock[macOS Dock]
        StatusBar[macOS Menu Bar]
        Screen[macOS Displays & Spaces]
    end

    subgraph Core Package [core/]
        ConfigMgr[config_manager.py\nJSON Config Store\n~/.quakmeeting/config.json]
        Scanner[calendar_scanner.py\nStale-While-Revalidate Engine]
        DiskCache[(~/.quakmeeting/calendar_cache.json)]
        AutoStart[autostart.py\nLaunchAgent Manager]
    end

    subgraph UI Package [ui/]
        MenuBar[menu_bar_app.py\nNSStatusItem + Background Daemon]
        Dashboard[dashboard_window.py\nFlight Deck Window Controller]
        Banner[banner_window.py\nQuartz 2D Flying Airplane HUD]
    end

    CalApp <-->|AppleScript IPC| Scanner
    Scanner <-->|0.000013s Read/Write| DiskCache
    ConfigMgr <--> MenuBar
    ConfigMgr <--> Dashboard
    ConfigMgr <--> Banner

    MenuBar <-->|Background Polling| Scanner
    Dashboard <-->|Instant Cache Read| Scanner

    MenuBar --> StatusBar
    Dashboard --> Screen
    Banner --> Screen
    AutoStart -->|Login Item| MenuBar
```

---

## 🔄 Lifecycle & Threading Model

### 1. Zero-Latency Stale-While-Revalidate Sync
- **The Challenge**: Direct AppleScript queries to `Calendar.app` can take 15–30 seconds if the user has multiple synchronized accounts with recurring events.
- **The Solution**: 
  - On launch or UI open, `calendar_scanner.py` immediately reads `~/.quakmeeting/calendar_cache.json` in **$0.000013\text{ seconds}$**.
  - A background daemon thread periodically queries `Calendar.app` without blocking the main event loop (`NSApplication`).
  - When fresh data arrives, it atomically replaces the in-memory cache, writes to disk, and signals the main thread to refresh the UI.

### 2. Window & Application Lifecycle
- `QuakMeetingAppDelegate` implements `applicationShouldTerminateAfterLastWindowClosed_` returning `False`.
- Both `dashboard_window.py` and `banner_window.py` set `window.setReleasedWhenClosed_(False)`.
- When the user closes $(✕)$ the Flight Deck or dismisses a flying banner, the window is simply hidden (`orderOut_`), allowing the background scanner and menu bar to run 24/7.

---

## 🎨 Rendering Engine (`ui/banner_window.py`)
- **Graphics Pipeline**: Native Apple Quartz 2D (`NSBezierPath`, `CGContext`, `NSColor`, `NSFont`).
- **Animation Loop**: 60 FPS `NSTimer` calculating smooth sinusoidal bobbing (`sin(t * 5.0)`), propeller rotation, and dynamic wind trail particles.
- **Multi-Monitor & Fullscreen Compatibility**: Uses `NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary` with `NSStatusWindowLevel` so banners float above fullscreen games, videos, and IDEs.
