"""
Reminder Engine for QuakMeeting.
Calculates multi-stage notification windows (e.g. 45m, 30m, 20m, 10m, 5m, 2m, 0m),
handles snooze timers, immediate first-time triggers for soon-starting events,
departure time triggers for travel/transit events, and publishes REMINDER_TRIGGERED events via EventBus.
"""
import logging
from datetime import datetime
from typing import List, Set, Dict, Optional, Tuple
from core.domain.models import Meeting
from core.services.event_bus import event_bus, EventBus
from core.services.config_service import config_service, ConfigService
from core.logger import setup_logging

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
            stages = list(self.config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        else:
            stages = list(self.config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
            
        # Ensure 0 (start time) is always checked unless empty
        if 0 not in stages:
            stages.append(0)
            
        return sorted([int(s) for s in stages], reverse=True)

    def is_within_stage_window(self, diff_minutes: float, stage: int) -> bool:
        """
        Check if diff_minutes (start_time - now) falls within the trigger window for a stage.
        Tolerance window ensures 15s-30s scanning loops never miss a trigger.
        For stage 0 (at start time): [-3.5 min, +1.2 min].
        For stage > 0: [stage - 1.8 min, stage + 1.2 min].
        """
        if stage == 0:
            return -3.5 <= diff_minutes <= 1.2
        return (stage - 1.8) <= diff_minutes <= (stage + 1.2)

    def has_notified_meeting(self, meeting_id: str) -> bool:
        """Checks if any stage has already been notified for this meeting."""
        prefix = f"{meeting_id}_"
        return any(k.startswith(prefix) for k in self.notified_stage_keys)

    def evaluate_meetings(self, meetings: List[Meeting], current_time: Optional[datetime] = None) -> List[Tuple[Meeting, int]]:
        """
        Evaluate all upcoming meetings against notification windows and departure times.
        Returns a list of (meeting, triggered_stage) tuples and publishes REMINDER_TRIGGERED events.
        """
        now = current_time or datetime.now()
        triggered_events = []

        if not meetings:
            logger.debug(f"[{now.strftime('%H:%M:%S')}] No events to evaluate.")
            return []

        logger.info(f"📊 [Scanner] Evaluating {len(meetings)} events at {now.strftime('%H:%M:%S')}...")

        for m in meetings:
            if not m.start_time:
                continue

            diff_min = (m.start_time - now).total_seconds() / 60.0
            start_str = m.start_time.strftime("%H:%M")
            stages = self.get_stages_for_meeting(m)
            
            # 1. Check Departure Time (Time to Leave) for physical/transit events
            if m.departure_time and m.is_travel:
                dep_diff_min = (m.departure_time - now).total_seconds() / 60.0
                dep_key = f"{m.id}_departure_alert"
                dep_str = m.departure_time.strftime("%H:%M")
                
                if -2.0 <= dep_diff_min <= 1.5 and dep_key not in self.notified_stage_keys:
                    self.notified_stage_keys.add(dep_key)
                    m_dep = Meeting.from_dict(m.to_dict())
                    m_dep.reminder_stage = max(0, round(diff_min))
                    triggered_events.append((m_dep, m_dep.reminder_stage))
                    logger.info(f"🚨 >>> TRIGGER DEPARTURE ALERT (Leave at {dep_str}) for \"{m.title}\" ({m.eta_text})")
                    self.bus.publish("REMINDER_TRIGGERED", meeting=m_dep, stage=m_dep.reminder_stage)
                    continue

            # 2. Check Standard Multi-Stage Intervals
            matched_stage = None
            for stage in stages:
                stage_key = f"{m.id}_stage_{stage}"
                if self.is_within_stage_window(diff_min, stage):
                    if stage_key not in self.notified_stage_keys:
                        matched_stage = stage
                        self.notified_stage_keys.add(stage_key)
                        m_triggered = Meeting.from_dict(m.to_dict())
                        m_triggered.reminder_stage = stage
                        triggered_events.append((m_triggered, stage))
                        
                        stage_label = f"at start (0m)" if stage == 0 else f"{stage}m ahead"
                        logger.info(f"🔔 >>> TRIGGER BANNER [{stage_label}] for \"{m.title}\" ({m.provider}, at {start_str}, diff={diff_min:+.1f}m)")
                        self.bus.publish("REMINDER_TRIGGERED", meeting=m_triggered, stage=stage)
                        break

            # 3. Fallback: If event is starting very soon (<= 5 min) or in progress and has NEVER been notified
            if matched_stage is None and not self.has_notified_meeting(m.id):
                if -3.5 <= diff_min <= 5.0:
                    fallback_stage = max(0, round(diff_min))
                    stage_key = f"{m.id}_stage_{fallback_stage}"
                    self.notified_stage_keys.add(stage_key)
                    m_triggered = Meeting.from_dict(m.to_dict())
                    m_triggered.reminder_stage = fallback_stage
                    triggered_events.append((m_triggered, fallback_stage))
                    
                    stage_label = f"at start (0m)" if fallback_stage == 0 else f"imminent ({fallback_stage}m)"
                    logger.info(f"🔔 >>> TRIGGER IMMEDIATE BANNER [{stage_label}] for \"{m.title}\" ({m.provider}, at {start_str}, diff={diff_min:+.1f}m)")
                    self.bus.publish("REMINDER_TRIGGERED", meeting=m_triggered, stage=fallback_stage)
                    matched_stage = fallback_stage

            if not matched_stage:
                logger.info(f"  📅 \"{m.title}\" ({m.provider}) | Start: {start_str} | In: {diff_min:+.1f} min | Stages: {stages}")

        return triggered_events

# Global shared instance
reminder_engine = ReminderEngine()
