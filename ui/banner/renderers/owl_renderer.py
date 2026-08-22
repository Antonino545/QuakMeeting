"""
Academic Owl Pilot Renderer for QuakMeeting.
Features amethyst glider, mortarboard hat with oscillating tassel, round gold spectacles, and graduation scroll.
"""
import math
import AppKit
from .base_renderer import BasePilotRenderer

class OwlPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Fusoliera / Aliante in legno nobile & Ametista
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 44, py - 13, 76, 28))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.44, 0.28, 0.65, 1.0).set()
        body.fill()

        # 2. Faccetta Gufo Saggio Soffice
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.70, 0.52, 0.40, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 2, 21, 21)).fill()

        # Dischi piumati bianchi intorno agli occhi
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.94, 0.88, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4, py + 7, 8.5, 8.5)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 5.5, py + 7, 8.5, 8.5)).fill()

        # Occhi grandi con pupilla nera e luce
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 2, py + 9, 4.5, 4.5)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 7.5, py + 9, 4.5, 4.5)).fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 0.8, py + 11, 1.6, 1.6)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 8.7, py + 11, 1.6, 1.6)).fill()

        # Montatura occhiali rotondi oro con ponte
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.25, 1.0).set()
        g1 = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4.5, py + 6.5, 9.5, 9.5))
        g1.setLineWidth_(1.6)
        g1.stroke()
        g2 = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 5.0, py + 6.5, 9.5, 9.5))
        g2.setLineWidth_(1.6)
        g2.stroke()

        # Becco Gufo
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 3, py + 9.5))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 8, py + 6.5))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 3, py + 3.5))
        beak.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.55, 0.1, 1.0).set()
        beak.fill()

        # 3. Tocco di Laurea (Mortarboard) con nappa d'oro oscillante
        grad = AppKit.NSBezierPath.bezierPath()
        grad.moveToPoint_(AppKit.NSMakePoint(px + 2, py + 27))
        grad.lineToPoint_(AppKit.NSMakePoint(px + 16, py + 20))
        grad.lineToPoint_(AppKit.NSMakePoint(px + 2, py + 15))
        grad.lineToPoint_(AppKit.NSMakePoint(px - 12, py + 20))
        grad.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.12, 0.16, 1.0).set()
        grad.fill()

        # Bottone centrale e Nappa d'oro oscillante
        tassel_wave = math.sin(tick * 0.2) * 3.0
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.2, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 20, 3, 3)).fill()
        
        tassel = AppKit.NSBezierPath.bezierPath()
        tassel.setLineWidth_(1.6)
        tassel.moveToPoint_(AppKit.NSMakePoint(px + 2, py + 21))
        tassel.lineToPoint_(AppKit.NSMakePoint(px - 7 + tassel_wave, py + 13))
        tassel.stroke()

        # 4. Pergamena di Laurea con sigillo rosso
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.94, 0.85, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(AppKit.NSMakeRect(px - 24, py - 19, 18, 8), 2.5, 2.5).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.9, 0.18, 0.18, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 16, py - 19, 3.5, 8)).fill()

        # 5. Ala
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.76, 0.52, 0.96, 1.0).set()
        wing.fill()

        # Propeller
        self.draw_propeller(px + 32.0, py + 2.0, tick)
