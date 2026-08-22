import EventKit, Foundation
from datetime import datetime, timedelta

store = EventKit.EKEventStore.alloc().init()
now = datetime.now()
start = now - timedelta(days=30)
end = now + timedelta(days=30)

ns_start = Foundation.NSDate.dateWithTimeIntervalSince1970_(start.timestamp())
ns_end = Foundation.NSDate.dateWithTimeIntervalSince1970_(end.timestamp())

cals = store.calendarsForEntityType_(EventKit.EKEntityTypeEvent)
predicate = store.predicateForEventsWithStartDate_endDate_calendars_(ns_start, ns_end, cals)
events = store.eventsMatchingPredicate_(predicate)
print(f"Total events in last/next 30 days: {len(events) if events else 0}")
for e in (events or []):
    print(e.title(), e.startDate())
