import sys
import logging
import threading
from core.services.event_bus import event_bus
from core.services.debounce_timer import DebounceTimer

logger = logging.getLogger("QuakMeeting.EDSSupervisor")

class EDSSupervisor:
    """
    Monitors Evolution Data Server (EDS) on Linux via D-Bus for calendar changes.
    Uses a dedicated GLib.MainLoop to cleanly receive D-Bus signals and dispatch
    debounced sync requests.
    """
    def __init__(self):
        self._loop = None
        self._thread = None
        self._is_running = False
        
        def _trigger_sync():
            event_bus.publish_on_main("CALENDAR_NEEDS_SYNC")
            
        self._debounce = DebounceTimer(0.5, 2.0, _trigger_sync)

    def start(self):
        if sys.platform == "darwin":
            return
            
        if self._is_running:
            return
            
        try:
            import pydbus
            import gi
            from gi.repository import GLib
            # Just to verify we have the deps
        except ImportError:
            logger.warning("pydbus/gi not installed. Linux instant sync disabled.")
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        import pydbus
        from gi.repository import GLib
        
        while self._is_running:
            try:
                bus = pydbus.SessionBus()
                
                # Evolution Data Server emits signals when calendar items change
                # We listen generally on the EDS bus name for PropertiesChanged or specific custom signals
                # For broad safety we can listen to org.gnome.evolution.dataserver.Calendar
                
                def _on_signal(*args, **kwargs):
                    self._debounce.trigger()
                
                # Subscribe to general calendar change signals. 
                # (The exact signal depends on the EDS version; listening to object manager or properties changed is safest)
                bus.subscribe(
                    sender="org.gnome.evolution.dataserver.Calendar",
                    signal_fired=_on_signal
                )
                
                logger.info("EDSSupervisor connected to D-Bus.")
                
                self._loop = GLib.MainLoop()
                self._loop.run()
                
            except Exception as e:
                logger.error(f"EDSSupervisor D-Bus error: {e}. Reconnecting in 5s...")
                if self._is_running:
                    import time
                    time.sleep(5.0)

    def stop(self):
        self._is_running = False
        if self._loop:
            self._loop.quit()
        if self._thread:
            self._thread.join(timeout=2.0)

# Global supervisor
eds_supervisor = EDSSupervisor()
