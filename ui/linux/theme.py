from PyQt6.QtGui import QColor

class Theme:
    # Catppuccin Mocha Colors
    CRUST = QColor("#11111b")
    MANTLE = QColor("#181825")
    BASE = QColor("#1e1e2e")
    SURFACE0 = QColor("#313244")
    SURFACE1 = QColor("#45475a")
    SURFACE2 = QColor("#585b70")
    
    TEXT = QColor("#cdd6f4")
    SUBTEXT1 = QColor("#bac2de")
    SUBTEXT0 = QColor("#a6adc8")
    OVERLAY2 = QColor("#9399b2")
    OVERLAY1 = QColor("#7f849c")
    OVERLAY0 = QColor("#6c7086")
    
    MAUVE = QColor("#cba6f7")
    BLUE = QColor("#89b4fa")
    SAPPHIRE = QColor("#74c7ec")
    SKY = QColor("#89dceb")
    TEAL = QColor("#94e2d5")
    GREEN = QColor("#a6e3a1")
    YELLOW = QColor("#f9e2af")
    PEACH = QColor("#fab387")
    MAROON = QColor("#eba0ac")
    RED = QColor("#f38ba8")
    FLAMINGO = QColor("#f2cdcd")
    ROSEWATER = QColor("#f5e0dc")

    @classmethod
    def get_color(cls, name: str, alpha: int = 255) -> QColor:
        color = getattr(cls, name.upper(), cls.TEXT)
        c = QColor(color)
        c.setAlpha(alpha)
        return c

