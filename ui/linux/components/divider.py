"""
Hairline divider widget for Linux PyQt6 matching Catppuccin Mocha SURFACE0.
"""
from PyQt6.QtWidgets import QFrame


class HairlineDivider(QFrame):
    """Subtle 1px horizontal divider line."""

    def __init__(self, parent=None, color_hex: str = "#313244"):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background-color: {color_hex}; border: none; max-height: 1px;")
