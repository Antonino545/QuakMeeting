import EventKit
import threading

store = EventKit.EKEventStore.alloc().init()
status = EventKit.EKEventStore.authorizationStatusForEntityType_(EventKit.EKEntityTypeEvent)
print("Initial Status:", status)

if status == EventKit.EKAuthorizationStatusNotDetermined:
    sem = threading.Semaphore(0)
    res = [False]
    def completion(granted, error):
        print("Granted:", granted, "Error:", error)
        res[0] = granted
        sem.release()
    store.requestAccessToEntityType_completion_(EventKit.EKEntityTypeEvent, completion)
    sem.acquire()
    print("Requested access, granted:", res[0])
    
cals = store.calendarsForEntityType_(EventKit.EKEntityTypeEvent)
print("Calendars:", len(cals))
for c in cals:
    print(c.title())
