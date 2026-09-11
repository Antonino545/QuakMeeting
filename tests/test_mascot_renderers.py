import unittest
from ui.common.mascot_catalog import ANIMALS, ACCESSORIES

class TestMascotRenderers(unittest.TestCase):
    def test_macos_modular_renderer_all_animals_and_ticks(self):
        try:
            import AppKit
        except ImportError:
            self.skipTest("AppKit not available on this platform")

        from ui.macos.banner.renderers.modular_renderer import ModularPilotRenderer

        size = AppKit.NSMakeSize(120, 120)
        image = AppKit.NSImage.alloc().initWithSize_(size)
        image.lockFocus()

        try:
            for animal, _ in ANIMALS:
                # Test with default outfit, student outfit, accessories
                for outfit in ("aviator", "student", "agent"):
                    renderer = ModularPilotRenderer(
                        animal=animal,
                        outfit=outfit,
                        accessories=("sunglasses", "bow_tie", "badge", "earpiece")
                    )
                    # Tick 10 (open eyes) and Tick 76 (blinking eye window)
                    for tick in (10, 76):
                        try:
                            renderer.draw_pilot(60, 60, tick)
                        except Exception as e:
                            self.fail(f"ModularPilotRenderer failed for animal='{animal}', outfit='{outfit}', tick={tick}: {e}")
        finally:
            image.unlockFocus()

    def test_linux_qt_modular_renderer_all_animals(self):
        try:
            from PyQt6.QtGui import QImage, QPainter
            from ui.linux.banner.renderers.modular_renderer import QtModularRenderer
        except (ImportError, ModuleNotFoundError):
            self.skipTest("PyQt6 not available in this environment")

        img = QImage(120, 120, QImage.Format.Format_ARGB32)
        p = QPainter(img)
        try:
            for animal, _ in ANIMALS:
                for outfit in ("aviator", "student", "agent"):
                    renderer = QtModularRenderer(
                        animal=animal,
                        outfit=outfit,
                        accessories=("sunglasses", "bow_tie", "badge", "earpiece")
                    )
                    for tick in (10, 76):
                        try:
                            renderer.draw_pilot(p, 60, 60, tick)
                        except Exception as e:
                            self.fail(f"QtModularRenderer failed for animal='{animal}', outfit='{outfit}', tick={tick}: {e}")
        finally:
            p.end()

if __name__ == "__main__":
    unittest.main()
