import AppKit
from ui.common.theme import CatppuccinMocha

class Theme:
    """Catppuccin Mocha Color Palette for macOS AppKit."""
    # Dark Base Surfaces
    CRUST = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.CRUST_RGB, 1.0)
    MANTLE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.MANTLE_RGB, 1.0)
    BASE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.BASE_RGB, 1.0)
    SURFACE0 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SURFACE0_RGB, 1.0)
    SURFACE1 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SURFACE1_RGB, 1.0)
    SURFACE2 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SURFACE2_RGB, 1.0)
    OVERLAY0 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.OVERLAY0_RGB, 1.0)
    OVERLAY1 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.OVERLAY1_RGB, 1.0)
    OVERLAY2 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.OVERLAY2_RGB, 1.0)

    # Typography & Foreground
    TEXT = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.TEXT_RGB, 1.0)
    SUBTEXT1 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SUBTEXT1_RGB, 1.0)
    SUBTEXT0 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SUBTEXT0_RGB, 1.0)

    # Accent Colors
    MAUVE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.MAUVE_RGB, 1.0)
    BLUE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.BLUE_RGB, 1.0)
    SAPPHIRE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SAPPHIRE_RGB, 1.0)
    SKY = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.SKY_RGB, 1.0)
    TEAL = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.TEAL_RGB, 1.0)
    GREEN = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.GREEN_RGB, 1.0)
    YELLOW = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.YELLOW_RGB, 1.0)
    PEACH = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.PEACH_RGB, 1.0)
    MAROON = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.MAROON_RGB, 1.0)
    RED = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.RED_RGB, 1.0)
    FLAMINGO = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.FLAMINGO_RGB, 1.0)
    ROSEWATER = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.ROSEWATER_RGB, 1.0)
    LAVENDER = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*CatppuccinMocha.LAVENDER_RGB, 1.0)

    @classmethod
    def get_color(cls, name: str, alpha: float = 1.0) -> AppKit.NSColor:
        color = getattr(cls, name.upper(), cls.TEXT)
        if alpha < 1.0:
            return color.colorWithAlphaComponent_(alpha)
        return color

    @classmethod
    def get_cgcolor(cls, name: str, alpha: float = 1.0):
        return cls.get_color(name, alpha).CGColor()

    @classmethod
    def style_button(cls, btn, bg_color=None, text_color=None, border_color=None, corner_radius=7.0, font_size=12.0, bold=False):
        """Applies solid Catppuccin layer-backed styling to NSButton."""
        btn.setWantsLayer_(True)
        btn.setBordered_(False)
        bg = bg_color if bg_color is not None else cls.SURFACE0
        btn.layer().setBackgroundColor_(bg.CGColor() if hasattr(bg, 'CGColor') else bg)
        btn.layer().setCornerRadius_(corner_radius)
        btn.layer().setMasksToBounds_(True)
        if border_color is not None:
            btn.layer().setBorderWidth_(1.0)
            btn.layer().setBorderColor_(border_color.CGColor() if hasattr(border_color, 'CGColor') else border_color)
        else:
            btn.layer().setBorderWidth_(0.0)

        fg = text_color if text_color is not None else cls.TEXT
        fnt = AppKit.NSFont.boldSystemFontOfSize_(font_size) if bold else AppKit.NSFont.systemFontOfSize_(font_size)
        title_str = btn.title() or ""
        attrs = {
            AppKit.NSForegroundColorAttributeName: fg,
            AppKit.NSFontAttributeName: fnt
        }
        attr_title = AppKit.NSAttributedString.alloc().initWithString_attributes_(title_str, attrs)
        btn.setAttributedTitle_(attr_title)

