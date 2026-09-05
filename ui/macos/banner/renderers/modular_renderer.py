"""
Modular Vector Pilot Renderer for QuakMeeting (macOS Quartz 2D).
Dynamically composites any base animal (Duck 🦆, Owl 🦉, Bunny 🐰)
with any costume/headwear (Student 🎓, Chef 👨‍🍳, Captain 🧑‍✈️, Agent 🕵️, Gym 🏋️, Racer 🏎️, Zen 🌸, Aviator 🪖).
"""
import math
import AppKit
from .base_renderer import BasePilotRenderer

class ModularPilotRenderer(BasePilotRenderer):
    def __init__(self, animal: str = "duck", outfit: str = "aviator"):
        self.animal = animal.lower()
        self.outfit = outfit.lower()

    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        ctx = AppKit.NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()

        # 1. Base Aircraft / Vehicle Fuselage
        self._draw_fuselage(px, py, tick)

        # 2. Base Animal (Duck, Owl, Bunny, Platypus, Squirrel)
        if self.animal == "bunny":
            self._draw_bunny(px, py, tick)
        elif self.animal == "owl":
            self._draw_owl(px, py, tick)
        elif self.animal == "platypus":
            self._draw_platypus(px, py, tick)
        elif self.animal == "squirrel":
            self._draw_squirrel(px, py, tick)
        else:
            self._draw_duck(px, py, tick)

        # 3. Costume / Headwear Overlay
        self._draw_outfit(px, py, tick)

        # 4. Front Propeller
        self.draw_propeller(px + 34, py + 1, tick)

        ctx.restoreGraphicsState()

    def _draw_fuselage(self, px: float, py: float, tick: int) -> None:
        # Fusoliera Vintage / Spy / Racer in base all'outfit
        body_rect = AppKit.NSMakeRect(px - 44, py - 13, 76, 28)
        body = AppKit.NSBezierPath.bezierPathWithOvalInRect_(body_rect)

        if self.outfit in ("agent", "racer"):
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.18, 0.22, 0.28, 1.0).set()
        elif self.outfit == "captain":
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.20, 0.38, 1.0).set()
        elif self.outfit == "student":
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.30, 0.22, 0.40, 1.0).set()
        else:
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.94, 0.82, 1.0).set()
        body.fill()

        # Striscia decorativa
        stripe = AppKit.NSBezierPath.bezierPath()
        stripe.moveToPoint_(AppKit.NSMakePoint(px - 38, py - 2))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 24, py - 2))
        stripe.lineToPoint_(AppKit.NSMakePoint(px + 22, py - 6))
        stripe.lineToPoint_(AppKit.NSMakePoint(px - 36, py - 6))
        stripe.closePath()

        if self.outfit == "student":
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.80, 0.65, 0.98, 1.0).set()
        elif self.outfit == "agent":
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.85, 0.82, 1.0).set()
        elif self.outfit == "captain":
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.78, 0.35, 1.0).set()
        else:
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.20, 0.18, 1.0).set()
        stripe.fill()

        # Bordo fusoliera
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.20, 0.15, 0.10, 0.80).set()
        body.setLineWidth_(1.4)
        body.stroke()

        # Cockpit
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.18, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py, 26, 16)).fill()

        # Ala
        # Ala
        wing = AppKit.NSBezierPath.bezierPath()
        wing.moveToPoint_(AppKit.NSMakePoint(px - 16, py - 4))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 14, py - 4))
        wing.lineToPoint_(AppKit.NSMakePoint(px + 2, py - 26))
        wing.lineToPoint_(AppKit.NSMakePoint(px - 14, py - 26))
        wing.closePath()
        wing.fill()

        # Strobo di navigazione
        self.draw_wingtip_strobe(px + 2.0, py - 26.0, tick)

    def _draw_duck(self, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        # Testa Papero Dorato con guancia morbida
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.28, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 10, py + 2 + hb_y, 22, 20)).fill()

        # Guanciotta aranciata / blush caldo
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.65, 0.20, 0.35).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 4 + hb_y, 8, 6)).fill()

        # Becco 3D Sagomato Curvo con Sorriso (Dettagliato)
        beak_bob = math.sin(tick * 0.12) * 0.7

        # Mandibola inferiore d'ombra
        lower_beak = AppKit.NSBezierPath.bezierPath()
        lower_beak.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 5.5 + hb_y))
        lower_beak.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 17, py + 6.5 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 9, py + 2.5 + hb_y),
            AppKit.NSMakePoint(px + 14, py + 3.8 + hb_y + beak_bob)
        )
        lower_beak.lineToPoint_(AppKit.NSMakePoint(px + 4, py + 6.5 + hb_y))
        lower_beak.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.35, 0.02, 1.0).set()
        lower_beak.fill()

        # Corpo principale del becco con concavità e punta arrotondata
        beak_path = AppKit.NSBezierPath.bezierPath()
        beak_path.moveToPoint_(AppKit.NSMakePoint(px + 4, py + 10.5 + hb_y))
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 18.5, py + 7.5 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 9, py + 11.2 + hb_y),
            AppKit.NSMakePoint(px + 15, py + 10.2 + hb_y + beak_bob)
        )
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 17.5, py + 5.5 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 19.5, py + 6.8 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 19.0, py + 5.8 + hb_y + beak_bob)
        )
        beak_path.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 4, py + 5.0 + hb_y),
            AppKit.NSMakePoint(px + 13, py + 5.0 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 8, py + 4.5 + hb_y)
        )
        beak_path.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.50, 0.03, 1.0).set()
        beak_path.fill()

        # Linea del sorriso / separazione labiale
        crease = AppKit.NSBezierPath.bezierPath()
        crease.moveToPoint_(AppKit.NSMakePoint(px + 4.5, py + 6.8 + hb_y))
        crease.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 16.5, py + 6.8 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 9, py + 6.5 + hb_y),
            AppKit.NSMakePoint(px + 13, py + 7.0 + hb_y + beak_bob)
        )
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.78, 0.28, 0.0, 0.90).set()
        crease.setLineWidth_(0.85)
        crease.stroke()

        # Riflesso speculare dorato superiore
        highlight = AppKit.NSBezierPath.bezierPath()
        highlight.moveToPoint_(AppKit.NSMakePoint(px + 6, py + 9.8 + hb_y))
        highlight.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 14.5, py + 8.4 + hb_y + beak_bob),
            AppKit.NSMakePoint(px + 9, py + 10.3 + hb_y),
            AppKit.NSMakePoint(px + 12, py + 9.5 + hb_y + beak_bob)
        )
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.78, 0.30, 0.85).set()
        highlight.setLineWidth_(1.1)
        highlight.stroke()

        # Narice d'anatra
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.65, 0.22, 0.0, 0.95).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(
            AppKit.NSMakeRect(px + 7.0, py + 8.8 + hb_y, 1.6, 1.2)
        ).fill()

        # Occhio con ciclo di ammiccamento e riflessi
        if self.is_eye_blinking(tick):
            eye_arc = AppKit.NSBezierPath.bezierPath()
            eye_arc.setLineWidth_(1.8)
            eye_arc.setLineCapStyle_(AppKit.NSLineCapStyleRound)
            eye_arc.moveToPoint_(AppKit.NSMakePoint(px + 1.5, py + 13.5 + hb_y))
            eye_arc.curveToPoint_controlPoint1_controlPoint2_(
                AppKit.NSMakePoint(px + 7.0, py + 13.5 + hb_y),
                AppKit.NSMakePoint(px + 3.5, py + 16.0 + hb_y),
                AppKit.NSMakePoint(px + 5.0, py + 16.0 + hb_y)
            )
            AppKit.NSColor.blackColor().set()
            eye_arc.stroke()
        else:
            AppKit.NSColor.blackColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1.5, py + 10.5 + hb_y, 5.0, 5.5)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3.0, py + 13.0 + hb_y, 2.0, 2.0)).fill()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.2, py + 11.2 + hb_y, 0.9, 0.9)).fill()

    def _draw_owl(self, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.12) * 1.0
        tuft_wave = math.sin(tick * 0.22) * 2.8
        # Piumaggio Gufo Saggio (Marrone Caffè / Grigio Tortora)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.58, 0.46, 0.38, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 11, py + 1 + hb_y, 23, 21)).fill()

        # Ciuffi auricolari a punta da gufo che ondeggiano nel vento
        tuft = AppKit.NSBezierPath.bezierPath()
        tuft.moveToPoint_(AppKit.NSMakePoint(px - 9, py + 17 + hb_y))
        tuft.lineToPoint_(AppKit.NSMakePoint(px - 13, py + 25 + hb_y + tuft_wave))
        tuft.lineToPoint_(AppKit.NSMakePoint(px - 4, py + 20 + hb_y))
        tuft.closePath()
        tuft.fill()

        # Maschera facciale chiara
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.88, 0.80, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 2, py + 4 + hb_y, 14, 14)).fill()

        # Becco ricurvo
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.65, 0.15, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPath()
        beak.moveToPoint_(AppKit.NSMakePoint(px + 7, py + 10 + hb_y))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 14, py + 7 + hb_y))
        beak.lineToPoint_(AppKit.NSMakePoint(px + 7, py + 5 + hb_y))
        beak.closePath()
        beak.fill()

        # Occhio dorato con ammiccamento
        if self.is_eye_blinking(tick):
            eye_arc = AppKit.NSBezierPath.bezierPath()
            eye_arc.setLineWidth_(2.0)
            eye_arc.setLineCapStyle_(AppKit.NSLineCapStyleRound)
            eye_arc.moveToPoint_(AppKit.NSMakePoint(px + 1.0, py + 12.5 + hb_y))
            eye_arc.curveToPoint_controlPoint1_controlPoint2_(
                AppKit.NSMakePoint(px + 9.0, py + 12.5 + hb_y),
                AppKit.NSMakePoint(px + 4.0, py + 16.0 + hb_y),
                AppKit.NSMakePoint(px + 6.0, py + 16.0 + hb_y)
            )
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.12, 0.08, 1.0).set()
            eye_arc.stroke()
        else:
            AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.80, 0.15, 1.0).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 10 + hb_y, 6.0, 6.0)).fill()
            AppKit.NSColor.blackColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4, py + 11.5 + hb_y, 3.0, 3.0)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 5, py + 13 + hb_y, 1.2, 1.2)).fill()

    def _draw_bunny(self, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        ear_base_wave = math.sin(tick * 0.18) * 2.5
        ear_tip_wave = math.sin(tick * 0.22 + 0.8) * 4.2

        # 🐰 1. Back Ear (Orecchio Posteriore per profondità 3D)
        ear_r = AppKit.NSBezierPath.bezierPath()
        ear_r.moveToPoint_(AppKit.NSMakePoint(px - 3, py + 17 + hb_y))
        ear_r.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 10, py + 36 + ear_tip_wave * 0.9 + hb_y),
            AppKit.NSMakePoint(px - 8, py + 26 + ear_base_wave * 0.8 + hb_y),
            AppKit.NSMakePoint(px - 17, py + 32 + ear_tip_wave * 0.9 + hb_y)
        )
        ear_r.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px + 2, py + 18 + hb_y),
            AppKit.NSMakePoint(px - 4, py + 33 + ear_tip_wave * 0.9 + hb_y),
            AppKit.NSMakePoint(px + 1, py + 25 + hb_y)
        )
        ear_r.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.88, 0.87, 1.0).set()
        ear_r.fill()

        # Interno Orecchio Posteriore
        ear_r_in = AppKit.NSBezierPath.bezierPath()
        ear_r_in.moveToPoint_(AppKit.NSMakePoint(px - 2, py + 19 + hb_y))
        ear_r_in.lineToPoint_(AppKit.NSMakePoint(px - 8, py + 32 + ear_tip_wave * 0.9 + hb_y))
        ear_r_in.lineToPoint_(AppKit.NSMakePoint(px, py + 21 + hb_y))
        ear_r_in.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.65, 0.72, 0.60).set()
        ear_r_in.fill()

        # 🐰 2. Front Ear (Orecchio Anteriore Floppy)
        ear_l = AppKit.NSBezierPath.bezierPath()
        ear_l.moveToPoint_(AppKit.NSMakePoint(px - 9, py + 16 + hb_y))
        ear_l.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 18, py + 35 + ear_tip_wave + hb_y),
            AppKit.NSMakePoint(px - 17, py + 24 + ear_base_wave + hb_y),
            AppKit.NSMakePoint(px - 25, py + 30 + ear_tip_wave + hb_y)
        )
        ear_l.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 4, py + 18 + hb_y),
            AppKit.NSMakePoint(px - 10, py + 32 + ear_tip_wave + hb_y),
            AppKit.NSMakePoint(px - 5, py + 24 + hb_y)
        )
        ear_l.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.96, 0.95, 1.0).set()
        ear_l.fill()

        # Interno Orecchio Anteriore Rosa Pastello
        ear_inner = AppKit.NSBezierPath.bezierPath()
        ear_inner.moveToPoint_(AppKit.NSMakePoint(px - 8, py + 18 + hb_y))
        ear_inner.lineToPoint_(AppKit.NSMakePoint(px - 16, py + 31 + ear_tip_wave + hb_y))
        ear_inner.lineToPoint_(AppKit.NSMakePoint(px - 6, py + 20 + hb_y))
        ear_inner.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.72, 0.78, 0.85).set()
        ear_inner.fill()

        # 🐰 3. Testa Rotonda Soffice
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.96, 0.95, 1.0).set()
        head = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 9, py + 2 + hb_y, 21, 19))
        head.fill()

        # 🐰 4. Musetto Morbido e Guancia Rosa (Zero Becco)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.82, 0.86, 0.65).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 1, py + 4 + hb_y, 9, 7)).fill()

        # Cuscinetto musetto bianco soffice
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
        muzzle = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 6, py + 3.5 + hb_y, 7.5, 6.5))
        muzzle.fill()

        # 🐰 5. Dente da Coniglietto (Cute Bunny Buck Tooth)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 0.98, 1.0).set()
        tooth = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px + 8.5, py + 2.0 + hb_y, 3.2, 3.2), 1.0, 1.0
        )
        tooth.fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.70, 0.65, 0.70, 0.60).set()
        tooth.setLineWidth_(0.6)
        tooth.stroke()

        # 🐰 6. Occhio Grande da Coniglio con riflessi dolci
        if self.is_eye_blinking(tick):
            eye_arc = AppKit.NSBezierPath.bezierPath()
            eye_arc.setLineWidth_(1.8)
            eye_arc.setLineCapStyle_(AppKit.NSLineCapStyleRound)
            eye_arc.moveToPoint_(AppKit.NSMakePoint(px + 1.0, py + 12.5 + hb_y))
            eye_arc.curveToPoint_controlPoint1_controlPoint2_(
                AppKit.NSMakePoint(px + 8.0, py + 12.5 + hb_y),
                AppKit.NSMakePoint(px + 3.5, py + 15.5 + hb_y),
                AppKit.NSMakePoint(px + 5.5, py + 15.5 + hb_y)
            )
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.15, 0.28, 1.0).set()
            eye_arc.stroke()
        else:
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.15, 0.28, 1.0).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1.5, py + 9.5 + hb_y, 5.5, 6.5)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3.0, py + 12.5 + hb_y, 2.2, 2.2)).fill()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.5, py + 10.5 + hb_y, 1.0, 1.0)).fill()

        # 🐰 7. Nasino a Bottone Rosa (Cute Button Bunny Nose)
        nose_twitch = 0.4 if (tick % 24) < 10 else 0.0
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.48, 0.62, 1.0).set()
        nose = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
            AppKit.NSMakeRect(px + 10.0, py + 7.0 + hb_y + nose_twitch, 3.5, 2.8)
        )
        nose.fill()

        # Fessura del musetto (Philtrum)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.40, 0.55, 0.80).set()
        philtrum = AppKit.NSBezierPath.bezierPath()
        philtrum.moveToPoint_(AppKit.NSMakePoint(px + 10.5, py + 7.0 + hb_y + nose_twitch))
        philtrum.lineToPoint_(AppKit.NSMakePoint(px + 10.5, py + 4.8 + hb_y))
        philtrum.setLineWidth_(0.8)
        philtrum.stroke()

        # 🐰 8. Lentiggini/Punti Musetto da Coniglietto (Zero becco grigio)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.85, 0.55, 0.65, 0.70).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.0, py + 6.5 + hb_y, 1.1, 1.1)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 6.0, py + 5.8 + hb_y, 1.1, 1.1)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.8, py + 4.8 + hb_y, 1.1, 1.1)).fill()

    def _draw_platypus(self, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        tail_bob = math.sin(tick * 0.16) * 3.5
        # Coda a castoro che ondeggia nel flusso
        tail_path = AppKit.NSBezierPath.bezierPath()
        tail_path.moveToPoint_(AppKit.NSMakePoint(px - 36, py - 4 + tail_bob * 0.3))
        tail_path.lineToPoint_(AppKit.NSMakePoint(px - 58, py + 4 + tail_bob))
        tail_path.lineToPoint_(AppKit.NSMakePoint(px - 62, py - 6 + tail_bob))
        tail_path.lineToPoint_(AppKit.NSMakePoint(px - 38, py - 12 + tail_bob * 0.3))
        tail_path.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.42, 0.26, 0.16, 1.0).set()
        tail_path.fill()

        # Testa e corpo verde acqua / ottanio (Perry Teal)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.65, 0.62, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 10, py + 2 + hb_y, 23, 19)).fill()

        # Becco piatto largo da ornitorinco
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.52, 0.12, 1.0).set()
        beak = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(px + 4, py + 3 + hb_y, 19, 8), 3.0, 3.0
        )
        beak.fill()

        # Occhio con ammiccamento
        if self.is_eye_blinking(tick):
            eye_arc = AppKit.NSBezierPath.bezierPath()
            eye_arc.setLineWidth_(1.8)
            eye_arc.setLineCapStyle_(AppKit.NSLineCapStyleRound)
            eye_arc.moveToPoint_(AppKit.NSMakePoint(px + 2.0, py + 13.0 + hb_y))
            eye_arc.curveToPoint_controlPoint1_controlPoint2_(
                AppKit.NSMakePoint(px + 8.0, py + 13.0 + hb_y),
                AppKit.NSMakePoint(px + 4.5, py + 15.5 + hb_y),
                AppKit.NSMakePoint(px + 6.0, py + 15.5 + hb_y)
            )
            AppKit.NSColor.blackColor().set()
            eye_arc.stroke()
        else:
            AppKit.NSColor.blackColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3, py + 11 + hb_y, 4.5, 4.5)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 4.5, py + 12.5 + hb_y, 1.5, 1.5)).fill()

    def _draw_squirrel(self, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        tail_wave = math.sin(tick * 0.18) * 3.8
        tail = AppKit.NSBezierPath.bezierPath()
        tail.moveToPoint_(AppKit.NSMakePoint(px - 34, py - 4))
        tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 44, py + 26 + tail_wave),
            AppKit.NSMakePoint(px - 48, py + 8 + tail_wave * 0.5),
            AppKit.NSMakePoint(px - 56, py + 22 + tail_wave)
        )
        tail.curveToPoint_controlPoint1_controlPoint2_(
            AppKit.NSMakePoint(px - 26, py + 4),
            AppKit.NSMakePoint(px - 36, py + 24 + tail_wave),
            AppKit.NSMakePoint(px - 30, py + 12)
        )
        tail.closePath()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.78, 0.42, 0.22, 1.0).set()
        tail.fill()

        # Testa castana
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.82, 0.46, 0.25, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 9, py + 2 + hb_y, 21, 19)).fill()

        # Petto e guanciotte bianche
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.95, 0.90, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 3 + hb_y, 10, 8)).fill()

        # Musetto e nasino
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.25, 0.15, 0.12, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 10, py + 6 + hb_y, 3.5, 3.5)).fill()

        # Occhio vispo con ammiccamento
        if self.is_eye_blinking(tick):
            eye_arc = AppKit.NSBezierPath.bezierPath()
            eye_arc.setLineWidth_(1.8)
            eye_arc.setLineCapStyle_(AppKit.NSLineCapStyleRound)
            eye_arc.moveToPoint_(AppKit.NSMakePoint(px + 1.0, py + 12.0 + hb_y))
            eye_arc.curveToPoint_controlPoint1_controlPoint2_(
                AppKit.NSMakePoint(px + 7.0, py + 12.0 + hb_y),
                AppKit.NSMakePoint(px + 3.5, py + 14.5 + hb_y),
                AppKit.NSMakePoint(px + 5.0, py + 14.5 + hb_y)
            )
            AppKit.NSColor.blackColor().set()
            eye_arc.stroke()
        else:
            AppKit.NSColor.blackColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 10 + hb_y, 4.5, 5.0)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 3.5, py + 12 + hb_y, 1.8, 1.8)).fill()

    def _draw_outfit(self, px: float, py: float, tick: int) -> None:
        if self.outfit == "student":
            # 🎓 CAPPELLO DA LAUREA (Mortarboard Academic Cap with dangling tassel)
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.22, 1.0).set()
            cap = AppKit.NSBezierPath.bezierPath()
            cap.moveToPoint_(AppKit.NSMakePoint(px - 14, py + 19))
            cap.lineToPoint_(AppKit.NSMakePoint(px + 3, py + 26))
            cap.lineToPoint_(AppKit.NSMakePoint(px + 18, py + 19))
            cap.lineToPoint_(AppKit.NSMakePoint(px + 1, py + 14))
            cap.closePath()
            cap.fill()

            # Nappina pendente dorata
            tassel_sway = math.sin(tick * 0.20) * 3.0
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.85, 0.35, 1.0).set()
            tassel = AppKit.NSBezierPath.bezierPath()
            tassel.moveToPoint_(AppKit.NSMakePoint(px + 2, py + 22))
            tassel.lineToPoint_(AppKit.NSMakePoint(px - 12 + tassel_sway, py + 10))
            tassel.setLineWidth_(1.4)
            tassel.stroke()

            # Occhiali rotondi da studioso
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.95, 0.80, 0.20, 1.0).set()
            lens = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 1, py + 8, 7.5, 7.5))
            lens.setLineWidth_(1.2)
            lens.stroke()

        elif self.outfit == "chef":
            # 👨‍🍳 CAPPELLO DA CHEF (Pleated White Toque)
            AppKit.NSColor.whiteColor().set()
            toque = AppKit.NSBezierPath.bezierPath()
            toque.moveToPoint_(AppKit.NSMakePoint(px - 8, py + 16))
            toque.lineToPoint_(AppKit.NSMakePoint(px - 10, py + 27))
            toque.curveToPoint_controlPoint1_controlPoint2_(
                AppKit.NSMakePoint(px + 10, py + 28),
                AppKit.NSMakePoint(px - 4, py + 34),
                AppKit.NSMakePoint(px + 6, py + 34)
            )
            toque.lineToPoint_(AppKit.NSMakePoint(px + 8, py + 16))
            toque.closePath()
            toque.fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.80, 0.82, 0.88, 1.0).set()
            toque.setLineWidth_(1.0)
            toque.stroke()

        elif self.outfit == "captain":
            # 🧑‍✈️ BERRETTO DA COMANDANTE DI VOLO (Navy Captain Cap with Gold Emblem)
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.12, 0.16, 0.28, 1.0).set()
            cap = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 16, 20, 8))
            cap.fill()
            # Visiera nera
            AppKit.NSColor.blackColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 14, 12, 4)).fill()
            # Fregio dorato
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.96, 0.80, 0.25, 1.0).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 19, 4, 4)).fill()

        elif self.outfit == "agent":
            # 🕵️‍♂️ CAPPELLO FEDORA DA AGENTE SEGRETO (Brown Fedora with Black Band)
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.48, 0.28, 0.15, 1.0).set()
            brim = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 14, py + 16, 28, 6))
            brim.fill()
            crown = AppKit.NSBezierPath.bezierPath()
            crown.moveToPoint_(AppKit.NSMakePoint(px - 7, py + 18))
            crown.lineToPoint_(AppKit.NSMakePoint(px - 5, py + 28))
            crown.lineToPoint_(AppKit.NSMakePoint(px + 5, py + 29))
            crown.lineToPoint_(AppKit.NSMakePoint(px + 7, py + 18))
            crown.closePath()
            crown.fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.18, 1.0).set()
            band = AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 6.5, py + 18, 13, 3))
            band.fill()

        elif self.outfit == "gym":
            # 🏋️‍♂️ FASCETTA SPORTIVA ROSSA
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.25, 0.25, 1.0).set()
            band = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                AppKit.NSMakeRect(px - 8, py + 14, 18, 5), 2.0, 2.0
            )
            band.fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 7, py + 15.5, 16, 1.5)).fill()

        elif self.outfit == "racer":
            # 🏎️ CASCO SPEED RACER
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.98, 0.45, 0.15, 1.0).set()
            helmet = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 8, py + 12, 19, 14))
            helmet.fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.18, 0.25, 0.85).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px + 2, py + 13, 10, 8)).fill()

        elif self.outfit == "zen":
            # 🌸 FIORE DI LOTO SULL'ORECCHIO
            AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.55, 0.75, 1.0).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 6, py + 16, 8, 8)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 4, py + 18, 4, 4)).fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.20, 1.0).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px - 3, py + 19, 2, 2)).fill()

        else:  # aviator
            # 🪖 OCCHIALONI DA AVIATORE CON CINGHIA
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 0.25, 0.18, 1.0).set()
            AppKit.NSBezierPath.bezierPathWithRect_(AppKit.NSMakeRect(px - 8, py + 13, 18, 3)).fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.90, 0.75, 0.35, 1.0).set()
            goggle = AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(px, py + 9, 10, 10))
            goggle.setLineWidth_(1.6)
            goggle.stroke()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.55, 0.88, 0.98, 0.75).set()
            goggle.fill()
