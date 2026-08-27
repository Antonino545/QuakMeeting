from __future__ import annotations
import math

try:
    from PyQt6.QtCore import Qt, QRectF, QPointF
    from PyQt6.QtGui import QPainter, QPen, QPainterPath
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPointF = object
    QPainter = object
    QPen = object
    QPainterPath = object

from .base_renderer import BaseQtPilotRenderer


class QtDuckRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        # Tail fin red
        tail = QPainterPath()
        tail.moveTo(px - 30, py - 2)
        tail.lineTo(px - 56, py + 24)
        tail.lineTo(px - 42, py - 2)
        tail.closeSubpath()
        p.setBrush(self._c(230, 56, 51))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(tail)

        deco = QPainterPath()
        deco.moveTo(px - 38, py + 3)
        deco.lineTo(px - 48, py + 16)
        deco.lineTo(px - 44, py + 16)
        deco.lineTo(px - 35, py + 3)
        deco.closeSubpath()
        p.setBrush(Qt.GlobalColor.white)
        p.drawPath(deco)

        # Cream vintage fuselage
        p.setBrush(self._c(250, 240, 209))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setBrush(self._c(225, 199, 158, 153))
        p.drawEllipse(QRectF(px - 42, py - 15, 72, 16))

        stripe = QPainterPath()
        stripe.moveTo(px - 38, py - 2)
        stripe.lineTo(px + 24, py - 2)
        stripe.lineTo(px + 22, py - 6)
        stripe.lineTo(px - 36, py - 6)
        stripe.closeSubpath()
        p.setBrush(self._c(225, 51, 46))
        p.drawPath(stripe)

        p.setPen(QPen(self._c(89, 64, 38, 217), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setPen(Qt.PenStyle.NoPen)

        # Cockpit + windshield
        p.setBrush(self._c(38, 46, 64))
        p.drawEllipse(QRectF(px - 14, py, 26, 16))
        glass = QPainterPath()
        glass.moveTo(px + 10, py + 1)
        glass.cubicTo(px + 8, py + 12, px + 2, py + 16, px - 2, py + 17)
        glass.lineTo(px - 8, py + 1)
        glass.closeSubpath()
        p.setBrush(self._c(166, 225, 250, 191))
        p.drawPath(glass)
        p.setPen(QPen(self._c(255, 255, 255, 229), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(glass)
        p.setPen(Qt.PenStyle.NoPen)

        # Animated scarf
        w1 = math.sin(tick * 0.28) * 5.0
        w2 = math.sin(tick * 0.28 + 1.2) * 6.5
        scarf = QPainterPath()
        scarf.moveTo(px - 8, py + 5)
        scarf.cubicTo(px - 15, py + 4 + w1 * 0.5, px - 22, py + 10 + w1, px - 28, py + 7 + w1)
        scarf.cubicTo(px - 34, py + 5 + w1, px - 40, py + 8 + w2, px - 46, py + 4 + w2)
        scarf.lineTo(px - 45, py - 1 + w2)
        scarf.cubicTo(px - 38, py + 3 + w2, px - 32, py + w1, px - 26, py + 2 + w1)
        scarf.closeSubpath()
        p.setBrush(self._c(235, 46, 46))
        p.drawPath(scarf)
        p.setPen(QPen(self._c(255, 217, 64), 1.6))
        p.drawLine(QPointF(px - 46, py + 4 + w2), QPointF(px - 49, py + 3 + w2))
        p.drawLine(QPointF(px - 45, py + 1.5 + w2), QPointF(px - 48, py + 0.5 + w2))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(217, 38, 38))
        p.drawEllipse(QRectF(px - 9, py + 2, 11, 7))

        # Duck head + blush
        p.setBrush(self._c(235, 166, 38))
        p.drawEllipse(QRectF(px - 7, py + 2, 19, 18))
        p.setBrush(self._c(255, 209, 61))
        p.drawEllipse(QRectF(px - 8, py + 3, 20, 20))
        p.setBrush(self._c(255, 235, 128, 178))
        p.drawEllipse(QRectF(px - 5, py + 9, 14, 13))
        p.setBrush(self._c(255, 107, 107, 115))
        p.drawEllipse(QRectF(px - 3, py + 5, 7, 5))

        # Eye + catchlights
        p.setBrush(self._c(26, 26, 31))
        p.drawEllipse(QRectF(px + 2.5, py + 12, 5.0, 5.5))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px + 4.2, py + 14.2, 2.2, 2.2))
        p.drawEllipse(QRectF(px + 3.2, py + 12.8, 1.0, 1.0))

        # Beak 3D
        beak = QPainterPath()
        beak.moveTo(px + 5, py + 12)
        beak.cubicTo(px + 10, py + 13, px + 15, py + 12, px + 18, py + 9.5)
        beak.cubicTo(px + 15, py + 7, px + 10, py + 6, px + 5, py + 5.5)
        beak.closeSubpath()
        p.setBrush(self._c(255, 122, 5))
        p.drawPath(beak)
        p.setPen(QPen(self._c(255, 184, 64, 217), 1.2))
        p.drawLine(QPointF(px + 7, py + 11), QPointF(px + 14, py + 9.5))
        p.setPen(Qt.PenStyle.NoPen)

        # Leather cap
        cap = QPainterPath()
        cap.moveTo(px - 8, py + 12)
        cap.cubicTo(px - 6, py + 23, px + 2, py + 24, px + 6, py + 22)
        cap.lineTo(px + 6, py + 18)
        cap.cubicTo(px, py + 18, px - 5, py + 14, px - 8, py + 12)
        cap.closeSubpath()
        p.setBrush(self._c(97, 56, 31))
        p.drawPath(cap)
        p.setBrush(self._c(64, 38, 20))
        p.drawRect(QRectF(px - 8, py + 12.5, 18, 3.5))

        # Gold goggles
        p.setPen(QPen(self._c(235, 199, 64), 2.4))
        p.setBrush(self._c(128, 217, 250, 217))
        p.drawEllipse(QRectF(px - 1.5, py + 10, 12, 11))
        p.setPen(QPen(self._c(255, 255, 255, 217), 1.4))
        p.drawLine(QPointF(px + 3, py + 18), QPointF(px + 7, py + 13))
        p.setPen(Qt.PenStyle.NoPen)

        # Wing red with white trim
        wing = QPainterPath()
        wing.moveTo(px - 18, py - 2)
        wing.lineTo(px + 18, py - 2)
        wing.lineTo(px + 8, py - 24)
        wing.lineTo(px - 12, py - 24)
        wing.closeSubpath()
        p.setBrush(self._c(230, 56, 51))
        p.drawPath(wing)
        p.setPen(QPen(Qt.GlobalColor.white, 2.0))
        p.drawLine(QPointF(px - 12, py - 24), QPointF(px + 8, py - 24))
        p.setPen(Qt.PenStyle.NoPen)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
