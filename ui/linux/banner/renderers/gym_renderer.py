from __future__ import annotations

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QPainterPath, QColor
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QPainterPath = object
    QColor = object

from .base_renderer import BaseQtPilotRenderer


class QtGymRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Sport Athletic Fuselage (Fiery Orange / Crimson)
        p.setBrush(c(1.0, 0.34, 0.15))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))

        # Athletic Energy Racing Stripe (Neon Yellow / Gold)
        p.setBrush(c(1.0, 0.90, 0.10))
        p.drawRect(QRectF(px - 40, py - 1, 68, 3.5))

        # Dumbbell / Barbell Emblem 🏋️ on Fuselage
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 28, py - 9, 16, 16))

        # Mini Dumbbell (Bar + 2 Weights)
        p.setBrush(c(0.15, 0.15, 0.20))
        p.drawRoundedRect(QRectF(px - 26, py - 7, 2.5, 12), 1, 1)
        p.drawRect(QRectF(px - 24, py - 2, 8, 2))
        p.drawRoundedRect(QRectF(px - 16, py - 7, 2.5, 12), 1, 1)

        # 2. Duck Pilot Head (Golden Yellow)
        p.setBrush(c(1.0, 0.85, 0.18))
        p.drawEllipse(QRectF(px - 6, py + 3, 19, 19))

        # Athletic Red Sweatband / Headband
        p.setBrush(c(0.92, 0.15, 0.20))
        p.drawRoundedRect(QRectF(px - 7, py + 12, 21, 6), 2, 2)

        # Sweatband Ribbon Tails
        tail = QPainterPath()
        tail.moveTo(px - 7, py + 14)
        tail.lineTo(px - 15, py + 18)
        tail.lineTo(px - 14, py + 12)
        tail.closeSubpath()
        p.drawPath(tail)

        # Duck Eye (Workout focus)
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px + 4, py + 7, 6, 6))
        p.setBrush(Qt.GlobalColor.black)
        p.drawEllipse(QRectF(px + 6, py + 8.5, 3.5, 3.5))

        # Orange Beak (Sculpted curves & nostril)
        beak = QPainterPath()
        beak.moveTo(px + 10, py + 10)
        beak.cubicTo(px + 14, py + 10.5, px + 19, py + 8.5, px + 23, py + 6.0)
        beak.cubicTo(px + 23.5, py + 5.0, px + 23.0, py + 4.0, px + 21.5, py + 3.5)
        beak.cubicTo(px + 17, py + 3.5, px + 13, py + 4.0, px + 10, py + 4.5)
        beak.closeSubpath()
        p.setBrush(c(1.0, 0.50, 0.05))
        p.drawPath(beak)

        # Nostril
        p.setBrush(c(0.7, 0.22, 0.02, 0.85))
        p.drawEllipse(QRectF(px + 12.5, py + 8.0, 1.6, 1.1))

        # 3. Dynamic Sport Wing & Propeller
        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 8, py - 24)
        wing.lineTo(px - 8, py - 24)
        wing.closeSubpath()
        p.setBrush(c(0.90, 0.20, 0.15))
        p.drawPath(wing)

        # Wing Lightning Stripe
        p.setBrush(c(1.0, 0.92, 0.25))
        p.drawRect(QRectF(px - 8, py - 12, 16, 2.5))

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
