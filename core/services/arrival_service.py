"""
Arrival & Presence Detection Service for QuakMeeting.
Detects whether the user has already arrived at a venue (Campus / Office Wi-Fi)
or is already participating in an online video call (Zoom, Teams, Webex, Skype, etc.).
Supports manual "I'm Here" suppression and user-configurable settings.
"""
import sys
import time
import subprocess
import logging
import threading
from typing import Set, Optional, Dict, Any, List
from core.domain.models import Meeting
from core.services.config_service import config_service, ConfigService

logger = logging.getLogger("QuakMeeting.ArrivalService")

class ArrivalService:
    """Manages automatic presence detection and manual arrival suppression."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ArrivalService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[ConfigService] = None):
        if self._initialized:
            return
        self.config = config or config_service
        self._manually_arrived_ids: Set[str] = set()
        self._arrival_reasons: Dict[str, str] = {}
        self._cached_wifi_ssid: Optional[str] = None
        self._last_wifi_check: float = 0.0
        self._wifi_cache_ttl: float = 4.0
        self._initialized = True

    def mark_arrived(self, meeting_id: str, reason: str = "manual") -> None:
        """Manually mark a meeting as arrived/attended, suppressing future reminders."""
        self._manually_arrived_ids.add(meeting_id)
        self._arrival_reasons[meeting_id] = reason
        logger.info(f"Marked event as arrived ({reason}): {meeting_id}")

    def is_manually_arrived(self, meeting_id: str) -> bool:
        return meeting_id in self._manually_arrived_ids

    def get_arrival_reason(self, meeting_id: str) -> Optional[str]:
        return self._arrival_reasons.get(meeting_id)

    def _get_wifi_ssid_linux(self) -> Optional[str]:
        """Queries current Wi-Fi SSID on Linux using NetworkManager (nmcli) or iwgetid."""
        # 1. Try nmcli
        try:
            res = subprocess.run(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.0
            )
            for line in res.stdout.splitlines():
                if line.startswith("yes:"):
                    ssid = line.split(":", 1)[1].strip()
                    if ssid:
                        return ssid
        except Exception:
            pass

        # 2. Try iwgetid fallback
        try:
            res = subprocess.run(
                ["iwgetid", "-r"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.0
            )
            ssid = res.stdout.strip()
            if ssid:
                return ssid
        except Exception:
            pass

        return None

    def _get_wifi_ssid_windows(self) -> Optional[str]:
        try:
            res = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.5
            )
            for line in res.stdout.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        ssid = parts[1].strip()
                        if ssid:
                            return ssid
        except Exception:
            pass
        return None

    def _get_wifi_ssid_macos(self) -> Optional[str]:
        try:
            cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.5)
            for line in res.stdout.splitlines():
                if " SSID:" in line:
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return None

    def get_current_wifi_ssid(self, force: bool = False) -> Optional[str]:
        """Queries current Wi-Fi SSID across macOS, Linux, or Windows with caching."""
        now = time.time()
        if not force and (now - self._last_wifi_check) < self._wifi_cache_ttl and self._cached_wifi_ssid is not None:
            return self._cached_wifi_ssid

        ssid = None
        if sys.platform == "win32":
            ssid = self._get_wifi_ssid_windows()
        elif sys.platform == "darwin":
            ssid = self._get_wifi_ssid_macos()
        else:
            ssid = self._get_wifi_ssid_linux()

        self._cached_wifi_ssid = ssid
        self._last_wifi_check = now
        logger.debug("Wi-Fi presence check on %s returned SSID=%r.", sys.platform, ssid)
        return ssid

    def _is_process_running_windows(self, process_name: str) -> bool:
        try:
            res = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/NH"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.5
            )
            return process_name.lower() in res.stdout.lower()
        except Exception:
            return False

    def _is_process_running_posix(self, pattern: str, exact: bool = False) -> bool:
        try:
            cmd = ["pgrep", "-x" if exact else "-f", pattern]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1.0)
            return res.returncode == 0
        except Exception:
            return False

    def _detect_any_active_call_app(self) -> Optional[str]:
        """Detects if any known video conferencing application is actively running."""
        # Windows
        if sys.platform == "win32":
            if self._is_process_running_windows("Zoom.exe"):
                return "Zoom"
            if self._is_process_running_windows("Teams.exe") or self._is_process_running_windows("ms-teams.exe"):
                return "Microsoft Teams"
            if self._is_process_running_windows("CiscoCollabHost.exe") or self._is_process_running_windows("webex.exe"):
                return "Cisco Webex"
            if self._is_process_running_windows("Skype.exe"):
                return "Skype"
            if self._is_process_running_windows("Slack.exe"):
                return "Slack"
            return None

        # macOS & Linux
        if self._is_process_running_posix("zoom.us", exact=True) or self._is_process_running_posix("zoom", exact=True):
            return "Zoom"
        if self._is_process_running_posix("Microsoft Teams") or self._is_process_running_posix("ms-teams") or self._is_process_running_posix("teams", exact=True):
            return "Microsoft Teams"
        if self._is_process_running_posix("CiscoCollabHost") or self._is_process_running_posix("webex"):
            return "Cisco Webex"
        if self._is_process_running_posix("Skype") or self._is_process_running_posix("skypeforlinux"):
            return "Skype"
        if self._is_process_running_posix("slack", exact=True):
            return "Slack"

        return None

    def is_active_video_call_running(self, meeting: Meeting) -> bool:
        """
        Detects if user is already in an active video call for this meeting.
        Checks running processes (Zoom, Microsoft Teams, Webex, Skype, Slack).
        """
        if not self.config.get("arrival_detect_active_calls", True):
            return False

        url = meeting.action_url or meeting.meeting_url
        if not url:
            return False

        url_lower = url.lower()

        # Check Zoom
        if "zoom.us" in url_lower:
            if sys.platform == "win32":
                return self._is_process_running_windows("Zoom.exe")
            return self._is_process_running_posix("zoom.us", exact=True) or self._is_process_running_posix("zoom", exact=True)

        # Check Microsoft Teams
        if "teams.microsoft.com" in url_lower or "teams.live.com" in url_lower:
            if sys.platform == "win32":
                return self._is_process_running_windows("Teams.exe") or self._is_process_running_windows("ms-teams.exe")
            return self._is_process_running_posix("Microsoft Teams") or self._is_process_running_posix("ms-teams") or self._is_process_running_posix("teams", exact=True)

        # Check Cisco Webex
        if "webex.com" in url_lower:
            if sys.platform == "win32":
                return self._is_process_running_windows("CiscoCollabHost.exe") or self._is_process_running_windows("webex.exe")
            return self._is_process_running_posix("CiscoCollabHost") or self._is_process_running_posix("webex")

        # Check Skype
        if "skype.com" in url_lower:
            if sys.platform == "win32":
                return self._is_process_running_windows("Skype.exe")
            return self._is_process_running_posix("Skype") or self._is_process_running_posix("skypeforlinux")

        # Check Slack
        if "slack.com" in url_lower:
            if sys.platform == "win32":
                return self._is_process_running_windows("Slack.exe")
            return self._is_process_running_posix("slack", exact=True)

        # Generic video call: If meeting is online and any video conference app is running
        detected_app = self._detect_any_active_call_app()
        if detected_app and (meeting.pilot_type == "duck" or "meet." in url_lower or "join" in url_lower):
            return True

        return False

    def is_connected_to_venue_wifi(self, meeting: Meeting) -> bool:
        """
        Checks if connected to campus / venue Wi-Fi for university lectures or office meetings.
        Uses user-configurable SSIDs list.
        """
        if not self.config.get("arrival_detect_venue_wifi", True):
            return False

        current_ssid = self.get_current_wifi_ssid()
        if not current_ssid:
            return False

        current_ssid_lower = current_ssid.lower()

        # Configurable campus & venue Wi-Fi networks
        configured_ssids = self.config.get("arrival_wifi_ssids", [
            "eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"
        ])
        venue_ssids = [s.strip().lower() for s in configured_ssids if s and s.strip()]

        if meeting.pilot_type == "owl" or meeting.classroom or meeting.is_travel:
            if any(c in current_ssid_lower for c in venue_ssids):
                return True

        return False

    def get_presence_diagnostics(self) -> Dict[str, Any]:
        """Returns real-time diagnostics on current network presence and call states for Settings UI."""
        current_wifi = self.get_current_wifi_ssid(force=True)
        configured_ssids = self.config.get("arrival_wifi_ssids", [
            "eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"
        ])
        venue_ssids = [s.strip().lower() for s in configured_ssids if s and s.strip()]

        is_venue_wifi = False
        if current_wifi:
            cw_lower = current_wifi.lower()
            is_venue_wifi = any(m in cw_lower for m in venue_ssids)

        detected_app = self._detect_any_active_call_app()
        logger.debug("Presence diagnostics: wifi=%r venue_wifi=%s active_call=%r.", current_wifi, is_venue_wifi, detected_app)
        return {
            "enabled": bool(self.config.get("enable_arrival_detection", True)),
            "detect_calls": bool(self.config.get("arrival_detect_active_calls", True)),
            "detect_wifi": bool(self.config.get("arrival_detect_venue_wifi", True)),
            "current_wifi": current_wifi,
            "is_venue_wifi": is_venue_wifi,
            "active_call_detected": bool(detected_app),
            "detected_call_app": detected_app,
            "monitored_ssids": configured_ssids,
        }

    def is_meeting_arrived(self, meeting: Meeting) -> bool:
        """
        Determines if user has arrived at the meeting (either manually or automatically).
        Sets meeting.is_arrived and meeting.arrival_reason accordingly.
        """
        # 1. Check explicit manual arrival
        if meeting.id in self._manually_arrived_ids or meeting.is_arrived:
            meeting.is_arrived = True
            if not meeting.arrival_reason:
                meeting.arrival_reason = self._arrival_reasons.get(meeting.id, "manual")
            logger.debug("Meeting %s is already marked arrived (%s).", meeting.id, meeting.arrival_reason)
            return True

        # Check master toggle
        if not self.config.get("enable_arrival_detection", True):
            logger.debug("Arrival detection disabled; skipping meeting %s.", meeting.id)
            return False

        # 2. Check active video meeting
        if self.is_active_video_call_running(meeting):
            app_name = self._detect_any_active_call_app() or "Video Call"
            reason = f"call:{app_name}"
            meeting.is_arrived = True
            meeting.arrival_reason = reason
            self._arrival_reasons[meeting.id] = reason
            logger.info(f"Auto-detected active video call ({app_name}) for '{meeting.title}'. Suppressing further notifications.")
            return True

        # 3. Check campus / venue Wi-Fi connection
        if self.is_connected_to_venue_wifi(meeting):
            ssid = self.get_current_wifi_ssid() or "Venue Wi-Fi"
            reason = f"wifi:{ssid}"
            meeting.is_arrived = True
            meeting.arrival_reason = reason
            self._arrival_reasons[meeting.id] = reason
            logger.info(f"Auto-detected campus/venue Wi-Fi ({ssid}) for '{meeting.title}'. Suppressing further notifications.")
            return True

        logger.debug("No arrival signal detected for meeting %s.", meeting.id)
        return False

# Global singleton
arrival_service = ArrivalService()

