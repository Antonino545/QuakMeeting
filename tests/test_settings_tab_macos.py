import sys
import unittest
from unittest.mock import MagicMock

HAS_APPKIT = False
if sys.platform == "darwin":
    try:
        import AppKit
        import objc
        from ui.macos.components.toggle_switch import ModernToggleSwitch
        from ui.macos.components.button import ModernButton
        from ui.macos.dashboard_tabs.settings_tab import SettingsTabController, FlippedView
        HAS_APPKIT = True
    except (ImportError, Exception):
        HAS_APPKIT = False


import warnings
if HAS_APPKIT and 'objc' in locals() and hasattr(objc, 'ObjCPointerWarning'):
    warnings.filterwarnings("ignore", category=objc.ObjCPointerWarning)



@unittest.skipUnless(HAS_APPKIT, "macOS AppKit required")
class TestSettingsTabMacOS(unittest.TestCase):

    def test_modern_toggle_switch_click_and_state(self):
        sw = ModernToggleSwitch.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 44, 24))
        self.assertFalse(sw.isChecked())
        self.assertEqual(sw.state(), AppKit.NSControlStateValueOff)
        self.assertTrue(sw.acceptsFirstMouse_(None))
        self.assertFalse(sw.mouseDownCanMoveWindow())

        called = []
        sw.setCallback_(lambda v: called.append(v))

        # First mouseDown toggles ON
        sw.mouseDown_(None)
        self.assertTrue(sw.isChecked())
        self.assertEqual(sw.state(), AppKit.NSControlStateValueOn)
        self.assertEqual(called, [True])

        # Second mouseDown toggles OFF
        sw.mouseDown_(None)
        self.assertFalse(sw.isChecked())
        self.assertEqual(sw.state(), AppKit.NSControlStateValueOff)
        self.assertEqual(called, [True, False])

        # setState_ works
        sw.setState_(AppKit.NSControlStateValueOn)
        self.assertTrue(sw.isChecked())
        sw.setState_(AppKit.NSControlStateValueOff)
        self.assertFalse(sw.isChecked())

    def test_modern_button_layer_and_first_mouse(self):
        btn = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, 120, 32))
        self.assertEqual(btn.title(), "")
        self.assertTrue(btn.wantsLayer())
        self.assertIsNotNone(btn.layer())
        self.assertFalse(btn.isBordered())
        self.assertTrue(btn.acceptsFirstMouse_(None))
        self.assertFalse(btn.mouseDownCanMoveWindow())

    def test_settings_tab_page_switching_preserves_sidebar(self):
        controller = SettingsTabController.alloc().init()
        mock_container = MagicMock()
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda k, d=None: d if d is not None else "transit"
        cached_calendars = [{"name": "Work", "enabled": True}]

        view = controller.render(mock_container, 800, 500, mock_config, cached_calendars)
        self.assertIsNotNone(view)
        self.assertIsNotNone(controller.right_container)
        self.assertEqual(len(controller.category_buttons), 5)

        # Retain references to the sidebar buttons
        original_buttons = list(controller.category_buttons)
        sidebar_button_0 = original_buttons[0]

        # Verify page 0 is displayed and uses FlippedView
        page0 = controller.right_container.subviews()[0]
        self.assertIsInstance(page0.documentView(), FlippedView)
        self.assertTrue(page0.documentView().isFlipped())

        # Switch to category 1 (Arrival)
        controller.select_category(1)
        self.assertEqual(controller.selected_category, 1)

        # Verify sidebar buttons are identical objects (never destroyed / rebuilt)
        self.assertEqual(controller.category_buttons, original_buttons)
        self.assertIs(controller.category_buttons[0], sidebar_button_0)

        # Verify active accent bar on button 1 is visible, button 0 hidden
        self.assertFalse(controller.category_buttons[1]._accent_bar.isHidden())
        self.assertTrue(controller.category_buttons[0]._accent_bar.isHidden())

        # Switch to category 3 (Commute)
        controller.select_category(3)
        self.assertEqual(controller.selected_category, 3)
        self.assertFalse(controller.category_buttons[3]._accent_bar.isHidden())
        self.assertTrue(controller.category_buttons[1]._accent_bar.isHidden())

        # Switching away from category 3 closes address autocomplete suggestions
        eta_card = controller.eta_card
        eta_card.close_suggestions = MagicMock()
        controller.select_category(0)
        eta_card.close_suggestions.assert_called()


if __name__ == "__main__":
    unittest.main()
