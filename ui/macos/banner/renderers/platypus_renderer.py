"""
Secret Agent Platypus Pilot Renderer for QuakMeeting (macOS Quartz 2D).
Inspired by Perry the Platypus from Phineas & Ferb:
Features stealth spy glider, teal platypus body, flat beaver tail, orange duck bill, and iconic brown fedora hat.
"""
import math
import AppKit
from .base_renderer import BasePilotRenderer

class PlatypusPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Coda a Castoro (Beaver Tail with crosshatch grid)
        tail_angle = math.sin(tick * 0.12) * 2.0
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 30, py - 4))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 60, py + 8 + tail_angle))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 56, py - 12 + tail_angle))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 30, py - 8))
        tail.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.72, 0.44, 0.24, 1.0).set()
        tail.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.45, 0.25, 0.12, 0.75).set()
        tail.setLineWidth_(1.2)
        tail.stroke()

        # Griglia sulla coda
        grid = AppKit.NSBezierPath.bezierPath()
        grid.moveToPoint_(AppKit.NSMakePoint(px - 52, py + 4 + tail_angle))
        grid.lineToPoint_(AppKit.NSMakePoint(px - 36, py - 8))
        grid.moveToPoint_(AppKit.NSMakePoint(px - 46, py + 6 + tail_angle))
        grid.lineToPoint_(AppKit.NSMakePoint(px - 32, py - 6))
        grid.moveToPoint_(AppKit.NSMakePoint(px - 54, py - 6 + tail_angle))
        grid.lineToPoint_(AppKit.NSMakePoint(px - 38, py + 6))
        grid.stroke()

        # 2. Fusoliera Stealth Spy Jet (Matte Dark Slate & Cyan Neon Trim)
        body_rect = AppKit.NSMakeRect(px - 40, py - 12, 74, 26)
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(body_rect)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.18, 0.22, 0.28, 1.0).set()
        body.fill()

        # Striscia Spy Cyan Neon
        stripe = AppKit.NSBezierPath.bezierPath()
        stripe.moveToPoint_(AppKit.NSMakePoint(px - 34, py - 3))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 22, py - 3))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 20, py - 6))
        stripe.lineToPoint_(AppKit.NSMakePoint(px - 32, py - 6))
        stripe.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.85, 0.82, 1.0).set()
        stripe.fill()

        # Bordo fusoliera
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.12, 0.16, 1.0).set()
        body.setLineWidth_(1.4)
        body.stroke()

        # 3. Cockpit Spy & Flusso
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.14, 0.20, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py - 1, 28, 18)).fill()

        # 4. Corpo e Testa del Platipo (Teal / Turchese Perry)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.0, 0.65, 0.58, 1.0).set()
        head = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 10, py + 2, 22, 20))
        head.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.0, 0.45, 0.40, 1.0).set()
        head.setLineWidth_(1.2)
        head.stroke()

        # 5. Becco Piatto da Ornitorinco (Wide Flat Orange Duck Bill)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.55, 0.05, 1.0).set()
        bill = AppKit.NSBezierPath.bezierPath()
        bill.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 7))
        bill.lineToPoint_(AppKit.NSMakePoint(px + 22, py + 5))
        bill.lineToPoint_(AppKit.NSMakePoint(px + 22, py + 1))
        bill.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 2))
        bill.closePath()
        bill.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.70, 0.35, 0.0, 1.0).set()
        bill.setLineWidth_(1.1)
        bill.stroke()

        # Narici becco
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.45, 0.22, 0.0, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 14, py + 4.5, 2.2, 1.8)).fill()

        # 6. Occhi Vigili da Agente Segreto
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 11, 5.5, 6.5)).fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3, py + 14, 2.0, 2.0)).fill()

        # 7. 🕵️‍♂️ CAPPELLO FEDORA DA AGENTE SEGRETO (Brown Fedora with Black Band)
        # Tesa del cappello (Fedora Brim)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.48, 0.28, 0.15, 1.0).set()
        brim = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py + 18, 30, 6))
        brim.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.16, 0.08, 1.0).set()
        brim.setLineWidth_(1.0)
        brim.stroke()

        # Corona del cappello (Fedora Crown)
        crown = AppKit.NSBezierPath.bezierPath()
        crown.moveToPoint_(AppKit.NSMakePoint(px - 8, py + 20))
        crown.lineToPoint_(AppKit.NSMakePoint(px - 6, py + 31))
        crown.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 32))
        crown.lineToPoint_(AppKit.NSMakePoint(px + 8, py + 30))
        crown.lineToPoint_(AppKit.NSMakePoint(px + 8, py + 20))
        crown.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.52, 0.30, 0.16, 1.0).set()
        crown.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.16, 0.08, 1.0).set()
        crown.setLineWidth_(1.0)
        crown.stroke()

        # Nastro nero del fedora (Black Ribbon Band)
        band = AppKit.NSBezierPath.bezierPath()
        band.moveToPoint_(AppKit.NSMakePoint(px - 7.5, py + 20))
        band.lineToPoint_(AppKit.NSMakePoint(px - 7, py + 23.5))
        band.lineToPoint_(AppKit.NSMakePoint(px + 7.5, py + 23.5))
        band.lineToPoint_(AppKit.NSMakePoint(px + 8, py + 20))
        band.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.18, 1.0).set()
        band.fill()

        # 8. Ala Spy Delta Stealth
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.15, 0.20, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 4))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 12, py - 4))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 4, py - 26))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 20, py - 26))
        wing.closePath()
        wing.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.85, 0.82, 0.70).set()
        wing.setLineWidth_(1.2)
        wing.stroke()

        # 9. Elica anteriore ad alta velocità
        self.draw_propeller(px + 34, py + 1, tick)
