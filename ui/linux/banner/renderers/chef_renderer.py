from __future__ import annotations
from ui.linux.theme import Theme
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


class QtChefRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.setBrush(Theme.PEACH)
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setPen(QPen(Theme.get_color('SURFACE0', 217), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(Theme.PEACH)
        p.drawEllipse(QRectF(px - 8, py + 2, 19, 19))
        p.setBrush(Theme.get_color('RED', 115))
        p.drawEllipse(QRectF(px - 3, py + 4, 7, 5))
        p.setBrush(Theme.MANTLE)
        p.drawEllipse(QRectF(px + 2, py + 10.5, 4.5, 5.0))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px + 3.8, py + 12.5, 2.0, 2.0))

        beak = QPainterPath()
        beak.moveTo(px + 4, py + 11)
        beak.cubicTo(px + 9, py + 12, px + 14, py + 11, px + 17, py + 8.5)
        beak.cubicTo(px + 14, py + 6, px + 9, py + 5.5, px + 4, py + 5.0)
        beak.closeSubpath()
        p.setBrush(Theme.PEACH)
        p.drawPath(beak)

        # Bandana
        p.setBrush(Theme.RED)
        p.drawEllipse(QRectF(px - 6, py - 2, 14, 8))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 3, py, 2.2, 2.2))
        p.drawEllipse(QRectF(px + 3, py, 2.2, 2.2))
        b_wave = math.sin(tick * 0.3) * 4.0
        bt = QPainterPath()
        bt.moveTo(px - 6, py + 1)
        bt.lineTo(px - 20, py + 2 + b_wave)
        bt.lineTo(px - 6, py - 3)
        bt.closeSubpath()
        p.setBrush(Theme.RED)
        p.drawPath(bt)

        # Toque blanche
        p.setBrush(Qt.GlobalColor.white)
        p.drawRoundedRect(QRectF(px - 6, py + 14, 16, 6), 2, 2)
        p.drawEllipse(QRectF(px - 12, py + 17, 14, 15))
        p.drawEllipse(QRectF(px - 3, py + 19, 15, 16))
        p.drawEllipse(QRectF(px + 4, py + 16, 12, 14))
        p.setPen(QPen(Theme.TEXT, 1.3))
        p.drawLine(QPointF(px - 4, py + 17), QPointF(px - 4, py + 30))
        p.drawLine(QPointF(px + 4, py + 17), QPointF(px + 4, py + 30))
        p.setPen(Qt.PenStyle.NoPen)

        # Silver tray + pizza
        p.setBrush(Theme.TEXT)
        p.drawEllipse(QRectF(px - 30, py - 20, 26, 8))
        pizza = QPainterPath()
        pizza.moveTo(px - 28, py - 18)
        pizza.lineTo(px - 9, py - 14)
        pizza.lineTo(px - 15, py - 7)
        pizza.closeSubpath()
        p.setBrush(Theme.PEACH)
        p.drawPath(pizza)
        p.setBrush(Theme.RED)
        p.drawEllipse(QRectF(px - 21, py - 15, 4.5, 4.5))
        p.drawEllipse(QRectF(px - 14, py - 13, 3.5, 3.5))

        steam_y = math.sin(tick * 0.15) * 3.0
        p.setPen(QPen(Theme.get_color('ROSEWATER', 166), 1.4))
        steam = QPainterPath()
        steam.moveTo(px - 17, py - 5)
        steam.cubicTo(px - 22, py + steam_y * 0.5, px - 10, py + 3 + steam_y, px - 14, py + 6 + steam_y)
        p.drawPath(steam)
        p.setPen(Qt.PenStyle.NoPen)

        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(Theme.RED)
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
