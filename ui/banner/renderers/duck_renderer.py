"""
Aviator Duck Pilot Renderer for QuakMeeting.
Features vintage biplane, animated scarf in the wind, 3D beak, and leather flight helmet with goggles.
"""
import math
import AppKit
from .base_renderer import BasePilotRenderer

class DuckPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. Timone di coda con pinna rossa e striscia bianca
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 30, py - 2))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 56, py + 24))
        tail.lineToPoint_(AppKit.NSMakePoint(px - 42, py - 2))
        tail.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.22, 0.20, 1.0).set()
        tail.fill()

        # Decoro pinna di coda
        AppKit.NSColor.whiteColor().set()
        tail_deco = AppKit.NSBezierPath.bezierPath()
        tail_deco.moveToPoint_(AppKit.NSMakePoint(px - 38, py + 3))
        tail_deco.lineToPoint_(AppKit.NSMakePoint(px - 48, py + 16))
        tail_deco.lineToPoint_(AppKit.NSMakePoint(px - 44, py + 16))
        tail_deco.lineToPoint_(AppKit.NSMakePoint(px - 35, py + 3))
        tail_deco.closePath()
        tail_deco.fill()

        # 2. Fusoliera Vintage Biplano (Doppio Tono Crema & Rosso Racing)
        body_rect = AppKit.NSMakeRect(px - 44, py - 13, 76, 28)
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(body_rect)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.94, 0.82, 1.0).set()
        body.fill()

        # Fiancata inferiore color terracotta/ombra
        bot_shade = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 42, py - 15, 72, 16))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.78, 0.62, 0.60).set()
        bot_shade.fill()

        # Striscia decorativa dinamica rossa
        stripe = AppKit.NSBezierPath.bezierPath()
        stripe.moveToPoint_(AppKit.NSMakePoint(px - 38, py - 2))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 24, py - 2))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 22, py - 6))
        stripe.lineToPoint_(AppKit.NSMakePoint(px - 36, py - 6))
        stripe.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.20, 0.18, 1.0).set()
        stripe.fill()

        # Bordo fusoliera rifinito
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 0.25, 0.15, 0.85).set()
        body.setLineWidth_(1.4)
        body.stroke()

        # 3. Cockpit & Parabrezza Curvo Lucido
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.18, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py, 26, 16)).fill()

        glass_path = AppKit.NSBezierPath.bezierPath()
        glass_path.moveToPoint_(AppKit.NSMakePoint(px + 10, py + 1))
        glass_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 2, py + 17),
            AppKit.NSMakePoint(px + 8, py + 12),
            AppKit.NSMakePoint(px + 2, py + 16)
        )
        glass_path.lineToPoint_(AppKit.NSMakePoint(px - 8, py + 1))
        glass_path.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.88, 0.98, 0.75).set()
        glass_path.fill()
        AppKit.NSColor.whiteColor().colorWithAlphaComponent_(0.9).set()
        glass_path.setLineWidth_(1.2)
        glass_path.stroke()

        # Bagliore speculare parabrezza
        glare = AppKit.NSBezierPath.bezierPath()
        glare.moveToPoint_(AppKit.NSMakePoint(px + 5, py + 5))
        glare.lineToPoint_(AppKit.NSMakePoint(px + 1, py + 14))
        glare.setLineWidth_(1.5)
        glare.stroke()

        # 4. Sciarpa Rossa Svolazzante Animata nel Vento 🧣
        scarf_wave1 = math.sin(tick * 0.28) * 5.0
        scarf_wave2 = math.sin(tick * 0.28 + 1.2) * 6.5
        
        scarf_tail = AppKit.NSBezierPath.bezierPath()
        scarf_tail.moveToPoint_(AppKit.NSMakePoint(px - 8, py + 5))
        scarf_tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 28, py + 7 + scarf_wave1),
            AppKit.NSMakePoint(px - 15, py + 4 + scarf_wave1 * 0.5),
            AppKit.NSMakePoint(px - 22, py + 10 + scarf_wave1)
        )
        scarf_tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 46, py + 4 + scarf_wave2),
            AppKit.NSMakePoint(px - 34, py + 5 + scarf_wave1),
            AppKit.NSMakePoint(px - 40, py + 8 + scarf_wave2)
        )
        scarf_tail.lineToPoint_(AppKit.NSMakePoint(px - 45, py - 1 + scarf_wave2))
        scarf_tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 26, py + 2 + scarf_wave1),
            AppKit.NSMakePoint(px - 38, py + 3 + scarf_wave2),
            AppKit.NSMakePoint(px - 32, py + scarf_wave1)
        )
        scarf_tail.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.18, 0.18, 1.0).set()
        scarf_tail.fill()

        # Frange sciarpa dorate
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.25, 1.0).set()
        fringe = AppKit.NSBezierPath.bezierPath()
        fringe.setLineWidth_(1.6)
        fringe.moveToPoint_(AppKit.NSMakePoint(px - 46, py + 4 + scarf_wave2))
        fringe.lineToPoint_(AppKit.NSMakePoint(px - 49, py + 3 + scarf_wave2))
        fringe.moveToPoint_(AppKit.NSMakePoint(px - 45, py + 1.5 + scarf_wave2))
        fringe.lineToPoint_(AppKit.NSMakePoint(px - 48, py + 0.5 + scarf_wave2))
        fringe.stroke()

        # Nodo sciarpa al collo
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.15, 0.15, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 9, py + 2, 11, 7)).fill()

        # 5. Testa Papero con Sfumature Calde e Guance Rosee 🦆
        head_rect = AppKit.NSMakeRect(px - 8, py + 3, 20, 20)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.65, 0.15, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 7, py + 2, 19, 18)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.24, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(head_rect).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.92, 0.50, 0.70).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 5, py + 9, 14, 13)).fill()

        # Guancia Rosa Morbida
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.42, 0.42, 0.45).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 3, py + 5, 7, 5)).fill()

        # 6. Occhio Espressivo con Doppio Catchlight
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 1.0).set()
        eye_rect = AppKit.NSMakeRect(px + 2.5, py + 12, 5.0, 5.5)
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(eye_rect).fill()

        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.2, py + 14.2, 2.2, 2.2)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3.2, py + 12.8, 1.0, 1.0)).fill()

        # 7. Becco Sagomato 3D con Sorriso
        beak_path = AppKit.NSBezierPath.bezierPath()
        beak_path.moveToPoint_(AppKit.NSMakePoint(px + 5, py + 12))
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 18, py + 9.5),
            AppKit.NSMakePoint(px + 10, py + 13),
            AppKit.NSMakePoint(px + 15, py + 12)
        )
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 5, py + 5.5),
            AppKit.NSMakePoint(px + 15, py + 7),
            AppKit.NSMakePoint(px + 10, py + 6)
        )
        beak_path.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.02, 1.0).set()
        beak_path.fill()

        # Luce riflessa sul labbro superiore del becco
        beak_hi = AppKit.NSBezierPath.bezierPath()
        beak_hi.moveToPoint_(AppKit.NSMakePoint(px + 7, py + 11))
        beak_hi.lineToPoint_(AppKit.NSMakePoint(px + 14, py + 9.5))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.72, 0.25, 0.85).set()
        beak_hi.setLineWidth_(1.2)
        beak_hi.stroke()

        # Narice
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.75, 0.30, 0.0, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 8, py + 10.5, 1.5, 1.2)).fill()

        # 8. Caschetto da Aviatore in Cuoio & Occhialoni Dorati
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.38, 0.22, 0.12, 1.0).set()
        cap_path = AppKit.NSBezierPath.bezierPath()
        cap_path.moveToPoint_(AppKit.NSMakePoint(px - 8, py + 12))
        cap_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 6, py + 22),
            AppKit.NSMakePoint(px - 6, py + 23),
            AppKit.NSMakePoint(px + 2, py + 24)
        )
        cap_path.lineToPoint_(AppKit.NSMakePoint(px + 6, py + 18))
        cap_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 8, py + 12),
            AppKit.NSMakePoint(px, py + 18),
            AppKit.NSMakePoint(px - 5, py + 14)
        )
        cap_path.closePath()
        cap_path.fill()

        # Cinghia occhialoni
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.25, 0.15, 0.08, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 8, py + 12.5, 18, 3.5)).fill()

        # Occhialone da aviatore dorato
        goggle_frame = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 1.5, py + 10, 12, 11))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.78, 0.25, 1.0).set()
        goggle_frame.setLineWidth_(2.4)
        goggle_frame.stroke()

        # Lente specchiata azzurra con riflesso cielo
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.50, 0.85, 0.98, 0.85).set()
        goggle_frame.fill()

        AppKit.NSColor.whiteColor().colorWithAlphaComponent_(0.85).set()
        lens_glare = AppKit.NSBezierPath.bezierPath()
        lens_glare.setLineWidth_(1.4)
        lens_glare.moveToPoint_(AppKit.NSMakePoint(px + 3, py + 18))
        lens_glare.lineToPoint_(AppKit.NSMakePoint(px + 7, py + 13))
        lens_glare.stroke()

        # 9. Ali Inferiori & Montanti Biplano
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 18, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 18, py - 2))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 8, py - 24))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 12, py - 24))
        wing.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.22, 0.20, 1.0).set()
        wing.fill()

        wing_trim = AppKit.NSBezierPath.bezierPath()
        wing_trim.moveToPoint_(AppKit.NSMakePoint(px - 12, py - 24))
        wing_trim.lineToPoint_(AppKit.NSMakePoint(px + 8, py - 24))
        AppKit.NSColor.whiteColor().set()
        wing_trim.setLineWidth_(2.0)
        wing_trim.stroke()
        
        # Propeller
        self.draw_propeller(px + 32.0, py + 2.0, tick)
