from datetime import datetime
from typing import Optional, Dict, Any
from core.domain.models import format_duration

class TrayViewModel:
    @staticmethod
    def get_status_bar_title(next_m: Any, now: datetime, mode: str, max_lookahead_min: int) -> str:
        """Formats the tray status title dynamically based on current meeting and config."""
        if not next_m:
            return "🦆" if mode == "icon_only" else "🦆 QuakMeeting"

        if now.tzinfo is None:
            now = now.astimezone()

        is_dict = isinstance(next_m, dict)
        get_val = lambda key, default=None: next_m.get(key, default) if is_dict else getattr(next_m, key, default)

        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}
        p_type = get_val("pilot_type", "duck")
        icon_prefix = icon_map.get(p_type, "🦆")

        if mode == "icon_only":
            return icon_prefix

        start_dt = get_val("start_time")
        if isinstance(start_dt, datetime) and start_dt.tzinfo is None:
            start_dt = start_dt.astimezone()

        end_dt = get_val("end_time")
        if isinstance(end_dt, datetime) and end_dt.tzinfo is None:
            end_dt = end_dt.astimezone()

        dep_dt = get_val("departure_time")
        if isinstance(dep_dt, datetime) and dep_dt.tzinfo is None:
            dep_dt = dep_dt.astimezone()

        travel_min = get_val("travel_time_minutes")
        m_title = (get_val("title") or "Event").strip()
        title_short = m_title[:14] + "…" if len(m_title) > 14 else m_title

        start_str = start_dt.astimezone().strftime("%H:%M") if isinstance(start_dt, datetime) else "--:--"

        if mode == "event_time":
            if travel_min:
                dur_str = format_duration(travel_min)
                return f"{icon_prefix} {start_str} {title_short} (~{dur_str})"
            return f"{icon_prefix} {start_str} {title_short}"

        elif mode == "time_only":
            if isinstance(start_dt, datetime):
                diff_m = int(round((start_dt - now).total_seconds() / 60.0))
                if 0 < diff_m <= max_lookahead_min:
                    if diff_m >= 60:
                        hrs = diff_m // 60
                        mins = diff_m % 60
                        t_part = f"{hrs}h" if mins == 0 else f"{hrs}h{mins:02d}m"
                        return f"{icon_prefix} {start_str} (in {t_part})"
                    return f"{icon_prefix} {start_str} (in {diff_m}m)"
                elif diff_m == 0:
                    return f"{icon_prefix} {start_str} (Now!)"
                elif end_dt and isinstance(end_dt, datetime) and start_dt <= now < end_dt:
                    return f"{icon_prefix} {start_str} (Active)"
            return f"{icon_prefix} {start_str}"

        else: # "countdown" (Default & Most Informative)
            # 1. Check Departure / Leave Time for travel events
            if dep_dt and isinstance(dep_dt, datetime):
                diff_dep = int(round((dep_dt - now).total_seconds() / 60.0))
                if 0 < diff_dep <= max_lookahead_min:
                    return f"{icon_prefix} Leave in {format_duration(diff_dep)} ({title_short})"
                elif -10 <= diff_dep <= 0:
                    return f"🚨 {icon_prefix} Leave NOW! ({title_short})"
                elif diff_dep > max_lookahead_min:
                    return f"{icon_prefix} {start_str} {title_short}"

            # 2. Check Event Start Time
            if isinstance(start_dt, datetime):
                diff_start = int(round((start_dt - now).total_seconds() / 60.0))
                if 0 < diff_start <= max_lookahead_min:
                    return f"{icon_prefix} in {format_duration(diff_start)}: {title_short}"
                elif diff_start == 0:
                    return f"🔔 {icon_prefix} Starting NOW: {title_short}"
                elif end_dt and isinstance(end_dt, datetime) and start_dt <= now < end_dt:
                    diff_end = int(round((end_dt - now).total_seconds() / 60.0))
                    return f"🟢 {icon_prefix} {title_short} ({format_duration(diff_end)} left)"
                elif diff_start > max_lookahead_min:
                    return f"{icon_prefix} {start_str} {title_short}"

            return f"{icon_prefix} {start_str} {title_short}"
