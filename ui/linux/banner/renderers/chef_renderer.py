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


class QtChefRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Coral & Cream Fuselage
        p.setBrush(c(1.0, 0.58, 0.48))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setPen(QPen(c(0.4, 0.2, 0.15, 0.85), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setPen(Qt.PenStyle.NoPen)

        # 2. Duck Head with Blush
        p.setBrush(c(1.0, 0.82, 0.24))
        p.drawEllipse(QRectF(px - 8, py + 2, 19, 19))

        # Rosy Cheek
        p.setBrush(c(1.0, 0.42, 0.42, 0.45))
        p.drawEllipse(QRectF(px - 3, py + 4, 7, 5))

        # Smiling Eye
        p.setBrush(c(0.10, 0.10, 0.12))
        p.drawEllipse(QRectF(px + 2, py + 10.5, 4.5, 5.0))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px + 3.8, py + 12.5, 2.0, 2.0))

        # 3D Beak
        beak = QPainterPath()
        beak.moveTo(px + 4, py + 11)
        beak.cubicTo(px + 9, py + 12, px + 14, py + 11, px + 17, py + 8.5)
        beak.cubicTo(px + 14, py + 6, px + 9, py + 5.5, px + 4, py + 5.0)
        beak.closeSubpath()
        p.setBrush(c(1.0, 0.48, 0.02))
        p.drawPath(beak)

        # Beak nostril
        p.setBrush(c(0.68, 0.25, 0.01, 0.85))
        p.drawEllipse(QRectF(px + 7.5, py + 9.5, 1.4, 1.1))

        # 3. Red Bandana with Polka Dots
        p.setBrush(c(0.92, 0.18, 0.18))
        p.drawEllipse(QRectF(px - 6, py - 2, 14, 8))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 3, py, 2.2, 2.2))
        p.drawEllipse(QRectF(px + 3, py, 2.2, 2.2))

        # Fluttering Bandana Tail
        b_wave = math.sin(tick * 0.3) * 4.0
        bt = QPainterPath()
        bt.moveTo(px - 6, py + 1)
        bt.lineTo(px - 20, py + 2 + b_wave)
        bt.lineTo(px - 6, py - 3)
        bt.closeSubpath()
        p.setBrush(c(0.92, 0.18, 0.18))
        p.drawPath(bt)

        # 4. Toque Blanche (Chef Hat)
        p.setBrush(Qt.GlobalColor.white)
        p.drawRoundedRect(QRectF(px - 6, py + 14, 16, 6), 2, 2)
        p.drawEllipse(QRectF(px - 12, py + 17, 14, 15))
        p.drawEllipse(QRectF(px - 3, py + 19, 15, 16))
        p.drawEllipse(QRectF(px + 4, py + 16, 12, 14))

        # Hat folds
        p.setPen(QPen(c(0.82, 0.85, 0.92), 1.3))
        p.drawLine(QPointF(px - 4, py + 17), QPointF(px - 4, py + 30))
        p.drawLine(QPointF(px + 4, py + 17), QPointF(px + 4, py + 30))
        p.setPen(Qt.PenStyle.NoPen)

        # 5. Silver Tray & Steaming Pizza
        p.setBrush(c(0.88, 0.92, 0.98))
        p.drawEllipse(QRectF(px - 30, py - 20, 26, 8))

        pizza = QPainterPath()
        pizza.moveTo(px - 28, py - 18)
        pizza.lineTo(px - 9, py - 14)
        pizza.lineTo(px - 15, py - 7)
        pizza.closeSubpath()
        p.setBrush(c(1.0, 0.82, 0.20))
        p.drawPath(pizza)

        # Pepperoni
        p.setBrush(c(0.90, 0.20, 0.15))
        p.drawEllipse(QRectF(px - 21, py - 15, 4.5, 4.5))
        p.drawEllipse(QRectF(px - 14, py - 13, 3.5, 3.5))

        # Animated Steam
        steam_y = math.sin(tick * 0.15) * 3.0
        p.setPen(QPen(c(0.95, 0.95, 1.0, 0.65), 1.4))
        steam = QPainterPath()
        steam.moveTo(px - 17, py - 5)
        steam.cubicTo(px - 22, py + steam_y * 0.5, px - 10, py + 3 + steam_y, px - 14, py + 6 + steam_y)
        p.drawPath(steam)
        p.setPen(Qt.PenStyle.NoPen)

        # 6. Wing & Propeller
        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(c(0.96, 0.42, 0.35))
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
