"""
Universal Cairo Vector Pilot Plane Renderers for Ubuntu Linux (Wayland / X11).
Renders all 7 pilot mascots and airplanes in pure Cairo graphics.
"""
import math
from typing import Dict, Any

class CairoPilotRenderer:
    """Draws mascot planes, propellers, and pilot details using Cairo 2D graphics."""

    @staticmethod
    def draw_propeller(ctx, px: float, py: float, tick: int):
        """Draws rotating animated propeller."""
        ctx.save()
        ctx.translate(px, py)
        angle = (tick * 0.45) % (2 * math.pi)
        ctx.rotate(angle)

        ctx.set_source_rgba(0.95, 0.95, 0.95, 0.85)
        ctx.rectangle(-2.5, -14, 5, 28)
        ctx.fill()

        # Propeller hub
        ctx.set_source_rgba(0.2, 0.2, 0.25, 1.0)
        ctx.arc(0, 0, 4, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

    @classmethod
    def draw_pilot(cls, ctx, pilot_type: str, px: float, py: float, tick: int):
        """Dispatches drawing to the specific pilot mascot."""
        draw_fn = getattr(cls, f"_draw_{pilot_type}", cls._draw_duck)
        draw_fn(ctx, px, py, tick)

    @classmethod
    def _draw_duck(cls, ctx, px: float, py: float, tick: int):
        """1. Aviator Duck (Google Meet / Zoom)"""
        # Fuselage (Yellow)
        ctx.set_source_rgba(1.0, 0.82, 0.18, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(38, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Aviator Cap (Brown Leather)
        ctx.set_source_rgba(0.42, 0.26, 0.15, 1.0)
        ctx.arc(px + 4, py + 8, 10, 0, 2 * math.pi)
        ctx.fill()

        # Aviator Goggles
        ctx.set_source_rgba(0.9, 0.9, 0.95, 0.9)
        ctx.arc(px + 9, py + 9, 4.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(0.2, 0.2, 0.2, 1.0)
        ctx.set_line_width(1.5)
        ctx.stroke()

        # Beak
        ctx.set_source_rgba(1.0, 0.48, 0.05, 1.0)
        ctx.move_to(px + 12, py + 4)
        ctx.line_to(px + 24, py + 2)
        ctx.line_to(px + 12, py + 9)
        ctx.close_path()
        ctx.fill()

        # Wing
        ctx.set_source_rgba(0.95, 0.70, 0.10, 1.0)
        ctx.move_to(px - 14, py - 2)
        ctx.line_to(px + 14, py - 2)
        ctx.line_to(px + 4, py - 20)
        ctx.line_to(px - 8, py - 20)
        ctx.close_path()
        ctx.fill()

        cls.draw_propeller(ctx, px + 34, py, tick)

    @classmethod
    def _draw_chef(cls, ctx, px: float, py: float, tick: int):
        """2. Chef Duck (Dinner / Food)"""
        # Fuselage (Coral Red)
        ctx.set_source_rgba(1.0, 0.42, 0.35, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(38, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Head
        ctx.set_source_rgba(1.0, 0.85, 0.18, 1.0)
        ctx.arc(px + 3, py + 7, 9, 0, 2 * math.pi)
        ctx.fill()

        # Tall White Chef Toque Hat
        ctx.set_source_rgba(0.98, 0.98, 0.98, 1.0)
        ctx.arc(px + 1, py + 18, 7.5, 0, 2 * math.pi)
        ctx.arc(px + 8, py + 19, 6.5, 0, 2 * math.pi)
        ctx.arc(px - 5, py + 17, 6.0, 0, 2 * math.pi)
        ctx.fill()

        # Beak
        ctx.set_source_rgba(1.0, 0.50, 0.05, 1.0)
        ctx.move_to(px + 11, py + 5)
        ctx.line_to(px + 22, py + 4)
        ctx.line_to(px + 11, py + 9)
        ctx.close_path()
        ctx.fill()

        # Wing
        ctx.set_source_rgba(0.92, 0.30, 0.25, 1.0)
        ctx.move_to(px - 14, py - 2)
        ctx.line_to(px + 14, py - 2)
        ctx.line_to(px + 4, py - 20)
        ctx.line_to(px - 8, py - 20)
        ctx.close_path()
        ctx.fill()

        cls.draw_propeller(ctx, px + 34, py, tick)

    @classmethod
    def _draw_captain(cls, ctx, px: float, py: float, tick: int):
        """3. Jet Captain (Flights / Travel)"""
        # Jet Fuselage (Airliner Sky Blue & White)
        ctx.set_source_rgba(0.35, 0.65, 0.98, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(42, 13)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Airline Stripe
        ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        ctx.rectangle(px - 42, py - 2, 75, 3)
        ctx.fill()

        # Captain Pilot Cap
        ctx.set_source_rgba(0.10, 0.15, 0.30, 1.0)
        ctx.arc(px + 4, py + 9, 9, 0, 2 * math.pi)
        ctx.fill()
        # Gold Captain Eagle Emblem
        ctx.set_source_rgba(1.0, 0.85, 0.20, 1.0)
        ctx.arc(px + 6, py + 14, 3, 0, 2 * math.pi)
        ctx.fill()

        # Swept-Back Jet Wings
        ctx.set_source_rgba(0.25, 0.50, 0.85, 1.0)
        ctx.move_to(px - 18, py - 2)
        ctx.line_to(px + 12, py - 2)
        ctx.line_to(px - 2, py - 22)
        ctx.line_to(px - 14, py - 22)
        ctx.close_path()
        ctx.fill()

        # Jet Engine Turbine
        ctx.set_source_rgba(0.2, 0.25, 0.35, 1.0)
        ctx.rectangle(px - 8, py - 16, 16, 6)
        ctx.fill()

    @classmethod
    def _draw_owl(cls, ctx, px: float, py: float, tick: int):
        """4. Academic Owl (University / Study)"""
        # Owl Body (Academic Purple/Brown)
        ctx.set_source_rgba(0.72, 0.48, 0.95, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(38, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Owl Face & Big Scholarly Glasses
        ctx.set_source_rgba(0.95, 0.95, 0.95, 1.0)
        ctx.arc(px + 9, py + 7, 5, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(0.1, 0.1, 0.1, 1.0)
        ctx.set_line_width(1.5)
        ctx.stroke()

        # Graduation Mortarboard Cap
        ctx.set_source_rgba(0.12, 0.12, 0.18, 1.0)
        ctx.move_to(px - 2, py + 16)
        ctx.line_to(px + 14, py + 18)
        ctx.line_to(px + 10, py + 12)
        ctx.line_to(px - 6, py + 10)
        ctx.close_path()
        ctx.fill()
        # Gold Tassel
        ctx.set_source_rgba(1.0, 0.85, 0.2, 1.0)
        ctx.move_to(px + 4, py + 15)
        ctx.line_to(px - 3, py + 9)
        ctx.set_line_width(1.5)
        ctx.stroke()

        cls.draw_propeller(ctx, px + 34, py, tick)

    @classmethod
    def _draw_gym(cls, ctx, px: float, py: float, tick: int):
        """5. Athlete Duck (Palestra / Gym / Sport)"""
        # Athletic Crimson/Orange Fuselage
        ctx.set_source_rgba(1.0, 0.35, 0.16, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(38, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Yellow Energy Stripe
        ctx.set_source_rgba(1.0, 0.90, 0.10, 1.0)
        ctx.rectangle(px - 40, py - 1, 68, 3)
        ctx.fill()

        # Head
        ctx.set_source_rgba(1.0, 0.85, 0.18, 1.0)
        ctx.arc(px + 3, py + 7, 9, 0, 2 * math.pi)
        ctx.fill()

        # Athletic Red Sweatband with Fluttering Tails
        ctx.set_source_rgba(0.92, 0.15, 0.20, 1.0)
        ctx.rectangle(px - 4, py + 10, 18, 5)
        ctx.fill()
        ctx.move_to(px - 4, py + 12)
        ctx.line_to(px - 12, py + 16)
        ctx.line_to(px - 11, py + 10)
        ctx.close_path()
        ctx.fill()

        # Beak
        ctx.set_source_rgba(1.0, 0.50, 0.05, 1.0)
        ctx.move_to(px + 11, py + 5)
        ctx.line_to(px + 22, py + 4)
        ctx.line_to(px + 11, py + 9)
        ctx.close_path()
        ctx.fill()

        # Sport Wing
        ctx.set_source_rgba(0.90, 0.20, 0.15, 1.0)
        ctx.move_to(px - 14, py - 2)
        ctx.line_to(px + 14, py - 2)
        ctx.line_to(px + 4, py - 20)
        ctx.line_to(px - 8, py - 20)
        ctx.close_path()
        ctx.fill()

        cls.draw_propeller(ctx, px + 34, py, tick)

    @classmethod
    def _draw_driver(cls, ctx, px: float, py: float, tick: int):
        """6. Speed Racer Driver (In-Person / Appointments)"""
        # Emerald Green Fuselage
        ctx.set_source_rgba(0.20, 0.82, 0.55, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(38, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Double White Racing Stripes
        ctx.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        ctx.rectangle(px - 38, py + 2, 65, 2.5)
        ctx.rectangle(px - 38, py - 4, 65, 2.5)
        ctx.fill()

        # Racing Helmet
        ctx.set_source_rgba(0.92, 0.20, 0.20, 1.0)
        ctx.arc(px + 4, py + 8, 9, 0, 2 * math.pi)
        ctx.fill()
        # Visor
        ctx.set_source_rgba(0.2, 0.8, 1.0, 0.9)
        ctx.rectangle(px + 7, py + 6, 7, 4.5)
        ctx.fill()

        cls.draw_propeller(ctx, px + 34, py, tick)

    @classmethod
    def _draw_zen_duck(cls, ctx, px: float, py: float, tick: int):
        """7. Zen Duck (Wellness / Therapy / Relaxation)"""
        # Teal Pastel Fuselage
        ctx.set_source_rgba(0.28, 0.88, 0.82, 1.0)
        ctx.save()
        ctx.translate(px - 6, py)
        ctx.scale(38, 14)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()

        # Head
        ctx.set_source_rgba(1.0, 0.88, 0.35, 1.0)
        ctx.arc(px + 3, py + 7, 9, 0, 2 * math.pi)
        ctx.fill()

        # Lotus Flower / Petal
        ctx.set_source_rgba(1.0, 0.6, 0.8, 1.0)
        ctx.arc(px + 2, py + 14, 4, 0, 2 * math.pi)
        ctx.fill()

        # Beak
        ctx.set_source_rgba(1.0, 0.55, 0.15, 1.0)
        ctx.move_to(px + 11, py + 5)
        ctx.line_to(px + 20, py + 4)
        ctx.line_to(px + 11, py + 8)
        ctx.close_path()
        ctx.fill()

        cls.draw_propeller(ctx, px + 34, py, tick)
