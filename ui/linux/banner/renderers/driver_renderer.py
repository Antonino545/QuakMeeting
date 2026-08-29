from __future__ import annotations

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QFont, QPainterPath, QColor
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QFont = object
    QPainterPath = object
    QColor = object

from .base_renderer import BaseQtPilotRenderer


class QtDriverRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Emerald Speedster Fuselage
        p.setBrush(c(0.15, 0.80, 0.54))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))

        # Double white racing stripes
        p.setBrush(Qt.GlobalColor.white)
        p.drawRect(QRectF(px - 40, py + 1, 68, 3))
        p.drawRect(QRectF(px - 40, py - 6, 68, 3))

        # Roundel Race Number #1
        p.drawEllipse(QRectF(px - 28, py - 8, 15, 15))

        p.setPen(Qt.GlobalColor.black)
        f = QFont("Arial", 9)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        # Un-flip Y around the text centre so "1" appears right-side-up
        ty = py - 1  # centre of the roundel
        p.save()
        p.translate(0, 2 * ty)
        p.scale(1, -1)
        p.drawText(QRectF(px - 28, py - 8, 15, 15), Qt.AlignmentFlag.AlignCenter, "1")
        p.restore()

        # 2. Racing Helmet with Iridescent Visor
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c(0.92, 0.20, 0.20))
        p.drawEllipse(QRectF(px - 8, py + 3, 20, 20))

        # Mirrored neon visor
        p.setBrush(c(0.08, 0.10, 0.15))
        p.drawRoundedRect(QRectF(px - 1, py + 8, 14, 9), 3.5, 3.5)
        p.setBrush(c(0.4, 0.9, 1.0, 0.85))
        p.drawRect(QRectF(px + 2, py + 12, 8, 2.5))

        # 3. Aerodynamic Wing & Propeller
        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(c(0.98, 0.85, 0.22))
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
