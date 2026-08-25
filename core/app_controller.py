import time
import threading
import logging
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.event_bus import event_bus

logger = logging.getLogger("QuakMeeting.AppController")

class AppController:
    """Central orchestrator for background tasks, removing polling from the UI layer."""
    def __init__(self):
        self.is_running = False
        self._thread = None

    def start_background_loop(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_background_loop(self):
        self.is_running = False

    def _loop(self):
        logger.info("Started background AppController loop.")
        while self.is_running:
            try:
                # 1. Fetch upcoming meetings
                meeting_objects = calendar_service.get_upcoming_meetings()
                
                # 2. Evaluate reminders cleanly in domain service
                reminder_engine.evaluate_meetings(meeting_objects)
                
                # 3. Publish update so UI components can re-render reactively
                event_bus.publish("AGENDA_UPDATED", meeting_objects=meeting_objects)
                
            except Exception as e:
                logger.error(f"Error in background AppController loop: {e}", exc_info=True)
                
            time.sleep(15)

app_controller = AppController()
