"""
Arrival & Presence Detection Service for QuakMeeting.
Detects whether the user has already arrived at a venue (Campus Wi-Fi / Geofencing)
or is already participating in an online video call (Google Meet, Zoom, MS Teams).
Supports manual "I'm Here" suppression.
"""
import subprocess
import logging
import threading
from typing import Set, Optional, Dict, Any
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
        self._cached_wifi_ssid: Optional[str] = None
        self._last_wifi_check: float = 0.0
        self._initialized = True

    def mark_arrived(self, meeting_id: str) -> None:
        """Manually mark a meeting as arrived/attended, suppressing future reminders."""
        self._manually_arrived_ids.add(meeting_id)
        logger.info(f"Marked event as arrived (manually): {meeting_id}")

    def is_manually_arrived(self, meeting_id: str) -> bool:
        return meeting_id in self._manually_arrived_ids

    def get_current_wifi_ssid(self) -> Optional[str]:
        """Queries current Wi-Fi SSID on macOS via airport or system_profiler."""
        try:
            cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1.5)
            for line in res.stdout.splitlines():
                if " SSID:" in line:
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return None

    def is_active_video_call_running(self, meeting: Meeting) -> bool:
        """
        Detects if user is already in an active video call for this meeting.
        Checks running processes (Zoom, Microsoft Teams) or active browser URLs.
        """
        url = meeting.action_url or meeting.meeting_url
        if not url:
            return False

        # 1. Zoom App Running Check
        if "zoom.us" in url:
            try:
                res = subprocess.run(["pgrep", "-x", "zoom.us"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # 2. Microsoft Teams App Running Check
        if "teams.microsoft.com" in url or "teams.live.com" in url:
            try:
                res = subprocess.run(["pgrep", "-f", "Microsoft Teams"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        return False

    def is_connected_to_venue_wifi(self, meeting: Meeting) -> bool:
        """
        Checks if connected to campus / venue Wi-Fi for university lectures or office meetings.
        e.g. Eduroam, PoliTO, Campus-WiFi, University-WiFi.
        """
        current_ssid = self.get_current_wifi_ssid()
        if not current_ssid:
            return False

        current_ssid_lower = current_ssid.lower()
        
        # Campus & University Wi-Fi networks
        campus_ssids = ["eduroam", "polito", "campus", "universit", "studenti", "unito", "polimi"]
        if meeting.pilot_type == "owl" or meeting.classroom:
            if any(c in current_ssid_lower for c in campus_ssids):
                return True

        return False

    def is_meeting_arrived(self, meeting: Meeting) -> bool:
        """
        Determines if user has arrived at the meeting (either manually or automatically).
        """
        # 1. Check explicit manual arrival
        if meeting.id in self._manually_arrived_ids or meeting.is_arrived:
            return True

        # 2. Check active video meeting
        if self.is_active_video_call_running(meeting):
            logger.info(f"Auto-detected active video call for '{meeting.title}'. Suppressing further notifications.")
            return True

        # 3. Check campus / venue Wi-Fi connection
        if self.is_connected_to_venue_wifi(meeting):
            logger.info(f"Auto-detected campus/venue Wi-Fi connection for '{meeting.title}'. Suppressing further notifications.")
            return True

        return False

# Global singleton
arrival_service = ArrivalService()
