"""
Zen Duck Pilot Renderer for QuakMeeting.
Features mint/teal cloud fuselage, meditating smiling duck, pink lotus flower, and pastel wing.
"""
import AppKit
from .base_renderer import BasePilotRenderer

class ZenDuckRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Fusoliera Nuvoletta / Teal pastello
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 44, py - 13, 76, 28))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.88, 0.84, 1.0).set()
        body.fill()

        # 2. Testa Papero
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.84, 0.32, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 2, 19, 19)).fill()

        # Guancia Rosa Zen
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.50, 0.60, 0.50).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 3, py + 4, 7, 5)).fill()

        # Occhio sereno socchiuso in meditazione (curva felice)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.25, 0.20, 0.18, 1.0).set()
        eye_arc = AppKit.NSBezierPath.bezierPath()
        eye_arc.setLineWidth_(1.8)
        eye_arc.moveToPoint_(AppKit.NSMakePoint(px + 1, py + 10.5))
        eye_arc.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 7.5, py + 10.5),
            AppKit.NSMakePoint(px + 3, py + 13),
            AppKit.NSMakePoint(px + 5.5, py + 13)
        )
        eye_arc.stroke()

        # Becco sorridente
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 11))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 15, py + 8.5))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 5.5))
        beak.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.52, 0.1, 1.0).set()
        beak.fill()

        # 3. Fiore di Loto rosa 🌸 sulla testa
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.62, 0.78, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 10, py + 14, 7, 7)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 5, py + 18, 7, 7)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px, py + 14, 7, 7)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.90, 0.30, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 5, py + 14, 5, 5)).fill()

        # 4. Ala
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.62, 0.94, 0.90, 1.0).set()
        wing.fill()

        # Propeller
        self.draw_propeller(px + 32.0, py + 2.0, tick)
