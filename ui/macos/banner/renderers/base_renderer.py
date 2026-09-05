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

    @staticmethod
    def is_eye_blinking(tick: int) -> bool:
        """Returns True if the pilot character is momentarily blinking shut (natural blink cycle)."""
        return (tick % 130) >= 124

    def draw_propeller(self, nose_x: float, nose_y: float, tick: int) -> None:
        """Draw high-RPM rotating propeller with motion blur disc, cross-blades, and tip trails."""
        # Disco di sfocatura di rotazione dell'elica
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.88, 0.94, 1.0, 0.30).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 4.5, nose_y - 20, 9, 40)).fill()
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.96, 0.80, 0.15).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 3.5, nose_y - 16, 7, 32)).fill()

        # Pale rotanti ad alti RPM (4-pale composite)
        prop_angle = tick * 0.85
        prop_len = 19.0

        # Pala primaria
        dx1 = math.cos(prop_angle) * 3.5
        dy1 = math.sin(prop_angle) * prop_len
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.94, 0.96, 1.0, 0.90).set()
        prop_path1 = AppKit.NSBezierPath.bezierPath()
        prop_path1.setLineWidth_(3.2)
        prop_path1.setLineCapStyle_(AppKit.NSLineCapStyleRound)
        prop_path1.moveToPoint_(AppKit.NSMakePoint(nose_x + dx1, nose_y - dy1))
        prop_path1.lineToPoint_(AppKit.NSMakePoint(nose_x - dx1, nose_y + dy1))
        prop_path1.stroke()

        # Pala secondaria incrociata (scia di rotazione)
        dx2 = math.cos(prop_angle + 1.5708) * 3.5
        dy2 = math.sin(prop_angle + 1.5708) * (prop_len * 0.92)
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.86, 0.92, 1.0, 0.55).set()
        prop_path2 = AppKit.NSBezierPath.bezierPath()
        prop_path2.setLineWidth_(2.6)
        prop_path2.setLineCapStyle_(AppKit.NSLineCapStyleRound)
        prop_path2.moveToPoint_(AppKit.NSMakePoint(nose_x + dx2, nose_y - dy2))
        prop_path2.lineToPoint_(AppKit.NSMakePoint(nose_x - dx2, nose_y + dy2))
        prop_path2.stroke()

        # Punti punta pala dorati di sicurezza
        AppKit.NSColor.colorWithRed_green_blue_alpha_(1.0, 0.85, 0.25, 0.85).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x + dx1 * 0.95 - 1.2, nose_y - dy1 * 0.95 - 1.2, 2.4, 2.4)).fill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - dx1 * 0.95 - 1.2, nose_y + dy1 * 0.95 - 1.2, 2.4, 2.4)).fill()

        # Cono d'ogiva cromato centrale con riflesso
        AppKit.NSColor.colorWithRed_green_blue_alpha_(0.19, 0.22, 0.29, 1.0).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(nose_x - 3.5, nose_y - 4.5, 9, 9)).fill()
        cone_glare_x = nose_x - 1.0 + math.cos(tick * 0.1) * 0.5
        cone_glare_y = nose_y - 1.5 + math.sin(tick * 0.1) * 0.5
        AppKit.NSColor.whiteColor().colorWithAlphaComponent_(0.85).set()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(cone_glare_x, cone_glare_y, 3, 3)).fill()

    def draw_wingtip_strobe(self, wx: float, wy: float, tick: int) -> None:
        """Draw aircraft navigation wingtip strobe beacon with authentic pulsing flash."""
        is_flash = (tick % 45) < 6
        if is_flash:
            # Lampo strobo verde smeraldo con alone morbido
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.35, 1.0, 0.55, 0.25).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(wx - 5.0, wy - 5.0, 10.0, 10.0)).fill()
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.62, 1.0, 0.75, 0.95).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(wx - 2.5, wy - 2.5, 5.0, 5.0)).fill()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(wx - 1.0, wy - 1.0, 2.0, 2.0)).fill()
        else:
            # Bulbo di navigazione a riposo
            AppKit.NSColor.colorWithRed_green_blue_alpha_(0.15, 0.62, 0.35, 0.55).set()
            AppKit.NSBezierPath.bezierPathWithOvalInRect_(AppKit.NSMakeRect(wx - 2.0, wy - 2.0, 4.0, 4.0)).fill()
