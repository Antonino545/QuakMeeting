import time
import threading
import logging
from core.services.calendar_service import calendar_service
from core.services.reminder_engine import reminder_engine
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.services.device_presence_service import device_presence_service
from core.services.study_focus_guardian import study_focus_guardian

logger = logging.getLogger("QuakMeeting.AppController")

class AppController:
    """Central orchestrator for background tasks, removing polling from the UI layer."""
    def __init__(self):
        self.is_running = False
        self._thread = None
        self._loop_count = 0

    def start_background_loop(self):
        if self.is_running:
            return
        self.is_running = True
        # Start local device sync server (for iPhone/iPad Shortcuts)
        device_presence_service.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_background_loop(self):
        self.is_running = False
        device_presence_service.stop()

    def _loop(self):
        logger.info("Started background AppController loop.")
        # Check updates on startup in background
        updater_service.check_for_updates(background=True)

        while self.is_running:
            try:
                # 1. Fetch upcoming meetings
                meeting_objects = calendar_service.get_upcoming_meetings()

                # 2. Evaluate reminders cleanly in domain service
                reminder_engine.evaluate_meetings(meeting_objects)

                # 3. Publish update so UI components can re-render reactively
                event_bus.publish("AGENDA_UPDATED", meeting_objects=meeting_objects)

                # 4. Periodic auto-update check every 4 hours (960 iterations of 15s)
                self._loop_count += 1
                if self._loop_count % 960 == 0:
                    updater_service.check_for_updates(background=True)

            except Exception as e:
                logger.error(f"Error in background AppController loop: {e}", exc_info=True)

            time.sleep(15)

app_controller = AppController()
