"""
Comprehensive system diagnostics and health check runner for QuakMeeting.
Provides human-understandable reporting for CLI (--check) and GUI dialogs.
"""
from __future__ import annotations

import os
import sys
import platform
from typing import Dict, Any, List


def run_system_diagnostics_check() -> Dict[str, Any]:
    """Runs a complete system health check and returns structured diagnostics data."""
    results: Dict[str, Any] = {
        "status": "OK",
        "warnings": [],
        "errors": [],
        "python": {},
        "gui": {},
        "calendar": {},
        "presence": {},
        "audio": {},
        "storage": {},
    }

    # 1. Python & OS Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    results["python"] = {
        "version": py_ver,
        "executable": sys.executable,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "is_supported": sys.version_info >= (3, 8),
    }
    if sys.version_info < (3, 8):
        results["errors"].append("Python 3.8 or higher is required.")
        results["status"] = "ERROR"

    # 2. GUI Runtime
    display_server = "Quartz (macOS)" if sys.platform == "darwin" else ("Windows" if sys.platform == "win32" else "X11 / Wayland")
    if sys.platform.startswith("linux"):
        is_wayland = "WAYLAND_DISPLAY" in os.environ or os.environ.get("XDG_SESSION_TYPE") == "wayland"
        display_server = f"Wayland (Qt XCB compat: {os.environ.get('QT_QPA_PLATFORM', 'default')})" if is_wayland else "X11"

    gui_info: Dict[str, Any] = {"display_server": display_server}
    if sys.platform == "darwin":
        try:
            import AppKit
            import objc
            gui_info["backend"] = "AppKit / PyObjC (Native Cocoa)"
            gui_info["available"] = True
        except ImportError as e:
            gui_info["backend"] = "AppKit (Missing)"
            gui_info["available"] = False
            results["errors"].append(f"PyObjC / AppKit import failed: {e}")
            results["status"] = "ERROR"
    else:
        try:
            import PyQt6.QtCore
            import PyQt6.QtWidgets
            gui_info["backend"] = f"PyQt6 {PyQt6.QtCore.PYQT_VERSION_STR}"
            gui_info["available"] = True
        except ImportError as e:
            gui_info["backend"] = "PyQt6 (Missing)"
            gui_info["available"] = False
            results["errors"].append(f"PyQt6 is not installed in current Python: {e}")
            results["status"] = "ERROR"

    results["gui"] = gui_info

    # 3. Calendar Subsystem
    cal_info: Dict[str, Any] = {}
    try:
        from core.services.calendar_service import calendar_service
        provider = calendar_service.get_active_provider()
        p_name = calendar_service.provider_name or (provider.__class__.__name__ if provider else "None")
        cal_info["active_provider"] = p_name
    except Exception as e:
        cal_info["active_provider"] = f"Error: {e}"
        results["warnings"].append(f"Could not query active calendar provider: {e}")

    # Check CalDAV module
    try:
        import caldav
        cal_info["caldav_library"] = f"Available ({getattr(caldav, '__version__', 'installed')})"
    except ImportError:
        cal_info["caldav_library"] = "Not installed (Optional for remote CalDAV)"

    # Check Evolution Data Server (EDS) on Linux
    if sys.platform.startswith("linux"):
        try:
            import gi
            gi.require_version('EDataServer', '1.2')
            from gi.repository import EDataServer
            cal_info["eds_library"] = "Available (EDataServer 1.2)"
        except Exception:
            cal_info["eds_library"] = "Unavailable (CalDAV provider will be used instead)"

    try:
        from core.services.config_service import config
        feeds = config.get("calendar_urls", [])
        cal_info["configured_feeds_count"] = len(feeds)
    except Exception:
        cal_info["configured_feeds_count"] = 0

    results["calendar"] = cal_info

    # 4. Smart Presence & Arrival Detection
    try:
        from core.services.arrival_service import arrival_service
        from core.services.config_service import config
        presence_diag = arrival_service.get_presence_diagnostics()
        is_enabled = bool(config.get("enable_arrival_detection", True))

        current_wifi = presence_diag.get("current_wifi")
        is_venue_wifi = presence_diag.get("is_venue_wifi", False)
        call_app = presence_diag.get("detected_call_app")

        # Operational status interpretation
        if not is_enabled:
            mode_desc = "⏸️ Presence Detection Paused (Disabled in Settings)"
        elif call_app:
            mode_desc = f"🟢 In-Call Mode ({call_app} running — Meeting alerts auto-suppressed)"
        elif is_venue_wifi and current_wifi:
            mode_desc = f"🟢 Venue Mode (Connected to {current_wifi} — Lecture alerts suppressed)"
        else:
            mode_desc = "⚪ Normal Mode (All scheduled flight banners will alert on time)"

        results["presence"] = {
            "enabled": is_enabled,
            "current_wifi": current_wifi or "Disconnected / Not connected",
            "is_venue_wifi": is_venue_wifi,
            "detected_call_app": call_app or "None running",
            "operational_mode": mode_desc,
            "venue_ssids": config.get("arrival_wifi_ssids", []),
        }
    except Exception as e:
        results["presence"] = {"error": str(e)}
        results["warnings"].append(f"Arrival service diagnostics unavailable: {e}")

    # 5. Audio & Sounds
    try:
        from core.services.sound_service import sound_service
        from core.services.config_service import config
        sound_enabled = bool(config.get("sound_enabled", True))
        sound_name = config.get("sound_name", "Glass")
        mute_in_lesson = bool(config.get("mute_during_lessons", True))

        results["audio"] = {
            "sound_enabled": sound_enabled,
            "sound_name": sound_name,
            "mute_during_lessons": mute_in_lesson,
            "backend": sound_service.get_backend_name() if hasattr(sound_service, "get_backend_name") else "Native OS",
        }
    except Exception as e:
        results["audio"] = {"error": str(e)}

    # 6. Configuration & Storage
    try:
        from core.services.config_service import CONFIG_PATH, CONFIG_DIR
        from core.logger import LOG_FILE
        results["storage"] = {
            "config_file": CONFIG_PATH,
            "config_exists": os.path.exists(CONFIG_PATH),
            "log_file": LOG_FILE,
            "log_writable": os.access(os.path.dirname(LOG_FILE), os.W_OK) if os.path.exists(os.path.dirname(LOG_FILE)) else True,
        }
    except Exception as e:
        results["storage"] = {"error": str(e)}

    return results


