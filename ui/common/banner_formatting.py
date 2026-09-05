"""
Common Banner Formatting & Time Differentials for QuakMeeting.
Provides unified countdown strings, urgency calculations, and travel formatting in English & Italian.
"""
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from core.services.language_service import t, get_active_language

MODE_ICONS = {
    "transit": "🚆",
    "driving": "🚗",
    "walking": "🚶",
    "cycling": "🚲",
    "plane": "✈️"
}

def format_travel_duration(minutes: Optional[int], lang: Optional[str] = None) -> str:
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
    title: Optional[str],
    lang: Optional[str] = None
) -> Tuple[str, bool]:
    """Computes the current countdown string and whether it is urgent."""
    active_lang = lang or get_active_language()
    countdown_text = f"⏰ {t('upcoming_alert', lang=active_lang)}"
    is_urgent = False
    mode_icon = MODE_ICONS.get(transport_mode, "🚆")
    
    is_self_study = (
        meeting_data.get("event_type") == "study"
        or meeting_data.get("category") == "study"
        or "STUDY" in (provider or "").upper()
        or "STUDIARE" in (title or "").upper()
        or "STUDIO" in (title or "").upper()
        or "STUDY" in (title or "").upper()
        or "SELF STUDY" in (title or "").upper()
        or "SELF-STUDY" in (title or "").upper()
        or "RIPASSO" in (title or "").upper()
        or "COMPITI" in (title or "").upper()
        or "HOMEWORK" in (title or "").upper()
    )

    if start_time:
        now = datetime.now().astimezone()
        diff = (start_time - now).total_seconds()

        if is_travel and departure_time:
            dep_diff = (departure_time - now).total_seconds()
            dep_mins = int(dep_diff // 60)
            dep_time_str = departure_time.astimezone().strftime("%H:%M")
            dur_str = format_travel_duration(travel_time_minutes, lang=active_lang)

            if dep_diff <= 0:
                late_min = abs(int(dep_diff // 60))
                if late_min > 0:
                    countdown_text = f"🚨 {mode_icon} {t('badge_travel_late_by', lang=active_lang, mins=late_min)}"
                else:
                    countdown_text = f"🚨 {mode_icon} {t('badge_travel_depart_now', lang=active_lang)}"
                is_urgent = True
            elif dep_mins <= 10:
                countdown_text = f"⏳ {mode_icon} {t('badge_travel_leave_in', lang=active_lang, mins=dep_mins, time=dep_time_str)}"
                is_urgent = True
            else:
                countdown_text = f"{mode_icon} {t('badge_travel_leave_at', lang=active_lang, time=dep_time_str, duration=dur_str)}"
        elif diff > 0:
            mins = int(diff // 60)
            secs = int(diff % 60)
            if is_self_study:
                if mins >= 15:
                    countdown_text = f"📖 {t('badge_study_in_mins', lang=active_lang, mins=mins)}"
                elif mins >= 5:
                    countdown_text = f"⏳ {t('badge_study_open_books', lang=active_lang, mins=mins)}"
                elif mins >= 1:
                    countdown_text = f"⚡ {t('badge_study_time_to_study', lang=active_lang, mins=mins)}"
                    is_urgent = True
                else:
                    countdown_text = f"⏳ {t('badge_study_starting', lang=active_lang)}"
                    is_urgent = True
            elif classroom:
                if mins >= 10:
                    countdown_text = f"🎓 {t('badge_class_in_mins', lang=active_lang, mins=mins, classroom=classroom)}"
                elif mins >= 1:
                    countdown_text = f"⏳ {t('badge_class_soon', lang=active_lang, mins=mins, classroom=classroom)}"
                    is_urgent = True
                else:
                    countdown_text = f"🚨 {t('badge_class_starting', lang=active_lang, classroom=classroom)}"
                    is_urgent = True
            elif is_travel:
                if mins >= 30:
                    countdown_text = f"{mode_icon} {t('badge_travel_in_mins', lang=active_lang, mins=mins)}"
                elif mins >= 15:
                    countdown_text = f"{mode_icon} {t('badge_travel_prepare', lang=active_lang, mins=mins)}"
                else:
                    countdown_text = f"🚨 {mode_icon} {t('badge_travel_leave_now', lang=active_lang)}"
                    is_urgent = True
            else:
                if mins >= 15:
                    countdown_text = f"⏰ {t('badge_in_mins_early', lang=active_lang, mins=mins)}"
                elif mins >= 5:
                    countdown_text = f"⏳ {t('badge_in_mins_ready', lang=active_lang, mins=mins)}"
                elif mins >= 1:
                    countdown_text = f"🚀 {t('badge_in_mins_almost', lang=active_lang, mins=mins)}"
                    is_urgent = True
                else:
                    countdown_text = f"⏳ {t('badge_in_secs_now', lang=active_lang)}"
                    is_urgent = True
        elif diff > -1800:
            late_mins = abs(int(diff // 60))
            if pilot_type == "owl" and is_self_study:
                if late_mins > 0:
                    countdown_text = f"🚨 {t('badge_late_study_by', lang=active_lang, mins=late_mins)}"
                else:
                    countdown_text = f"📖 {t('badge_study_now', lang=active_lang)}"
            elif classroom:
                if late_mins > 0:
                    countdown_text = f"🔴 {t('badge_late_class_by', lang=active_lang, mins=late_mins, classroom=classroom)}"
                else:
                    countdown_text = f"🔴 {t('badge_class_started', lang=active_lang, classroom=classroom)}"
            else:
                if late_mins > 0:
                    countdown_text = f"🔴 {t('badge_late_by_mins', lang=active_lang, mins=late_mins)}"
                else:
                    countdown_text = f"🔴 {t('badge_in_progress', lang=active_lang)}"
            is_urgent = True

    return countdown_text, is_urgent
