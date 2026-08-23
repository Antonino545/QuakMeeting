"""
Unit tests for CairoPilotRenderer on Ubuntu Linux.
"""
import unittest
from unittest.mock import MagicMock
from ui.banner.cairo_renderers import CairoPilotRenderer

class TestCairoRenderers(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()

    def test_all_pilots_have_draw_functions(self):
        pilots = ["duck", "chef", "captain", "owl", "gym", "driver", "zen_duck"]
        for p in pilots:
            CairoPilotRenderer.draw_pilot(self.mock_ctx, p, 50.0, 50.0, 10)
            self.mock_ctx.fill.assert_called()
            self.mock_ctx.reset_mock()

if __name__ == "__main__":
    unittest.main()
