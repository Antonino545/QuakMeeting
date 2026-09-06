"""
Reusable Catppuccin Mocha Card widget for Linux PyQt6.
"""
from PyQt6.QtWidgets import QFrame


class CardWidget(QFrame):
    """Container frame styled with Catppuccin Mocha colors and rounded corners."""

    def __init__(
        self,
        parent=None,
        bg_hex: str = "#1e1e2e",
        border_hex: str = "#313244",
        border_width: int = 1,
        border_radius: int = 12,
    ):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg_hex};
                border: {border_width}px solid {border_hex};
                border-radius: {border_radius}px;
            }}
            """
        )
