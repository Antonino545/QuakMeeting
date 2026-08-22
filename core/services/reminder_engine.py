"""
Reminder Engine for QuakMeeting.
Calculates multi-stage notification windows (e.g. 20m, 10m, 5m, 2m), handles snooze timers,
departure time triggers for travel/transit events, and publishes REMINDER_TRIGGERED events via EventBus.
"""
import logging
from datetime import datetime
from typing import List, Set, Dict, Optional, Tuple
from core.domain.models import Meeting
from core.services.event_bus import event_bus, EventBus
from core.services.config_service import config_service, ConfigService

logger = logging.getLogger("QuakMeeting.ReminderEngine")

class ReminderEngine:
    """Calculates reminder triggers for meetings based on configurable stage intervals and travel ETA."""

    def __init__(self, config: Optional[ConfigService] = None, bus: Optional[EventBus] = None):
        self.config = config or config_service
        self.bus = bus or event_bus
        self.notified_stage_keys: Set[str] = set()

    def reset_state(self) -> None:
        """Clear fired notifications cache (useful for testing or daily reset)."""
        self.notified_stage_keys.clear()

    def get_stages_for_meeting(self, meeting: Meeting) -> List[int]:
        """Retrieve configured stage intervals (minutes before start) for a given meeting type."""
        if meeting.is_travel:
            stages = self.config.get("travel_reminder_stages", [45, 30, 15, 5])
            if not stages:
                stages = [int(self.config.get("lead_time_travel_minutes", 35))]
        else:
            stages = self.config.get("meeting_reminder_stages", [20, 10, 5, 2])
            if not stages:
                stages = [int(self.config.get("lead_time_meeting_minutes", 6))]
        return sorted([int(s) for s in stages], reverse=True)

    def is_within_stage_window(self, diff_minutes: float, stage: int) -> bool:
        """
        Check if diff_minutes (start_time - now) falls within the trigger window for a stage.
        Stage window allows a tolerance of [-1.5, +0.8] minutes for standard stages,
        and [-2.0, +0.8] for stage 0 (at meeting start).
        """
        if stage == 0:
            return -2.0 <= diff_minutes <= 0.8
        return (stage - 1.5) <= diff_minutes <= (stage + 0.8)

    def evaluate_meetings(self, meetings: List[Meeting], current_time: Optional[datetime] = None) -> List[Tuple[Meeting, int]]:
        """
        Evaluate all upcoming meetings against notification windows and departure times.
        Returns a list of (meeting, triggered_stage) tuples and publishes REMINDER_TRIGGERED events.
        """
        now = current_time or datetime.now()
        triggered_events = []

        for m in meetings:
            if not m.start_time:
                continue

            diff_min = (m.start_time - now).total_seconds() / 60.0
            
            # 1. Check Departure Time (Time to Leave / Parti Ora!) for physical/transit events
            if m.departure_time and m.is_travel:
                dep_diff_min = (m.departure_time - now).total_seconds() / 60.0
                dep_key = f"{m.id}_departure_alert"
                # If now is within [-1.5, +1.0] of departure time
                if -1.5 <= dep_diff_min <= 1.0 and dep_key not in self.notified_stage_keys:
                    self.notified_stage_keys.add(dep_key)
                    m_dep = Meeting.from_dict(m.to_dict())
                    m_dep.reminder_stage = max(1, round((m.start_time - now).total_seconds() / 60.0))
                    triggered_events.append((m_dep, m_dep.reminder_stage))
                    logger.info(f"Triggering DEPARTURE REMINDER for '{m.title}' ({m.eta_text})")
                    self.bus.publish("REMINDER_TRIGGERED", meeting=m_dep, stage=m_dep.reminder_stage)
                    continue

            # 2. Check Standard Multi-Stage Intervals
            stages = self.get_stages_for_meeting(m)
            for stage in stages:
                stage_key = f"{m.id}_stage_{stage}"
                if self.is_within_stage_window(diff_min, stage):
                    if stage_key not in self.notified_stage_keys:
                        self.notified_stage_keys.add(stage_key)
                        m_triggered = Meeting.from_dict(m.to_dict())
                        m_triggered.reminder_stage = stage
                        triggered_events.append((m_triggered, stage))
                        logger.info(f"Triggering reminder ({stage}m before) for '{m.title}'")
                        self.bus.publish("REMINDER_TRIGGERED", meeting=m_triggered, stage=stage)
                        break

        return triggered_events

# Global shared instance
reminder_engine = ReminderEngine()
