from __future__ import annotations
from ui.linux.theme import Theme

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QPainterPath
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QPainterPath = object

from .base_renderer import BaseQtPilotRenderer


class QtGymRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.setBrush(Theme.PEACH)
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setBrush(Theme.PEACH)
        p.drawRect(QRectF(px - 40, py - 1, 68, 3.5))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 28, py - 9, 16, 16))
        p.setBrush(Theme.BASE)
        p.drawRoundedRect(QRectF(px - 26, py - 7, 2.5, 12), 1, 1)
        p.drawRect(QRectF(px - 24, py - 2, 8, 2))
        p.drawRoundedRect(QRectF(px - 16, py - 7, 2.5, 12), 1, 1)

        p.setBrush(Theme.PEACH)
        p.drawEllipse(QRectF(px - 6, py + 3, 19, 19))
        p.setBrush(Theme.RED)
        p.drawRoundedRect(QRectF(px - 7, py + 12, 21, 6), 2, 2)

        tail = QPainterPath()
        tail.moveTo(px - 7, py + 14)
        tail.lineTo(px - 15, py + 18)
        tail.lineTo(px - 14, py + 12)
        tail.closeSubpath()
        p.drawPath(tail)

        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px + 4, py + 7, 6, 6))
        p.setBrush(Qt.GlobalColor.black)
        p.drawEllipse(QRectF(px + 6, py + 8.5, 3.5, 3.5))

        beak = QPainterPath()
        beak.moveTo(px + 10, py + 5)
        beak.lineTo(px + 22, py + 4)
        beak.lineTo(px + 10, py + 10)
        beak.closeSubpath()
        p.setBrush(Theme.PEACH)
        p.drawPath(beak)

        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 8, py - 24)
        wing.lineTo(px - 8, py - 24)
        wing.closeSubpath()
        p.setBrush(Theme.RED)
        p.drawPath(wing)

        p.setBrush(Theme.PEACH)
        p.drawRect(QRectF(px - 8, py - 12, 16, 2.5))

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
