from __future__ import annotations

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QPen, QPainterPath
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QPen = object
    QPainterPath = object

from .base_renderer import BaseQtPilotRenderer


class QtZenDuckRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.setBrush(self._c(107, 224, 214))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setBrush(self._c(255, 214, 82))
        p.drawEllipse(QRectF(px - 8, py + 2, 19, 19))
        p.setBrush(self._c(255, 128, 153, 128))
        p.drawEllipse(QRectF(px - 3, py + 4, 7, 5))

        pen = QPen(self._c(64, 51, 46), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        eye = QPainterPath()
        eye.moveTo(px + 1, py + 10.5)
        eye.cubicTo(px + 3, py + 13, px + 5.5, py + 13, px + 7.5, py + 10.5)
        p.drawPath(eye)
        p.setPen(Qt.PenStyle.NoPen)

        beak = QPainterPath()
        beak.moveTo(px + 4, py + 11)
        beak.lineTo(px + 15, py + 8.5)
        beak.lineTo(px + 4, py + 5.5)
        beak.closeSubpath()
        p.setBrush(self._c(255, 133, 26))
        p.drawPath(beak)

        # Lotus 🌸
        p.setBrush(self._c(255, 158, 199))
        p.drawEllipse(QRectF(px - 10, py + 14, 7, 7))
        p.drawEllipse(QRectF(px - 5, py + 18, 7, 7))
        p.drawEllipse(QRectF(px, py + 14, 7, 7))
        p.setBrush(self._c(255, 230, 77))
        p.drawEllipse(QRectF(px - 5, py + 14, 5, 5))

        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(self._c(158, 240, 230))
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
