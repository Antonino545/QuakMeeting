"""
High-Performance Banner View component for QuakMeeting.
Features:
- Pilot Speech Bubbles with Late Urgency Quotes & Classroom context
- Turbo Afterburner flame particle emission in Emergency Late Mode
- Smart '📍 I'm Here' arrival dismissal button
- Dedicated Classroom badge and smart lecture countdowns
"""
import AppKit
import objc
import math
import random
from datetime import datetime
from typing import Dict, Any, Optional

from core.services.config_service import config
from core.services.eta_service import MODE_ICONS, MODE_LABELS
from core.domain.models import format_duration
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

        # Classroom & Teacher Metadata
        self.classroom = meeting_data.get("classroom")
        self.teacher = meeting_data.get("teacher")

        # Multi-modal Travel & ETA metadata
        self.travel_time_minutes = meeting_data.get("travel_time_minutes")
        self.travel_distance_km = meeting_data.get("travel_distance_km")
        self.transport_mode = meeting_data.get("transport_mode", config.get("transport_mode", "transit"))
        self.departure_time = meeting_data.get("departure_time")
        self.origin_address = meeting_data.get("origin_address")
        self.eta_text = meeting_data.get("eta_text")

        # Determine Late Status
        self.is_late = self._compute_is_late()

        # Instantiate pilot renderer
        self.renderer = get_pilot_renderer(self.pilot_type)

        # Reminder stage metadata (e.g. 20, 10, 5, 2, 0)
        self.reminder_stage = meeting_data.get("reminder_stage")

        # Flight dynamics & geometry (Boost speed by 40% when late)
        base_speed = float(config.get("flight_speed", 3.2))
        self.speed = base_speed * 1.40 if self.is_late else base_speed
        self.x = -720.0
        self.base_y = 48.0
        self.tick = 0
        self.is_paused = False

        self.has_real_url = bool(
            self.action_url and
            self.action_url.strip() and
            self.action_url != "https://calendar.apple.com"
        )
        self.has_maps_url = bool(
            self.has_real_url and
            "maps.apple.com" in self.action_url.lower()
        )

        # Particle emitters (Smoke, Sparkles, Turbo Afterburner Flames)
        self.smoke_particles = []
        self.sparkle_particles = []
        self.flame_particles = []

        # Hover & Click Interaction State
        self.pressed_button = None
        self.hovered_button = None

        # Card Layout Dimensions
        self.banner_w = 535.0
        self.banner_h = 126.0

        # Precompute Theme Palette & Cached Fonts/Colors
        self._palette = self._build_theme_palette()
        self._init_cached_resources()

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

    def _compute_is_late(self) -> bool:
        """Determines if the event is already past departure time or past start time."""
        now = datetime.now().astimezone()
        if self.is_travel and self.departure_time:
            return now > self.departure_time
        if self.start_time:
            return now > self.start_time
        return False

    def _init_cached_resources(self):
        """Precomputes and caches NSFont and NSColor attributes to avoid allocation in draw loop."""
        self._font_title = AppKit.NSFont.boldSystemFontOfSize_(14.5)
        self._font_pill = AppKit.NSFont.boldSystemFontOfSize_(11)
        self._font_btn = AppKit.NSFont.boldSystemFontOfSize_(12.0)
        self._font_btn_sec = AppKit.NSFont.boldSystemFontOfSize_(11.5)
        self._font_sub = AppKit.NSFont.systemFontOfSize_(12)
        self._font_bubble = AppKit.NSFont.boldSystemFontOfSize_(10.5)

        self._color_white = AppKit.NSColor.whiteColor()
        self._color_sub = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.72, 0.76, 0.88, 1.0)
        self._color_urgent_time = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.35, 0.35, 1.0)
        self._color_normal_time = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.88, 0.65, 1.0)
        self._color_arrived = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.85, 0.55, 1.0)

        # Precompute static truncated title
        max_chars = 34
        self._cached_short_title = self.title if len(self.title) <= max_chars else self.title[:max_chars - 3] + "..."

        # Precompute static details string
        detail_text = ""
        if self.start_time:
            s_time = self.start_time.astimezone().strftime("%H:%M")
            if self.end_time:
                e_time = self.end_time.astimezone().strftime("%H:%M")
                detail_text = f"🕒 {s_time} - {e_time}"
            else:
                detail_text = f"🕒 At {s_time}"

        if self.classroom:
            detail_text += f"  •  🏫 {self.classroom}"
        elif self.location:
            loc_short = self.location if len(self.location) <= 20 else self.location[:17] + "..."
            detail_text += f"  •  📍 {loc_short}"
            if self.travel_time_minutes:
                mode_icon = MODE_ICONS.get(self.transport_mode, "🚆")
                dur_str = format_duration(self.travel_time_minutes)
                detail_text += f" ({mode_icon} ~{dur_str})"
        elif self.action_url and ("meet.google.com" in self.action_url or "zoom" in self.action_url):
            detail_text += "  •  🌐 Online Meeting"

        if self.teacher:
            detail_text += f" ({self.teacher})"

        self._cached_detail_text = detail_text

        # Precompute pilot speech bubble text
        self._cached_speech_text = self._build_pilot_speech_text()

        # Cached countdown string (refreshed every 0.5s in stepAnimation_)
        self._cached_countdown_text = "⏰ Upcoming Alert"
        self._cached_is_urgent = False
        self._update_countdown_text()

    def _build_pilot_speech_text(self) -> str:
        """Constructs funny context-aware quote for the pilot speech bubble."""
        if self.is_late:
            if self.pilot_type == "owl":
                if self.classroom:
                    return f"🚨 CLASS STARTED IN {self.classroom.upper()}! SPRINT!"
                return "🚨 PROFESSOR IS STARTING! YOU'RE LATE!"
            elif self.pilot_type == "chef":
                return "🔥 THE FOOD IS GETTING COLD! HURRY!"
            elif self.pilot_type == "captain":
                return "⚠️ LAST CALL FOR BOARDING! SPRINT TO GATE!"
            elif self.pilot_type == "driver":
                return "🔥 FLOOR THE GAS! WE ARE LATE!"
            elif self.pilot_type == "gym":
                return "🔥 DON'T SKIP WORKOUT! TIME FOR GAINS! 🏋️‍♂️"
            elif self.pilot_type == "zen_duck":
                return "🚨 BREATHE IN... AND SPRINT! 🏃💨"
            else:
                return "QUAAK! 🚨 YOU ARE LATE! RUN!"
        else:
            if self.pilot_type == "owl":
                if self.classroom:
                    return f"Class in {self.classroom} soon! 📚"
                return "Class starting soon! 🦉"
            elif self.pilot_type == "chef":
                return "Dinner / food time soon! 🍕"
            elif self.pilot_type == "captain":
                return "Cabin crew, prepare for takeoff ✈️"
            elif self.pilot_type == "driver":
                return "Engines running, ready to roll! 🏎️"
            elif self.pilot_type == "gym":
                return "Time to train & crush workout! 🏋️‍♂️💪"
            elif self.pilot_type == "zen_duck":
                return "Time for wellness & calm 🌸"
            else:
                return "Quak! Ready for takeoff! 🦆"

    def _update_countdown_text(self):
        countdown_text = "⏰ Upcoming Alert"
        is_urgent = False
        mode_icon = MODE_ICONS.get(self.transport_mode, "🚆")

        if self.start_time:
            now = datetime.now().astimezone()
            diff = (self.start_time - now).total_seconds()

            if self.is_travel and self.departure_time:
                dep_diff = (self.departure_time - now).total_seconds()
                dep_mins = int(dep_diff // 60)
                dep_time_str = self.departure_time.astimezone().strftime("%H:%M")
                dur_str = format_duration(self.travel_time_minutes or 20)

                if dep_diff <= 0:
                    late_min = abs(int(dep_diff // 60))
                    countdown_text = f"🚨 {mode_icon} LATE BY {late_min}m • LEAVE NOW!" if late_min > 0 else f"🚨 {mode_icon} DEPART NOW!"
                    is_urgent = True
                elif dep_mins <= 10:
                    countdown_text = f"⏳ {mode_icon} Leave in {dep_mins}m ({dep_time_str})"
                    is_urgent = True
                else:
                    countdown_text = f"{mode_icon} Leave at {dep_time_str} (~{dur_str})"
            elif diff > 0:
                mins = int(diff // 60)
                secs = int(diff % 60)
                if self.classroom:
                    if mins >= 10:
                        countdown_text = f"🎓 Lesson in {mins}m • {self.classroom}"
                    elif mins >= 1:
                        countdown_text = f"⏳ Class in {mins}m • {self.classroom}"
                        is_urgent = True
                    else:
                        countdown_text = f"🚨 Class starting now • {self.classroom}"
                        is_urgent = True
                elif self.is_travel:
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
                late_mins = abs(int(diff // 60))
                countdown_text = f"🔴 LATE BY {late_mins}m • IN PROGRESS" if late_mins > 0 else "🔴 IN PROGRESS NOW"
                is_urgent = True

        self._cached_countdown_text = countdown_text
        self._cached_is_urgent = is_urgent

    def _get_button_rects(self, banner_x, banner_y):
        """Returns accurate bounding rects for all interactive elements."""
        btn_close_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 36, banner_y + self.banner_h - 34, 24, 24)
        btn_close_hit_rect = AppKit.NSMakeRect(banner_x + self.banner_w - 44, banner_y + self.banner_h - 44, 40, 40)

        # 4 Button Bar: [Action] [I'm Here] [Snooze 5m] [Snooze 15m]
        btn_action_rect = AppKit.NSMakeRect(banner_x + 18, banner_y + 12, 220, 33)
        is_stage_zero = (self.reminder_stage == 0)

        if self.has_maps_url:
            btn_arrived_rect = AppKit.NSMakeRect(banner_x + 246, banner_y + 12, 100, 33)
            if is_stage_zero:
                if not self.has_real_url:
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
                if not self.has_real_url:
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
        elif AppKit.NSPointInRect(loc, rects["arrived"]):
            self.hovered_button = "arrived"
            AppKit.NSCursor.pointingHandCursor().set()
        elif AppKit.NSPointInRect(loc, rects["snooze1"]):
            self.hovered_button = "snooze1"
            AppKit.NSCursor.pointingHandCursor().set()
        elif AppKit.NSPointInRect(loc, rects["snooze2"]):
            self.hovered_button = "snooze2"
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
        elif AppKit.NSPointInRect(loc, rects["arrived"]):
            self.pressed_button = "arrived"
        elif AppKit.NSPointInRect(loc, rects["snooze1"]):
            self.pressed_button = "snooze1"
        elif AppKit.NSPointInRect(loc, rects["snooze2"]):
            self.pressed_button = "snooze2"
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
                if self.has_real_url:
                    self.controller.trigger_action()
                else:
                    self.controller.trigger_acknowledge()
        elif clicked == "arrived" and AppKit.NSPointInRect(loc, rects["arrived"]):
            if self.controller:
                self.controller.trigger_arrived()
        elif clicked == "snooze1" and AppKit.NSPointInRect(loc, rects["snooze1"]):
            if self.controller:
                if self.reminder_stage == 0:
                    self.controller.trigger_acknowledge()
                else:
                    self.controller.trigger_snooze(300) # 5 minutes
        elif clicked == "snooze2" and AppKit.NSPointInRect(loc, rects["snooze2"]):
            if self.controller:
                if self.reminder_stage == 0:
                    self.controller.trigger_acknowledge()
                else:
                    self.controller.trigger_arrived() # Skip event
        elif clicked == "card" and AppKit.NSPointInRect(loc, rects["card"]):
            if self.controller:
                if self.has_real_url:
                    self.controller.trigger_action()
                else:
                    self.controller.trigger_acknowledge()

    def stepAnimation_(self, timer):
        self.tick += 1
        screen_w = self.bounds().size.width

        if not self.is_paused:
            self.x += self.speed
            if self.x > screen_w + 650:
                # Pre-event stages (> 0) fly across only once, then auto-dismiss.
                # Event-time (stage 0) persists/loops until acknowledged.
                if self.reminder_stage is not None and self.reminder_stage > 0:
                    if self.controller:
                        self.controller.dismiss()
                    return
                else:
                    self.x = -720.0

        # Update countdown once every 30 frames (~0.5s) to save CPU
        if self.tick % 30 == 0:
            self._update_countdown_text()

        plane_x = self.x + 605.0
        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        plane_y = y_wave + 4.0

        # 1. Turbo Flame Emitter (When Late / Emergency Mode)
        if self.is_late and not self.is_paused:
            # Emit dual afterburner fiery particles
            for dy_eng in [-10, 10]:
                self.flame_particles.append({
                    "x": plane_x - 30.0,
                    "y": plane_y + dy_eng + (random.random() - 0.5) * 4.0,
                    "r": 5.5 + random.random() * 3.0,
                    "alpha": 0.95,
                    "vx": -4.2 - random.random() * 2.0,
                    "vy": (random.random() - 0.5) * 1.5,
                    "color_stage": 0 # 0=gold/yellow, 1=orange, 2=red
                })

        # 2. Standard Smoke / Sparkles (Active during flight)
        if self.tick % 4 == 0 and not self.is_paused:
            if not self.is_late:
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

        # Update flames
        new_flames = []
        for f in self.flame_particles:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            f["r"] += 0.4
            f["alpha"] -= 0.05
            f["color_stage"] = min(2, f["color_stage"] + 0.1)
            if f["alpha"] > 0 and f["r"] < 28:
                new_flames.append(f)
        self.flame_particles = new_flames

        # Update smoke
        new_particles = []
        for p in self.smoke_particles:
            p["x"] -= 2.4
            p["y"] += p.get("drift", 0.0) + math.sin(p["x"] * 0.04) * 0.3
            p["r"] += 0.35
            p["alpha"] -= 0.022
            if p["alpha"] > 0 and p["r"] < 24:
                new_particles.append(p)
        self.smoke_particles = new_particles

        # Update sparkles
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

    def _build_theme_palette(self):
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
        elif self.pilot_type == "gym":
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.38, 0.18, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.58, 0.28, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.40, 0.16, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.20, 0.08, 1.0)
            card_tint = (0.14, 0.07, 0.06)
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

        palette = self._palette
        accent = palette["accent"]

        y_wave = self.base_y + math.sin(self.tick * 0.038) * 8.0
        plane_x = self.x + 605.0
        plane_y = y_wave + 4.0

        banner_x = self.x
        banner_y = y_wave - 10.0
        banner_w = self.banner_w
        banner_h = self.banner_h

        # 1. Turbo Flame Particles (Afterburners)
        for f in self.flame_particles:
            stage = f["color_stage"]
            if stage < 1.0:
                f_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.90, 0.30, f["alpha"])
            elif stage < 2.0:
                f_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.52, 0.15, f["alpha"])
            else:
                f_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.22, 0.18, f["alpha"] * 0.8)

            f_col.set()
            f_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
                AppKit.NSMakeRect(f["x"] - f["r"], f["y"] - f["r"], f["r"] * 2, f["r"] * 2)
            )
            f_path.fill()

        # 2. Standard Smoke & Sparkles
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

        # 3. Towing Cables
        self._draw_towing_cables(banner_x, banner_y, banner_w, banner_h, plane_x, plane_y)

        # 4. Card HUD
        self._draw_glass_banner_card(banner_x, banner_y, banner_w, banner_h, palette)

        # 5. Provider Pill & Classroom Badge
        self._draw_provider_pill(banner_x, banner_y, banner_h, accent)

        # 6. Countdown Pill
        self._draw_countdown_pill(banner_x, banner_y, banner_w, banner_h, accent)

        # 7. Close Button
        self._draw_close_button(banner_x, banner_y, banner_w, banner_h)

        # 8. Event Details & Classroom / ETA Route
        self._draw_event_details(banner_x, banner_y, banner_w, banner_h)

        # 9. Action Buttons Bar ([Action] [📍 I'm Here] [💤 Snooze])
        self._draw_buttons_bar(banner_x, banner_y, palette)

        # 10. Delegate Pilot Drawing to Renderer Strategy
        self.renderer.draw_pilot(plane_x, plane_y, self.tick)

        # 11. Pilot Speech Bubble (Animated dialogue above the pilot)
        self._draw_pilot_speech_bubble(plane_x, plane_y)

    def _draw_towing_cables(self, bx, by, bw, bh, px, py):
        cable_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.40, 0.35, 0.65) if self.is_late else AppKit.NSColor.colorWithWhite_alpha_(0.85, 0.42)
        cable_col.set()

        cable_top = AppKit.NSBezierPath.bezierPath()
        cable_top.setLineWidth_(1.5)
        cable_top.moveToPoint_(AppKit.NSMakePoint(bx + bw, by + bh - 24.0))
        ctrl_pt1 = AppKit.NSMakePoint(bx + bw + (px - bx - bw) * 0.45, by + bh - 16.0)
        cable_top.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 16.0, py + 8.0),
            ctrl_pt1,
            AppKit.NSMakePoint(px - 32.0, py + 12.0)
        )
        cable_top.stroke()

        cable_bot = AppKit.NSBezierPath.bezierPath()
        cable_bot.setLineWidth_(1.5)
        cable_bot.moveToPoint_(AppKit.NSMakePoint(bx + bw, by + 24.0))
        ctrl_pt2 = AppKit.NSMakePoint(bx + bw + (px - bx - bw) * 0.45, by + 16.0)
        cable_bot.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 16.0, py - 4.0),
            ctrl_pt2,
            AppKit.NSMakePoint(px - 32.0, py - 6.0)
        )
        cable_bot.stroke()

    def _draw_glass_banner_card(self, bx, by, bw, bh, palette):
        card_rect = AppKit.NSMakeRect(bx, by, bw, bh)
        card_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(card_rect, 18.0, 18.0)

        # Frosted glass dark base
        tint = palette["card_tint"]
        bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(tint[0], tint[1], tint[2], 0.95)
        bg_col.set()
        card_path.fill()

        # Subtle rim highlight / Emergency red pulse when late
        if self.is_late:
            pulse = math.sin(self.tick * 0.15) * 0.3 + 0.7
            border_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.30, 0.30, pulse)
            card_path.setLineWidth_(1.8)
        else:
            border_col = AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.16)
            card_path.setLineWidth_(1.0)

        border_col.set()
        card_path.stroke()

    def _draw_provider_pill(self, bx, by, bh, accent):
        attrs = {
            AppKit.NSFontAttributeName: self._font_pill,
            AppKit.NSForegroundColorAttributeName: accent
        }

        ns_str = AppKit.NSString.stringWithString_(self.provider.upper())
        str_size = ns_str.sizeWithAttributes_(attrs)
        pill_w = str_size.width + 16.0
        pill_h = 20.0

        pill_x = bx + 18.0
        pill_y = by + bh - 32.0

        pill_rect = AppKit.NSMakeRect(pill_x, pill_y, pill_w, pill_h)
        pill_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pill_rect, 10.0, 10.0)

        accent.colorWithAlphaComponent_(0.14).set()
        pill_path.fill()

        accent.colorWithAlphaComponent_(0.38).set()
        pill_path.setLineWidth_(1.0)
        pill_path.stroke()

        text_pt = AppKit.NSMakePoint(pill_x + 8.0, pill_y + 3.0)
        ns_str.drawAtPoint_withAttributes_(text_pt, attrs)

        # Draw Classroom Badge if available
        if self.classroom:
            c_attrs = {
                AppKit.NSFontAttributeName: self._font_pill,
                AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.72, 1.0, 1.0)
            }
            c_str = AppKit.NSString.stringWithString_(f"🏫 {self.classroom}")
            c_size = c_str.sizeWithAttributes_(c_attrs)
            c_pill_x = pill_x + pill_w + 8.0
            c_pill_rect = AppKit.NSMakeRect(c_pill_x, pill_y, c_size.width + 14.0, pill_h)
            c_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(c_pill_rect, 10.0, 10.0)

            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 0.20, 0.55, 0.65).set()
            c_path.fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.75, 0.55, 0.95, 0.65).set()
            c_path.setLineWidth_(1.0)
            c_path.stroke()

            c_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(c_pill_x + 7.0, pill_y + 3.0), c_attrs)

    def _draw_countdown_pill(self, bx, by, bw, bh, accent):
        countdown_text = self._cached_countdown_text
        is_urgent = self._cached_is_urgent

        time_col = self._color_urgent_time if is_urgent else self._color_normal_time

        attrs = {
            AppKit.NSFontAttributeName: self._font_pill,
            AppKit.NSForegroundColorAttributeName: time_col
        }

        ns_str = AppKit.NSString.stringWithString_(countdown_text)
        str_size = ns_str.sizeWithAttributes_(attrs)
        pill_w = str_size.width + 18.0
        pill_h = 20.0

        pill_x = bx + bw - 44.0 - pill_w
        pill_y = by + bh - 32.0

        pill_rect = AppKit.NSMakeRect(pill_x, pill_y, pill_w, pill_h)
        pill_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pill_rect, 10.0, 10.0)

        bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.26, 0.08, 0.08, 0.88) if is_urgent else AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.24, 0.85)
        bg_col.set()
        pill_path.fill()

        border_col = time_col.colorWithAlphaComponent_(0.55)
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
            AppKit.NSFontAttributeName: self._font_btn_sec,
            AppKit.NSForegroundColorAttributeName: self._color_white
        }
        AppKit.NSString.stringWithString_("✕").drawAtPoint_withAttributes_(
            AppKit.NSMakePoint(btn_rect.origin.x + 7.0, btn_rect.origin.y + 4.0),
            close_attrs
        )

    def _draw_event_details(self, bx, by, bw, bh):
        title_attrs = {
            AppKit.NSFontAttributeName: self._font_title,
            AppKit.NSForegroundColorAttributeName: self._color_white
        }

        title_pt = AppKit.NSMakePoint(bx + 18.0, by + bh - 58.0)
        AppKit.NSString.stringWithString_(self._cached_short_title).drawAtPoint_withAttributes_(title_pt, title_attrs)

        sub_attrs = {
            AppKit.NSFontAttributeName: self._font_sub,
            AppKit.NSForegroundColorAttributeName: self._color_sub
        }
        sub_pt = AppKit.NSMakePoint(bx + 18.0, by + bh - 78.0)
        AppKit.NSString.stringWithString_(self._cached_detail_text).drawAtPoint_withAttributes_(sub_pt, sub_attrs)

    def _draw_buttons_bar(self, bx, by, palette):
        # 1. Main Action Button
        is_pressed_act = (self.pressed_button == "action")
        is_hovered_act = (self.hovered_button == "action")

        btn_act_rect = AppKit.NSMakeRect(bx + 18.0, by + 12.0, 220.0, 33.0)
        btn_act_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(btn_act_rect, 9.0, 9.0)

        if not self.has_real_url:
            # Render as "✅ Got it" acknowledge button (blue tint)
            top_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.1, 0.6, 0.7, 1.0)
            bot_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.0, 0.4, 0.5, 1.0)
            btn_text = "✅ Got it"
        else:
            top_c = palette["btn_gradient_top"]
            bot_c = palette["btn_gradient_bot"]
            btn_text = self.action_btn_text

        if is_pressed_act:
            grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(bot_c, top_c)
        elif is_hovered_act:
            hover_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.2, 0.8, 0.9, 1.0) if not self.has_real_url else palette["accent_bright"]
            grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(hover_color, bot_c)
        else:
            grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(top_c, bot_c)

        grad.drawInBezierPath_angle_(btn_act_path, 270.0)

        btn_attrs = {
            AppKit.NSFontAttributeName: self._font_btn,
            AppKit.NSForegroundColorAttributeName: self._color_white
        }
        ns_btn_str = AppKit.NSString.stringWithString_(btn_text)
        str_size = ns_btn_str.sizeWithAttributes_(btn_attrs)
        text_x = btn_act_rect.origin.x + (btn_act_rect.size.width - str_size.width) * 0.5
        text_y = btn_act_rect.origin.y + (btn_act_rect.size.height - str_size.height) * 0.5
        ns_btn_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(text_x, text_y), btn_attrs)

        rects = self._get_button_rects(bx, by)

        # 2. "📍 I'm Here" Arrival Dismissal Button
        if self.has_maps_url:
            is_pressed_arr = (self.pressed_button == "arrived")
            is_hovered_arr = (self.hovered_button == "arrived")

            btn_arr_rect = rects["arrived"]
            btn_arr_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(btn_arr_rect, 9.0, 9.0)

            if is_pressed_arr:
                arr_fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.45, 0.28, 0.95)
            elif is_hovered_arr:
                arr_fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.38, 0.22, 0.90)
            else:
                arr_fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.08, 0.25, 0.16, 0.85)

            arr_fill.set()
            btn_arr_path.fill()

            arr_border = self._color_arrived.colorWithAlphaComponent_(0.45)
            arr_border.set()
            btn_arr_path.setLineWidth_(1.0)
            btn_arr_path.stroke()

            arr_attrs = {
                AppKit.NSFontAttributeName: self._font_btn_sec,
                AppKit.NSForegroundColorAttributeName: self._color_arrived
            }
            ns_arr_str = AppKit.NSString.stringWithString_("📍 I'm Here")
            arr_size = ns_arr_str.sizeWithAttributes_(arr_attrs)
            arr_tx = btn_arr_rect.origin.x + (btn_arr_rect.size.width - arr_size.width) * 0.5
            arr_ty = btn_arr_rect.origin.y + (btn_arr_rect.size.height - arr_size.height) * 0.5
            ns_arr_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(arr_tx, arr_ty), arr_attrs)

        # 3. Snooze / Acknowledge Buttons
        is_stage_zero = (self.reminder_stage == 0)

        def _draw_snooze_btn(btn_key, rect, text_str):
            if rect.size.width == 0: return
            is_pressed = (self.pressed_button == btn_key)
            is_hovered = (self.hovered_button == btn_key)
            path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 9.0, 9.0)

            if is_stage_zero:
                # "✅ Got it" styling
                if is_pressed:
                    fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.18, 0.40, 0.65, 0.95)
                elif is_hovered:
                    fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.48, 0.80, 0.90)
                else:
                    fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.30, 0.55, 0.85)
                border = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.65, 1.0, 0.50)
                txt_col = AppKit.NSColor.whiteColor()
            else:
                # "💤 Snooze" styling
                if is_pressed:
                    fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.32, 0.44, 0.95)
                elif is_hovered:
                    fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.25, 0.36, 0.90)
                else:
                    fill = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.17, 0.25, 0.85)
                border = AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.16)
                txt_col = self._color_sub

            fill.set()
            path.fill()
            border.set()
            path.setLineWidth_(1.0)
            path.stroke()

            s_attrs = {
                AppKit.NSFontAttributeName: self._font_btn_sec,
                AppKit.NSForegroundColorAttributeName: txt_col
            }
            ns_str = AppKit.NSString.stringWithString_(text_str)
            s_size = ns_str.sizeWithAttributes_(s_attrs)
            tx = rect.origin.x + (rect.size.width - s_size.width) * 0.5
            ty = rect.origin.y + (rect.size.height - s_size.height) * 0.5
            ns_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(tx, ty), s_attrs)

        if is_stage_zero:
            _draw_snooze_btn("snooze1", rects["snooze1"], "✅ Got it")
        else:
            _draw_snooze_btn("snooze1", rects["snooze1"], "💤 5m")
            _draw_snooze_btn("snooze2", rects["snooze2"], "⏭️ Skip")

    def _draw_pilot_speech_bubble(self, px, py):
        """Draws an animated floating speech bubble pointing directly at the pilot."""
        text = self._cached_speech_text
        if not text:
            return

        bubble_attrs = {
            AppKit.NSFontAttributeName: self._font_bubble,
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
        }
        ns_str = AppKit.NSString.stringWithString_(text)
        text_size = ns_str.sizeWithAttributes_(bubble_attrs)

        bw = text_size.width + 20.0
        bh = 26.0
        bx = px - bw * 0.5
        by = py + 36.0 + math.sin(self.tick * 0.08) * 3.0

        # Bubble Container Shape with Tail
        bubble_rect = AppKit.NSMakeRect(bx, by, bw, bh)
        bubble_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bubble_rect, 10.0, 10.0)

        # Tail pointing to pilot
        tail_path = AppKit.NSBezierPath.bezierPath()
        tail_path.moveToPoint_(AppKit.NSMakePoint(px - 6.0, by))
        tail_path.lineToPoint_(AppKit.NSMakePoint(px, by - 8.0))
        tail_path.lineToPoint_(AppKit.NSMakePoint(px + 6.0, by))
        tail_path.closePath()

        if self.is_late:
            bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.16, 0.16, 0.95)
            border_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.45, 0.45, 1.0)
        else:
            bg_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.14, 0.16, 0.24, 0.92)
            border_col = AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.25)

        bg_col.set()
        bubble_path.fill()
        tail_path.fill()

        border_col.set()
        bubble_path.setLineWidth_(1.2)
        bubble_path.stroke()

        text_pt = AppKit.NSMakePoint(bx + 10.0, by + 5.0)
        ns_str.drawAtPoint_withAttributes_(text_pt, bubble_attrs)
