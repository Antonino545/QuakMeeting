"""
Modular Vector Pilot Renderer for QuakMeeting (Linux PyQt6 QPainter).
Dynamically composites any base animal (Duck 🦆, Owl 🦉, Bunny 🐰)
with any costume/headwear (Student 🎓, Chef 👨‍🍳, Captain 🧑‍✈️, Agent 🕵️, Gym 🏋️, Racer 🏎️, Zen 🌸, Aviator 🪖).
"""
from __future__ import annotations
import math

try:
    from PyQt6.QtCore import Qt, QRectF, QPointF
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPointF = object
    QPainter = object
    QColor = object
    QPen = object
    QBrush = object
    QPainterPath = object

from .base_renderer import BaseQtPilotRenderer

class QtModularRenderer(BaseQtPilotRenderer):
    def __init__(self, animal: str = "duck", outfit: str = "aviator"):
        self.animal = animal.lower()
        self.outfit = outfit.lower()

    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Base Aircraft / Vehicle Fuselage
        self._draw_fuselage(p, px, py, tick)

        # 2. Base Animal (Duck, Owl, Bunny, Platypus, Squirrel)
        if self.animal == "bunny":
            self._draw_bunny(p, px, py, tick)
        elif self.animal == "owl":
            self._draw_owl(p, px, py, tick)
        elif self.animal == "platypus":
            self._draw_platypus(p, px, py, tick)
        elif self.animal == "squirrel":
            self._draw_squirrel(p, px, py, tick)
        else:
            self._draw_duck(p, px, py, tick)

        # 3. Costume / Headwear Overlay
        self._draw_outfit(p, px, py, tick)

        # 4. Propeller
        self.draw_propeller(p, px + 34, py + 1, tick)

        p.restore()

    def _draw_fuselage(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.setPen(QPen(QColor(51, 38, 25, 204), 1.4))
        if self.outfit in ("agent", "racer"):
            p.setBrush(QColor(46, 56, 71))
        elif self.outfit == "captain":
            p.setBrush(QColor(31, 51, 97))
        elif self.outfit == "student":
            p.setBrush(QColor(76, 56, 102))
        else:
            p.setBrush(QColor(250, 240, 209))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))

        # Stripe
        stripe_path = QPainterPath()
        stripe_path.moveTo(px - 38, py - 2)
        stripe_path.lineTo(px + 24, py - 2)
        stripe_path.lineTo(px + 22, py - 6)
        stripe_path.lineTo(px - 36, py - 6)
        stripe_path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        if self.outfit == "student":
            p.setBrush(QColor(204, 166, 250))
        elif self.outfit == "agent":
            p.setBrush(QColor(38, 217, 209))
        elif self.outfit == "captain":
            p.setBrush(QColor(242, 199, 89))
        else:
            p.setBrush(QColor(224, 51, 46))
        p.drawPath(stripe_path)

        # Cockpit
        p.setBrush(QColor(38, 46, 64))
        p.drawEllipse(QRectF(px - 14, py, 26, 16))

        # Wing & Strobe
        wing_path = QPainterPath()
        wing_path.moveTo(px - 16, py - 4)
        wing_path.lineTo(px + 14, py - 4)
        wing_path.lineTo(px + 2, py - 26)
        wing_path.lineTo(px - 14, py - 26)
        wing_path.closeSubpath()
        p.setBrush(QColor(245, 158, 38, 217))
        p.drawPath(wing_path)

        # Wingtip navigation strobe beacon
        self.draw_wingtip_strobe(p, px + 2.0, py - 26.0, tick)

    def _draw_duck(self, p: QPainter, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 209, 71))
        p.drawEllipse(QRectF(px - 10, py + 2 + hb_y, 22, 20))

        # Beak with breathing bob
        beak_bob = math.sin(tick * 0.12) * 0.7
        beak_path = QPainterPath()
        beak_path.moveTo(px + 4, py + 8 + hb_y)
        beak_path.lineTo(px + 18, py + 6 + hb_y + beak_bob)
        beak_path.lineTo(px + 4, py + 2 + hb_y)
        beak_path.closeSubpath()
        p.setBrush(QColor(255, 122, 0))
        p.drawPath(beak_path)

        # Eye with natural blinking
        if self.is_eye_blinking(tick):
            eye_arc = QPainterPath()
            eye_arc.moveTo(px + 1.5, py + 13.5 + hb_y)
            eye_arc.quadTo(px + 4.2, py + 16.0 + hb_y, px + 7.0, py + 13.5 + hb_y)
            p.setPen(QPen(QColor(0, 0, 0), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(eye_arc)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(0, 0, 0))
            p.drawEllipse(QRectF(px + 2, py + 11 + hb_y, 4.5, 4.5))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(px + 3.5, py + 12.5 + hb_y, 1.5, 1.5))

    def _draw_owl(self, p: QPainter, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.12) * 1.0
        tuft_wave = math.sin(tick * 0.22) * 2.8
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(148, 117, 97))
        p.drawEllipse(QRectF(px - 11, py + 1 + hb_y, 23, 21))

        # Ear tufts fluttering in slipstream
        tuft_path = QPainterPath()
        tuft_path.moveTo(px - 9, py + 17 + hb_y)
        tuft_path.lineTo(px - 13, py + 25 + hb_y + tuft_wave)
        tuft_path.lineTo(px - 4, py + 20 + hb_y)
        tuft_path.closeSubpath()
        p.drawPath(tuft_path)

        # Face mask
        p.setBrush(QColor(235, 224, 204))
        p.drawEllipse(QRectF(px - 2, py + 4 + hb_y, 14, 14))

        # Beak
        beak_path = QPainterPath()
        beak_path.moveTo(px + 7, py + 10 + hb_y)
        beak_path.lineTo(px + 14, py + 7 + hb_y)
        beak_path.lineTo(px + 7, py + 5 + hb_y)
        beak_path.closeSubpath()
        p.setBrush(QColor(242, 166, 38))
        p.drawPath(beak_path)

        # Eye with natural blinking
        if self.is_eye_blinking(tick):
            eye_arc = QPainterPath()
            eye_arc.moveTo(px + 1.0, py + 12.5 + hb_y)
            eye_arc.quadTo(px + 5.0, py + 16.0 + hb_y, px + 9.0, py + 12.5 + hb_y)
            p.setPen(QPen(QColor(40, 30, 20), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(eye_arc)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(255, 204, 38))
            p.drawEllipse(QRectF(px + 2, py + 10 + hb_y, 6.0, 6.0))
            p.setBrush(QColor(0, 0, 0))
            p.drawEllipse(QRectF(px + 4, py + 11.5 + hb_y, 3.0, 3.0))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(px + 5, py + 13 + hb_y, 1.2, 1.2))

    def _draw_bunny(self, p: QPainter, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        ear_base_wave = math.sin(tick * 0.18) * 2.5
        ear_tip_wave = math.sin(tick * 0.22 + 0.8) * 4.2
        p.setPen(Qt.PenStyle.NoPen)

        # Floppy ears with dual-wave inertia
        ear_path = QPainterPath()
        ear_path.moveTo(px - 8, py + 16 + hb_y)
        ear_path.cubicTo(px - 16, py + 24 + ear_base_wave + hb_y, px - 24, py + 30 + ear_tip_wave + hb_y, px - 16, py + 35 + ear_tip_wave + hb_y)
        ear_path.cubicTo(px - 9, py + 32 + ear_tip_wave + hb_y, px - 4, py + 24 + hb_y, px - 3, py + 18 + hb_y)
        ear_path.closeSubpath()
        p.setBrush(QColor(250, 245, 240))
        p.drawPath(ear_path)

        # Pink inner ear
        p.setBrush(QColor(255, 184, 199, 217))
        inner_path = QPainterPath()
        inner_path.moveTo(px - 7, py + 18 + hb_y)
        inner_path.lineTo(px - 14, py + 31 + ear_tip_wave + hb_y)
        inner_path.lineTo(px - 5, py + 20 + hb_y)
        inner_path.closeSubpath()
        p.drawPath(inner_path)

        # Head
        p.setBrush(QColor(250, 245, 240))
        p.drawEllipse(QRectF(px - 9, py + 2 + hb_y, 21, 19))

        # Cheeks
        p.setBrush(QColor(255, 224, 230, 153))
        p.drawEllipse(QRectF(px + 1, py + 3 + hb_y, 10, 8))

        # Eye with blinking
        if self.is_eye_blinking(tick):
            eye_arc = QPainterPath()
            eye_arc.moveTo(px + 1.0, py + 12.5 + hb_y)
            eye_arc.quadTo(px + 4.5, py + 15.5 + hb_y, px + 8.0, py + 12.5 + hb_y)
            p.setPen(QPen(QColor(56, 38, 71), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(eye_arc)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(56, 38, 71))
            p.drawEllipse(QRectF(px + 2, py + 10 + hb_y, 5.0, 6.0))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(px + 3.5, py + 12.5 + hb_y, 2.0, 2.0))

        # Twitching cute nose
        nose_twitch = 0.5 if (tick % 26) < 10 else 0.0
        p.setBrush(QColor(255, 115, 153))
        nose_path = QPainterPath()
        nose_path.moveTo(px + 11, py + 7.5 + hb_y + nose_twitch)
        nose_path.lineTo(px + 14, py + 7.5 + hb_y + nose_twitch)
        nose_path.lineTo(px + 12.5, py + 5.5 + hb_y)
        nose_path.closeSubpath()
        p.drawPath(nose_path)

        # Whiskers
        p.setPen(QPen(QColor(128, 115, 115, 178), 0.9))
        p.drawLine(QPointF(px + 13, py + 6.5 + hb_y), QPointF(px + 21, py + 8.5 + hb_y))
        p.drawLine(QPointF(px + 13, py + 5.5 + hb_y), QPointF(px + 20, py + 3.5 + hb_y))

    def _draw_platypus(self, p: QPainter, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        tail_bob = math.sin(tick * 0.16) * 3.5
        p.setPen(Qt.PenStyle.NoPen)
        # Tail bobbing in slipstream
        tail_path = QPainterPath()
        tail_path.moveTo(px - 36, py - 4 + tail_bob * 0.3)
        tail_path.lineTo(px - 58, py + 4 + tail_bob)
        tail_path.lineTo(px - 62, py - 6 + tail_bob)
        tail_path.lineTo(px - 38, py - 12 + tail_bob * 0.3)
        tail_path.closeSubpath()
        p.setBrush(QColor(107, 66, 41))
        p.drawPath(tail_path)

        # Head / Body
        p.setBrush(QColor(38, 166, 158))
        p.drawEllipse(QRectF(px - 10, py + 2 + hb_y, 23, 19))

        # Flat bill
        p.setBrush(QColor(245, 133, 31))
        p.drawRoundedRect(QRectF(px + 4, py + 3 + hb_y, 19, 8), 3.0, 3.0)

        # Eye with blinking
        if self.is_eye_blinking(tick):
            eye_arc = QPainterPath()
            eye_arc.moveTo(px + 2.0, py + 13.0 + hb_y)
            eye_arc.quadTo(px + 5.0, py + 15.5 + hb_y, px + 8.0, py + 13.0 + hb_y)
            p.setPen(QPen(QColor(0, 0, 0), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(eye_arc)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(0, 0, 0))
            p.drawEllipse(QRectF(px + 3, py + 11 + hb_y, 4.5, 4.5))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(px + 4.5, py + 12.5 + hb_y, 1.5, 1.5))

    def _draw_squirrel(self, p: QPainter, px: float, py: float, tick: int) -> None:
        hb_y = math.sin(tick * 0.14) * 1.2
        tail_wave = math.sin(tick * 0.18) * 3.8
        tail_path = QPainterPath()
        tail_path.moveTo(px - 34, py - 4)
        tail_path.cubicTo(px - 48, py + 8 + tail_wave * 0.5, px - 56, py + 22 + tail_wave, px - 44, py + 26 + tail_wave)
        tail_path.cubicTo(px - 36, py + 24 + tail_wave, px - 30, py + 12, px - 26, py + 4)
        tail_path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(199, 107, 56))
        p.drawPath(tail_path)

        # Head
        p.setBrush(QColor(209, 117, 64))
        p.drawEllipse(QRectF(px - 9, py + 2 + hb_y, 21, 19))

        # Cheeks
        p.setBrush(QColor(250, 242, 230))
        p.drawEllipse(QRectF(px + 1, py + 3 + hb_y, 10, 8))

        # Muzzle
        p.setBrush(QColor(64, 38, 31))
        p.drawEllipse(QRectF(px + 10, py + 6 + hb_y, 3.5, 3.5))

        # Eye with blinking
        if self.is_eye_blinking(tick):
            eye_arc = QPainterPath()
            eye_arc.moveTo(px + 1.0, py + 12.0 + hb_y)
            eye_arc.quadTo(px + 4.0, py + 14.5 + hb_y, px + 7.0, py + 12.0 + hb_y)
            p.setPen(QPen(QColor(0, 0, 0), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(eye_arc)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(0, 0, 0))
            p.drawEllipse(QRectF(px + 2, py + 10 + hb_y, 4.5, 5.0))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(px + 3.5, py + 12 + hb_y, 1.8, 1.8))

    def _draw_outfit(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.setPen(Qt.PenStyle.NoPen)
        if self.outfit == "student":
            # 🎓 Mortarboard
            p.setBrush(QColor(38, 41, 56))
            cap_path = QPainterPath()
            cap_path.moveTo(px - 14, py + 19)
            cap_path.lineTo(px + 3, py + 26)
            cap_path.lineTo(px + 18, py + 19)
            cap_path.lineTo(px + 1, py + 14)
            cap_path.closeSubpath()
            p.drawPath(cap_path)

            # Tassel
            tassel_sway = math.sin(tick * 0.20) * 3.0
            p.setPen(QPen(QColor(250, 217, 89), 1.4))
            p.drawLine(QPointF(px + 2, py + 22), QPointF(px - 12 + tassel_sway, py + 10))

            # Spectacles
            p.setPen(QPen(QColor(242, 204, 51), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(px + 1, py + 8, 7.5, 7.5))

        elif self.outfit == "chef":
            # 👨‍🍳 Toque
            p.setPen(QPen(QColor(204, 209, 224), 1.0))
            p.setBrush(QColor(255, 255, 255))
            toque_path = QPainterPath()
            toque_path.moveTo(px - 8, py + 16)
            toque_path.lineTo(px - 10, py + 27)
            toque_path.cubicTo(px - 4, py + 34, px + 6, py + 34, px + 10, py + 28)
            toque_path.lineTo(px + 8, py + 16)
            toque_path.closeSubpath()
            p.drawPath(toque_path)

        elif self.outfit == "captain":
            # 🧑‍✈️ Captain Hat
            p.setBrush(QColor(31, 41, 71))
            p.drawEllipse(QRectF(px - 8, py + 16, 20, 8))
            p.setBrush(QColor(0, 0, 0))
            p.drawEllipse(QRectF(px + 2, py + 14, 12, 4))
            p.setBrush(QColor(245, 204, 64))
            p.drawEllipse(QRectF(px + 2, py + 19, 4, 4))

        elif self.outfit == "agent":
            # 🕵️ Fedora
            p.setBrush(QColor(122, 71, 38))
            p.drawEllipse(QRectF(px - 14, py + 16, 28, 6))
            crown_path = QPainterPath()
            crown_path.moveTo(px - 7, py + 18)
            crown_path.lineTo(px - 5, py + 28)
            crown_path.lineTo(px + 5, py + 29)
            crown_path.lineTo(px + 7, py + 18)
            crown_path.closeSubpath()
            p.drawPath(crown_path)
            p.setBrush(QColor(38, 38, 46))
            p.drawRect(QRectF(px - 6.5, py + 18, 13, 3))

        elif self.outfit == "gym":
            p.setBrush(QColor(235, 64, 64))
            p.drawRoundedRect(QRectF(px - 8, py + 14, 18, 5), 2.0, 2.0)
            p.setBrush(QColor(255, 255, 255))
            p.drawRect(QRectF(px - 7, py + 15.5, 16, 1.5))

        elif self.outfit == "racer":
            p.setBrush(QColor(250, 115, 38))
            p.drawEllipse(QRectF(px - 8, py + 12, 19, 14))
            p.setBrush(QColor(38, 46, 64, 217))
            p.drawEllipse(QRectF(px + 2, py + 13, 10, 8))

        elif self.outfit == "zen":
            p.setBrush(QColor(255, 140, 191))
            p.drawEllipse(QRectF(px - 6, py + 16, 8, 8))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(QRectF(px - 4, py + 18, 4, 4))
            p.setBrush(QColor(255, 217, 51))
            p.drawEllipse(QRectF(px - 3, py + 19, 2, 2))

        else:
            p.setBrush(QColor(89, 64, 46))
            p.drawRect(QRectF(px - 8, py + 13, 18, 3))
            p.setPen(QPen(QColor(230, 191, 89), 1.6))
            p.setBrush(QColor(140, 224, 250, 191))
            p.drawEllipse(QRectF(px, py + 9, 10, 10))
