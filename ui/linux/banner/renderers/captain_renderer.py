from __future__ import annotations
from ui.linux.theme import Theme

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
        p.setBrush(Theme.SURFACE1)
        p.drawPath(tail)

        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 48, py - 12, 88, 26))
        p.setPen(QPen(Theme.SURFACE1, 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 48, py - 12, 88, 26))
        p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(Theme.SURFACE2)
        p.drawRect(QRectF(px - 36, py - 2, 62, 4))
        p.setBrush(Theme.TEXT)
        for i in range(5):
            p.drawEllipse(QRectF(px - 28 + i * 8, py - 1, 4.5, 3.5))

        p.setBrush(Theme.get_color('SURFACE0', 242))
        p.drawEllipse(QRectF(px + 20, py + 2, 17, 9))
        p.setBrush(Theme.PEACH)
        p.drawEllipse(QRectF(px - 4, py + 2, 18, 18))
        p.setBrush(Theme.get_color('BASE', 242))
        p.drawEllipse(QRectF(px + 3, py + 7, 7, 6))
        p.setPen(QPen(Theme.PEACH, 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px + 3, py + 7, 7, 6))
        p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(Theme.SURFACE0)
        p.drawRect(QRectF(px - 3, py + 14, 18, 6))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 4, py + 16, 20, 7))
        p.setBrush(Theme.PEACH)
        p.drawEllipse(QRectF(px + 2, py + 15, 6, 5))

        wing = QPainterPath()
        wing.moveTo(px - 14, py - 2)
        wing.lineTo(px + 18, py - 2)
        wing.lineTo(px + 4, py - 26)
        wing.lineTo(px - 8, py - 26)
        wing.closeSubpath()
        p.setBrush(Theme.TEXT)
        p.drawPath(wing)

        p.setBrush(Theme.SURFACE2)
        p.drawRoundedRect(QRectF(px - 4, py - 22, 20, 9), 3.5, 3.5)
        p.setBrush(Theme.SUBTEXT1)
        p.drawEllipse(QRectF(px + 12, py - 21, 3.5, 7))

        self.draw_propeller(p, px + 42.0, py + 2.0, tick)
