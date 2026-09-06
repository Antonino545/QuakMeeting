import AppKit
import objc
from ui.macos.theme import Theme


class CardView(AppKit.NSView):
    """Reusable Catppuccin Mocha Card container for macOS dashboard panels and settings."""

    def initWithFrame_bgColor_cornerRadius_borderWidth_borderColor_(
        self,
        frame,
        bg_color=None,
        corner_radius=12.0,
        border_width=1.0,
        border_color=None,
    ):
        self = objc.super(CardView, self).initWithFrame_(frame)
        self.setWantsLayer_(True)
        bg = bg_color if bg_color is not None else Theme.BASE
        self.layer().setBackgroundColor_(
            bg.CGColor() if hasattr(bg, "CGColor") else bg
        )
        self.layer().setCornerRadius_(corner_radius)
        self.layer().setMasksToBounds_(True)
        self.layer().setBorderWidth_(border_width)
        b_col = border_color if border_color is not None else Theme.SURFACE0
        self.layer().setBorderColor_(
            b_col.CGColor() if hasattr(b_col, "CGColor") else b_col
        )
        return self

    @classmethod
    @objc.python_method
    def create(
        cls,
        frame,
        bg_color=None,
        corner_radius=12.0,
        border_width=1.0,
        border_color=None,
    ):
        """Factory method to instantiate a styled CardView."""
        return cls.alloc().initWithFrame_bgColor_cornerRadius_borderWidth_borderColor_(
            frame, bg_color, corner_radius, border_width, border_color
        )

    @objc.python_method
    def set_card_background(self, color):
        """Updates the card background color."""
        if self.layer():
            self.layer().setBackgroundColor_(
                color.CGColor() if hasattr(color, "CGColor") else color
            )

    @objc.python_method
    def set_card_border(self, color, width=1.0):
        """Updates the card border color and width."""
        if self.layer():
            self.layer().setBorderWidth_(width)
            self.layer().setBorderColor_(
                color.CGColor() if hasattr(color, "CGColor") else color
            )
