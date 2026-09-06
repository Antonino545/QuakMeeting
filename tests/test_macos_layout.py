"""
Unit tests for Qt-style macOS relative layout components (VBox, HBox).
"""

import sys
import unittest

try:
    import AppKit
    from ui.macos.components.layout import VBox, HBox, BaseStack
    HAS_APPKIT = True
except (ImportError, Exception):
    HAS_APPKIT = False


@unittest.skipUnless(HAS_APPKIT and sys.platform == "darwin", "Requires macOS AppKit and PyObjC")
class TestMacOSLayoutComponents(unittest.TestCase):
    """Tests for VBox and HBox layout stacks."""

    def test_vbox_instantiation_and_orientation(self):
        vbox = VBox.create(spacing=12.0)
        self.assertIsInstance(vbox, VBox)
        self.assertIsInstance(vbox, BaseStack)
        self.assertEqual(vbox.orientation(), AppKit.NSUserInterfaceLayoutOrientationVertical)
        self.assertEqual(vbox.spacing(), 12.0)

    def test_hbox_instantiation_and_orientation(self):
        hbox = HBox.create(spacing=6.0)
        self.assertIsInstance(hbox, HBox)
        self.assertIsInstance(hbox, BaseStack)
        self.assertEqual(hbox.orientation(), AppKit.NSUserInterfaceLayoutOrientationHorizontal)
        self.assertEqual(hbox.spacing(), 6.0)

    def test_add_widget_and_widgets(self):
        box = VBox.create(spacing=10.0)
        lbl1 = AppKit.NSTextField.labelWithString_("Label 1")
        lbl2 = AppKit.NSTextField.labelWithString_("Label 2")
        btn = AppKit.NSButton.buttonWithTitle_target_action_("Action", None, None)

        box.add_widget(lbl1, spacing=15.0)
        box.add_widgets(lbl2, btn)

        arranged = box.arrangedSubviews()
        self.assertEqual(len(arranged), 3)
        self.assertEqual(arranged[0], lbl1)
        self.assertEqual(arranged[1], lbl2)
        self.assertEqual(arranged[2], btn)
        self.assertEqual(box.customSpacingAfterView_(lbl1), 15.0)

    def test_add_stretch_horizontal(self):
        hbox = HBox.create()
        spacer = hbox.add_stretch()
        arranged = hbox.arrangedSubviews()
        self.assertIn(spacer, arranged)
        prio = spacer.contentHuggingPriorityForOrientation_(
            AppKit.NSLayoutConstraintOrientationHorizontal
        )
        self.assertEqual(prio, AppKit.NSLayoutPriorityFittingSizeCompression)

    def test_add_stretch_vertical(self):
        vbox = VBox.create()
        spacer = vbox.add_stretch()
        arranged = vbox.arrangedSubviews()
        self.assertIn(spacer, arranged)
        prio = spacer.contentHuggingPriorityForOrientation_(
            AppKit.NSLayoutConstraintOrientationVertical
        )
        self.assertEqual(prio, AppKit.NSLayoutPriorityFittingSizeCompression)

    def test_set_padding(self):
        box = VBox.create()
        box.set_padding(top=10.0, right=15.0, bottom=20.0, left=25.0)
        insets = box.edgeInsets()
        self.assertEqual(insets.top, 10.0)
        self.assertEqual(insets.right, 15.0)
        self.assertEqual(insets.bottom, 20.0)
        self.assertEqual(insets.left, 25.0)


if __name__ == "__main__":
    unittest.main()
