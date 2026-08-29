"""
Hyper Squirrel Pilot Renderer for QuakMeeting (Linux PyQt6 QPainter).
Features chestnut squirrel with dynamic bushy tail wave, white chest fluff, acorn-shell pilot helmet with stem, and golden goggles.
"""
from __future__ import annotations
import math

try:
    from PyQt6.QtCore import Qt, QRectF, QPointF
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
except (ImportError, ModuleNotFoundError):
    Qt = object
    QRectF = object
    QPointF = object
    QPainter = object
    QColor = object
    QPen = object
    QBrush = object
    QPainterPath = object

from .base_renderer import BaseQtPilotRenderer

class QtSquirrelRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. 🐿️ Coda Voluminosa e Ondulante (Dynamic Bushy Tail)
        tail_wave = math.sin(tick * 0.18) * 3.0
        tail_path = QPainterPath()
        tail_path.moveTo(px - 28, py - 4)
        tail_path.cubicTo(
            px - 44, py + 4,
            px - 66, py + 14 + tail_wave,
            px - 58, py + 26 + tail_wave
        )
        tail_path.cubicTo(
            px - 50, py + 34 + tail_wave,
            px - 38, py + 24 + tail_wave,
            px - 36, py + 14 + tail_wave * 0.5
        )
        tail_path.lineTo(px - 26, py - 6)
        tail_path.closeSubpath()

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(209, 107, 51))
        p.drawPath(tail_path)

        # Highlight inner tail
        tail_inner = QPainterPath()
        tail_inner.moveTo(px - 32, py)
        tail_inner.cubicTo(
            px - 42, py + 8,
            px - 58, py + 16 + tail_wave,
            px - 50, py + 22 + tail_wave
        )
        p.setPen(QPen(QColor(242, 166, 97, 204), 2.4))
        p.drawPath(tail_inner)

        # 2. Fusoliera Ghianda / Legno Vintage
        p.setPen(QPen(QColor(76, 38, 20), 1.4))
        p.setBrush(QColor(148, 89, 51))
        p.drawEllipse(QRectF(px - 38, py - 12, 72, 26))

        # Bottom shade
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(107, 56, 30, 178))
        p.drawEllipse(QRectF(px - 36, py - 14, 68, 14))

        # Stripe
        stripe_path = QPainterPath()
        stripe_path.moveTo(px - 32, py - 3)
        stripe_path.lineTo(px + 22, py - 3)
        stripe_path.lineTo(px + 20, py - 6)
        stripe_path.lineTo(px - 30, py - 6)
        stripe_path.closeSubpath()
        p.setBrush(QColor(245, 158, 38))
        p.drawPath(stripe_path)

        # 3. Cockpit
        p.setBrush(QColor(51, 30, 20))
        p.drawEllipse(QRectF(px - 14, py - 1, 28, 18))

        # 4. Testa e Guance (Chestnut Face & White Chest)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(217, 115, 56))
        p.drawEllipse(QRectF(px - 10, py + 2, 22, 20))

        # Guance panna
        p.setBrush(QColor(250, 240, 224))
        p.drawEllipse(QRectF(px - 2, py + 3, 14, 12))

        # Orecchie
        ear_path = QPainterPath()
        ear_path.moveTo(px - 8, py + 18)
        ear_path.lineTo(px - 12, py + 26)
        ear_path.lineTo(px - 4, py + 20)
        ear_path.closeSubpath()
        p.setBrush(QColor(199, 97, 46))
        p.drawPath(ear_path)

        # Occhio nero & riflesso
        p.setBrush(QColor(0, 0, 0))
        p.drawEllipse(QRectF(px + 4, py + 10, 5.0, 5.0))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(QRectF(px + 5.5, py + 12, 1.8, 1.8))

        # Nasino
        p.setBrush(QColor(51, 25, 20))
        p.drawEllipse(QRectF(px + 10, py + 6.5, 3.2, 2.5))

        # 5. 🌰 CASCHETTO GHIANDA (Acorn Shell Helmet)
        p.setPen(QPen(QColor(76, 46, 20), 1.2))
        p.setBrush(QColor(115, 71, 36))
        p.drawEllipse(QRectF(px - 9, py + 14, 20, 14))

        # Stem
        stem_path = QPainterPath()
        stem_path.moveTo(px + 1, py + 26)
        stem_path.lineTo(px + 3, py + 32)
        stem_path.lineTo(px + 5, py + 31)
        stem_path.lineTo(px + 3, py + 26)
        stem_path.closeSubpath()
        p.setBrush(QColor(76, 46, 20))
        p.drawPath(stem_path)

        # Goggles
        p.setPen(QPen(QColor(235, 191, 64), 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(px + 1, py + 9, 10, 10))

        # 6. Ala
        wing_path = QPainterPath()
        wing_path.moveTo(px - 14, py - 4)
        wing_path.lineTo(px + 14, py - 4)
        wing_path.lineTo(px + 2, py - 26)
        wing_path.lineTo(px - 14, py - 26)
        wing_path.closeSubpath()
        p.setPen(QPen(QColor(245, 158, 38, 217), 1.2))
        p.setBrush(QColor(199, 102, 46))
        p.drawPath(wing_path)

        # 7. Elica
        self.draw_propeller(p, px + 34, py + 1, tick)
        p.restore()
