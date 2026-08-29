from __future__ import annotations
import math

try:
    from PyQt6.QtCore import Qt, QRectF, QPointF
    from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPointF = object
    QPainter = object
    QPen = object
    QPainterPath = object
    QColor = object

from .base_renderer import BaseQtPilotRenderer


class QtOwlRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Noble Wood & Amethyst Glider Fuselage
        p.setBrush(c(0.44, 0.28, 0.65))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))

        # 2. Wise Owl Face
        p.setBrush(c(0.70, 0.52, 0.40))
        p.drawEllipse(QRectF(px - 8, py + 2, 21, 21))

        # Feathered eye disks
        p.setBrush(c(0.96, 0.94, 0.88))
        p.drawEllipse(QRectF(px - 4, py + 7, 8.5, 8.5))
        p.drawEllipse(QRectF(px + 5.5, py + 7, 8.5, 8.5))

        # Large eyes with black pupil and catchlight
        p.setBrush(Qt.GlobalColor.black)
        p.drawEllipse(QRectF(px - 2, py + 9, 4.5, 4.5))
        p.drawEllipse(QRectF(px + 7.5, py + 9, 4.5, 4.5))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 0.8, py + 11, 1.6, 1.6))
        p.drawEllipse(QRectF(px + 8.7, py + 11, 1.6, 1.6))

        # Round gold spectacles
        p.setPen(QPen(c(1.0, 0.85, 0.25), 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 4.5, py + 6.5, 9.5, 9.5))
        p.drawEllipse(QRectF(px + 5.0, py + 6.5, 9.5, 9.5))
        p.setPen(Qt.PenStyle.NoPen)

        # Owl Beak
        beak = QPainterPath()
        beak.moveTo(px + 3, py + 9.5)
        beak.lineTo(px + 8, py + 6.5)
        beak.lineTo(px + 3, py + 3.5)
        beak.closeSubpath()
        p.setBrush(c(0.95, 0.55, 0.1))
        p.drawPath(beak)

        # 3. Mortarboard Graduation Hat
        grad = QPainterPath()
        grad.moveTo(px + 2, py + 27)
        grad.lineTo(px + 16, py + 20)
        grad.lineTo(px + 2, py + 15)
        grad.lineTo(px - 12, py + 20)
        grad.closeSubpath()
        p.setBrush(c(0.12, 0.12, 0.16))
        p.drawPath(grad)

        # Oscillating gold tassel
        tassel_wave = math.sin(tick * 0.2) * 3.0
        p.setBrush(c(1.0, 0.85, 0.2))
        p.drawEllipse(QRectF(px + 1, py + 20, 3, 3))
        p.setPen(QPen(c(1.0, 0.85, 0.2), 1.6))
        p.drawLine(QPointF(px + 2, py + 21), QPointF(px - 7 + tassel_wave, py + 13))
        p.setPen(Qt.PenStyle.NoPen)

        # 4. Graduation Scroll with red ribbon
        p.setBrush(c(0.96, 0.94, 0.85))
        p.drawRoundedRect(QRectF(px - 24, py - 19, 18, 8), 2.5, 2.5)
        p.setBrush(c(0.9, 0.18, 0.18))
        p.drawRect(QRectF(px - 16, py - 19, 3.5, 8))

        # 5. Wing & Propeller
        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(c(0.76, 0.52, 0.96))
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
