from PyQt6.QtGui import QColor
from ui.common.theme import CatppuccinMocha, PILOT_THEME_COLORS

class Theme:
    """Catppuccin Mocha Color Palette for Linux PyQt6."""
    # Dark Base Surfaces
    CRUST = QColor(CatppuccinMocha.CRUST_HEX)
    MANTLE = QColor(CatppuccinMocha.MANTLE_HEX)
    BASE = QColor(CatppuccinMocha.BASE_HEX)
    SURFACE0 = QColor(CatppuccinMocha.SURFACE0_HEX)
    SURFACE1 = QColor(CatppuccinMocha.SURFACE1_HEX)
    SURFACE2 = QColor(CatppuccinMocha.SURFACE2_HEX)
    OVERLAY0 = QColor(CatppuccinMocha.OVERLAY0_HEX)
    OVERLAY1 = QColor(CatppuccinMocha.OVERLAY1_HEX)
    OVERLAY2 = QColor(CatppuccinMocha.OVERLAY2_HEX)

    # Typography & Text
    TEXT = QColor(CatppuccinMocha.TEXT_HEX)
    SUBTEXT1 = QColor(CatppuccinMocha.SUBTEXT1_HEX)
    SUBTEXT0 = QColor(CatppuccinMocha.SUBTEXT0_HEX)

    # Accent Colors
    MAUVE = QColor(CatppuccinMocha.MAUVE_HEX)
    BLUE = QColor(CatppuccinMocha.BLUE_HEX)
    SAPPHIRE = QColor(CatppuccinMocha.SAPPHIRE_HEX)
    SKY = QColor(CatppuccinMocha.SKY_HEX)
    TEAL = QColor(CatppuccinMocha.TEAL_HEX)
    GREEN = QColor(CatppuccinMocha.GREEN_HEX)
    YELLOW = QColor(CatppuccinMocha.YELLOW_HEX)
    PEACH = QColor(CatppuccinMocha.PEACH_HEX)
    MAROON = QColor(CatppuccinMocha.MAROON_HEX)
    RED = QColor(CatppuccinMocha.RED_HEX)
    FLAMINGO = QColor(CatppuccinMocha.FLAMINGO_HEX)
    ROSEWATER = QColor(CatppuccinMocha.ROSEWATER_HEX)
    LAVENDER = QColor(CatppuccinMocha.LAVENDER_HEX)

    # Pilot mappings
    PILOT_COLORS = PILOT_THEME_COLORS

    @classmethod
    def get_color(cls, name: str, alpha: int = 255) -> QColor:
        color = getattr(cls, name.upper(), cls.TEXT)
        c = QColor(color)
        c.setAlpha(alpha)
        return c

    @classmethod
    def rgba_str(cls, qcolor: QColor, alpha: float = 1.0) -> str:
        """Returns css rgba(r, g, b, a) string."""
        return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {alpha:.2f})"

