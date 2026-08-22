"""
Native macOS EventKit Calendar Provider for QuakMeeting.
Uses PyObjC EventKit (EKEventStore) for fast, low-overhead direct API access.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.domain.models import Meeting
from core.domain.classifier import EventClassifier
from core.services.config_service import config_service, ConfigService
from .base import BaseCalendarProvider

logger = logging.getLogger("QuakMeeting.EventKitProvider")

class EventKitCalendarProvider(BaseCalendarProvider):
    """Calendar provider using native macOS EventKit."""

    def __init__(self, config: Optional[ConfigService] = None):
        self.config = config or config_service
        self._store = None
        self._is_authorized = None

    def _get_store(self):
        if self._store is None:
            try:
                import EventKit
                self._store = EventKit.EKEventStore.alloc().init()
            except ImportError:
                self._store = None
        return self._store

    def is_available(self) -> bool:
        return self._get_store() is not None

    def fetch_events(self, start_offset_hours: int = 2, end_offset_hours: int = 24) -> List[Meeting]:
        store = self._get_store()
        if not store:
            return []

        import EventKit
        import Foundation

        now = datetime.now()
        start_date = Foundation.NSDate.dateWithTimeIntervalSinceNow_(-start_offset_hours * 3600)
        end_date = Foundation.NSDate.dateWithTimeIntervalSinceNow_(end_offset_hours * 3600)

        ignored = set(self.config.get("ignored_calendars", []))
        all_cals = store.calendarsForEntityType_(EventKit.EKEntityTypeEvent)
        active_cals = [c for c in all_cals if str(c.title()) not in ignored]

        predicate = store.predicateForEventsWithStartDate_endDate_calendars_(start_date, end_date, active_cals)
        ek_events = store.eventsMatchingPredicate_(predicate)

        meetings: List[Meeting] = []
        custom_kw = self.config.get("custom_keywords", {})

        for ev in ek_events:
            title = str(ev.title() or "Senza Titolo")
            loc = str(ev.location() or "")
            desc = str(ev.notes() or "")
            url_str = str(ev.URL().absoluteString()) if ev.URL() else ""

            meeting_url = (
                EventClassifier.extract_meeting_url(url_str) or 
                EventClassifier.extract_meeting_url(loc) or 
                EventClassifier.extract_meeting_url(desc)
            )

            # Convert NSDate to python datetime
            start_ts = ev.startDate().timeIntervalSince1970()
            start_dt = datetime.fromtimestamp(start_ts)

            end_dt = None
            if ev.endDate():
                end_ts = ev.endDate().timeIntervalSince1970()
                end_dt = datetime.fromtimestamp(end_ts)

            meta = EventClassifier.classify(title, loc, desc, meeting_url, custom_kw)

            meeting = Meeting(
                title=title,
                start_time=start_dt,
                end_time=end_dt,
                meeting_url=meeting_url,
                location=loc,
                description=desc,
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
        store = self._get_store()
        if not store:
            return []

        import EventKit
        ignored = set(self.config.get("ignored_calendars", []))
        all_cals = store.calendarsForEntityType_(EventKit.EKEntityTypeEvent)
        return [{"name": str(c.title()), "enabled": (str(c.title()) not in ignored)} for c in all_cals]
