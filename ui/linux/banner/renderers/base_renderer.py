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

    def draw_propeller(self, p: QPainter, nx: float, ny: float, tick: int) -> None:
        """Draw rotating propeller with motion blur disc and chrome nose cone."""
        # 1. Motion blur disc
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(224, 240, 255, 64))
        p.drawEllipse(QRectF(nx - 4, ny - 18, 8, 36))

        # 2. Rotating blades with specular gloss
        prop_angle = tick * 0.70
        prop_len = 18.0
        dx = math.cos(prop_angle) * 3.5
        dy = math.sin(prop_angle) * prop_len

        pen = QPen(QColor(235, 242, 255, 230), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(nx + dx, ny - dy), QPointF(nx - dx, ny + dy))

        # 3. Chrome ogive nose cone with specular dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(56, 66, 89))
        p.drawEllipse(QRectF(nx - 3.5, ny - 4.5, 9, 9))
        p.setBrush(QColor(255, 255, 255, 204))
        p.drawEllipse(QRectF(nx - 1, ny - 1.5, 3, 3))

    @abstractmethod
    def draw_pilot(self, p: QPainter, px: float, py: float, tick: int) -> None:
        """Draw vehicle and character at pilot origin (px, py)."""
        pass
