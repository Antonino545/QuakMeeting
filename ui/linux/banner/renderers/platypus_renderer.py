"""
Secret Agent Platypus Pilot Renderer for QuakMeeting (Linux PyQt6 QPainter).
Inspired by Perry the Platypus from Phineas & Ferb:
Features stealth spy glider, teal platypus body, flat beaver tail, orange duck bill, and iconic brown fedora hat.
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

class QtPlatypusRenderer(BaseQtPilotRenderer):
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Coda a Castoro (Beaver Tail with crosshatch grid)
        tail_angle = math.sin(tick * 0.12) * 2.0
        tail_path = QPainterPath()
        tail_path.moveTo(px - 30, py - 4)
        tail_path.lineTo(px - 60, py + 8 + tail_angle)
        tail_path.lineTo(px - 56, py - 12 + tail_angle)
        tail_path.lineTo(px - 30, py - 8)
        tail_path.closeSubpath()

        p.setPen(QPen(QColor(115, 64, 30, 192), 1.2))
        p.setBrush(QColor(184, 112, 61))
        p.drawPath(tail_path)

        # Grid lines
        p.setPen(QPen(QColor(115, 64, 30, 192), 1.0))
        p.drawLine(QPointF(px - 52, py + 4 + tail_angle), QPointF(px - 36, py - 8))
        p.drawLine(QPointF(px - 46, py + 6 + tail_angle), QPointF(px - 32, py - 6))
        p.drawLine(QPointF(px - 54, py - 6 + tail_angle), QPointF(px - 38, py + 6))

        # 2. Fusoliera Stealth Spy Jet (Matte Dark Slate & Cyan Neon Trim)
        p.setPen(QPen(QColor(25, 30, 40), 1.4))
        p.setBrush(QColor(46, 56, 71))
        p.drawEllipse(QRectF(px - 40, py - 12, 74, 26))

        # Cyan Neon Stripe
        stripe_path = QPainterPath()
        stripe_path.moveTo(px - 34, py - 3)
        stripe_path.lineTo(px + 22, py - 3)
        stripe_path.lineTo(px + 20, py - 6)
        stripe_path.lineTo(px - 32, py - 6)
        stripe_path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(38, 217, 209))
        p.drawPath(stripe_path)

        # 3. Cockpit Spy
        p.setBrush(QColor(30, 36, 50))
        p.drawEllipse(QRectF(px - 14, py - 1, 28, 18))

        # 4. Corpo e Testa del Platipo (Teal Perry)
        p.setPen(QPen(QColor(0, 115, 102), 1.2))
        p.setBrush(QColor(0, 166, 148))
        p.drawEllipse(QRectF(px - 10, py + 2, 22, 20))

        # 5. Becco Piatto da Ornitorinco (Wide Flat Orange Bill)
        bill_path = QPainterPath()
        bill_path.moveTo(px + 4, py + 7)
        bill_path.lineTo(px + 22, py + 5)
        bill_path.lineTo(px + 22, py + 1)
        bill_path.lineTo(px + 4, py + 2)
        bill_path.closeSubpath()
        p.setPen(QPen(QColor(178, 89, 0), 1.1))
        p.setBrush(QColor(245, 140, 13))
        p.drawPath(bill_path)

        # Narici
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(115, 56, 0))
        p.drawEllipse(QRectF(px + 14, py + 4.5, 2.2, 1.8))

        # 6. Occhi Vigili da Agente Segreto
        p.setBrush(QColor(0, 0, 0))
        p.drawEllipse(QRectF(px + 1, py + 11, 5.5, 6.5))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(QRectF(px + 3, py + 14, 2.0, 2.0))

        # 7. 🕵️‍♂️ CAPPELLO FEDORA DA AGENTE SEGRETO (Brown Fedora with Black Band)
        # Tesa
        p.setPen(QPen(QColor(76, 40, 20), 1.0))
        p.setBrush(QColor(122, 71, 38))
        p.drawEllipse(QRectF(px - 14, py + 18, 30, 6))

        # Corona
        crown_path = QPainterPath()
        crown_path.moveTo(px - 8, py + 20)
        crown_path.lineTo(px - 6, py + 31)
        crown_path.lineTo(px + 4, py + 32)
        crown_path.lineTo(px + 8, py + 30)
        crown_path.lineTo(px + 8, py + 20)
        crown_path.closeSubpath()
        p.setBrush(QColor(132, 76, 40))
        p.drawPath(crown_path)

        # Nastro nero
        band_path = QPainterPath()
        band_path.moveTo(px - 7.5, py + 20)
        band_path.lineTo(px - 7, py + 23.5)
        band_path.lineTo(px + 7.5, py + 23.5)
        band_path.lineTo(px + 8, py + 20)
        band_path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(38, 38, 46))
        p.drawPath(band_path)

        # 8. Ala Stealth
        wing_path = QPainterPath()
        wing_path.moveTo(px - 16, py - 4)
        wing_path.lineTo(px + 12, py - 4)
        wing_path.lineTo(px - 4, py - 26)
        wing_path.lineTo(px - 20, py - 26)
        wing_path.closeSubpath()
        p.setPen(QPen(QColor(38, 217, 209, 178), 1.2))
        p.setBrush(QColor(30, 38, 51))
        p.drawPath(wing_path)

        # 9. Elica
        self.draw_propeller(p, px + 34, py + 1, tick)
        p.restore()
