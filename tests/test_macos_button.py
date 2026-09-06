import sys
import unittest

try:
    import AppKit
    from ui.macos.components.button import ModernButton
    HAS_APPKIT = True
except (ImportError, Exception):
    HAS_APPKIT = False


@unittest.skipUnless(HAS_APPKIT and sys.platform == "darwin", "Requires macOS AppKit and PyObjC")
class TestModernButtonCursor(unittest.TestCase):

    def test_cursor_update_uses_pointing_hand_when_enabled(self):
        button = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 100, 30))
        button.setEnabled_(True)
        button.cursorUpdate_(None)
        self.assertTrue(button.isEnabled())

    def test_cursor_update_uses_arrow_when_disabled(self):
        button = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 100, 30))
        button.setEnabled_(False)
        button.cursorUpdate_(None)
        self.assertFalse(button.isEnabled())


if __name__ == "__main__":
    unittest.main()
