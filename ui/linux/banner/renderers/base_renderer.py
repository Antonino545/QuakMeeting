"""
Base Pilot Renderer interface for QuakMeeting Qt Banner.
Defines abstract drawing hooks for vehicle and character rendering using PyQt6 QPainter.
"""
from __future__ import annotations
from ui.linux.theme import Theme
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

    def _c(self, r: int, g: int, b: int, a: int = 255) -> QColor:
        return QColor(r, g, b, a)

    def draw_propeller(self, p: QPainter, nx: float, ny: float, tick: int) -> None:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(Theme.get_color('TEXT', 64))
        p.drawEllipse(QRectF(nx - 4, ny - 18, 8, 36))
        angle = tick * 0.70
        dx = math.cos(angle) * 3.5
        dy = math.sin(angle) * 18.0
        pen = QPen(Theme.get_color('ROSEWATER', 230), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(nx + dx, ny - dy), QPointF(nx - dx, ny + dy))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(Theme.SURFACE1)
        p.drawEllipse(QRectF(nx - 3.5, ny - 4.5, 9, 9))
        p.setBrush(Theme.get_color('ROSEWATER', 200))
        p.drawEllipse(QRectF(nx - 1, ny - 1.5, 3, 3))

    @abstractmethod
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        """Draw vehicle and character at pilot origin (px, py)."""
        pass
