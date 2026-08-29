from __future__ import annotations

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QPen = object
    QPainterPath = object
    QColor = object

from .base_renderer import BaseQtPilotRenderer


class QtZenDuckRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Cloud Mint / Pastel Teal Fuselage
        p.setBrush(c(0.42, 0.88, 0.84))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))

        # 2. Duck Head & Rosy Cheek
        p.setBrush(c(1.0, 0.84, 0.32))
        p.drawEllipse(QRectF(px - 8, py + 2, 19, 19))

        p.setBrush(c(1.0, 0.50, 0.60, 0.50))
        p.drawEllipse(QRectF(px - 3, py + 4, 7, 5))

        # Serene smiling closed eye
        pen = QPen(c(0.25, 0.20, 0.18), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        eye = QPainterPath()
        eye.moveTo(px + 1, py + 10.5)
        eye.cubicTo(px + 3, py + 13, px + 5.5, py + 13, px + 7.5, py + 10.5)
        p.drawPath(eye)
        p.setPen(Qt.PenStyle.NoPen)

        # Smiling Beak
        beak = QPainterPath()
        beak.moveTo(px + 4, py + 11)
        beak.lineTo(px + 15, py + 8.5)
        beak.lineTo(px + 4, py + 5.5)
        beak.closeSubpath()
        p.setBrush(c(1.0, 0.52, 0.1))
        p.drawPath(beak)

        # 3. Pink Lotus Flower 🌸 on head
        p.setBrush(c(1.0, 0.62, 0.78))
        p.drawEllipse(QRectF(px - 10, py + 14, 7, 7))
        p.drawEllipse(QRectF(px - 5, py + 18, 7, 7))
        p.drawEllipse(QRectF(px, py + 14, 7, 7))
        p.setBrush(c(1.0, 0.90, 0.30))
        p.drawEllipse(QRectF(px - 5, py + 14, 5, 5))

        # 4. Wing & Propeller
        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(c(0.62, 0.94, 0.90))
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
