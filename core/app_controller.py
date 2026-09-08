import time
import threading
import logging
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus

logger = logging.getLogger("QuakMeeting.AppController")

class AppController:
    """Central orchestrator for background tasks, removing polling from the UI layer."""
    def __init__(self):
        self.is_running = False
        self._thread = None
        self._loop_count = 0
        self._stop_event = threading.Event()
        self._start_lock = threading.Lock()

    def start_background_loop(self):
        with self._start_lock:
            if self.is_running:
                logger.debug("Background loop start requested while already running.")
                return
            self._stop_event.clear()
            self.is_running = True
            logger.debug("Starting background loop thread.")
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop_background_loop(self):
        logger.debug("Stopping background loop.")
        self.is_running = False
        self._stop_event.set()

    def _loop(self):
        logger.info("Started background AppController loop.")
        while self.is_running:
            try:
                # 1. Fetch upcoming meetings
                meeting_objects = calendar_service.get_upcoming_meetings()
                logger.debug("Fetched %d upcoming meetings.", len(meeting_objects))

                # 2. Evaluate reminders cleanly in domain service
                reminder_engine.evaluate_meetings(meeting_objects)

                # 3. Publish update so UI components can re-render reactively
                event_bus.publish("AGENDA_UPDATED", meeting_objects=meeting_objects)

                # 4. Periodic auto-update check every 4 hours (960 iterations of 15s)
                self._loop_count += 1
                logger.debug("Completed background loop iteration %d.", self._loop_count)
                if self._loop_count % 960 == 0:
                    updater_service.check_for_updates(background=True)

            except Exception as e:
                logger.error(f"Error in background AppController loop: {e}", exc_info=True)

            self._stop_event.wait(15)

app_controller = AppController()
