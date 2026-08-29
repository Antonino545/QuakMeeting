"""
Common Banner Formatting & Time Differentials for QuakMeeting.
Provides unified countdown strings, urgency calculations, and travel formatting.
"""
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

MODE_ICONS = {
    "transit": "🚆",
    "driving": "🚗",
    "walking": "🚶",
    "cycling": "🚲",
    "plane": "✈️"
}

def format_travel_duration(minutes: Optional[int]) -> str:
    mins = minutes or 20
    if mins >= 60:
        h = mins // 60
        m = mins % 60
        return f"{h}h {m}m" if m > 0 else f"{h}h"
    return f"{mins} min"

def compute_countdown_text(
    meeting_data: Dict[str, Any],
    start_time: Optional[datetime],
    departure_time: Optional[datetime],
    travel_time_minutes: Optional[int],
    is_travel: bool,
    transport_mode: str,
    classroom: Optional[str],
    pilot_type: Optional[str],
    provider: Optional[str],
    title: Optional[str]
) -> Tuple[str, bool]:
    """Computes the current countdown string and whether it is urgent."""
    countdown_text = "⏰ Upcoming Alert"
    is_urgent = False
    mode_icon = MODE_ICONS.get(transport_mode, "🚆")
    
    is_self_study = (
        meeting_data.get("event_type") == "study"
        or "STUDY" in (provider or "").upper()
        or "STUDIARE" in (title or "").upper()
        or (not classroom and "STUDY" in (title or "").upper())
    )

    if start_time:
        now = datetime.now().astimezone()
        diff = (start_time - now).total_seconds()

        if is_travel and departure_time:
            dep_diff = (departure_time - now).total_seconds()
            dep_mins = int(dep_diff // 60)
            dep_time_str = departure_time.astimezone().strftime("%H:%M")
            dur_str = format_travel_duration(travel_time_minutes)

            if dep_diff <= 0:
                late_min = abs(int(dep_diff // 60))
                countdown_text = f"🚨 {mode_icon} LATE BY {late_min}m • LEAVE NOW!" if late_min > 0 else f"🚨 {mode_icon} DEPART NOW!"
                is_urgent = True
            elif dep_mins <= 10:
                countdown_text = f"⏳ {mode_icon} Leave in {dep_mins}m ({dep_time_str})"
                is_urgent = True
            else:
                countdown_text = f"{mode_icon} Leave at {dep_time_str} (~{dur_str})"
        elif diff > 0:
            mins = int(diff // 60)
            secs = int(diff % 60)
            if is_self_study:
                if mins >= 15:
                    countdown_text = f"📖 In {mins}m • Study Time"
                elif mins >= 5:
                    countdown_text = f"⏳ In {mins}m • Open Books"
                elif mins >= 1:
                    countdown_text = f"⚡ In {mins}m • Time to Study!"
                    is_urgent = True
                else:
                    countdown_text = f"⏳ In {secs}s • Study Starting!"
                    is_urgent = True
            elif classroom:
                if mins >= 10:
                    countdown_text = f"🎓 Lesson in {mins}m • {classroom}"
                elif mins >= 1:
                    countdown_text = f"⏳ Class in {mins}m • {classroom}"
                    is_urgent = True
                else:
                    countdown_text = f"🚨 Class starting now • {classroom}"
                    is_urgent = True
            elif is_travel:
                if mins >= 30:
                    countdown_text = f"{mode_icon} In {mins}m • Travel Notice"
                elif mins >= 15:
                    countdown_text = f"{mode_icon} In {mins}m • Prepare to Leave"
                else:
                    countdown_text = f"🚨 {mode_icon} Leave Now!"
                    is_urgent = True
            else:
                if mins >= 15:
                    countdown_text = f"⏰ In {mins}m • Early Alert"
                elif mins >= 5:
                    countdown_text = f"⏳ In {mins}m • Get Ready"
                elif mins >= 1:
                    countdown_text = f"🚀 In {mins}m • Almost Time!"
                    is_urgent = True
                else:
                    countdown_text = f"⏳ In {secs}s • Starting Now!"
                    is_urgent = True
        elif diff > -1800:
            late_mins = abs(int(diff // 60))
            if pilot_type == "owl" and is_self_study:
                countdown_text = f"🚨 STUDY OVERDUE BY {late_mins}m • DO IT!" if late_mins > 0 else "📖 TIME TO STUDY • DO IT!"
            elif classroom:
                countdown_text = f"🔴 LATE BY {late_mins}m • {classroom}" if late_mins > 0 else f"🔴 CLASS STARTED • {classroom}"
            else:
                countdown_text = f"🔴 LATE BY {late_mins}m • IN PROGRESS" if late_mins > 0 else "🔴 IN PROGRESS NOW"
            is_urgent = True

    return countdown_text, is_urgent
