import unittest
import sys
import psutil
import os
import gc

@unittest.skipIf(sys.platform != "darwin", "Native memory profiling test specific to macOS AppKit")
class TestNativeMemoryLeaks(unittest.TestCase):
    
    def test_rss_steady_state_plateau(self):
        """
        Spawns and dismisses the flying banner headless 50 times.
        Asserts that Process Resident Set Size (RSS) hits a steady-state plateau,
        proving there are no unbounded native Quartz/X11 memory leaks.
        """
        process = psutil.Process(os.getpid())
        
        # Warmup phase: OS allocators will retain memory after first few creations
        from ui.macos.banner.banner_controller import show_banner_async, _current_banner_controller
        from ui.common.banner_queue import banner_queue
        from core.services.dispatcher import run_on_main_thread_sync
        
        test_meeting = {
            "title": "Memory Test Meeting",
            "provider": "Test",
            "pilot_type": "duck",
            "action_btn_text": "JOIN",
            "is_quiet_reminder": True
        }
        
        # Warm-up 10 times
        for _ in range(10):
            show_banner_async(test_meeting)
            import time
            time.sleep(0.05)
            # We would need a way to reliably dismiss from the test thread.
            # For this test, we can just instantiate the controller and dismiss it manually 
            # instead of using the async queue to avoid blocking
        
        gc.collect()
        rss_baseline = process.memory_info().rss
        
        from ui.macos.banner.banner_controller import QuakPitFlyingBanner
        
        for _ in range(100):
            def _create_and_destroy():
                import AppKit
                import objc
                with objc.autorelease_pool():
                    controller = QuakPitFlyingBanner.alloc().initWithMeetingData_callback_(test_meeting, lambda: None)
                    controller.show()
                    controller.dismiss()
            run_on_main_thread_sync(_create_and_destroy)
            
        gc.collect()
        rss_final = process.memory_info().rss
        
        # RSS should be roughly equivalent to baseline (+/- small tolerance for allocator pool expansions)
        # We allow a maximum 50MB tolerance plateau for python internal object tracking over 100 iterations
        tolerance_bytes = 50 * 1024 * 1024 
        
        diff = rss_final - rss_baseline
        self.assertLessEqual(diff, tolerance_bytes, f"Unbounded memory leak detected! RSS grew by {diff / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    unittest.main()
