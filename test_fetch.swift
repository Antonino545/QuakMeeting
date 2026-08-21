import Foundation
import EventKit

let store = EKEventStore()
let semaphore = DispatchSemaphore(value: 0)

if #available(macOS 14.0, *) {
    store.requestFullAccessToEvents { granted, error in
        semaphore.signal()
    }
} else {
    store.requestAccess(to: .event) { granted, error in
        semaphore.signal()
    }
}
_ = semaphore.wait(timeout: .now() + 2.0)

let now = Date()
let startDate = now.addingTimeInterval(-86400)
let endDate = now.addingTimeInterval(86400 * 2)

let predicate = store.predicateForEvents(withStart: startDate, end: endDate, calendars: nil)
let events = store.events(matching: predicate)

print("FOUND_EVENTS_COUNT:\(events.count)")
for ev in events {
    let title = ev.title ?? "No Title"
    let start = Int(ev.startDate.timeIntervalSince1970)
    let end = Int(ev.endDate.timeIntervalSince1970)
    let url = ev.url?.absoluteString ?? ""
    let location = ev.location ?? ""
    let notes = ev.notes ?? ""
    print("EV|\(title)|\(start)|\(end)|\(url)|\(location)|\(notes.replacingOccurrences(of: "\n", with: " "))")
}
