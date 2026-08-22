"""
Chef Duck Pilot Renderer for QuakMeeting.
Features coral biplane, Toque Blanche chef hat, polka dot bandana, steaming pizza slice, and propeller.
"""
import math
import AppKit
from .base_renderer import BasePilotRenderer

class ChefPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Fusoliera Corallo & Crema
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 44, py - 13, 76, 28))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.58, 0.48, 1.0).set()
        body.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.4, 0.2, 0.15, 0.85).set()
        body.setLineWidth_(1.4)
        body.stroke()

        # 2. Testa Papero con Blush
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.24, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 2, 19, 19)).fill()

        # Guancia Rosa
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.42, 0.42, 0.45).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 3, py + 4, 7, 5)).fill()

        # Occhio Sorridente e Vivace
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 10.5, 4.5, 5.0)).fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3.8, py + 12.5, 2.0, 2.0)).fill()

        # Becco 3D
        beak_path = AppKit.NSBezierPath.bezierPath()
        beak_path.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 11))
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 17, py + 8.5),
            AppKit.NSMakePoint(px + 9, py + 12),
            AppKit.NSMakePoint(px + 14, py + 11)
        )
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 4, py + 5.0),
            AppKit.NSMakePoint(px + 14, py + 6),
            AppKit.NSMakePoint(px + 9, py + 5.5)
        )
        beak_path.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.02, 1.0).set()
        beak_path.fill()

        # 3. Bandana Rossa al collo con pois bianchi
        bandana = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 6, py - 2, 14, 8))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.18, 0.18, 1.0).set()
        bandana.fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 3, py, 2.2, 2.2)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3, py, 2.2, 2.2)).fill()

        # Coda bandana svolazzante
        b_wave = math.sin(tick * 0.3) * 4.0
        b_tail = AppKit.NSBezierPath.bezierPath()
        b_tail.moveToPoint_(AppKit.NSMakePoint(px - 6, py + 1))
        b_tail.lineToPoint_(AppKit.NSMakePoint(px - 20, py + 2 + b_wave))
        b_tail.lineToPoint_(AppKit.NSMakePoint(px - 6, py - 3))
        b_tail.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.18, 0.18, 1.0).set()
        b_tail.fill()

        # 4. Cappello Chef (Toque Blanche) con volume e ombreggiatura
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(AppKit.NSMakeRect(px - 6, py + 14, 16, 6), 2, 2).fill()
        
        # Puffy Crown Toque
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 12, py + 17, 14, 15)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 3, py + 19, 15, 16)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4, py + 16, 12, 14)).fill()

        # Ombreggiatura pieghe Toque
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.82, 0.85, 0.92, 1.0).set()
        f1 = AppKit.NSBezierPath.bezierPath()
        f1.setLineWidth_(1.3)
        f1.moveToPoint_(AppKit.NSMakePoint(px - 4, py + 17))
        f1.lineToPoint_(AppKit.NSMakePoint(px - 4, py + 30))
        f1.stroke()
        f2 = AppKit.NSBezierPath.bezierPath()
        f2.setLineWidth_(1.3)
        f2.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 17))
        f2.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 30))
        f2.stroke()

        # 5. Vassoio d'argento porta pizza
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.92, 0.98, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 30, py - 20, 26, 8)).fill()

        # Trancio di Pizza Fumante 🍕
        pizza = AppKit.NSBezierPath.bezierPath()
        pizza.moveToPoint_(AppKit.NSMakePoint(px - 28, py - 18))
        pizza.lineToPoint_(AppKit.NSMakePoint(px - 9, py - 14))
        pizza.lineToPoint_(AppKit.NSMakePoint(px - 15, py - 7))
        pizza.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.20, 1.0).set()
        pizza.fill()
        
        # Salame / Pepperoni
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.20, 0.15, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 21, py - 15, 4.5, 4.5)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py - 13, 3.5, 3.5)).fill()

        # Volute di vapore caldo animate
        steam_y = math.sin(tick * 0.15) * 3.0
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 1.0, 0.65).set()
        steam = AppKit.NSBezierPath.bezierPath()
        steam.setLineWidth_(1.4)
        steam.moveToPoint_(AppKit.NSMakePoint(px - 17, py - 5))
        steam.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 14, py + 6 + steam_y),
            AppKit.NSMakePoint(px - 22, py + steam_y * 0.5),
            AppKit.NSMakePoint(px - 10, py + 3 + steam_y)
        )
        steam.stroke()

        # 6. Ala
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 16, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 6, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 10, py - 24))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.42, 0.35, 1.0).set()
        wing.fill()

        # Propeller
        self.draw_propeller(px + 32.0, py + 2.0, tick)
