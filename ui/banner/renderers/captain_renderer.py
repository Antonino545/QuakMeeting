"""
Captain Jet Pilot Renderer for QuakMeeting.
Features modern airliner livery, turbofan engine, pilot sunglasses, and naval captain cap with gold emblem.
"""
import AppKit
from .base_renderer import BasePilotRenderer

class CaptainPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Stabilizzatore verticale con livrea blu notte e logo oro
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 38, py))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 66, py + 28))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 48, py))
        tail.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.22, 0.48, 1.0).set()
        tail.fill()

        # 2. Fusoliera Airliner bianca lucida
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 48, py - 12, 88, 26))
        AppKit.NSColor.whiteColor().set()
        body.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.2, 0.3, 0.45, 1.0).set()
        body.setLineWidth_(1.4)
        body.stroke()

        # 3. Fascia Cheatline blu metallizzato e finestrini passeggeri illuminati
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.32, 0.65, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 36, py - 2, 62, 4)).fill()
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.94, 1.0, 1.0).set()
        for i in range(5):
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 28 + i * 8, py - 1, 4.5, 3.5)).fill()

        # 4. Parabrezza Cockpit inclinato lucido
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.18, 0.32, 0.95).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 20, py + 2, 17, 9)).fill()

        # 5. Capitano Papero con Berretto Ufficiale di Marina
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.24, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4, py + 2, 18, 18)).fill()

        # Occhiali da sole da pilota a goccia
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.12, 0.18, 0.95).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3, py + 7, 7, 6)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3, py + 7, 7, 6)).stroke()

        # Berretto da Capitano con visiera nera lucida e ancora d'oro
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.15, 0.35, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 3, py + 14, 18, 6)).fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4, py + 16, 20, 7)).fill()
        
        # Stemma ancora oro
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.85, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 15, 6, 5)).fill()

        # 6. Ala a freccia con Turbofan Jet Engine
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 14, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 18, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 4, py - 26))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 8, py - 26))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.82, 0.87, 0.95, 1.0).set()
        wing.fill()

        # Turbofan Jet Nacelle
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.28, 0.32, 0.42, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px - 4, py - 22, 20, 9), 3.5, 3.5
        ).fill()
        # Ventola turbina
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.75, 0.90, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 12, py - 21, 3.5, 7)).fill()
