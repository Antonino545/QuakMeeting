"""
Athlete / Gym Sport Duck Pilot Renderer for QuakMeeting.
Features fiery athletic crimson chassis, athletic sweatband, dumbbell emblem,
lightning sport wing stripes, and workout energy aura.
"""
import AppKit
from .base_renderer import BasePilotRenderer

class GymPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Sport Athletic Fuselage (Fiery Orange / Crimson)
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 44, py - 13, 76, 28))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.34, 0.15, 1.0).set()
        body.fill()

        # Athletic Energy Racing Stripe (Neon Yellow / Gold)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.90, 0.10, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 40, py - 1, 68, 3.5)).fill()

        # Dumbbell / Barbell Emblem 🏋️ on Fuselage
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 28, py - 9, 16, 16)).fill()

        # Draw Mini Dumbbell (Bar + 2 Weights)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.20, 1.0).set()
        # Left plate
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 26, py - 7, 2.5, 12), 1, 1
        ).fill()
        # Bar
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 24, py - 2, 8, 2)).fill()
        # Right plate
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 16, py - 7, 2.5, 12), 1, 1
        ).fill()

        # 2. Duck Pilot Head (Golden Yellow)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.18, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 6, py + 3, 19, 19)).fill()

        # Athletic Red Sweatband / Headband
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.15, 0.20, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 7, py + 12, 21, 6), 2, 2
        ).fill()

        # Sweatband Knots / Fluttering Ribbon Tails
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 7, py + 14))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 15, py + 18))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 14, py + 12))
        tail.closePath()
        tail.fill()

        # Duck Eye (Determined Workout Focus)
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4, py + 7, 6, 6)).fill()
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 6, py + 8.5, 3.5, 3.5)).fill()

        # Duck Orange Beak
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.50, 0.05, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 10, py + 5))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 22, py + 4))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 10, py + 10))
        beak.closePath()
        beak.fill()

        # 3. Dynamic Sport Wing
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 8, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 8, py - 24))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.20, 0.15, 1.0).set()
        wing.fill()

        # Wing Lightning Stripe
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.92, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 8, py - 12, 16, 2.5)).fill()

        # Propeller
        self.draw_propeller(px + 32.0, py + 2.0, tick)
