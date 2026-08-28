"""
Reminder Engine for QuakMeeting.
Calculates multi-stage notification windows (e.g. 45m, 30m, 20m, 10m, 5m, 2m, 0m),
handles snooze timers, immediate first-time triggers for soon-starting events,
departure time triggers for travel/transit events, and publishes REMINDER_TRIGGERED events via EventBus.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Set, Dict, Optional, Tuple
from core.domain.models import Meeting
from core.services.event_bus import event_bus, EventBus
from core.services.config_service import config_service, ConfigService
from core.services.arrival_service import arrival_service, ArrivalService
from core.services.state_store import NotifiedStateStore
from core.logger import setup_logging

logger = logging.getLogger("QuakMeeting.ReminderEngine")

class ReminderEngine:
    """Calculates reminder triggers for meetings based on configurable stage intervals, arrival status, and travel ETA."""

    def __init__(self, config: Optional[ConfigService] = None, bus: Optional[EventBus] = None):
        self.config = config or config_service
        self.bus = bus or event_bus
        self._state_store = NotifiedStateStore()
        self.notified_stage_keys: Set[str] = self._state_store.load()

    def _add_notified_key(self, key: str) -> None:
        self.notified_stage_keys.add(key)
        self._state_store.add(key)

    def mark_arrived(self, meeting_id: str) -> None:
        """Marks meeting as arrived, suppressing all remaining reminder stages for it."""
        arrival_service.mark_arrived(meeting_id)
        # Suppress all future keys for this meeting
        for s in range(0, 60):
            self._add_notified_key(f"{meeting_id}_stage_{s}")
        self._add_notified_key(f"{meeting_id}_departure_alert")
        logger.info(f"Suppressed future reminders for arrived event: {meeting_id}")

    def reset_state(self) -> None:
        """Clear fired notifications cache (useful for testing or daily reset)."""
        self.notified_stage_keys.clear()
        self._state_store._state.clear()
        self._state_store.force_save()

    def check_and_notify(self, current_time: Optional[datetime] = None) -> List[Tuple[Meeting, int]]:
        """
        Convenience method that fetches upcoming meetings from calendar_service and evaluates them.
        """
        from core.services.calendar_service import calendar_service
        meetings = calendar_service.get_upcoming_meetings()
        return self.evaluate_meetings(meetings, current_time=current_time)

    def is_meeting_active(self, m: Meeting, now: datetime) -> bool:
        """Determines if the meeting is currently active and taking user's attention."""
        from datetime import timezone
        if now.tzinfo is None:
            now = now.astimezone(timezone.utc)
        else:
            now = now.astimezone(timezone.utc)
            
        if m.is_travel and m.departure_time:
            end = m.end_time or m.start_time or (m.departure_time + timedelta(minutes=60))
            if m.departure_time <= now <= end:
                return True
        if m.start_time and m.end_time:
            if m.start_time <= now <= m.end_time:
                return True
        elif m.start_time:
            diff = (now - m.start_time).total_seconds() / 60.0
            if 0 <= diff <= 45:
                return True
        return False

    def get_stages_for_meeting(self, meeting: Meeting) -> List[int]:
        """Retrieve configured stage intervals (minutes before start) for a given meeting type."""
        if meeting.is_travel:
            stages = list(self.config.get("travel_reminder_stages", [45, 30, 15, 5, 2, 0]))
        elif meeting.event_type == "video_meeting":
            stages = list(self.config.get("meeting_reminder_stages", [20, 10, 5, 2, 0]))
        else:
            stages = list(self.config.get("general_reminder_stages", [20, 10, 5, 2, 0]))

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

    def has_notified_meeting(self, base_key: str) -> bool:
        """Checks if any stage has already been notified for this meeting schedule revision."""
        prefix = f"{base_key}_"
        return any(k.startswith(prefix) for k in self.notified_stage_keys)

    def evaluate_meetings(self, meetings: List[Meeting], current_time: Optional[datetime] = None) -> List[Tuple[Meeting, int]]:
        """
        Evaluate all upcoming meetings against notification windows and departure times.
        Returns a list of (meeting, triggered_stage) tuples and publishes REMINDER_TRIGGERED events.
        """
        from datetime import timezone
        if current_time:
            now = current_time.astimezone(timezone.utc) if current_time.tzinfo is None else current_time.astimezone(timezone.utc)
        else:
            now = datetime.now(timezone.utc)
        triggered_events = []

        if not meetings:
            logger.debug(f"[{now.astimezone().strftime('%H:%M:%S')}] No events to evaluate.")
            return []

        # Determine if there are currently active meetings taking user's attention
        has_active_meeting = any(self.is_meeting_active(m, now) for m in meetings)

        logger.info(f"📊 [Scanner] Evaluating {len(meetings)} events at {now.astimezone().strftime('%H:%M:%S')} (Busy: {has_active_meeting})...")

        for m in meetings:
            if m.is_all_day:
                continue
            if not m.start_time:
                continue

            # Check if user already arrived (manually or via Wi-Fi/Active app)
            if arrival_service.is_meeting_arrived(m):
                logger.info(f"  ✓ \"{m.title}\" ({m.provider}) | Arrived / Active. Suppressed.")
                continue

            # Determine reference target time and label:
            # - For travel/transit events with ETA: stages are relative to DEPARTURE (leave) time
            # - For video meetings & regular events: stages are relative to START time
            is_departure_mode = bool(m.is_travel and m.departure_time)
            target_time = m.departure_time if is_departure_mode else m.start_time

            # State key timestamp (revision hash)
            rev_ts = int(target_time.timestamp())
            base_key = f"{m.id}_{rev_ts}"

            # Prune obsolete keys for this meeting
            if m.uid:
                keys_to_remove = [k for k in self.notified_stage_keys if k.startswith(f"{m.uid}_") and not k.startswith(base_key)]
                for k in keys_to_remove:
                    self.notified_stage_keys.remove(k)
                    self._state_store.remove(k)
                    logger.info(f"Pruned obsolete reminder state for rescheduled event: {k}")

            diff_min = (target_time - now).total_seconds() / 60.0

            # If event is on a future date and more than 3 hours away, do not trigger reminders today
            if m.start_time.astimezone().date() > now.astimezone().date() and diff_min > 180:
                continue

            start_str = m.start_time.astimezone().strftime("%H:%M")
            dep_str = m.departure_time.astimezone().strftime("%H:%M") if m.departure_time else ""
            stages = self.get_stages_for_meeting(m)

            matched_stage = None

            # 1. Evaluate Multi-Stage Intervals relative to target time (Departure vs Start)
            for stage in stages:
                stage_key = f"{base_key}_dep_stage_{stage}" if is_departure_mode else f"{base_key}_stage_{stage}"
                if self.is_within_stage_window(diff_min, stage):
                    if stage_key not in self.notified_stage_keys:
                        matched_stage = stage
                        self._add_notified_key(stage_key)

                        # Apply busy mode logic
                        if has_active_meeting and not self.is_meeting_active(m, now):
                            if stage > 10:
                                logger.info(f"🔇 Suppressed stage {stage} reminder for '{m.title}' (User is busy).")
                                continue

                        m_triggered = Meeting.from_dict(m.to_dict())
                        m_triggered.reminder_stage = stage

                        if has_active_meeting and not self.is_meeting_active(m, now) and stage > 0:
                            m_triggered.is_quiet_reminder = True
                            logger.info(f"🤫 Downgrading to quiet reminder for '{m.title}' at stage {stage} (User is busy).")

                        triggered_events.append((m_triggered, stage))

                        if is_departure_mode:
                            stage_label = "LEAVE NOW (0m)" if stage == 0 else f"leave in {stage}m"
                            logger.info(f"🚨 >>> TRIGGER DEPARTURE BANNER [{stage_label}] for \"{m.title}\" (Leave at {dep_str}, Event at {start_str}, diff={diff_min:+.1f}m)")
                        else:
                            stage_label = "at start (0m)" if stage == 0 else f"{stage}m ahead"
                            logger.info(f"🔔 >>> TRIGGER BANNER [{stage_label}] for \"{m.title}\" ({m.provider}, at {start_str}, diff={diff_min:+.1f}m)")

                        self.bus.publish("REMINDER_TRIGGERED", meeting=m_triggered, stage=stage)
                        break

            # 2. Fallback: If target time is imminent (<= 5 min) or in progress and has NEVER been notified
            if matched_stage is None and not self.has_notified_meeting(base_key):
                if -3.5 <= diff_min <= 5.0:
                    fallback_stage = max(0, round(diff_min))
                    stage_key = f"{base_key}_dep_stage_{fallback_stage}" if is_departure_mode else f"{base_key}_stage_{fallback_stage}"
                    self._add_notified_key(stage_key)

                    m_triggered = Meeting.from_dict(m.to_dict())
                    m_triggered.reminder_stage = fallback_stage

                    if has_active_meeting and not self.is_meeting_active(m, now) and fallback_stage > 0:
                        m_triggered.is_quiet_reminder = True
                        logger.info(f"🤫 Downgrading fallback to quiet reminder for '{m.title}' at stage {fallback_stage} (User is busy).")

                    triggered_events.append((m_triggered, fallback_stage))

                    if is_departure_mode:
                        stage_label = "DEPART NOW" if fallback_stage == 0 else f"leave imminent ({fallback_stage}m)"
                        logger.info(f"🚨 >>> TRIGGER IMMEDIATE DEPARTURE BANNER [{stage_label}] for \"{m.title}\" (Leave at {dep_str}, Event at {start_str}, diff={diff_min:+.1f}m)")
                    else:
                        stage_label = "at start (0m)" if fallback_stage == 0 else f"imminent ({fallback_stage}m)"
                        logger.info(f"🔔 >>> TRIGGER IMMEDIATE BANNER [{stage_label}] for \"{m.title}\" ({m.provider}, at {start_str}, diff={diff_min:+.1f}m)")

                    self.bus.publish("REMINDER_TRIGGERED", meeting=m_triggered, stage=fallback_stage)
                    matched_stage = fallback_stage

            if not matched_stage:
                if is_departure_mode:
                    logger.info(f"  🚗 \"{m.title}\" (Travel) | Leave: {dep_str} | Event: {start_str} | Leave In: {diff_min:+.1f} min | Stages: {stages}")
                else:
                    logger.info(f"  📅 \"{m.title}\" ({m.provider}) | Start: {start_str} | In: {diff_min:+.1f} min | Stages: {stages}")

        return triggered_events

# Global shared instance
reminder_engine = ReminderEngine()
