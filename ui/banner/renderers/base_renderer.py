"""
Base Pilot Renderer interface for QuakMeeting Banner.
Defines abstract drawing hooks for vehicle and character rendering.
"""
import math
import AppKit
from abc import ABC, abstractmethod

class BasePilotRenderer(ABC):
    """Abstract base class for all vehicle & pilot drawing strategies."""

    @abstractmethod
    def draw_pilot(self, px: float, py: float, tick: int) -> None:
        """Draw vehicle and character at pilot origin (px, py)."""
        pass

    def draw_propeller(self, nose_x: float, nose_y: float, tick: int) -> None:
        """Draw rotating propeller with motion blur disc and chrome nose cone."""
        # Disco di sfocatura di rotazione dell'elica
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.94, 1.0, 0.25).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 4, nose_y - 18, 8, 36)).fill()
        
        # Pale rotanti con riflesso lucido
        prop_angle = tick * 0.70
        prop_len = 18.0
        dx = math.cos(prop_angle) * 3.5
        dy = math.sin(prop_angle) * prop_len
        
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.92, 0.95, 1.0, 0.90).set()
        prop_path = AppKit.NSBezierPath.bezierPath()
        prop_path.setLineWidth_(3.2)
        prop_path.setLineCapStyle_(AppKit.NSLineCapStyleRound)
        prop_path.moveToPoint_(AppKit.NSMakePoint(nose_x + dx, nose_y - dy))
        prop_path.lineToPoint_(AppKit.NSMakePoint(nose_x - dx, nose_y + dy))
        prop_path.stroke()

        # Cono d'ogiva cromato centrale con riflesso
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.22, 0.26, 0.35, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 3.5, nose_y - 4.5, 9, 9)).fill()
        AppKit.NSColor.whiteColor().colorWithAlphaComponent_(0.8).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 1, nose_y - 1.5, 3, 3)).fill()
