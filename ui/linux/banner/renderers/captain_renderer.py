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


class QtCaptainRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        tail = QPainterPath()
        tail.moveTo(px - 38, py)
        tail.lineTo(px - 66, py + 28)
        tail.lineTo(px - 48, py)
        tail.closeSubpath()
        p.setBrush(self._c(26, 56, 122))
        p.drawPath(tail)

        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 48, py - 12, 88, 26))
        p.setPen(QPen(self._c(51, 77, 115), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 48, py - 12, 88, 26))
        p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(self._c(31, 82, 166))
        p.drawRect(QRectF(px - 36, py - 2, 62, 4))
        p.setBrush(self._c(217, 240, 255))
        for i in range(5):
            p.drawEllipse(QRectF(px - 28 + i * 8, py - 1, 4.5, 3.5))

        p.setBrush(self._c(31, 46, 82, 242))
        p.drawEllipse(QRectF(px + 20, py + 2, 17, 9))
        p.setBrush(self._c(255, 209, 61))
        p.drawEllipse(QRectF(px - 4, py + 2, 18, 18))
        p.setBrush(self._c(26, 31, 46, 242))
        p.drawEllipse(QRectF(px + 3, py + 7, 7, 6))
        p.setPen(QPen(self._c(255, 217, 64), 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px + 3, py + 7, 7, 6))
        p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(self._c(26, 38, 89))
        p.drawRect(QRectF(px - 3, py + 14, 18, 6))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 4, py + 16, 20, 7))
        p.setBrush(self._c(250, 217, 64))
        p.drawEllipse(QRectF(px + 2, py + 15, 6, 5))

        wing = QPainterPath()
        wing.moveTo(px - 14, py - 2)
        wing.lineTo(px + 18, py - 2)
        wing.lineTo(px + 4, py - 26)
        wing.lineTo(px - 8, py - 26)
        wing.closeSubpath()
        p.setBrush(self._c(209, 222, 242))
        p.drawPath(wing)

        p.setBrush(self._c(71, 82, 107))
        p.drawRoundedRect(QRectF(px - 4, py - 22, 20, 9), 3.5, 3.5)
        p.setBrush(self._c(166, 191, 230))
        p.drawEllipse(QRectF(px + 12, py - 21, 3.5, 7))

        self.draw_propeller(p, px + 42.0, py + 2.0, tick)
