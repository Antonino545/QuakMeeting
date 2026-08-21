import AppKit
import objc
import webbrowser
import math
import subprocess
import time
import os
from datetime import datetime
from config_manager import config

class QuakPitBannerView(AppKit.NSView):
    def initWithFrame_meetingData_controller_(self, frame, meeting_data, controller):
        self = objc.super(QuakPitBannerView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.meeting_data = meeting_data
        self.controller = controller
        
        self.title = meeting_data.get("title", "Promemoria Evento")
        self.provider = meeting_data.get("provider", "Evento")
        self.action_url = meeting_data.get("action_url") or meeting_data.get("meeting_url")
        self.action_btn_text = meeting_data.get("action_btn_text", "🚀 PARTECIPA ORA")
        self.start_time = meeting_data.get("start_time")
        self.end_time = meeting_data.get("end_time")
        self.location = meeting_data.get("location", "")
        self.pilot_type = meeting_data.get("pilot_type", "duck")
        self.is_travel = meeting_data.get("is_travel", False)
        
        # Flight dynamics & geometry (Caricati dinamicamente da config.json)
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
        
        # Card Layout Dimensions (Expanded height to guarantee zero compenetration)
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
        elif AppKit.NSPointInRect(loc, rects["snooze"]):
            self.hovered_button = "snooze"
            AppKit.NSCursor.pointingHandCursor().set()
        elif AppKit.NSPointInRect(loc, rects["action"]):
            self.hovered_button = "action"
            AppKit.NSCursor.pointingHandCursor().set()
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
        elif AppKit.NSPointInRect(loc, rects["snooze"]):
            self.pressed_button = "snooze"
        elif AppKit.NSPointInRect(loc, rects["action"]):
            self.pressed_button = "action"
        elif AppKit.NSPointInRect(loc, rects["card"]):
            self.pressed_button = "action"
            
        self.setNeedsDisplay_(True)

    def mouseUp_(self, event):
        loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        btn = self.pressed_button
        self.pressed_button = None
        self.setNeedsDisplay_(True)
        
        if btn == "close":
            self.controller.close()
        elif btn == "snooze":
            snooze_sec = int(config.get("default_snooze_seconds", 120))
            self.controller.snooze(snooze_sec)
        elif btn == "action":
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
                # Twin jet contrails
                self.smoke_particles.append({"x": plane_x - 22, "y": plane_y - 12, "r": 4.0, "alpha": 0.75, "drift": -0.2})
                self.smoke_particles.append({"x": plane_x - 22, "y": plane_y + 12, "r": 4.0, "alpha": 0.75, "drift": 0.2})
            elif self.pilot_type == "zen_duck":
                # Gentle cloud & sparkle
                self.smoke_particles.append({"x": plane_x - 28, "y": plane_y + 4, "r": 4.5, "alpha": 0.65, "drift": 0.0})
                if self.tick % 8 == 0:
                    self.sparkle_particles.append({"x": plane_x - 24, "y": plane_y + 8, "r": 3.0, "alpha": 0.9, "vy": 0.4})
            elif self.pilot_type == "owl":
                # Magic golden star dust
                self.smoke_particles.append({"x": plane_x - 26, "y": plane_y + 6, "r": 4.2, "alpha": 0.6, "drift": 0.0})
                if self.tick % 10 == 0:
                    self.sparkle_particles.append({"x": plane_x - 22, "y": plane_y + 10, "r": 3.2, "alpha": 0.95, "vy": 0.3})
            else:
                # Classic biplane / delivery exhaust puff
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
        """Returns refined color palette for card accents, gradients, and buttons."""
        if self.pilot_type == "chef":
            # Coral / Warm Tangerine Food theme
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.44, 0.38, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.62, 0.48, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.38, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.30, 0.22, 1.0)
            card_tint = (0.13, 0.08, 0.08)
        elif self.pilot_type == "captain":
            # Sky Blue / Airline Aero theme
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.38, 0.68, 1.0, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.58, 0.82, 1.0, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.38, 0.68, 1.0, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.18, 0.45, 0.90, 1.0)
            card_tint = (0.07, 0.09, 0.14)
        elif self.pilot_type == "owl":
            # Royal Amethyst / Academic Purple theme
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.76, 0.52, 1.0, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.68, 1.0, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.75, 0.50, 0.98, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.55, 0.30, 0.82, 1.0)
            card_tint = (0.10, 0.07, 0.14)
        elif self.pilot_type == "driver":
            # Emerald / Fast Transit theme
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.85, 0.58, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.95, 0.72, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.24, 0.86, 0.58, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.65, 0.40, 1.0)
            card_tint = (0.06, 0.12, 0.09)
        elif self.pilot_type == "zen_duck":
            # Seafoam Teal / Wellness & Serenis theme
            accent = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.28, 0.88, 0.82, 1.0)
            accent_bright = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.48, 0.96, 0.90, 1.0)
            btn_gradient_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.28, 0.88, 0.82, 1.0)
            btn_gradient_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.68, 0.62, 1.0)
            card_tint = (0.06, 0.11, 0.12)
        else:
            # Sunny Golden Amber / Classic Video Meeting
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
        
        # 1. Scia di fumo particellare soffice & Sparkles
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
            
        # 2. Corde di traino dinamiche con catenaria flessuosa & raccordi metallici
        self._draw_towing_cables(banner_x, banner_y, banner_w, banner_h, plane_x, plane_y)

        # 3. Card del Banner (Frosted Glass HUD con Multi-layer Drop Shadow & Rim Lighting)
        self._draw_glass_banner_card(banner_x, banner_y, banner_w, banner_h, palette)

        # 4. Badge Provider Pill (Top-Left)
        self._draw_provider_pill(banner_x, banner_y, banner_h, accent)

        # 5. Live Countdown Pill (Top-Right)
        self._draw_countdown_pill(banner_x, banner_y, banner_w, banner_h, accent)

        # 6. Pulsante Chiudi Frosted Glass (Top-Right)
        self._draw_close_button(banner_x, banner_y, banner_w, banner_h)

        # 7. Titolo Evento & Sottotitolo Dettagli / Luogo (Spaziati perfettamente)
        self._draw_event_details(banner_x, banner_y, banner_w, banner_h)

        # 8. Pulsante Azione Primaria (PARTECIPA / MAPPE)
        self._draw_action_button(banner_x, banner_y, palette)

        # 9. Pulsante Snooze Secondario (💤 Snooze 2m)
        self._draw_snooze_button(banner_x, banner_y, banner_w)

        # 10. Disegna il Veicolo e Pilota con grafica vettoriale HD
        self._draw_dynamic_airplane(plane_x, plane_y)

        ctx.restoreGraphicsState()

    def _draw_towing_cables(self, bx, by, bw, bh, px, py):
        """Disegna doppie corde di traino elastiche con attacchi metallici."""
        cable_hitch_x = px - 26
        cable_hitch_y = py + 8
        
        # Attacchi metallici sull'aereo
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.4, 0.45, 0.55, 1.0).set()
        hitch_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
            AppKit.NSMakeRect(cable_hitch_x - 3, cable_hitch_y - 3, 6, 6)
        )
        hitch_path.fill()
        
        # Gommini di rinforzo sul banner
        grommet_top = AppKit.NSMakePoint(bx + bw, by + bh - 24)
        grommet_bot = AppKit.NSMakePoint(bx + bw, by + 24)
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.6, 0.65, 0.75, 0.9).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(grommet_top.x - 3, grommet_top.y - 3, 6, 6)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(grommet_bot.x - 3, grommet_bot.y - 3, 6, 6)).fill()
        
        # Corde con leggera curvatura dinamica (sag)
        rope_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.94, 0.98, 0.85)
        rope_col.set()
        
        sag = math.sin(self.tick * 0.08) * 3.0
        
        # Cavo superiore
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
        
        # Cavo inferiore
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
        """Disegna la card principale con stile Frosted Glass Dark HUD di macOS."""
        card_rect = AppKit.NSMakeRect(bx, by, bw, bh)
        corner_radius = 20.0
        card_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(card_rect, corner_radius, corner_radius)
        
        # Multi-layer Soft Drop Shadow per profondità realistica
        shadow_layers = [
            (0.0, -8.0, 18.0, 0.35),
            (0.0, -3.0, 8.0, 0.25)
        ]
        for sx, sy, sblur, salpha in shadow_layers:
            s_rect = AppKit.NSMakeRect(bx + sx, by + sy, bw, bh)
            s_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(s_rect, corner_radius + 1, corner_radius + 1)
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.0, 0.0, 0.0, salpha).set()
            s_path.fill()
            
        # Sfondo con Gradiente Acrylic Dark & Tinta Tema sottile
        cr, cg, cb = palette["card_tint"]
        bg_top = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.09 + cr * 0.3, 0.10 + cg * 0.3, 0.15 + cb * 0.3, 0.96)
        bg_bot = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.04, 0.05, 0.08, 0.98)
        
        bg_gradient = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(bg_top, bg_bot)
        bg_gradient.drawInBezierPath_angle_(card_path, 270.0)
        
        # Inner Glass Rim / Luce Riflessa sul bordo superiore
        highlight_rect = AppKit.NSMakeRect(bx + 1.5, by + bh - 3.0, bw - 3.0, 1.5)
        highlight_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(highlight_rect, 1.0, 1.0)
        AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.22).set()
        highlight_path.fill()
        
        # Bordo con Luce d'Accento del Tema
        border_col = palette["accent"].colorWithAlphaComponent_(0.65)
        border_col.set()
        card_path.setLineWidth_(1.8)
        card_path.stroke()

    def _draw_provider_pill(self, bx, by, bh, accent):
        """Pillola badge elegante con icona e nome provider (es. Google Meet, Serenis, Volo)."""
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
        
        # Sfondo pillola semi-trasparente
        accent.colorWithAlphaComponent_(0.16).set()
        pill_path.fill()
        
        # Bordo sottile pillola
        accent.colorWithAlphaComponent_(0.38).set()
        pill_path.setLineWidth_(1.0)
        pill_path.stroke()
        
        # Testo pillola centrato verticalmente
        text_pt = AppKit.NSMakePoint(pill_x + 9.0, pill_y + 3.0)
        ns_str.drawAtPoint_withAttributes_(text_pt, attrs)

    def _draw_countdown_pill(self, bx, by, bw, bh, accent):
        """Badge con Countdown Dinamico / Avviso Anticipato."""
        countdown_text = "⏰ Avviso Imminente"
        is_urgent = False
        
        if self.start_time:
            now = datetime.now()
            diff = (self.start_time - now).total_seconds()
            if diff > 0:
                mins = int(diff // 60)
                secs = int(diff % 60)
                if self.is_travel:
                    countdown_text = f"🚗 Parti tra {mins} min"
                else:
                    if mins < 1:
                        countdown_text = f"⏳ Inizia tra {secs}s"
                        is_urgent = True
                    else:
                        countdown_text = f"⏳ Inizia tra {mins}m"
                        if mins <= 5:
                            is_urgent = True
            elif diff > -1800:
                countdown_text = "🔴 IN CORSO ORA"
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
        
        # Sfondo pillola countdown
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
        """Pulsante circolare di chiusura con feedback hover e click."""
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
        """Titolo evento nitido e riga di dettagli con spaziatura perfetta."""
        # Titolo Evento (SF Pro Display Bold 14.5pt)
        max_chars = 36
        short_title = self.title if len(self.title) <= max_chars else self.title[:max_chars - 3] + "..."
        
        title_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(14.5),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
        }
        
        # Sottotitolo con Dettagli (Orario e Luogo/URL)
        detail_text = ""
        if self.start_time:
            s_time = self.start_time.strftime("%H:%M")
            if self.end_time:
                e_time = self.end_time.strftime("%H:%M")
                detail_text = f"🕒 {s_time} - {e_time}"
            else:
                detail_text = f"🕒 Ore {s_time}"
                
        if self.location:
            loc_short = self.location if len(self.location) <= 24 else self.location[:21] + "..."
            detail_text += f"  •  📍 {loc_short}"
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
            # Senza sottotitolo: centra verticalmente il titolo nel corpo della card
            title_pt = AppKit.NSMakePoint(bx + 18.0, by + 60.0)
            AppKit.NSString.stringWithString_(short_title).drawAtPoint_withAttributes_(title_pt, title_attrs)

    def _draw_action_button(self, bx, by, palette):
        """Pulsante principale con gradiente dinamico e tactile click feedback."""
        is_pressed = (self.pressed_button == "action")
        is_hovered = (self.hovered_button == "action")
        
        btn_rect = AppKit.NSMakeRect(bx + 18.0, by + 12.0, 255.0, 33.0)
        btn_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(btn_rect, 10.0, 10.0)
        
        # Gradient Fill
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
        
        # Bordo superiore lucido (3D highlight bevel)
        if not is_pressed:
            hi_rect = AppKit.NSMakeRect(btn_rect.origin.x + 1.0, btn_rect.origin.y + btn_rect.size.height - 2.0, btn_rect.size.width - 2.0, 1.5)
            AppKit.NSColor.colorWithWhite_alpha_(1.0, 0.30).set()
            AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(hi_rect, 1.0, 1.0).fill()
            
        # Testo Pulsante
        btn_text = self.action_btn_text
        text_font = AppKit.NSFont.boldSystemFontOfSize_(11.5)
        text_attrs = {
            AppKit.NSFontAttributeName: text_font,
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.12, 1.0)
        }
        
        ns_str = AppKit.NSString.stringWithString_(btn_text)
        str_size = ns_str.sizeWithAttributes_(text_attrs)
        
        # Centratura testo nel pulsante
        text_x = btn_rect.origin.x + (btn_rect.size.width - str_size.width) * 0.5
        text_y = btn_rect.origin.y + (btn_rect.size.height - str_size.height) * 0.5 + 1.0
        
        if is_pressed:
            text_y -= 1.0
            
        ns_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(text_x, text_y), text_attrs)

    def _draw_snooze_button(self, bx, by, bw):
        """Pulsante snooze secondario con stile translucent frosted glass."""
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

    def _draw_dynamic_airplane(self, px, py):
        """Disegna il veicolo & pilota con grafica vettoriale HD e dettagli personalizzati."""
        if self.pilot_type == "chef":
            self._draw_chef_duck(px, py)
        elif self.pilot_type == "captain":
            self._draw_captain_jet(px, py)
        elif self.pilot_type == "owl":
            self._draw_academic_owl(px, py)
        elif self.pilot_type == "driver":
            self._draw_speed_racer(px, py)
        elif self.pilot_type == "zen_duck":
            self._draw_zen_duck(px, py)
        else:
            self._draw_aviator_duck(px, py)
            
        # Elica Rotante per tutti i velivoli a pistoni (tranne il Jet di linea)
        if self.pilot_type != "captain":
            self._draw_propeller(px + 32.0, py + 2.0)

    def _draw_aviator_duck(self, px, py):
        """🦆 Papero Aviatore Classico: Biplano vintage, occhialoni e berretto da volo."""
        # Timone di coda
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.40, 0.35, 1.0).set()
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 32, py))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 54, py + 22))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 44, py))
        tail.closePath()
        tail.fill()

        # Fusoliera Vintage dorata / avorio
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.88, 0.65, 1.0).set()
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 42, py - 12, 74, 28))
        body.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.4, 0.3, 0.2, 1.0).set()
        body.setLineWidth_(1.5)
        body.stroke()

        # Striscia decorativa rossa sulla fiancata
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.28, 0.25, 1.0).set()
        stripe = AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 34, py - 2, 54, 5))
        stripe.fill()

        # Parabrezza lucido
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.60, 0.88, 0.98, 0.85).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py - 1, 28, 22)).fill()

        # Testa del Papero 🦆
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.30, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 3, 18, 18)).fill()

        # Occhio con punto luce
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 12, 4, 4)).fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3.5, py + 13.5, 1.5, 1.5)).fill()

        # Becco d'Anatra arancione
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.0, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 5, py + 12))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 16, py + 9))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 5, py + 6))
        beak.closePath()
        beak.fill()

        # Occhialoni da Aviatore con riflesso azzurro
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 0.25, 0.18, 1.0).set()
        strap = AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 8, py + 10, 18, 3))
        strap.fill()
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.72, 0.35, 1.0).set()
        goggle = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 2, py + 8, 11, 10))
        goggle.setLineWidth_(2.2)
        goggle.stroke()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.55, 0.85, 0.98, 0.75).set()
        goggle.fill()

        # Ala inferiore e montanti
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.40, 0.35, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        wing.fill()

    def _draw_chef_duck(self, px, py):
        """👨‍🍳 Papero Chef: Toque Blanche, bandana rossa a pois e pizza fumante su vassoio d'argento."""
        # Fusoliera Corallo & Crema
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.55, 0.45, 1.0).set()
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 42, py - 12, 74, 28))
        body.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.4, 0.2, 0.15, 1.0).set()
        body.setLineWidth_(1.5)
        body.stroke()

        # Testa Papero
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.30, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 2, 17, 17)).fill()

        # Occhio con sorriso
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 10, 3.5, 3.5)).fill()

        # Becco
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.0, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 11))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 15, py + 8))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 5))
        beak.closePath()
        beak.fill()

        # Bandana Rossa al collo
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.18, 0.18, 1.0).set()
        bandana = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 5, py - 2, 12, 7))
        bandana.fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 2, py, 2, 2)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3, py, 2, 2)).fill()

        # Cappello Chef (Toque Blanche) con pieghe eleganti
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 6, py + 14, 15, 5)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 11, py + 17, 24, 16)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.87, 0.92, 1.0).set()
        fold1 = AppKit.NSBezierPath.bezierPath()
        fold1.setLineWidth_(1.2)
        fold1.moveToPoint_(AppKit.NSMakePoint(px - 4, py + 18))
        fold1.lineToPoint_(AppKit.NSMakePoint(px - 4, py + 29))
        fold1.stroke()
        fold2 = AppKit.NSBezierPath.bezierPath()
        fold2.setLineWidth_(1.2)
        fold2.moveToPoint_(AppKit.NSMakePoint(px + 3, py + 18))
        fold2.lineToPoint_(AppKit.NSMakePoint(px + 3, py + 29))
        fold2.stroke()

        # Vassoio d'argento porta pizza
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.88, 0.94, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 28, py - 20, 24, 8)).fill()

        # Trancio di Pizza Fumante 🍕
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.80, 0.20, 1.0).set()
        pizza = AppKit.NSBezierPath.bezierPath()
        pizza.moveToPoint_(AppKit.NSMakePoint(px - 26, py - 18))
        pizza.lineToPoint_(AppKit.NSMakePoint(px - 8, py - 14))
        pizza.lineToPoint_(AppKit.NSMakePoint(px - 14, py - 8))
        pizza.closePath()
        pizza.fill()
        
        # Salame / Pomodoro
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.20, 0.15, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 19, py - 15, 4, 4)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 13, py - 13, 3, 3)).fill()

        # Volute di vapore caldo dalla pizza
        steam_col = AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 1.0, 0.60)
        steam_col.set()
        steam = AppKit.NSBezierPath.bezierPath()
        steam.setLineWidth_(1.2)
        steam.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 6))
        steam.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 14, py + 4),
            AppKit.NSMakePoint(px - 20, py - 1),
            AppKit.NSMakePoint(px - 10, py + 1)
        )
        steam.stroke()

        # Ala
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.42, 0.35, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        wing.fill()

    def _draw_captain_jet(self, px, py):
        """🧑‍✈️ Jet di Linea & Capitano: Livrea aerodinamica, turbofan e berretto con fregio dorato."""
        # Stabilizzatore verticale di coda con livrea blu notte
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.22, 0.48, 1.0).set()
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 38, py))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 64, py + 26))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 48, py))
        tail.closePath()
        tail.fill()

        # Fusoliera Airliner bianca lucida
        AppKit.NSColor.whiteColor().set()
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 48, py - 12, 86, 26))
        body.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.2, 0.3, 0.45, 1.0).set()
        body.setLineWidth_(1.5)
        body.stroke()

        # Fascia Cheatline blu metallizzato e finestrini passeggeri
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.32, 0.65, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 36, py - 2, 60, 4)).fill()
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.92, 1.0, 1.0).set()
        for i in range(5):
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 28 + i * 8, py - 1, 4, 3)).fill()

        # Parabrezza Cockpit inclinato
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.20, 0.35, 0.95).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 18, py + 2, 16, 9)).fill()

        # Capitano / Pilota con berretto della Marina
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.30, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4, py + 2, 16, 16)).fill()

        # Berretto da Capitano con visiera e fregio oro
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.15, 0.35, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 3, py + 13, 16, 6)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.85, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 15, 6, 4)).fill()

        # Ala a freccia con Turbofan
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.80, 0.85, 0.94, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 14, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 18, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 4, py - 26))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 8, py - 26))
        wing.closePath()
        wing.fill()

        # Motore Turbofan sotto l'ala
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.35, 0.45, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 4, py - 22, 18, 8), 3.0, 3.0
        ).fill()

    def _draw_academic_owl(self, px, py):
        """🦉 Gufo Accademico: Tocco di laurea, occhiali tondi d'oro e ali piumate."""
        # Corpo dell'aereo / aliante in legno dorato
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.28, 0.62, 1.0).set()
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 42, py - 12, 74, 28))
        body.fill()

        # Gufo Saggio (Marrone soffice)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.68, 0.50, 0.38, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 2, 20, 20)).fill()

        # Occhi grandi con occhiali rotondi d'oro
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4, py + 7, 8, 8)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 5, py + 7, 8, 8)).fill()
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 2, py + 9, 4, 4)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 7, py + 9, 4, 4)).fill()

        # Montatura occhiali oro
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.25, 1.0).set()
        g1 = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4.5, py + 6.5, 9, 9))
        g1.setLineWidth_(1.4)
        g1.stroke()
        g2 = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.5, py + 6.5, 9, 9))
        g2.setLineWidth_(1.4)
        g2.stroke()

        # Becco a punta
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.55, 0.1, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 3, py + 9))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 7, py + 6))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 3, py + 3))
        beak.closePath()
        beak.fill()

        # Tocco di Laurea (Mortarboard) con nappa dorata
        AppKit.NSColor.blackColor().set()
        grad = AppKit.NSBezierPath.bezierPath()
        grad.moveToPoint_(AppKit.NSMakePoint(px + 2, py + 26))
        grad.lineToPoint_(AppKit.NSMakePoint(px + 14, py + 20))
        grad.lineToPoint_(AppKit.NSMakePoint(px + 2, py + 15))
        grad.lineToPoint_(AppKit.NSMakePoint(px - 10, py + 20))
        grad.closePath()
        grad.fill()

        # Nappa dorata penzolante
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.2, 1.0).set()
        tassel = AppKit.NSBezierPath.bezierPath()
        tassel.setLineWidth_(1.4)
        tassel.moveToPoint_(AppKit.NSMakePoint(px + 2, py + 21))
        tassel.lineToPoint_(AppKit.NSMakePoint(px - 6, py + 14))
        tassel.stroke()

        # Pergamena di Laurea legata all'ala
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.94, 0.85, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(AppKit.NSMakeRect(px - 22, py - 18, 16, 7), 2, 2).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.9, 0.2, 0.2, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 15, py - 18, 3, 7)).fill()

        # Ala
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.76, 0.52, 0.96, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 22))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 22))
        wing.closePath()
        wing.fill()

    def _draw_speed_racer(self, px, py):
        """🏎️ Pilota da Corsa: Fusoliera aerodinamica verde smeraldo/rosso, strisce racing e casco."""
        # Fusoliera Speedster
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.78, 0.52, 1.0).set()
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 42, py - 12, 74, 28))
        body.fill()

        # Doppia striscia da corsa bianca
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 38, py + 1, 64, 3)).fill()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 38, py - 6, 64, 3)).fill()

        # Cerchio Numero 1 di Gara
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 26, py - 8, 14, 14)).fill()
        num_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(9),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.blackColor()
        }
        AppKit.NSString.stringWithString_("1").drawAtPoint_withAttributes_(AppKit.NSMakePoint(px - 22, py - 7), num_attrs)

        # Casco Racing con visiera a specchio
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.22, 0.22, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 3, 19, 19)).fill()

        # Visiera scura a specchio
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.1, 0.12, 0.18, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 1, py + 8, 13, 8), 3.0, 3.0
        ).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.5, 0.85, 1.0, 0.8).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px + 2, py + 12, 7, 2)).fill()

        # Ala aerodinamica
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.85, 0.25, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        wing.fill()

    def _draw_zen_duck(self, px, py):
        """🦆🌸 Papero Zen: Velivolo pastello teal/menta, fiore di loto e aura rilassante per Serenis."""
        # Fusoliera Nuvoletta / Teal pastello
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.40, 0.86, 0.82, 1.0).set()
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 42, py - 12, 74, 28))
        body.fill()

        # Testa Papero
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.84, 0.35, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 2, 17, 17)).fill()

        # Occhio sereno socchiuso (meditazione)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.3, 0.25, 0.2, 1.0).set()
        eye_arc = AppKit.NSBezierPath.bezierPath()
        eye_arc.setLineWidth_(1.6)
        eye_arc.moveToPoint_(AppKit.NSMakePoint(px, py + 10))
        eye_arc.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 6, py + 10),
            AppKit.NSMakePoint(px + 2, py + 7),
            AppKit.NSMakePoint(px + 4, py + 7)
        )
        eye_arc.stroke()

        # Becco
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.52, 0.1, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 11))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 14, py + 8))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 5))
        beak.closePath()
        beak.fill()

        # Fiore di Loto rosa 🌸 dietro l'orecchio
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.60, 0.75, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 9, py + 14, 6, 6)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 5, py + 17, 6, 6)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 1, py + 14, 6, 6)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.90, 0.30, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 5, py + 14, 4, 4)).fill()

        # Ala
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.60, 0.94, 0.90, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 22))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 22))
        wing.closePath()
        wing.fill()

    def _draw_propeller(self, nose_x, nose_y):
        """Disegna il cono d'ogiva e l'elica rotante ad alta velocità con motion blur."""
        # Ogiva centrale dell'elica
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.25, 0.32, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 3, nose_y - 4, 8, 8)).fill()
        
        # Disco di sfocatura di rotazione (Motion blur disc)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.90, 1.0, 0.22).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 4, nose_y - 17, 8, 34)).fill()
        
        # Pale rotanti ad alta velocità
        prop_angle = self.tick * 0.65
        prop_len = 17.0
        dx = math.cos(prop_angle) * 3.5
        dy = math.sin(prop_angle) * prop_len
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.92, 1.0, 0.85).set()
        prop_path = AppKit.NSBezierPath.bezierPath()
        prop_path.setLineWidth_(3.0)
        prop_path.setLineCapStyle_(AppKit.NSLineCapStyleRound)
        prop_path.moveToPoint_(AppKit.NSMakePoint(nose_x + dx, nose_y - dy))
        prop_path.lineToPoint_(AppKit.NSMakePoint(nose_x - dx, nose_y + dy))
        prop_path.stroke()


