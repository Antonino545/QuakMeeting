import unittest
import threading
import time
import sys
from typing import List

from core.services.event_bus import event_bus
from core.notifications.payload import NotificationPayload
from core.notifications.pipeline import notification_pipeline

class TestChaosConcurrency(unittest.TestCase):
    """
    Chaos Engineering: Fire 1,000 reminder events simultaneously from 10 different 
    background threads to guarantee the Main-Thread UI Dispatcher queues and handles 
    the chaos perfectly without OS window manager lockups or deadlocks.
    """
    
    def test_massive_event_storm(self):
        # We temporarily mock the actual channels so we don't open 1000 windows or make 1000 webhooks
        original_channels = notification_pipeline.channels
        
        class DummyChannel:
            def __init__(self):
                self.received = []
                self.lock = threading.Lock()
            def send(self, payload: NotificationPayload) -> bool:
                with self.lock:
                    self.received.append(payload)
                return True
                
        dummy = DummyChannel()
        notification_pipeline.channels = [dummy]
        
        # Fire 1000 events from 10 threads
        num_threads = 10
        events_per_thread = 100
        
        threads: List[threading.Thread] = []
        
        def _worker_spam(thread_id: int):
            for i in range(events_per_thread):
                event_bus.publish(
                    "REMINDER_TRIGGERED", 
                    meeting={
                        "id": f"chaos_{thread_id}_{i}",
                        "title": f"Chaos Event {thread_id}-{i}",
                        "is_quiet_reminder": True
                    }, 
                    stage=5
                )
                # tiny sleep to actually simulate real concurrency interleaving
                time.sleep(0.001)

        start_time = time.monotonic()
        for i in range(num_threads):
            t = threading.Thread(target=_worker_spam, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        duration = time.monotonic() - start_time
        
        # Restore channels
        notification_pipeline.channels = original_channels
        
        self.assertEqual(len(dummy.received), num_threads * events_per_thread, 
                         f"Pipeline dropped events! Received {len(dummy.received)}, expected {num_threads * events_per_thread}")
                         
        print(f"Chaos test processed {num_threads * events_per_thread} events concurrently across {num_threads} threads in {duration:.2f} seconds.")

if __name__ == "__main__":
    unittest.main()
