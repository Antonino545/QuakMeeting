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
                import Foundation
                self._store = EventKit.EKEventStore.alloc().init()
                status = EventKit.EKEventStore.authorizationStatusForEntityType_(EventKit.EKEntityTypeEvent)
                # status: 0=NotDetermined, 1=Restricted, 2=Denied, 3=Authorized/FullAccess, 4=WriteOnly
                if status == 0:  # Only prompt user once if Not Determined
                    def completion(granted, error):
                        if granted:
                            from core.services.event_bus import event_bus
                            event_bus.publish_on_main("CALENDAR_NEEDS_SYNC")

                    if hasattr(self._store, "requestFullAccessToEventsWithCompletion_"):
                        self._store.requestFullAccessToEventsWithCompletion_(completion)
                    else:
                        self._store.requestAccessToEntityType_completion_(EventKit.EKEntityTypeEvent, completion)

                if status not in (0, 3, 4):  # Not Authorized and not pending
                    logger.warning(f"EventKit Calendar access status: {status}. If events are missing, check System Settings.")
                    
                from core.services.debounce_timer import DebounceTimer
                from core.services.event_bus import event_bus
                
                def _trigger_sync():
                    event_bus.publish_on_main("CALENDAR_NEEDS_SYNC")
                    
                self._debounce = DebounceTimer(0.5, 2.0, _trigger_sync)
                
                def _on_change(notification):
                    self._debounce.trigger()
                    
                self._observer = Foundation.NSNotificationCenter.defaultCenter().addObserverForName_object_queue_usingBlock_(
                    EventKit.EKEventStoreChangedNotification,
                    self._store,
                    None,
                    _on_change
                )

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
        try:
            store.reset()
        except Exception:
            pass

        from datetime import timezone
        now = datetime.now().astimezone() # Local time to determine 'today' and 'tomorrow' properly
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=start_offset_hours)
        end_of_tomorrow = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

        start_date = Foundation.NSDate.dateWithTimeIntervalSince1970_(start_of_today.timestamp())
        end_date = Foundation.NSDate.dateWithTimeIntervalSince1970_(end_of_tomorrow.timestamp())

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
            start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)

            end_dt = None
            if ev.endDate():
                end_ts = ev.endDate().timeIntervalSince1970()
                end_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)

            meeting = EventClassifier.classify(
                title=title,
                location=loc,
                description=desc,
                meeting_url=meeting_url,
                custom_keywords=custom_kw,
                start_time=start_dt,
                end_time=end_dt
            )

            # Extract Apple Calendar's native travel time & structured location.
            # These are set when a user enables "Travel Time" on a calendar event.
            try:
                travel_seconds = ev.travelTime()
                if travel_seconds and travel_seconds > 0:
                    travel_min = int(round(travel_seconds / 60.0))
                    meeting.travel_time_minutes = travel_min
                    meeting.is_travel = True
                    if meeting.start_time:
                        meeting.departure_time = meeting.start_time - timedelta(minutes=travel_min)
                    logger.debug(f"EventKit travelTime for '{title}': {travel_min}m")
            except Exception:
                pass

            try:
                struct_loc = ev.structuredLocation()
                if struct_loc:
                    geo = struct_loc.geoLocation()
                    if geo:
                        lat = geo.coordinate().latitude
                        lon = geo.coordinate().longitude
                        if lat != 0.0 or lon != 0.0:
                            # Store coordinates as "lat,lon" for downstream ETA/routing
                            meeting._ek_latitude = lat
                            meeting._ek_longitude = lon
                            logger.debug(f"EventKit structuredLocation for '{title}': ({lat}, {lon})")
            except Exception:
                pass

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
