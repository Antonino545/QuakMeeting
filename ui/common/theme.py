"""
Shared Catppuccin Mocha Theme System for QuakMeeting.
Single source of truth for color palette tokens across macOS (AppKit) and Linux (PyQt6).
"""
from typing import Dict, Tuple

class CatppuccinMocha:
    """Standardized Catppuccin Mocha Palette."""

    # 1. Dark Base Surfaces
    CRUST_HEX = "#11111b"
    CRUST_RGB = (0.067, 0.067, 0.106)

    MANTLE_HEX = "#181825"
    MANTLE_RGB = (0.094, 0.094, 0.145)

    BASE_HEX = "#1e1e2e"
    BASE_RGB = (0.118, 0.118, 0.180)

    SURFACE0_HEX = "#313244"
    SURFACE0_RGB = (0.192, 0.196, 0.267)

    SURFACE1_HEX = "#45475a"
    SURFACE1_RGB = (0.271, 0.278, 0.353)

    SURFACE2_HEX = "#585b70"
    SURFACE2_RGB = (0.345, 0.357, 0.439)

    OVERLAY0_HEX = "#6c7086"
    OVERLAY0_RGB = (0.424, 0.439, 0.525)

    OVERLAY1_HEX = "#7f849c"
    OVERLAY1_RGB = (0.498, 0.518, 0.612)

    OVERLAY2_HEX = "#9399b2"
    OVERLAY2_RGB = (0.576, 0.600, 0.698)

    # 2. Typography & Text
    TEXT_HEX = "#cdd6f4"
    TEXT_RGB = (0.804, 0.839, 0.957)

    SUBTEXT1_HEX = "#bac2de"
    SUBTEXT1_RGB = (0.729, 0.761, 0.871)

    SUBTEXT0_HEX = "#a6adc8"
    SUBTEXT0_RGB = (0.651, 0.678, 0.784)

    # 3. Accent Colors
    MAUVE_HEX = "#cba6f7"
    MAUVE_RGB = (0.796, 0.651, 0.969)

    BLUE_HEX = "#89b4fa"
    BLUE_RGB = (0.537, 0.706, 0.980)

    SAPPHIRE_HEX = "#74c7ec"
    SAPPHIRE_RGB = (0.455, 0.780, 0.925)

    SKY_HEX = "#89dceb"
    SKY_RGB = (0.537, 0.863, 0.922)

    TEAL_HEX = "#94e2d5"
    TEAL_RGB = (0.580, 0.886, 0.835)

    GREEN_HEX = "#a6e3a1"
    GREEN_RGB = (0.651, 0.890, 0.631)

    YELLOW_HEX = "#f9e2af"
    YELLOW_RGB = (0.976, 0.886, 0.686)

    PEACH_HEX = "#fab387"
    PEACH_RGB = (0.980, 0.702, 0.529)

    MAROON_HEX = "#eba0ac"
    MAROON_RGB = (0.922, 0.627, 0.675)

    RED_HEX = "#f38ba8"
    RED_RGB = (0.953, 0.545, 0.659)

    FLAMINGO_HEX = "#f2cdcd"
    FLAMINGO_RGB = (0.949, 0.804, 0.804)

    ROSEWATER_HEX = "#f5e0dc"
    ROSEWATER_RGB = (0.961, 0.878, 0.863)

    LAVENDER_HEX = "#b4befe"
    LAVENDER_RGB = (0.706, 0.745, 0.996)


# Pilot mascot palette mapping
PILOT_THEME_COLORS: Dict[str, Dict[str, str]] = {
    "chef": {
        "accent": CatppuccinMocha.PEACH_HEX,
        "accent_bright": CatppuccinMocha.YELLOW_HEX,
        "btn_gradient_top": CatppuccinMocha.PEACH_HEX,
        "btn_gradient_bot": CatppuccinMocha.MAROON_HEX,
    },
    "captain": {
        "accent": CatppuccinMocha.SAPPHIRE_HEX,
        "accent_bright": CatppuccinMocha.SKY_HEX,
        "btn_gradient_top": CatppuccinMocha.SAPPHIRE_HEX,
        "btn_gradient_bot": CatppuccinMocha.BLUE_HEX,
    },
    "owl": {
        "accent": CatppuccinMocha.MAUVE_HEX,
        "accent_bright": CatppuccinMocha.LAVENDER_HEX,
        "btn_gradient_top": CatppuccinMocha.MAUVE_HEX,
        "btn_gradient_bot": CatppuccinMocha.LAVENDER_HEX,
    },
    "driver": {
        "accent": CatppuccinMocha.YELLOW_HEX,
        "accent_bright": CatppuccinMocha.PEACH_HEX,
        "btn_gradient_top": CatppuccinMocha.YELLOW_HEX,
        "btn_gradient_bot": CatppuccinMocha.PEACH_HEX,
    },
    "zen_duck": {
        "accent": CatppuccinMocha.TEAL_HEX,
        "accent_bright": CatppuccinMocha.SKY_HEX,
        "btn_gradient_top": CatppuccinMocha.TEAL_HEX,
        "btn_gradient_bot": CatppuccinMocha.SKY_HEX,
    },
    "gym": {
        "accent": CatppuccinMocha.RED_HEX,
        "accent_bright": CatppuccinMocha.MAROON_HEX,
        "btn_gradient_top": CatppuccinMocha.RED_HEX,
        "btn_gradient_bot": CatppuccinMocha.MAROON_HEX,
    },
    "duck": {
        "accent": CatppuccinMocha.GREEN_HEX,
        "accent_bright": CatppuccinMocha.TEAL_HEX,
        "btn_gradient_top": CatppuccinMocha.GREEN_HEX,
        "btn_gradient_bot": CatppuccinMocha.TEAL_HEX,
    }
}
