"""
AppleScript-based Calendar Provider for QuakMeeting.
Queries Calendar.app via osascript.
"""
import subprocess
import logging
from typing import List, Dict, Any, Optional
from core.domain.models import Meeting
from core.domain.classifier import EventClassifier
from core.services.config_service import config_service, ConfigService
from .base import BaseCalendarProvider

logger = logging.getLogger("QuakMeeting.AppleScriptProvider")

class AppleScriptCalendarProvider(BaseCalendarProvider):
    """Calendar provider utilizing AppleScript osascript for macOS Calendar.app."""

    def __init__(self, config: Optional[ConfigService] = None):
        self.config = config or config_service

    def fetch_events(self, start_offset_hours: int = 2, end_offset_hours: int = 24) -> List[Meeting]:
        ignored = self.config.get("ignored_calendars", [
            "Festività in Italia", "Birthdays", "Scheduled Reminders", "Siri Suggestions"
        ])
        
        if ignored:
            cond_parts = [f'cName is not "{cal}"' for cal in ignored]
            cal_filter_cond = " and ".join(cond_parts)
        else:
            cal_filter_cond = "true"

        script = f'''
        tell application "Calendar"
            set todayStart to (current date) - ({start_offset_hours} * hours)
            set todayEnd to (current date) + ({end_offset_hours} * hours)
            set outEvents to {{}}
            repeat with cal in calendars
                set cName to name of cal
                if {cal_filter_cond} then
                    try
                        set evs to (every event of cal whose start date >= todayStart and start date <= todayEnd)
                        repeat with ev in evs
                            set t to summary of ev
                            set s to (start date of ev) as string
                            set e to (end date of ev) as string
                            set u to ""
                            try
                                set u to url of ev
                            end try
                            set l to ""
                            try
                                set l to location of ev
                            end try
                            set d to ""
                            try
                                set d to description of ev
                            end try
                            set end of outEvents to (t & "<|>" & s & "<|>" & e & "<|>" & u & "<|>" & l & "<|>" & d)
                        end repeat
                    end try
                end if
            end repeat
            set AppleScript's text item delimiters to "
###EVENT###
"
            return outEvents as string
        end tell
        '''
        
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, errors='replace', timeout=90)
            if res.returncode != 0 or not res.stdout.strip():
                return []
        except Exception as e:
            logger.error(f"Error executing AppleScript calendar fetch: {e}")
            return []
            
        raw_events = res.stdout.strip().split('###EVENT###')
        meetings: List[Meeting] = []
        custom_kw = self.config.get("custom_keywords", {})
        
        for raw_ev in raw_events:
            parts = raw_ev.strip().split('<|>')
            if len(parts) < 6:
                continue
                
            title, start_str, end_str, url_raw, loc_raw, desc_raw = parts[:6]
            
            meeting_url = (
                EventClassifier.extract_meeting_url(url_raw) or 
                EventClassifier.extract_meeting_url(loc_raw) or 
                EventClassifier.extract_meeting_url(desc_raw)
            )
            
            start_dt = EventClassifier.parse_applescript_date(start_str)
            end_dt = EventClassifier.parse_applescript_date(end_str)
            
            if not start_dt:
                continue

            loc_clean = loc_raw if loc_raw != "missing value" else ""
            desc_clean = desc_raw if desc_raw != "missing value" else ""
            
            meta = EventClassifier.classify(title, loc_clean, desc_clean, meeting_url, custom_kw)
            
            meeting = Meeting(
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                meeting_url=meeting_url,
                location=loc_clean,
                description=desc_clean,
                event_type=meta["event_type"],
                pilot_type=meta["pilot_type"],
                provider=meta["provider"],
                action_btn_text=meta["action_btn_text"],
                action_url=meta["action_url"],
                theme_name=meta["theme_name"],
                is_travel=meta["is_travel"]
            )
            meetings.append(meeting)
            
        meetings.sort(key=lambda x: x.start_time)
        return meetings

    def get_available_calendars(self) -> List[Dict[str, Any]]:
        script = '''
        tell application "Calendar"
            set outCals to {}
            repeat with cal in calendars
                set end of outCals to (name of cal)
            end repeat
            set AppleScript's text item delimiters to "
"
            return outCals as string
        end tell
        '''
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, errors='replace', timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                cal_names = [line.strip() for line in res.stdout.strip().split('\n') if line.strip()]
                ignored = set(self.config.get("ignored_calendars", []))
                return [{"name": name, "enabled": (name not in ignored)} for name in cal_names]
        except Exception as e:
            logger.error(f"Error fetching calendars list: {e}")
        return []