class QuakPitFlyingBanner:
    def __init__(self, meeting_data, on_close_callback=None):
        self.meeting_data = meeting_data
        self.on_close_callback = on_close_callback
        self.window = None
        self.timer = None
        self.action_url = meeting_data.get("action_url") or meeting_data.get("meeting_url")
        
    def show(self):
        screen = AppKit.NSScreen.mainScreen()
        screen_rect = screen.frame() if screen else AppKit.NSMakeRect(0, 0, 1440, 900)
        
        window_w = screen_rect.size.width
        window_h = 220.0
        
        # Posizione configurabile: in Alto (Top) o in Basso (Bottom)
        banner_pos = config.get("banner_position", "top")
        if banner_pos == "bottom":
            y_pos = 40.0
        else:
            y_pos = screen_rect.size.height - window_h - 20.0
        
        frame = AppKit.NSMakeRect(0, y_pos, window_w, window_h)
        
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False
        )
        
        self.window.setLevel_(AppKit.NSStatusWindowLevel)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces |
            AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary |
            AppKit.NSWindowCollectionBehaviorStationary |
            AppKit.NSWindowCollectionBehaviorIgnoresCycle
        )
        self.window.setHidesOnDeactivate_(False)
        
        self.view = QuakPitBannerView.alloc().initWithFrame_meetingData_controller_(
            AppKit.NSMakeRect(0, 0, window_w, window_h),
            self.meeting_data,
            self
        )
        self.window.setContentView_(self.view)
        
        # Riproduzione suono personalizzato
        if config.get("sound_enabled", True):
            sound_name = config.get("sound_name", "Glass")
            sound_path = f"/System/Library/Sounds/{sound_name}.aiff"
            if not os.path.exists(sound_path):
                sound_path = "/System/Library/Sounds/Glass.aiff"
            try:
                subprocess.Popen(["afplay", sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        self.timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / 60.0,
            self.view,
            "stepAnimation:",
            None,
            True
        )
        
        self.window.makeKeyAndOrderFront_(None)

    def trigger_action(self):
        """Apre il link nel browser/Mappe e chiude SOLO la finestra temporanea di notifica (l'app rimane attiva in background)."""
        if self.action_url:
            print(f"🚀 Apertura azione/mappe/link: {self.action_url}")
            webbrowser.open(self.action_url)
        self.close()

    def snooze(self, seconds=120):
        print(f"💤 Banner posticipato di {seconds // 60} minuti...")
        self.close()
        import threading
        def delayed_show():
            time.sleep(seconds)
            show_banner_async(self.meeting_data)
        threading.Thread(target=delayed_show, daemon=True).start()

    def close(self):
        """Chiude definitivamente la finestra volante."""
        if self.timer:
            self.timer.invalidate()
            self.timer = None
        if self.window:
            self.window.orderOut_(None)
            self.window.close()
            self.window = None
            
        global active_banner_instance
        active_banner_instance = None
        
        if self.on_close_callback:
            self.on_close_callback()
        elif AppKit.NSApp().delegate() is None:
            # Modalità standalone (es. test da terminale): termina il processo
            AppKit.NSApplication.sharedApplication().terminate_(None)

# Riferimento globale
active_banner_instance = None

def _run_banner(meeting_data):
    global active_banner_instance
    if active_banner_instance:
        active_banner_instance.close()
    active_banner_instance = QuakPitFlyingBanner(meeting_data)
    active_banner_instance.show()

def show_banner_async(meeting_data):
    """Apre la finestra banner nativa Cocoa nel Main Thread in modo completamente thread-safe."""
    try:
        if AppKit.NSThread.isMainThread():
            _run_banner(meeting_data)
        else:
            AppKit.NSApp().performSelectorOnMainThread_withObject_waitUntilDone_(
                "showBannerOnMainThread:",
                meeting_data,
                False
            )
    except Exception as e:
        print(f"Errore visualizzazione banner: {e}")

if __name__ == "__main__":
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    test_m = {
        "title": "Cena con Amici in Pizzeria",
        "provider": "Cena / Cibo 🍕🍽️",
        "pilot_type": "chef",
        "action_btn_text": "🗺️ INDICAZIONI RISTORANTE (MAPPE)",
        "action_url": "https://maps.apple.com/?q=Pizzeria+Torino",
        "location": "Pizzeria Da Michele, Torino",
        "start_time": datetime.now(),
        "is_travel": True
    }
    _run_banner(test_m)
    app.run()

