"""
Event State Machine and Lifecycle Transitions for QuakMeeting.
Replaces scattered boolean conditions with explicit deterministic lifecycle states.
"""
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from core.domain.clock import Clock, system_clock


class EventState(str, Enum):
    """Lifecycle states for a calendar event."""
    UPCOMING = "upcoming"              # Distant event (> prepare window)
    PREPARE = "prepare"                # Advance preparation window (e.g. 15-45m ahead)
    TIME_TO_LEAVE = "time_to_leave"    # Departure window reached (leave now or soon)
    ARRIVING = "arriving"              # En route to venue (between departure and start)
    ARRIVED = "arrived"                # Arrived at venue (on-site Wi-Fi or manual check-in)
    ACTIVE = "active"                  # Event is currently underway (or in video call)
    COMPLETED = "completed"            # Event has finished
    DISMISSED = "dismissed"            # Acknowledged / dismissed by user
    CANCELLED = "cancelled"            # Cancelled event


def resolve_event_state(
    event: Any,
    clock: Optional[Clock] = None
) -> EventState:
    """
    Computes the current lifecycle EventState for an event against the provided clock.
    Works with CalendarEvent or legacy Meeting instances.
    """
    current_clock = clock or system_clock
    now = current_clock.now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    # 1. Check cancelled
    if getattr(event, "is_cancelled", False):
        return EventState.CANCELLED

    # Extract temporal timestamps
    start_dt = getattr(event, "start_time", None)
    end_dt = getattr(event, "end_time", None)
    dep_dt = getattr(event, "departure_time", None)
    is_travel = bool(getattr(event, "is_travel", False))
    is_arrived = bool(getattr(event, "is_arrived", False))
    arrival_reason = getattr(event, "arrival_reason", None) or ""

    if start_dt and start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    elif start_dt:
        start_dt = start_dt.astimezone(timezone.utc)

    if end_dt and end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    elif end_dt:
        end_dt = end_dt.astimezone(timezone.utc)

    if dep_dt and dep_dt.tzinfo is None:
        dep_dt = dep_dt.replace(tzinfo=timezone.utc)
    elif dep_dt:
        dep_dt = dep_dt.astimezone(timezone.utc)

    # Fallback if no start_time
    if not start_dt:
        return EventState.UPCOMING

    # 2. Check if event has ended
    if end_dt and now >= end_dt:
        return EventState.COMPLETED
    if not end_dt and (now - start_dt).total_seconds() > 45 * 60:
        return EventState.COMPLETED

    # 3. Active video call presence signal
    if arrival_reason.startswith("call:"):
        return EventState.ACTIVE

    # 4. Check if event is underway (start <= now < end)
    if end_dt and start_dt <= now < end_dt:
        return EventState.ACTIVE
    if not end_dt and start_dt <= now and (now - start_dt).total_seconds() <= 45 * 60:
        return EventState.ACTIVE

    # 5. Check arrived presence signal (reached early before start)
    if is_arrived:
        return EventState.ARRIVED

    # 6. Travel-aware departure transitions
    if is_travel and dep_dt:
        diff_dep_sec = (dep_dt - now).total_seconds()
        diff_dep_min = diff_dep_sec / 60.0

        if diff_dep_sec <= 0 and now < start_dt:
            # Past departure time, traveling toward start location
            return EventState.ARRIVING
        elif 0 < diff_dep_min <= 15:
            # Imminent departure window
            return EventState.TIME_TO_LEAVE
        elif 15 < diff_dep_min <= 45:
            # Advance preparation window before leaving
            return EventState.PREPARE
        else:
            return EventState.UPCOMING

    # 7. Standard event transitions
    diff_start_min = (start_dt - now).total_seconds() / 60.0
    if 0 < diff_start_min <= 20:
        return EventState.PREPARE
    elif diff_start_min > 20:
        return EventState.UPCOMING

    return EventState.UPCOMING
