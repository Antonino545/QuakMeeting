"""
Hyper Squirrel Pilot Renderer for QuakMeeting (macOS Quartz 2D).
Features chestnut squirrel with dynamic bushy tail wave, white chest fluff, acorn-shell pilot helmet with stem, and golden goggles.
"""
import math
import AppKit
from .base_renderer import BasePilotRenderer

class SquirrelPilotRenderer(BasePilotRenderer):
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        # 1. 🐿️ Coda Voluminosa e Ondulante (Dynamic Bushy Squirrel Tail)
        tail_wave = math.sin(tick * 0.18) * 3.0
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 28, py - 4))
        # Curva ad S fluida della coda da scoiattolo
        tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 58, py + 26 + tail_wave),
            AppKit.NSMakePoint(px - 44, py + 4),
            AppKit.NSMakePoint(px - 66, py + 14 + tail_wave)
        )
        tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 36, py + 14 + tail_wave * 0.5),
            AppKit.NSMakePoint(px - 50, py + 34 + tail_wave),
            AppKit.NSMakePoint(px - 38, py + 24 + tail_wave)
        )
        tail.lineToPoint_(AppKit.NSMakePoint(px - 26, py - 6))
        tail.closePath()

        # Pelo ramato ricco
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.82, 0.42, 0.20, 1.0).set()
        tail.fill()

        # Striatura interna più chiara per volume 3D
        tail_inner = AppKit.NSBezierPath.bezierPath()
        tail_inner.moveToPoint_(AppKit.NSMakePoint(px - 32, py))
        tail_inner.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 50, py + 22 + tail_wave),
            AppKit.NSMakePoint(px - 42, py + 8),
            AppKit.NSMakePoint(px - 58, py + 16 + tail_wave)
        )
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.65, 0.38, 0.80).set()
        tail_inner.setLineWidth_(2.4)
        tail_inner.stroke()

        # 2. Fusoliera Ghianda / Legno Vintage (Acorn Rocket Fuselage)
        body_rect = AppKit.NSMakeRect(px - 38, py - 12, 72, 26)
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(body_rect)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.58, 0.35, 0.20, 1.0).set()
        body.fill()

        # Fiancata inferiore color nocciola
        bot_shade = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 36, py - 14, 68, 14))
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.22, 0.12, 0.70).set()
        bot_shade.fill()

        # Striscia decorativa foglia d'autunno (Orange / Gold Racing Stripe)
        stripe = AppKit.NSBezierPath.bezierPath()
        stripe.moveToPoint_(AppKit.NSMakePoint(px - 32, py - 3))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 22, py - 3))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 20, py - 6))
        stripe.lineToPoint_(AppKit.NSMakePoint(px - 30, py - 6))
        stripe.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.62, 0.15, 1.0).set()
        stripe.fill()

        # Bordo fusoliera
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.15, 0.08, 1.0).set()
        body.setLineWidth_(1.4)
        body.stroke()

        # 3. Cockpit & Parabrezza
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.20, 0.12, 0.08, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py - 1, 28, 18)).fill()

        # 4. Corpo e Guance dello Scoiattolo (Chestnut Face & White Chest)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.45, 0.22, 1.0).set()
        head = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 10, py + 2, 22, 20))
        head.fill()

        # Petto e guance morbide panna
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.94, 0.88, 1.0).set()
        cheeks = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 2, py + 3, 14, 12))
        cheeks.fill()

        # Orecchie a ciuffo
        ear = AppKit.NSBezierPath.bezierPath()
        ear.moveToPoint_(AppKit.NSMakePoint(px - 8, py + 18))
        ear.lineToPoint_(AppKit.NSMakePoint(px - 12, py + 26))
        ear.lineToPoint_(AppKit.NSMakePoint(px - 4, py + 20))
        ear.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.78, 0.38, 0.18, 1.0).set()
        ear.fill()

        # Occhio nero brillante & nasino
        AppKit.NSColor.blackColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4, py + 10, 5.0, 5.0)).fill()
        AppKit.NSColor.whiteColor().set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 5.5, py + 12, 1.8, 1.8)).fill()

        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.20, 0.10, 0.08, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 10, py + 6.5, 3.2, 2.5)).fill()

        # 5. 🌰 CASCHETTO DA PILOTA A CUPOLA DI GHIANDA (Acorn Shell Helmet with Stem)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.45, 0.28, 0.14, 1.0).set()
        acorn_cap = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 9, py + 14, 20, 14))
        acorn_cap.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.18, 0.08, 1.0).set()
        acorn_cap.setLineWidth_(1.2)
        acorn_cap.stroke()

        # Picciolo della ghianda (Acorn Stem)
        stem = AppKit.NSBezierPath.bezierPath()
        stem.moveToPoint_(AppKit.NSMakePoint(px + 1, py + 26))
        stem.lineToPoint_(AppKit.NSMakePoint(px + 3, py + 32))
        stem.lineToPoint_(AppKit.NSMakePoint(px + 5, py + 31))
        stem.lineToPoint_(AppKit.NSMakePoint(px + 3, py + 26))
        stem.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.18, 0.08, 1.0).set()
        stem.fill()

        # Occhialoni da aviatore dorati
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.75, 0.25, 1.0).set()
        goggle = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 9, 10, 10))
        goggle.setLineWidth_(1.8)
        goggle.stroke()

        # 6. Ala Foglia / Aerodinamica Vintage
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.78, 0.40, 0.18, 1.0).set()
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 14, py - 4))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 14, py - 4))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 2, py - 26))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 14, py - 26))
        wing.closePath()
        wing.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.62, 0.15, 0.85).set()
        wing.setLineWidth_(1.2)
        wing.stroke()

        # 7. Elica Anteriore Golden Spinner
        self.draw_propeller(px + 34, py + 1, tick)
