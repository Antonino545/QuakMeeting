import sys
import threading
import logging

logger = logging.getLogger("QuakMeeting.Dispatcher")

_is_mac = sys.platform == "darwin"

if _is_mac:
    import AppKit
    import objc

    def is_main_thread() -> bool:
        return AppKit.NSThread.isMainThread()

    def run_on_main_thread_async(func, *args, **kwargs):
        """Fire-and-forget dispatch to the main OS UI thread (macOS)."""
        def _safe_wrapper():
            try:
                with objc.autorelease_pool():
                    func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Unhandled exception in AppKit main-thread dispatch ({func}): {e}")

        AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_safe_wrapper)

    def run_on_main_thread_sync(func, *args, **kwargs):
        """Synchronous dispatch with deadlock protection (macOS)."""
        if is_main_thread():
            return func(*args, **kwargs)
        
        result = []
        error = []
        event = threading.Event()

        def _sync_wrapper():
            try:
                with objc.autorelease_pool():
                    result.append(func(*args, **kwargs))
            except Exception as e:
                error.append(e)
                logger.exception(f"Exception in synchronous main-thread execution: {e}")
            finally:
                event.set()

        AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_sync_wrapper)
        event.wait(timeout=10.0) # Prevent permanent deadlock
        if error:
            raise error[0]
        return result[0] if result else None

else:
    # Linux (PyQt6)
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt

    class QtMainThreadDispatcher(QObject):
        _dispatch_async_signal = pyqtSignal(object, tuple, dict)
        
        def __init__(self):
            super().__init__()
            self._dispatch_async_signal.connect(self._execute_async, Qt.ConnectionType.QueuedConnection)

        @pyqtSlot(object, tuple, dict)
        def _execute_async(self, func, args, kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Unhandled exception in Qt main-thread dispatch ({func}): {e}")

        def dispatch_async(self, func, *args, **kwargs):
            self._dispatch_async_signal.emit(func, args, kwargs)
            
    # We must instantiate the dispatcher on the main thread (during module load on main thread)
    _qt_dispatcher = None

    def _get_qt_dispatcher():
        global _qt_dispatcher
        if _qt_dispatcher is None:
            _qt_dispatcher = QtMainThreadDispatcher()
        return _qt_dispatcher

    def is_main_thread() -> bool:
        import threading
        return threading.current_thread() is threading.main_thread()

    def run_on_main_thread_async(func, *args, **kwargs):
        """Fire-and-forget dispatch to the main OS UI thread (Linux PyQt6)."""
        dispatcher = _get_qt_dispatcher()
        dispatcher.dispatch_async(func, *args, **kwargs)

    def run_on_main_thread_sync(func, *args, **kwargs):
        """Synchronous dispatch (Linux PyQt6). Note: less commonly needed, but implemented with Event."""
        if is_main_thread():
            return func(*args, **kwargs)
            
        result = []
        error = []
        event = threading.Event()

        def _sync_wrapper():
            try:
                result.append(func(*args, **kwargs))
            except Exception as e:
                error.append(e)
                logger.exception(f"Exception in synchronous main-thread execution: {e}")
            finally:
                event.set()

        dispatcher = _get_qt_dispatcher()
        dispatcher.dispatch_async(_sync_wrapper)
        event.wait(timeout=10.0)
        if error:
            raise error[0]
        return result[0] if result else None

class CoalescedUIUpdater:
    """Debounces/coalesces high-frequency UI updates into a single main-thread update."""
    def __init__(self, update_func, delay_sec=0.05):
        self.update_func = update_func
        self.delay_sec = delay_sec
        self._pending = False
        self._lock = threading.Lock()

    def request_update(self):
        with self._lock:
            if self._pending:
                return
            self._pending = True
        
        def _scheduled():
            with self._lock:
                self._pending = False
            self.update_func()

        run_on_main_thread_async(_scheduled)
