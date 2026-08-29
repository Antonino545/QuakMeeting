from __future__ import annotations

try:
    from PyQt6.QtCore import Qt, QRectF
    from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPainter = object
    QPen = object
    QPainterPath = object
    QColor = object

from .base_renderer import BaseQtPilotRenderer


class QtCaptainRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        c = self._c

        # 1. Midnight blue tail fin
        tail = QPainterPath()
        tail.moveTo(px - 38, py)
        tail.lineTo(px - 66, py + 28)
        tail.lineTo(px - 48, py)
        tail.closeSubpath()
        p.setBrush(c(0.10, 0.22, 0.48))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(tail)

        # 2. Glossy white airliner fuselage
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 48, py - 12, 88, 26))
        p.setPen(QPen(c(0.2, 0.3, 0.45), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px - 48, py - 12, 88, 26))
        p.setPen(Qt.PenStyle.NoPen)

        # 3. Metallic blue cheatline & illuminated windows
        p.setBrush(c(0.12, 0.32, 0.65))
        p.drawRect(QRectF(px - 36, py - 2, 62, 4))

        p.setBrush(c(0.85, 0.94, 1.0))
        for i in range(5):
            p.drawEllipse(QRectF(px - 28 + i * 8, py - 1, 4.5, 3.5))

        # 4. Cockpit windshield
        p.setBrush(c(0.12, 0.18, 0.32, 0.95))
        p.drawEllipse(QRectF(px + 20, py + 2, 17, 9))

        # 5. Captain Duck with sunglasses & naval cap
        p.setBrush(c(1.0, 0.82, 0.24))
        p.drawEllipse(QRectF(px - 4, py + 2, 18, 18))

        # Aviator sunglasses
        p.setBrush(c(0.10, 0.12, 0.18, 0.95))
        p.drawEllipse(QRectF(px + 3, py + 7, 7, 6))
        p.setPen(QPen(c(1.0, 0.85, 0.25), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px + 3, py + 7, 7, 6))
        p.setPen(Qt.PenStyle.NoPen)

        # Captain's naval cap with visor & gold anchor emblem
        p.setBrush(c(0.10, 0.15, 0.35))
        p.drawRect(QRectF(px - 3, py + 14, 18, 6))
        p.setBrush(Qt.GlobalColor.white)
        p.drawEllipse(QRectF(px - 4, py + 16, 20, 7))

        # Gold anchor
        p.setBrush(c(0.98, 0.85, 0.25))
        p.drawEllipse(QRectF(px + 2, py + 15, 6, 5))

        # 6. Swept airliner wing & Turbofan Jet Engine
        wing = QPainterPath()
        wing.moveTo(px - 14, py - 2)
        wing.lineTo(px + 18, py - 2)
        wing.lineTo(px + 4, py - 26)
        wing.lineTo(px - 8, py - 26)
        wing.closeSubpath()
        p.setBrush(c(0.82, 0.87, 0.95))
        p.drawPath(wing)

        # Turbofan Jet Nacelle
        p.setBrush(c(0.28, 0.32, 0.42))
        p.drawRoundedRect(QRectF(px - 4, py - 22, 20, 9), 3.5, 3.5)
        # Fan disk
        p.setBrush(c(0.65, 0.75, 0.90))
        p.drawEllipse(QRectF(px + 12, py - 21, 3.5, 7))

