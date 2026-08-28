"""
Thread-safe EventBus (Publish-Subscribe) for QuakMeeting.
Allows loose coupling across background workers, UI controllers, and services.
"""
import threading
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Any

logger = logging.getLogger("QuakMeeting.EventBus")

class EventBus:
    """Thread-safe event dispatcher supporting synchronous and asynchronous subscribers."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers = defaultdict(list)
                cls._instance._sub_lock = threading.RLock()
            return cls._instance

    def subscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """Register a callback for an event name."""
        with self._sub_lock:
            if handler not in self._subscribers[event_name]:
                self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """Unregister a callback for an event name."""
        with self._sub_lock:
            if handler in self._subscribers[event_name]:
                self._subscribers[event_name].remove(handler)

    def publish(self, event_name: str, **kwargs) -> None:
        """Dispatch event to all registered subscribers."""
        with self._sub_lock:
            handlers = list(self._subscribers.get(event_name, []))

        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception as e:
                logger.error(f"Error in EventBus handler for '{event_name}': {e}", exc_info=True)

    def publish_on_main(self, event_name: str, **kwargs) -> None:
        """Dispatch event to all registered subscribers, ensuring handlers run on the OS main thread."""
        with self._sub_lock:
            handlers = list(self._subscribers.get(event_name, []))

        if not handlers:
            return

        from core.services.dispatcher import run_on_main_thread_async
        
        for handler in handlers:
            def _wrapped(h=handler):
                try:
                    h(**kwargs)
                except Exception as e:
                    logger.error(f"Error in EventBus main-thread handler for '{event_name}': {e}", exc_info=True)
            
            run_on_main_thread_async(_wrapped)

    def clear(self) -> None:
        """Clear all subscriptions (primarily used for unit tests)."""
        with self._sub_lock:
            self._subscribers.clear()

# Global shared instance
event_bus = EventBus()
