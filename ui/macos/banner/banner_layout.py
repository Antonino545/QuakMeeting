"""
Banner Layout Geometry and Hit Testing for macOS QuakPit Banners.
Computes bounding boxes for cards, buttons, close hit targets, and action bars.
"""
import AppKit
from typing import Dict, Any, Optional

class BannerLayout:
    def __init__(self, banner_w: float = 535.0, banner_h: float = 148.0):
        self.banner_w = banner_w
        self.banner_h = banner_h

    def get_button_rects(
        self,
        banner_x: float,
        banner_y: float,
        has_maps_url: bool,
        has_real_url: bool,
        reminder_stage: Optional[int]
    ) -> Dict[str, AppKit.NSRect]:
        """Returns accurate bounding rects for all interactive elements."""
        btn_close_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 36, banner_y + self.banner_h - 34, 24, 24)
        btn_close_hit_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 44, banner_y + self.banner_h - 44, 40, 40)

        # 4 Button Bar: [Action] [I'm Here] [Snooze 5m] [Snooze 15m]
        btn_action_rect = AppKit.NSMakeRect(banner_x + 18, banner_y + 12, 220, 33)
        is_stage_zero = (reminder_stage == 0)

        if has_maps_url:
            btn_arrived_rect = AppKit.NSMakeRect(banner_x + 246, banner_y + 12, 100, 33)
            if is_stage_zero:
                if not has_real_url:
                    btn_snooze1_rect = AppKit.NSMakeRect(0, 0, 0, 0)
                else:
                    btn_snooze1_rect = AppKit.NSMakeRect(banner_x + 354, banner_y + 12, 163, 33)
                btn_snooze2_rect = AppKit.NSMakeRect(0, 0, 0, 0)
            else:
                btn_snooze1_rect = AppKit.NSMakeRect(banner_x + 354, banner_y + 12, 85, 33)
                btn_snooze2_rect = AppKit.NSMakeRect(banner_x + 447, banner_y + 12, 70, 33)
        else:
            btn_arrived_rect = AppKit.NSMakeRect(0, 0, 0, 0)
            if is_stage_zero:
                if not has_real_url:
                    btn_snooze1_rect = AppKit.NSMakeRect(0, 0, 0, 0)
                else:
                    btn_snooze1_rect = AppKit.NSMakeRect(banner_x + 246, banner_y + 12, 208, 33)
                btn_snooze2_rect = AppKit.NSMakeRect(0, 0, 0, 0)
            else:
                btn_snooze1_rect = AppKit.NSMakeRect(banner_x + 246, banner_y + 12, 100, 33)
                btn_snooze2_rect = AppKit.NSMakeRect(banner_x + 354, banner_y + 12, 100, 33)

        return {
            "close": btn_close_rect,
            "close_hit": btn_close_hit_rect,
            "action": btn_action_rect,
            "arrived": btn_arrived_rect,
            "snooze1": btn_snooze1_rect,
            "snooze2": btn_snooze2_rect,
            "card": AppKit.NSMakeRect(banner_x, banner_y, self.banner_w, self.banner_h)
        }
