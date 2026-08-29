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


class QtDuckRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Red tail fin & white decoration
        tail = QPainterPath()
        tail.moveTo(px - 30, py - 2)
        tail.lineTo(px - 56, py + 24)
        tail.lineTo(px - 42, py - 2)
        tail.closeSubpath()
        p.setBrush(c(0.90, 0.22, 0.20))
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

        # 2. Cream vintage biplane fuselage
        p.setBrush(c(0.98, 0.94, 0.82))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))

        # Bottom shade
        p.setBrush(c(0.88, 0.78, 0.62, 0.60))
        p.drawEllipse(QRectF(px - 42, py - 15, 72, 16))

        # Dynamic red racing stripe
        stripe = QPainterPath()
        stripe.moveTo(px - 38, py - 2)
        stripe.lineTo(px + 24, py - 2)
        stripe.lineTo(px + 22, py - 6)
        stripe.lineTo(px - 36, py - 6)
        stripe.closeSubpath()
        p.setBrush(c(0.88, 0.20, 0.18))
        p.drawPath(stripe)

        # Fuselage rim stroke
        p.setPen(QPen(c(0.35, 0.25, 0.15, 0.85), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setPen(Qt.PenStyle.NoPen)

        # 3. Cockpit & Curved Glass Windshield
        p.setBrush(c(0.15, 0.18, 0.25))
        p.drawEllipse(QRectF(px - 14, py, 26, 16))

        glass = QPainterPath()
        glass.moveTo(px + 10, py + 1)
        glass.cubicTo(px + 8, py + 12, px + 2, py + 16, px - 2, py + 17)
        glass.lineTo(px - 8, py + 1)
        glass.closeSubpath()
        p.setBrush(c(0.65, 0.88, 0.98, 0.75))
        p.drawPath(glass)
        p.setPen(QPen(QColor(255, 255, 255, 230), 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(glass)

        # Windshield specular glare line
        p.setPen(QPen(QColor(255, 255, 255, 230), 1.5))
        p.drawLine(QPointF(px + 5, py + 5), QPointF(px + 1, py + 14))
        p.setPen(Qt.PenStyle.NoPen)

        # 4. Animated Red Flying Scarf
        scarf_wave1 = math.sin(tick * 0.28) * 5.0
        scarf_wave2 = math.sin(tick * 0.28 + 1.2) * 6.5

        scarf = QPainterPath()
        scarf.moveTo(px - 8, py + 5)
        scarf.cubicTo(px - 15, py + 4 + scarf_wave1 * 0.5, px - 22, py + 10 + scarf_wave1, px - 28, py + 7 + scarf_wave1)
        scarf.cubicTo(px - 34, py + 5 + scarf_wave1, px - 40, py + 8 + scarf_wave2, px - 46, py + 4 + scarf_wave2)
        scarf.lineTo(px - 45, py - 1 + scarf_wave2)
        scarf.cubicTo(px - 38, py + 3 + scarf_wave2, px - 32, py + scarf_wave1, px - 26, py + 2 + scarf_wave1)
        scarf.closeSubpath()
        p.setBrush(c(0.92, 0.18, 0.18))
        p.drawPath(scarf)

        # Golden scarf fringe
        p.setPen(QPen(c(1.0, 0.85, 0.25), 1.6))
        p.drawLine(QPointF(px - 46, py + 4 + scarf_wave2), QPointF(px - 49, py + 3 + scarf_wave2))
        p.drawLine(QPointF(px - 45, py + 1.5 + scarf_wave2), QPointF(px - 48, py + 0.5 + scarf_wave2))
        p.setPen(Qt.PenStyle.NoPen)

        # Neck knot
        p.setBrush(c(0.85, 0.15, 0.15))
        p.drawEllipse(QRectF(px - 9, py + 2, 11, 7))

        # 5. Duck Head with warm highlights & rosy cheek
        p.setBrush(c(0.92, 0.65, 0.15))
        p.drawEllipse(QRectF(px - 7, py + 2, 19, 18))
        p.setBrush(c(1.0, 0.82, 0.24))
        p.drawEllipse(QRectF(px - 8, py + 3, 20, 20))
        p.setBrush(c(1.0, 0.92, 0.50, 0.70))
        p.drawEllipse(QRectF(px - 5, py + 9, 14, 13))

        # Rosy Cheek
        p.setBrush(c(1.0, 0.42, 0.42, 0.45))
        p.drawEllipse(QRectF(px - 3, py + 5, 7, 5))

        # 6. Eye with double catchlight
        p.setBrush(c(0.10, 0.10, 0.12))
        p.drawEllipse(QRectF(px + 2.5, py + 12, 5.0, 5.5))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px + 4.2, py + 14.2, 2.2, 2.2))
        p.drawEllipse(QRectF(px + 3.2, py + 12.8, 1.0, 1.0))

        # 7. 3D Beak with smile
        beak = QPainterPath()
        beak.moveTo(px + 5, py + 12)
        beak.cubicTo(px + 10, py + 13, px + 15, py + 12, px + 18, py + 9.5)
        beak.cubicTo(px + 15, py + 7, px + 10, py + 6, px + 5, py + 5.5)
        beak.closeSubpath()
        p.setBrush(c(1.0, 0.48, 0.02))
        p.drawPath(beak)

        # Beak lip reflection
        p.setPen(QPen(c(1.0, 0.72, 0.25, 0.85), 1.2))
        p.drawLine(QPointF(px + 7, py + 11), QPointF(px + 14, py + 9.5))
        p.setPen(Qt.PenStyle.NoPen)

        # Nostril
        p.setBrush(c(0.75, 0.30, 0.0))
        p.drawEllipse(QRectF(px + 8, py + 10.5, 1.5, 1.2))

        # 8. Leather Aviator Cap & Gold Goggles
        cap = QPainterPath()
        cap.moveTo(px - 8, py + 12)
        cap.cubicTo(px - 6, py + 23, px + 2, py + 24, px + 6, py + 22)
        cap.lineTo(px + 6, py + 18)
        cap.cubicTo(px, py + 18, px - 5, py + 14, px - 8, py + 12)
        cap.closeSubpath()
        p.setBrush(c(0.38, 0.22, 0.12))
        p.drawPath(cap)

        # Strap
        p.setBrush(c(0.25, 0.15, 0.08))
        p.drawRect(QRectF(px - 8, py + 12.5, 18, 3.5))

        # Gold goggle frame
        p.setPen(QPen(c(0.92, 0.78, 0.25), 2.4))
        p.setBrush(c(0.50, 0.85, 0.98, 0.85))
        p.drawEllipse(QRectF(px - 1.5, py + 10, 12, 11))

        # Lens glare
        p.setPen(QPen(QColor(255, 255, 255, 217), 1.4))
        p.drawLine(QPointF(px + 3, py + 18), QPointF(px + 7, py + 13))
        p.setPen(Qt.PenStyle.NoPen)

        # 9. Wings & Propeller
        wing = QPainterPath()
        wing.moveTo(px - 18, py - 2)
        wing.lineTo(px + 18, py - 2)
        wing.lineTo(px + 8, py - 24)
        wing.lineTo(px - 12, py - 24)
        wing.closeSubpath()
        p.setBrush(c(0.90, 0.22, 0.20))
        p.drawPath(wing)
        p.setPen(QPen(Qt.GlobalColor.white, 2.0))
        p.drawLine(QPointF(px - 12, py - 24), QPointF(px + 8, py - 24))
        p.setPen(Qt.PenStyle.NoPen)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)

