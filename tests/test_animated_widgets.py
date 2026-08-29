import unittest
import sys

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from ui.linux.animated_widgets import (
        BouncingMascotLabel, AnimatedSpinButton, AnimatedUpdateCard, UpdatingHUDWidget
    )
    _HAS_PYQT6 = True
except (ImportError, ModuleNotFoundError):
    _HAS_PYQT6 = False


class TestAnimatedWidgets(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if _HAS_PYQT6:
            cls.app = QApplication.instance()
            if cls.app is None:
                cls.app = QApplication(sys.argv)

    def test_bouncing_mascot_label(self):
        if not _HAS_PYQT6:
            self.skipTest("PyQt6 is required for UI widget tests")
        lbl = BouncingMascotLabel(emoji="🦆")
        self.assertTrue(lbl._is_bouncing)
        lbl.trigger_bounce()
        self.assertTrue(lbl._is_bouncing)
        lbl._on_bounce_tick()

    def test_animated_spin_button(self):
        if not _HAS_PYQT6:
            self.skipTest("PyQt6 is required for UI widget tests")
        btn = AnimatedSpinButton("🔄 Sync Now")
        self.assertEqual(btn.text(), "🔄 Sync Now")

        btn.start_spinning("Syncing...")
        self.assertTrue(btn._is_spinning)
        self.assertFalse(btn.isEnabled())

        btn._on_spin_tick()
        self.assertIn("Syncing...", btn.text())

        btn.stop_spinning("✅ Synced!", is_success=True, reset_delay_ms=5000)
        self.assertFalse(btn._is_spinning)
        self.assertTrue(btn.isEnabled())
        self.assertEqual(btn.text(), "✅ Synced!")

        btn._on_reset_timeout()
        self.assertEqual(btn.text(), "🔄 Sync Now")

    def test_animated_update_card(self):
        if not _HAS_PYQT6:
            self.skipTest("PyQt6 is required for UI widget tests")
        card = AnimatedUpdateCard()
        card.set_scanning(True)
        self.assertTrue(card._is_scanning)
        card._on_tick()
        self.assertGreater(card._scan_phase, 0.0)

        card.set_update_available("v2.0.0")
        self.assertFalse(card._is_scanning)
        self.assertTrue(card._has_update)

        card.set_up_to_date()
        self.assertFalse(card._has_update)
        self.assertTrue(card._is_up_to_date)

    def test_updating_hud_widget(self):
        if not _HAS_PYQT6:
            self.skipTest("PyQt6 is required for UI widget tests")
        hud = UpdatingHUDWidget()
        self.assertFalse(hud.isVisible())

        hud.start_downloading("package.deb")
        self.assertTrue(hud.isVisible())
        self.assertEqual(hud._phase_index, 1)

        hud.set_progress(45, 4500000, 10000000)
        self.assertEqual(hud._target_percent, 45.0)
        hud._on_tick()

        hud.set_installing()
        self.assertEqual(hud._phase_index, 2)
        self.assertEqual(hud._target_percent, 100.0)
        hud._on_tick()

        hud.set_installed()
        self.assertEqual(hud._phase_index, 3)


if __name__ == "__main__":
    unittest.main()
