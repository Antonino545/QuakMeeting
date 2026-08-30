"""
Study Focus Guardian Service for QuakMeeting.
Monitors user attention during scheduled self-study events and classes.
Evaluates iPad note-taking heartbeats vs iPhone distractions, and triggers
timely motivational Owl Pilot HUD banners when off-task.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple

from core.domain.models import Meeting, DeviceActivity, DeviceState, DeviceType, PilotType
from core.services.config_service import config, ConfigService
from core.services.event_bus import event_bus, EventBus
from core.services.calendar_service import calendar_service, CalendarService
from core.services.reminder_engine import reminder_engine, ReminderEngine

logger = logging.getLogger("QuakMeeting.StudyFocusGuardian")


class StudyFocusGuardian:
    """Evaluates cross-device activity (iPad vs iPhone) during active Study calendar events."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(StudyFocusGuardian, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.config = config
        self.bus = event_bus
        self.last_distraction_banner_time: Optional[datetime] = None
        self.active_study_meeting: Optional[Meeting] = None
        self.cached_meetings: Optional[List[Meeting]] = None
        
        # Subscribe to EventBus
        self.bus.subscribe("DEVICE_ACTIVITY_RECEIVED", self._on_device_activity)
        self.bus.subscribe("AGENDA_UPDATED", self._on_agenda_updated)
        self.bus.subscribe("VISUAL_ATTENTION_STATE", self._on_visual_attention_state)

    def _on_agenda_updated(self, meeting_objects: Optional[List[Any]] = None, **kwargs) -> None:
        if meeting_objects is not None:
            self.cached_meetings = [m if isinstance(m, Meeting) else Meeting.from_dict(m) for m in meeting_objects]
        # Check if we should start/stop visual attention sampling
        active_study = self.get_active_study_event()
        from core.services.visual_attention_service import visual_attention_service
        if active_study:
            if not visual_attention_service.is_running:
                visual_attention_service.start_sampling()
        else:
            if visual_attention_service.is_running:
                visual_attention_service.stop_sampling()

    def _on_visual_attention_state(self, state: str = "focused_screen", is_distracted: bool = False, **kwargs) -> None:
        now = datetime.now(timezone.utc)
        active_study = self.get_active_study_event(now)
        if not active_study:
            return

        if state == "focused_desk_ipad":
            logger.debug(f"📖 [FocusGuardian] Visual AI detected iPad / Desk Notes study focus for '{active_study.title}'.")
            return

        if is_distracted:
            # Check cooldown rate limiting
            cooldown_min = int(self.config.get("study_distraction_cooldown_minutes", 5))
            if self.last_distraction_banner_time:
                elapsed_min = (now - self.last_distraction_banner_time).total_seconds() / 60.0
                if elapsed_min < cooldown_min:
                    return

            self.last_distraction_banner_time = now
            banner_data = {
                "uid": f"visual_distraction_{active_study.id}_{int(now.timestamp())}",
                "title": "Stay Focused! Eyes on your books 🦉",
                "provider": f"Study Guardian 📖 • {active_study.title}",
                "action_btn_text": "⚡ BACK TO STUDY 📚",
                "action_url": active_study.meeting_url or active_study.action_url or "https://calendar.apple.com",
                "pilot_type": PilotType.OWL.value,
                "animal": "owl",
                "outfit": "student",
                "theme_name": "Academic Purple",
                "is_travel": False,
                "is_quiet_reminder": False,
                "start_time": active_study.start_time,
                "end_time": active_study.end_time,
                "description": f"Scheduled study session '{active_study.title}' is in progress. Phone or off-task distraction detected by camera."
            }

            logger.info(f"🚨 >>> TRIGGER VISUAL DISTRACTION BANNER for \"{active_study.title}\" (Visual State: {state})")
            self.bus.publish("REMINDER_TRIGGERED", meeting=None, stage=0, event_dict=banner_data)
            self.bus.publish("STUDY_DISTRACTION_DETECTED", meeting_id=active_study.id, activity={"type": "visual", "state": state})

    def _on_device_activity(self, activity: Optional[DeviceActivity] = None, **kwargs) -> None:
        if activity is None:
            dev_type = kwargs.get("device_type", "unknown")
            state = kwargs.get("state", "active")
            app_name = kwargs.get("app_name")
            activity = DeviceActivity(device_type=dev_type, state=state, app_name=app_name)
        
        self.evaluate_activity(activity)

    def get_active_study_event(self, current_time: Optional[datetime] = None) -> Optional[Meeting]:
        """Finds any currently active Study or Academic Class event."""
        now = (current_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
        meetings = self.cached_meetings if self.cached_meetings is not None else calendar_service.get_upcoming_meetings()
        
        for m in meetings:
            if not m.is_study_event:
                continue
            if reminder_engine.is_meeting_active(m, now):
                return m
        return None

    def is_ipad_studying(self, current_time: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
        """
        Checks if iPad is currently considered in active study mode based on heartbeat and TTL.
        Returns (is_active, last_app_name).
        """
        from core.services.device_presence_service import device_presence_service
        now = (current_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
        ipad_record = device_presence_service.get_device_state("ipad")
        
        if not ipad_record:
            return False, None
        
        state = (ipad_record.get("state") or "").lower()
        if state not in ("studying", "active"):
            return False, None
            
        last_seen = ipad_record.get("last_seen")
        if not last_seen:
            return False, None
            
        if isinstance(last_seen, str):
            try:
                last_seen = datetime.fromisoformat(last_seen)
            except Exception:
                return False, None
                
        last_seen = last_seen.astimezone(timezone.utc)
        ttl_minutes = int(self.config.get("ipad_activity_ttl_minutes", 15))
        
        diff_sec = (now - last_seen).total_seconds()
        if diff_sec <= (ttl_minutes * 60):
            return True, ipad_record.get("app_name")
        
        return False, None

    def evaluate_activity(self, activity: DeviceActivity, current_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluates incoming device activity against active study events and focus rules.
        Returns the triggered banner payload if a distraction alert is fired, or None.
        """
        if not self.config.get("study_guardian_enabled", True):
            logger.debug("StudyFocusGuardian is disabled in configuration.")
            return None

        now = (current_time or activity.timestamp or datetime.now(timezone.utc)).astimezone(timezone.utc)
        dev_type = (activity.device_type or "").lower()
        state = (activity.state or "").lower()

        # 1. Handle iPad study heartbeat
        if dev_type == "ipad" and state in ("studying", "active"):
            app_str = f" ({activity.app_name})" if activity.app_name else ""
            logger.info(f"📖 [FocusGuardian] iPad study heartbeat registered{app_str}. Focus TTL extended.")
            return None

        # 2. Handle iPhone activity
        if dev_type == "iphone" and state == "distracted":
            active_study = self.get_active_study_event(now)
            if not active_study:
                logger.info(f"📱 [FocusGuardian] iPhone distraction received, but no active study event is scheduled right now. Ignoring.")
                return None

            # Check if iPad is currently active in a study session
            ipad_active, ipad_app = self.is_ipad_studying(now)
            if ipad_active:
                logger.info(f"🛡️ [FocusGuardian] iPhone distraction suppressed — iPad study session is active ({ipad_app or 'GoodNotes'}).")
                return None

            # Check cooldown rate limiting
            cooldown_min = int(self.config.get("study_distraction_cooldown_minutes", 5))
            if self.last_distraction_banner_time:
                elapsed_min = (now - self.last_distraction_banner_time).total_seconds() / 60.0
                if elapsed_min < cooldown_min:
                    logger.info(f"⏳ [FocusGuardian] Distraction banner on cooldown ({elapsed_min:.1f}m / {cooldown_min}m elapsed). Suppressing.")
                    return None

            # Trigger distraction alert banner!
            self.last_distraction_banner_time = now
            banner_data = self._create_distraction_banner_payload(active_study, activity)
            
            logger.info(f"🚨 >>> TRIGGER STUDY DISTRACTION BANNER for \"{active_study.title}\" (Phone: {activity.app_name or 'Distracted'})")
            
            # Publish to EventBus
            self.bus.publish("REMINDER_TRIGGERED", meeting=None, stage=0, event_dict=banner_data)
            self.bus.publish("STUDY_DISTRACTION_DETECTED", meeting_id=active_study.id, activity=activity.to_dict())
            
            return banner_data

        return None

    def _create_distraction_banner_payload(self, study_meeting: Meeting, activity: DeviceActivity) -> Dict[str, Any]:
        """Builds a customized Meeting dictionary for the Owl Pilot distraction banner."""
        app_text = f" ({activity.app_name})" if activity.app_name else ""
        return {
            "uid": f"distraction_{study_meeting.id}_{int(datetime.now(timezone.utc).timestamp())}",
            "title": f"Stay Focused! Put your phone away 🦉",
            "provider": f"Study Guardian 📖 • {study_meeting.title}",
            "action_btn_text": "⚡ BACK TO STUDY 📚",
            "action_url": study_meeting.meeting_url or study_meeting.action_url or "https://calendar.apple.com",
            "pilot_type": PilotType.OWL.value,
            "animal": "owl",
            "outfit": "student",
            "theme_name": "Academic Purple",
            "is_travel": False,
            "is_quiet_reminder": False,
            "start_time": study_meeting.start_time,
            "end_time": study_meeting.end_time,
            "description": f"Scheduled study session '{study_meeting.title}' is currently ongoing. Distraction detected on phone{app_text}."
        }


# Global singleton instance
study_focus_guardian = StudyFocusGuardian()
