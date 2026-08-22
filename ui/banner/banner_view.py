"""
Banner View component for QuakMeeting.
Handles HUD layout, multi-modal travel countdown, buttons, particle physics, and pilot sprite delegation.
"""
import AppKit
import objc
import math
from datetime import datetime
from typing import Dict, Any, Optional

from core.services.config_service import config
from core.services.eta_service import MODE_ICONS, MODE_LABELS
from .renderers import get_pilot_renderer

class QuakPitBannerView(AppKit.NSView):
    def initWithFrame_meetingData_controller_(self, frame, meeting_data, controller):
        self = objc.super(QuakPitBannerView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.meeting_data = meeting_data
        self.controller = controller
        
        self.title = str(meeting_data.get("title") or "Event Reminder")
        self.provider = str(meeting_data.get("provider") or "Event")
        self.action_url = meeting_data.get("action_url") or meeting_data.get("meeting_url")
        self.action_btn_text = str(meeting_data.get("action_btn_text") or "🚀 JOIN NOW")
        self.start_time = meeting_data.get("start_time")
        self.end_time = meeting_data.get("end_time")
        self.location = str(meeting_data.get("location") or "")
        self.pilot_type = str(meeting_data.get("pilot_type") or "duck")
        self.is_travel = bool(meeting_data.get("is_travel", False))
        
        # Multi-modal Travel & ETA metadata
        self.travel_time_minutes = meeting_data.get("travel_time_minutes")
        self.travel_distance_km = meeting_data.get("travel_distance_km")
        self.transport_mode = meeting_data.get("transport_mode", config.get("transport_mode", "transit"))
        self.departure_time = meeting_data.get("departure_time")
        self.origin_address = meeting_data.get("origin_address")
        self.eta_text = meeting_data.get("eta_text")
        
        # Instantiate pilot renderer
        self.renderer = get_pilot_renderer(self.pilot_type)
        
        # Flight dynamics & geometry
        self.x = -680.0
        self.base_y = 48.0
        self.tick = 0
        self.speed = float(config.get("flight_speed", 3.2))
        self.is_paused = False
        self.smoke_particles = []
        self.sparkle_particles = []
        
        # Hover & Click Interaction State
        self.pressed_button = None    # 'action', 'snooze', 'close', or None
        self.hovered_button = None    # 'action', 'snooze', 'close', or None
        
        # Card Layout Dimensions
        self.banner_w = 515.0
        self.banner_h = 126.0
        
        tracking_options = (
            AppKit.NSTrackingMouseEnteredAndExited |
            AppKit.NSTrackingMouseMoved |
            AppKit.NSTrackingActiveAlways |
            AppKit.NSTrackingInVisibleRect
        )
        self.tracking_area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            tracking_options,
            self,
            None
        )
        self.addTrackingArea_(self.tracking_area)
        
        return self

    def _get_button_rects(self, banner_x, banner_y):
        """Returns accurate bounding rects for all interactive elements."""
        btn_close_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 38, banner_y + self.banner_h - 36, 26, 26)
        btn_close_hit_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 44, banner_y + self.banner_h - 44, 40, 40)
        btn_action_rect = AppKit.NSMakeRect(banner_x + 18, banner_y + 12, 255, 33)
        btn_snooze_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 128, banner_y + 12, 110, 33)
        
        return {
            "close": btn_close_rect,
            "close_hit": btn_close_hit_rect,
            "action": btn_action_rect,
            "snooze": btn_snooze_rect,
            "card": AppKit.NSMakeRect(banner_x, banner_y, self.banner_w, self.banner_h)
        }

    def mouseEntered_(self, event):
        self.is_paused = True

    def mouseExited_(self, event):
        self.is_paused = False
        self.pressed_button = None
        self.hovered_button = None
        AppKit.NSCursor.arrowCursor().set()
        self.setNeedsDisplay_(True)

    def mouseMoved_(self, event):
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        
        banner_x = self.x
        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        banner_y = y_wave - 10.0
        
        rects = self._get_button_rects(banner_x, banner_y)
        old_hover = self.hovered_button
        
        if AppKit.NSPointInRect(loc, rects["close_hit"]):
            self.hovered_button = "close"
            AppKit.NSCursor.pointingHandCursor().set()
        elif AppKit.NSPointInRect(loc, rects["action"]):
            self.hovered_button = "action"
            AppKit.NSCursor.pointingHandCursor().set()
        elif AppKit.NSPointInRect(loc, rects["snooze"]):
            self.hovered_button = "snooze"
            AppKit.NSCursor.pointingHandCursor().set()
        elif AppKit.NSPointInRect(loc, rects["card"]):
            self.hovered_button = "card"
            AppKit.NSCursor.arrowCursor().set()
        else:
            self.hovered_button = None
            AppKit.NSCursor.arrowCursor().set()
            
        if old_hover != self.hovered_button:
            self.setNeedsDisplay_(True)

    def mouseDown_(self, event):
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        banner_x = self.x
        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        banner_y = y_wave - 10.0
        rects = self._get_button_rects(banner_x, banner_y)
        
        if AppKit.NSPointInRect(loc, rects["close_hit"]):
            self.pressed_button = "close"
        elif AppKit.NSPointInRect(loc, rects["action"]):
            self.pressed_button = "action"
        elif AppKit.NSPointInRect(loc, rects["snooze"]):
            self.pressed_button = "snooze"
        elif AppKit.NSPointInRect(loc, rects["card"]):
            self.pressed_button = "card"
        else:
            self.pressed_button = None
            
        self.setNeedsDisplay_(True)

    def mouseUp_(self, event):
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        banner_x = self.x
        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        banner_y = y_wave - 10.0
        rects = self._get_button_rects(banner_x, banner_y)
        
        clicked = self.pressed_button
        self.pressed_button = None
        self.setNeedsDisplay_(True)
        
        if clicked == "close" and AppKit.NSPointInRect(loc, rects["close_hit"]):
            if self.controller:
                self.controller.dismiss()
        elif clicked == "action" and AppKit.NSPointInRect(loc, rects["action"]):
            if self.controller:
                self.controller.trigger_action()
        elif clicked == "snooze" and AppKit.NSPointInRect(loc, rects["snooze"]):
            if self.controller:
                self.controller.trigger_snooze()
        elif clicked == "card" and AppKit.NSPointInRect(loc, rects["card"]):
            if self.controller:
                self.controller.trigger_action()

    def stepAnimation_(self, timer):
        self.tick += 1
        screen_w = self.bounds().size.width
        
        if not self.is_paused:
            self.x += self.speed
            if self.x > screen_w + 650:
                self.x = -680.0
                
        plane_x = self.x + 585.0
        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        plane_y = y_wave + 4.0
        
        # Smoke & Propulsion particle emitter
        if self.tick % 4 == 0 and not self.is_paused:
            if self.pilot_type == "captain":
                self.smoke_particles.append({"x": plane_x - 22, "y": plane_y - 12, "r": 4.0, "alpha": 0.75, "drift": -0.2})
                self.smoke_particles.append({"x": plane_x - 22, "y": plane_y + 12, "r": 4.0, "alpha": 0.75, "drift": 0.2})
            elif self.pilot_type == "zen_duck":
                self.smoke_particles.append({"x": plane_x - 28, "y": plane_y + 4, "r": 4.5, "alpha": 0.65, "drift": 0.0})
                if self.tick % 8 == 0:
                    self.sparkle_particles.append({"x": plane_x - 24, "y": plane_y + 8, "r": 3.0, "alpha": 0.9, "vy": 0.4})
            elif self.pilot_type == "owl":
                self.smoke_particles.append({"x": plane_x - 26, "y": plane_y + 6, "r": 4.2, "alpha": 0.6, "drift": 0.0})
                if self.tick % 10 == 0:
                    self.sparkle_particles.append({"x": plane_x - 22, "y": plane_y + 10, "r": 3.2, "alpha": 0.95, "vy": 0.3})
            else:
                self.smoke_particles.append({
                    "x": plane_x - 28,
                    "y": plane_y + 6,
                    "r": 4.8,
                    "alpha": 0.75,
                    "drift": math.sin(self.tick * 0.1) * 0.4
                })
            
        new_particles = []
        for p in self.smoke_particles:
            p["x"] -= 2.4
            p["y"] += p.get("drift", 0.0) + math.sin(p["x"] * 0.04) * 0.3
            p["r"] += 0.35
            p["alpha"] -= 0.022
            if p["alpha"] > 0 and p["r"] < 24:
                new_particles.append(p)
        self.smoke_particles = new_particles
        
        new_sparkles = []
        for s in self.sparkle_particles:
            s["x"] -= 1.8
            s["y"] += s["vy"]
            s["alpha"] -= 0.028
            s["r"] = max(0.5, s["r"] - 0.04)
            if s["alpha"] > 0:
                new_sparkles.append(s)
        self.sparkle_particles = new_sparkles
        
        self.setNeedsDisplay_(True)

    def _get_theme_palette(self):
        if self.pilot_type == "chef":
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.44, 0.38, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.62, 0.48, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.38, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.30, 0.22, 1.0)
            card_tint = (0.13, 0.08, 0.08)
        elif self.pilot_type == "captain":
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.38, 0.68, 1.0, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.58, 0.82, 1.0, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.38, 0.68, 1.0, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.18, 0.45, 0.90, 1.0)
            card_tint = (0.07, 0.09, 0.14)
        elif self.pilot_type == "owl":
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.76, 0.52, 1.0, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.68, 1.0, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.75, 0.50, 0.98, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.55, 0.30, 0.82, 1.0)
            card_tint = (0.10, 0.07, 0.14)
        elif self.pilot_type == "driver":
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.85, 0.58, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.95, 0.72, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.24, 0.86, 0.58, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.65, 0.40, 1.0)
            card_tint = (0.06, 0.12, 0.09)
        elif self.pilot_type == "zen_duck":
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.28, 0.88, 0.82, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.48, 0.96, 0.90, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.28, 0.88, 0.82, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.68, 0.62, 1.0)
            card_tint = (0.06, 0.11, 0.12)
        else:
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.76, 0.28, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.88, 0.45, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.76, 0.28, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.56, 0.12, 1.0)
            card_tint = (0.12, 0.10, 0.06)
            
        return {
            "accent": accent,
            "accent_bright": accent_bright,
            "btn_gradient_top": btn_gradient_top,
            "btn_gradient_bot": btn_gradient_bot,
            "card_tint": card_tint
        }

    def drawRect_(self, rect):
        AppKit.NSColor.clearColor().set()
        AppKit.NSRectFill(rect)
        
        ctx = AppKit.NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()
        
        palette = self._get_theme_palette()
        accent = palette["accent"]
        
        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        plane_x = self.x + 585.0
        plane_y = y_wave + 4.0
        
        banner_x = self.x
        banner_y = y_wave - 10.0
        banner_w = self.banner_w
        banner_h = self.banner_h
        
        # 1. Particles
        for p in self.smoke_particles:
            smoke_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.88, 0.98, p["alpha"] * 0.50)
            smoke_col.set()
            smoke_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
                AppKit.NSMakeRect(p["x"] - p["r"], p["y"] - p["r"], p["r"] * 2, p["r"] * 2)
            )
            smoke_path.fill()
            
        for s in self.sparkle_particles:
            sparkle_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.92, 0.45, s["alpha"])
            sparkle_col.set()
            sparkle_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
                AppKit.NSMakeRect(s["x"] - s["r"], s["y"] - s["r"], s["r"] * 2, s["r"] * 2)
            )
            sparkle_path.fill()
            
        # 2. Towing Cables
        self._draw_towing_cables(banner_x, banner_y, banner_w, banner_h, plane_x, plane_y)

        # 3. Card HUD
        self._draw_glass_banner_card(banner_x, banner_y, banner_w, banner_h, palette)

        # 4. Provider Pill
        self._draw_provider_pill(banner_x, banner_y, banner_h, accent)

        # 5. Countdown Pill (with Multi-modal ETA)
        self._draw_countdown_pill(banner_x, banner_y, banner_w, banner_h, accent)

        # 6. Close Button
        self._draw_close_button(banner_x, banner_y, banner_w, banner_h)

        # 7. Event Details & ETA Route
        self._draw_event_details(banner_x, banner_y, banner_w, banner_h)

        # 8. Action Button
        self._draw_action_button(banner_x, banner_y, palette)

        # 9. Snooze Button
        self._draw_snooze_button(banner_x, banner_y, banner_w)

        # 10. Delegate Pilot Drawing to Renderer Strategy
        self.renderer.draw_pilot(plane_x, plane_y, self.tick)

        ctx.restoreGraphicsState()

    def _draw_towing_cables(self, bx, by, bw, bh, px, py):
        cable_hitch_x = px - 26
        cable_hitch_y = py + 8
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.4, 0.45, 0.55, 1.0).set()
        hitch_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
            AppKit.NSMakeRect(cable_hitch_x - 3, cable_hitch_y - 3, 6, 6)
        )
        hitch_path.fill()
        
        grommet_top = AppKit.NSMakePoint(bx + bw, by + bh - 24)
        grommet_bot = AppKit.NSMakePoint(bx + bw, by + 24)
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.6, 0.65, 0.75, 0.9).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(grommet_top.x - 3, grommet_top.y - 3, 6, 6)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(grommet_bot.x - 3, grommet_bot.y - 3, 6, 6)).fill()
        
        rope_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.94, 0.98, 0.85)
        rope_col.set()
        
        sag = math.sin(self.tick * 0.08) * 3.0
        
        top_rope = AppKit.NSBezierPath.bezierPath()
        top_rope.setLineWidth_(1.8)
        pattern = [5.0, 3.0]
        top_rope.setLineDash_count_phase_(pattern, 2, self.tick * 0.2)
        top_rope.moveToPoint_(grommet_top)
        mid_x1 = (grommet_top.x + cable_hitch_x) * 0.5
        mid_y1 = (grommet_top.y + cable_hitch_y) * 0.5 - 4.0 + sag
        top_rope.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(cable_hitch_x, cable_hitch_y + 3),
            AppKit.NSMakePoint(mid_x1, mid_y1),
            AppKit.NSMakePoint(mid_x1, mid_y1)
        )
        top_rope.stroke()
        
        bot_rope = AppKit.NSBezierPath.bezierPath()
        bot_rope.setLineWidth_(1.8)
        bot_rope.setLineDash_count_phase_(pattern, 2, self.tick * 0.2)
        bot_rope.moveToPoint_(grommet_bot)
        mid_x2 = (grommet_bot.x + cable_hitch_x) * 0.5
        mid_y2 = (grommet_bot.y + cable_hitch_y) * 0.5 - 6.0 + sag
        bot_rope.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(cable_hitch_x, cable_hitch_y - 3),
            AppKit.NSMakePoint(mid_x2, mid_y2),
            AppKit.NSMakePoint(mid_x2, mid_y2)
        )
        bot_rope.stroke()

    def _draw_glass_banner_card(self, bx, by, bw, bh, palette):
        card_rect = AppKit.NSMakeRect(bx, by, bw, bh)
        corner_radius = 20.0
        card_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(card_rect, corner_radius, corner_radius)
        
        shadow_layers = [
            (0.0, -8.0, 18.0, 0.35),
            (0.0, -3.0, 8.0, 0.25)
        ]
        for sx, sy, sblur, salpha in shadow_layers:
            s_rect = AppKit.NSMakeRect(bx + sx, by + sy, bw, bh)
            s_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(s_rect, corner_radius + 1, corner_radius + 1)
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.0, 0.0, 0.0, salpha).set()
            s_path.fill()
            
        cr, cg, cb = palette["card_tint"]
        bg_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.09 + cr * 0.3, 0.10 + cg * 0.3, 0.15 + cb * 0.3, 0.96)
        bg_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.04, 0.05, 0.08, 0.98)
        
        bg_gradient = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(bg_top, bg_bot)
        bg_gradient.drawInBezierPath_angle_(card_path, 270.0)
        
        border_col = palette["accent"].colorWithAlphaComponent_(0.65)
        border_col.set()
        card_path.setLineWidth_(1.8)
        card_path.stroke()

    def _draw_provider_pill(self, bx, by, bh, accent):
        prov_text = self.provider.strip()
        pill_x = bx + 18.0
        pill_y = by + bh - 32.0
        
        font = AppKit.NSFont.boldSystemFontOfSize_(11)
        attrs = {
            AppKit.NSFontAttributeName: font,
            AppKit.NSForegroundColorAttributeName: accent
        }
        
        ns_str = AppKit.NSString.stringWithString_(prov_text)
        str_size = ns_str.sizeWithAttributes_(attrs)
        pill_w = max(110.0, str_size.width + 18.0)
        pill_h = 20.0
        
        pill_rect = AppKit.NSMakeRect(pill_x, pill_y, pill_w, pill_h)
        pill_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pill_rect, 10.0, 10.0)
        
        accent.colorWithAlphaComponent_(0.16).set()
        pill_path.fill()
        
        accent.colorWithAlphaComponent_(0.38).set()
        pill_path.setLineWidth_(1.0)
        pill_path.stroke()
        
        text_pt = AppKit.NSMakePoint(pill_x + 9.0, pill_y + 3.0)
        ns_str.drawAtPoint_withAttributes_(text_pt, attrs)

    def _draw_countdown_pill(self, bx, by, bw, bh, accent):
        countdown_text = "⏰ Upcoming Alert"
        is_urgent = False
        mode_icon = MODE_ICONS.get(self.transport_mode, "🚆")
        
        if self.start_time:
            now = datetime.now()
            diff = (self.start_time - now).total_seconds()
            
            # Check Departure Deadline if available
            if self.is_travel and self.departure_time:
                dep_diff = (self.departure_time - now).total_seconds()
                dep_mins = int(dep_diff // 60)
                dep_time_str = self.departure_time.strftime("%H:%M")
                
                if dep_diff <= 0:
                    countdown_text = f"🚨 {mode_icon} TIME TO LEAVE!"
                    is_urgent = True
                elif dep_mins <= 10:
                    countdown_text = f"⏳ {mode_icon} Leave in {dep_mins}m ({dep_time_str})"
                    is_urgent = True
                else:
                    countdown_text = f"{mode_icon} Leave at {dep_time_str} (~{self.travel_time_minutes or 20}m)"
            elif diff > 0:
                mins = int(diff // 60)
                secs = int(diff % 60)
                if self.is_travel:
                    if mins >= 30:
                        countdown_text = f"{mode_icon} In {mins}m • Travel Notice"
                    elif mins >= 15:
                        countdown_text = f"{mode_icon} In {mins}m • Prepare to Leave"
                    else:
                        countdown_text = f"🚨 {mode_icon} Leave Now!"
                        is_urgent = True
                else:
                    if mins >= 15:
                        countdown_text = f"⏰ In {mins}m • Early Alert"
                    elif mins >= 5:
                        countdown_text = f"⏳ In {mins}m • Get Ready"
                    elif mins >= 1:
                        countdown_text = f"🚀 In {mins}m • Almost Time!"
                        is_urgent = True
                    else:
                        countdown_text = f"⏳ In {secs}s • Starting Now!"
                        is_urgent = True
            elif diff > -1800:
                countdown_text = "🔴 IN PROGRESS NOW"
                is_urgent = True
                
        time_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.40, 0.40, 1.0) if is_urgent else AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.88, 0.65, 1.0)
        
        font = AppKit.NSFont.boldSystemFontOfSize_(11)
        attrs = {
            AppKit.NSFontAttributeName: font,
            AppKit.NSForegroundColorAttributeName: time_col
        }
        
        ns_str = AppKit.NSString.stringWithString_(countdown_text)
        str_size = ns_str.sizeWithAttributes_(attrs)
        pill_w = str_size.width + 18.0
        pill_h = 20.0
        
        pill_x = bx + bw - 46.0 - pill_w
        pill_y = by + bh - 32.0
        
        pill_rect = AppKit.NSMakeRect(pill_x, pill_y, pill_w, pill_h)
        pill_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pill_rect, 10.0, 10.0)
        
        bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.08, 0.08, 0.8) if is_urgent else AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.24, 0.85)
        bg_col.set()
        pill_path.fill()
        
        border_col = time_col.colorWithAlphaComponent_(0.45)
        border_col.set()
        pill_path.setLineWidth_(1.0)
        pill_path.stroke()
        
        text_pt = AppKit.NSMakePoint(pill_x + 9.0, pill_y + 3.0)
        ns_str.drawAtPoint_withAttributes_(text_pt, attrs)

    def _draw_close_button(self, bx, by, bw, bh):
        is_pressed = (self.pressed_button == "close")
        is_hovered = (self.hovered_button == "close")
        
        btn_rect = AppKit.NSMakeRect(bx + bw - 36.0, by + bh - 34.0, 24.0, 24.0)
        btn_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(btn_rect)
        
        if is_pressed:
            fill_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.44, 0.58, 1.0)
        elif is_hovered:
            fill_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.32, 0.44, 1.0)
        else:
            fill_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.18, 0.20, 0.28, 0.85)
            
        fill_col.set()
        btn_path.fill()
        
        border_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.50, 0.55, 0.70, 0.65)
        border_col.set()
        btn_path.setLineWidth_(1.0)
        btn_path.stroke()
        
        close_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(13),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
        }
        AppKit.NSString.stringWithString_("✕").drawAtPoint_withAttributes_(
            AppKit.NSMakePoint(btn_rect.origin.x + 6.5, btn_rect.origin.y + 4.0),
            close_attrs
        )

    def _draw_event_details(self, bx, by, bw, bh):
        max_chars = 36
        short_title = self.title if len(self.title) <= max_chars else self.title[:max_chars - 3] + "..."
        
        title_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(14.5),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
        }
        
        detail_text = ""
        if self.start_time:
            s_time = self.start_time.strftime("%H:%M")
            if self.end_time:
                e_time = self.end_time.strftime("%H:%M")
                detail_text = f"🕒 {s_time} - {e_time}"
            else:
                detail_text = f"🕒 At {s_time}"
                
        if self.location:
            loc_short = self.location if len(self.location) <= 24 else self.location[:21] + "..."
            detail_text += f"  •  📍 {loc_short}"
            if self.travel_time_minutes:
                mode_icon = MODE_ICONS.get(self.transport_mode, "🚆")
                detail_text += f" ({mode_icon} ~{self.travel_time_minutes}m)"
        elif self.action_url and ("meet.google.com" in self.action_url or "zoom" in self.action_url):
            detail_text += "  •  🌐 Online Meeting"

        if detail_text:
            title_pt = AppKit.NSMakePoint(bx + 18.0, by + 72.0)
            AppKit.NSString.stringWithString_(short_title).drawAtPoint_withAttributes_(title_pt, title_attrs)

            sub_attrs = {
                AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(11.0),
                AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithRed_green_blue_alpha_(0.72, 0.76, 0.88, 1.0)
            }
            sub_pt = AppKit.NSMakePoint(bx + 18.0, by + 53.0)
            AppKit.NSString.stringWithString_(detail_text).drawAtPoint_withAttributes_(sub_pt, sub_attrs)
        else:
            title_pt = AppKit.NSMakePoint(bx + 18.0, by + 60.0)
            AppKit.NSString.stringWithString_(short_title).drawAtPoint_withAttributes_(title_pt, title_attrs)

    def _draw_action_button(self, bx, by, palette):
        is_pressed = (self.pressed_button == "action")
        is_hovered = (self.hovered_button == "action")
        
        btn_rect = AppKit.NSMakeRect(bx + 18.0, by + 12.0, 255.0, 33.0)
        btn_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(btn_rect, 10.0, 10.0)
        
        if is_pressed:
            c_top = palette["btn_gradient_bot"]
            c_bot = palette["btn_gradient_bot"]
        elif is_hovered:
            c_top = palette["accent_bright"]
            c_bot = palette["btn_gradient_top"]
        else:
            c_top = palette["btn_gradient_top"]
            c_bot = palette["btn_gradient_bot"]
            
        btn_grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(c_top, c_bot)
        btn_grad.drawInBezierPath_angle_(btn_path, 270.0)
        
        if not is_pressed:
            hi_rect = AppKit.NSMakeRect(btn_rect.origin.x + 1.0, btn_rect.origin.y + btn_rect.size.height - 2.0, btn_rect.size.width - 2.0, 1.5)
            AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.30).set()
            AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(hi_rect, 1.0, 1.0).fill()
            
        btn_text = self.action_btn_text
        text_font = AppKit.NSFont.boldSystemFontOfSize_(11.5)
        text_attrs = {
            AppKit.NSFontAttributeName: text_font,
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.12, 1.0)
        }
        
        ns_str = AppKit.NSString.stringWithString_(btn_text)
        str_size = ns_str.sizeWithAttributes_(text_attrs)
        
        text_x = btn_rect.origin.x + (btn_rect.size.width - str_size.width) * 0.5
        text_y = btn_rect.origin.y + (btn_rect.size.height - str_size.height) * 0.5 + 1.0
        
        if is_pressed:
            text_y -= 1.0
            
        ns_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(text_x, text_y), text_attrs)

    def _draw_snooze_button(self, bx, by, bw):
        is_pressed = (self.pressed_button == "snooze")
        is_hovered = (self.hovered_button == "snooze")
        
        btn_rect = AppKit.NSMakeRect(bx + bw - 128.0, by + 12.0, 110.0, 33.0)
        btn_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(btn_rect, 10.0, 10.0)
        
        if is_pressed:
            bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.32, 0.35, 0.48, 1.0)
        elif is_hovered:
            bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.24, 0.26, 0.36, 1.0)
        else:
            bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.23, 0.90)
            
        bg_col.set()
        btn_path.fill()
        
        border_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.38, 0.42, 0.56, 0.70)
        border_col.set()
        btn_path.setLineWidth_(1.0)
        btn_path.stroke()
        
        text_font = AppKit.NSFont.boldSystemFontOfSize_(11.5)
        text_attrs = {
            AppKit.NSFontAttributeName: text_font,
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.92, 1.0, 1.0)
        }
        
        snooze_sec = int(config.get("default_snooze_seconds", 120))
        snooze_mins = max(1, snooze_sec // 60)
        ns_str = AppKit.NSString.stringWithString_(f"💤 Snooze {snooze_mins}m")
        str_size = ns_str.sizeWithAttributes_(text_attrs)
        
        text_x = btn_rect.origin.x + (btn_rect.size.width - str_size.width) * 0.5
        text_y = btn_rect.origin.y + (btn_rect.size.height - str_size.height) * 0.5 + 1.0
        
        if is_pressed:
            text_y -= 1.0
            
        ns_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(text_x, text_y), text_attrs)
