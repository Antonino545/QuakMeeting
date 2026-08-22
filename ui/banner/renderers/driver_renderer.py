"""
Speed Racer Driver Pilot Renderer for QuakMeeting.
Features emerald speedster chassis, racing double stripes, race number #1, and red racing helmet with mirrored neon visor.
"""
import AppKit
from .base_renderer import BasePilotRenderer

class DriverPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Fusoliera Speedster
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 44, py - 13, 76, 28))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.80, 0.54, 1.0).set()
        body.fill()

        # Doppia striscia da corsa bianca
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 40, py + 1, 68, 3)).fill()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 40, py - 6, 68, 3)).fill()

        # Rondella Numero 1 di Gara
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 28, py - 8, 15, 15)).fill()
        num_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(9.5),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.blackColor()
        }
        AppKit.NSString.stringWithString_("1").drawAtPoint_withAttributes_(AppKit.NSMakePoint(px - 24, py - 7), num_attrs)

        # 2. Casco Racing con visiera iridescente
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.20, 0.20, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 3, 20, 20)).fill()

        # Visiera a specchio con riflesso neon
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.08, 0.10, 0.15, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 1, py + 8, 14, 9), 3.5, 3.5
        ).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.4, 0.9, 1.0, 0.85).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px + 2, py + 12, 8, 2.5)).fill()

        # 3. Ala aerodinamica
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.85, 0.22, 1.0).set()
        wing.fill()

        # Propeller
        self.draw_propeller(px + 32.0, py + 2.0, tick)