def format_diagnostics_report(diag: Dict[str, Any] | None = None) -> str:
    """Formats system diagnostics into a clear, understandable, human-readable terminal report."""
    if diag is None:
        diag = run_system_diagnostics_check()

    py = diag.get("python", {})
    gui = diag.get("gui", {})
    cal = diag.get("calendar", {})
    pres = diag.get("presence", {})
    audio = diag.get("audio", {})
    stor = diag.get("storage", {})

    lines: List[str] = [
        "=" * 64,
        " 🦆 QuakMeeting System Health & Diagnostics Check",
        "=" * 64,
        "",
        "[1/5] 🐍 Python & Runtime Environment:",
        f"  • Python Version:    {py.get('version', 'Unknown')} ({sys.maxsize > 2**32 and '64-bit' or '32-bit'})",
        f"  • Executable:        {py.get('executable', sys.executable)}",
        f"  • Platform:          {py.get('platform', platform.platform())}",
        f"  • GUI Backend:       {gui.get('backend', 'Unknown')}",
        f"  • Window Server:     {gui.get('display_server', 'Unknown')}",
        "",
        "[2/5] 📅 Calendar Integration:",
        f"  • Active Provider:   {cal.get('active_provider', 'None')}",
    ]

    if "eds_library" in cal:
        lines.append(f"  • Evolution (EDS):   {cal.get('eds_library')}")
    if "caldav_library" in cal:
        lines.append(f"  • CalDAV Module:     {cal.get('caldav_library')}")
    lines.append(f"  • Configured Feeds:  {cal.get('configured_feeds_count', 0)} calendar feed(s)")

    lines.extend([
        "",
        "[3/5] 📶 Smart Presence & Arrival Detection:",
        f"  • Presence Active:   {'Enabled ✅' if pres.get('enabled') else 'Disabled ⏸️'}",
        f"  • Current Wi-Fi:     {pres.get('current_wifi', 'None')}" + (" (Recognized Venue ✅)" if pres.get("is_venue_wifi") else ""),
        f"  • Video Call App:    {pres.get('detected_call_app', 'None running')}",
        f"  • Operational State: {pres.get('operational_mode', 'Normal')}",
    ])

    venues = pres.get("venue_ssids", [])
    if venues:
        venue_str = ", ".join(venues[:5]) + (f" (+{len(venues)-5} more)" if len(venues) > 5 else "")
        lines.append(f"  • Monitored Venues:  {venue_str}")

    lines.extend([
        "",
        "[4/5] 🔊 Audio & Notifications:",
        f"  • Sound Alert:       {'Enabled 🔔' if audio.get('sound_enabled') else 'Muted 🔕'} (Sound: {audio.get('sound_name', 'Glass')})",
        f"  • Lesson Quiet Mode: {'Active (Mutes during class) 🤫' if audio.get('mute_during_lessons') else 'Disabled'}",
        "",
        "[5/5] 📁 Storage & Configuration:",
        f"  • Config File:       {stor.get('config_file', 'Unknown')} ({'Found ✅' if stor.get('config_exists') else 'Will create on save'})",
        f"  • Log File:          {stor.get('log_file', 'Unknown')}",
        "",
        "=" * 64,
    ])

    errors = diag.get("errors", [])
    warnings = diag.get("warnings", [])

    if errors:
        lines.append("❌ ATTENTION: Issues detected that may prevent QuakMeeting from running:")
        for err in errors:
            lines.append(f"   • {err}")
        lines.append("")
    elif warnings:
        lines.append("⚠️ NOTE: Minor issues detected:")
        for warn in warnings:
            lines.append(f"   • {warn}")
        lines.append("")
    else:
        lines.append("✨ All systems operational. QuakMeeting is ready to fly! 🦆")

    lines.append("=" * 64)
    return "\n".join(lines)
