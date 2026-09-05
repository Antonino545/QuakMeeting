"""
Base Pilot Renderer interface for QuakMeeting Qt Banner.
Defines abstract drawing hooks for vehicle and character rendering using PyQt6 QPainter.
"""
from __future__ import annotations
import math
from abc import ABC, abstractmethod

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


class BaseQtPilotRenderer(ABC):
    """Abstract base class for all vehicle & pilot drawing strategies in PyQt6."""

    @staticmethod
    def _c(r: float, g: float, b: float, a: float = 1.0) -> QColor:
        return QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))

    @staticmethod
    def is_eye_blinking(tick: int) -> bool:
        """Returns True if the pilot character is momentarily blinking shut (natural blink cycle)."""
        return (tick % 130) >= 124

    def draw_propeller(self, p: QPainter, nx: float, ny: float, tick: int) -> None:
        """Draw high-RPM rotating propeller with motion blur disc, cross-blades, and tip trails."""
        # 1. Motion blur disc
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(224, 240, 255, 75))
        p.drawEllipse(QRectF(nx - 4.5, ny - 20, 9, 40))
        p.setBrush(QColor(255, 245, 200, 35))
        p.drawEllipse(QRectF(nx - 3.5, ny - 16, 7, 32))

        # 2. Dual rotating cross-blades (high-RPM 4-blade feel)
        prop_angle = tick * 0.85
        prop_len = 19.0

        # Primary blade
        dx1 = math.cos(prop_angle) * 3.5
        dy1 = math.sin(prop_angle) * prop_len
        p.setPen(QPen(QColor(240, 246, 255, 230), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(nx + dx1, ny - dy1), QPointF(nx - dx1, ny + dy1))

        # Secondary cross-blade (motion phase trail)
        dx2 = math.cos(prop_angle + 1.5708) * 3.5
        dy2 = math.sin(prop_angle + 1.5708) * (prop_len * 0.92)
        p.setPen(QPen(QColor(220, 235, 255, 140), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(nx + dx2, ny - dy2), QPointF(nx - dx2, ny + dy2))

        # Yellow blade tip highlights (spinning safety markers)
        p.setPen(QPen(QColor(255, 215, 60, 220), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPoint(QPointF(nx + dx1 * 0.95, ny - dy1 * 0.95))
        p.drawPoint(QPointF(nx - dx1 * 0.95, ny + dy1 * 0.95))

        # 3. Chrome ogive nose cone with dynamic specular shine
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(48, 56, 74))
        p.drawEllipse(QRectF(nx - 3.5, ny - 4.5, 9, 9))
        cone_glare_x = nx - 1.0 + math.cos(tick * 0.1) * 0.5
        cone_glare_y = ny - 1.5 + math.sin(tick * 0.1) * 0.5
        p.setBrush(QColor(255, 255, 255, 220))
        p.drawEllipse(QRectF(cone_glare_x, cone_glare_y, 3, 3))

    def draw_wingtip_strobe(self, p: QPainter, wx: float, wy: float, tick: int) -> None:
        """Draw aircraft navigation wingtip strobe beacon with authentic pulsing flash."""
        is_flash = (tick % 45) < 6
        p.setPen(Qt.PenStyle.NoPen)
        if is_flash:
            # Intense emerald beacon flash with soft halo bloom
            p.setBrush(QColor(90, 255, 140, 60))
            p.drawEllipse(QRectF(wx - 5.0, wy - 5.0, 10.0, 10.0))
            p.setBrush(QColor(160, 255, 190, 240))
            p.drawEllipse(QRectF(wx - 2.5, wy - 2.5, 5.0, 5.0))
            p.setBrush(QColor(255, 255, 255, 255))
            p.drawEllipse(QRectF(wx - 1.0, wy - 1.0, 2.0, 2.0))
        else:
            # Idle translucent navigation lamp bulb
            p.setBrush(QColor(40, 160, 90, 140))
            p.drawEllipse(QRectF(wx - 2.0, wy - 2.0, 4.0, 4.0))

    @abstractmethod
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        """Draw vehicle and character at pilot origin (px, py)."""
        pass
