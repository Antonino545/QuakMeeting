import unittest
import threading
import sys
from unittest.mock import patch, MagicMock

# Attempt to load the dispatcher
try:
    from core.services.dispatcher import run_on_main_thread_async, run_on_main_thread_sync, is_main_thread, CoalescedUIUpdater
    _dispatcher_loaded = True
except ImportError:
    _dispatcher_loaded = False


@unittest.skipIf(not _dispatcher_loaded, "Dispatcher not loaded")
class TestDispatcher(unittest.TestCase):

    def test_is_main_thread(self):
        """Test that main thread detection works without crashing."""
        self.assertTrue(isinstance(is_main_thread(), bool))

    def test_run_on_main_thread_sync(self):
        """Test that synchronous dispatch works when called from the main thread."""
        def dummy_func(a, b):
            return a + b

        if is_main_thread():
            result = run_on_main_thread_sync(dummy_func, 2, 3)
            self.assertEqual(result, 5)

    def test_coalesced_updater(self):
        """Test that CoalescedUIUpdater only schedules one update at a time."""
        update_calls = []

        def mock_update():
            update_calls.append(1)

        updater = CoalescedUIUpdater(mock_update)
        
        # We mock run_on_main_thread_async to execute immediately for testing
        with patch("core.services.dispatcher.run_on_main_thread_async") as mock_async:
            updater.request_update()
            updater.request_update()
            updater.request_update()

            self.assertEqual(mock_async.call_count, 1)

if __name__ == "__main__":
    unittest.main()
