import threading
from typing import Callable
import time

class DebounceTimer:
    """
    A sliding-window debounce timer.
    Defers execution of the callback until there have been no new triggers for `wait_time` seconds,
    up to a maximum of `max_wait_time` seconds (to prevent infinite starvation).
    Protects against Apple EventKit 'sync storms' where 50+ notifications fire in 100ms.
    """
    def __init__(self, wait_time: float, max_wait_time: float, callback: Callable):
        self.wait_time = wait_time
        self.max_wait_time = max_wait_time
        self.callback = callback
        
        self._timer = None
        self._lock = threading.Lock()
        self._first_trigger_time = 0.0

    def _execute(self):
        with self._lock:
            self._timer = None
            self._first_trigger_time = 0.0
        self.callback()

    def trigger(self):
        with self._lock:
            now = time.monotonic()
            if self._first_trigger_time == 0.0:
                self._first_trigger_time = now

            # If we've hit the ceiling, we must execute now
            if (now - self._first_trigger_time) >= self.max_wait_time:
                if self._timer:
                    self._timer.cancel()
                    self._timer = None
                
                # Execute in background thread so trigger() remains non-blocking
                threading.Thread(target=self._execute, daemon=True).start()
                return

            if self._timer:
                self._timer.cancel()
            
            self._timer = threading.Timer(self.wait_time, self._execute)
            self._timer.daemon = True
            self._timer.start()
