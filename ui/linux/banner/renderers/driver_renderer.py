from __future__ import annotations

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QFont, QPainterPath
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QFont = object
    QPainterPath = object

from .base_renderer import BaseQtPilotRenderer


class QtDriverRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.setBrush(self._c(38, 204, 138))
        p.drawEllipse(QRectF(px - 44, py - 13, 76, 28))
        p.setBrush(Qt.GlobalColor.white)
        p.drawRect(QRectF(px - 40, py + 1, 68, 3))
        p.drawRect(QRectF(px - 40, py - 6, 68, 3))
        p.drawEllipse(QRectF(px - 28, py - 8, 15, 15))

        p.setPen(Qt.GlobalColor.black)
        f = QFont("Arial", 9)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        # Un-flip Y around the text centre so "1" appears right-side-up
        tx, ty = px - 19, py - 1  # centre of the roundel
        p.save()
        p.translate(0, 2 * ty)
        p.scale(1, -1)
        p.drawText(QRectF(px - 24, py - 7, 10, 12), Qt.AlignmentFlag.AlignCenter, "1")
        p.restore()

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._c(235, 51, 51))
        p.drawEllipse(QRectF(px - 8, py + 3, 20, 20))
        p.setBrush(self._c(20, 26, 38))
        p.drawRoundedRect(QRectF(px - 1, py + 8, 14, 9), 3.5, 3.5)
        p.setBrush(self._c(102, 230, 255, 217))
        p.drawRect(QRectF(px + 2, py + 12, 8, 2.5))

        wing = QPainterPath()
        wing.moveTo(px - 16, py - 2)
        wing.lineTo(px + 16, py - 2)
        wing.lineTo(px + 6, py - 24)
        wing.lineTo(px - 10, py - 24)
        wing.closeSubpath()
        p.setBrush(self._c(250, 217, 56))
        p.drawPath(wing)

        self.draw_propeller(p, px + 32.0, py + 2.0, tick)
