import AppKit

class Theme:
    """Catppuccin Mocha Color Palette for macOS AppKit."""
    # Dark Base Surfaces
    CRUST = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.067, 0.067, 0.106, 1.0)       # #11111b
    MANTLE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.094, 0.094, 0.145, 1.0)      # #181825
    BASE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.118, 0.118, 0.180, 1.0)        # #1e1e2e
    SURFACE0 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.192, 0.196, 0.267, 1.0)    # #313244
    SURFACE1 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.271, 0.278, 0.353, 1.0)    # #45475a
    SURFACE2 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.345, 0.357, 0.439, 1.0)    # #585b70
    OVERLAY0 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.424, 0.439, 0.525, 1.0)    # #6c7086

    # Typography & Foreground
    TEXT = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.804, 0.839, 0.957, 1.0)        # #cdd6f4
    SUBTEXT1 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.729, 0.761, 0.871, 1.0)    # #bac2de
    SUBTEXT0 = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.678, 0.784, 1.0)    # #a6adc8

    # Accent Colors
    MAUVE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0)       # #cba6f7
    BLUE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.706, 0.980, 1.0)        # #89b4fa
    SAPPHIRE = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.455, 0.780, 0.925, 1.0)    # #74c7ec
    SKY = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.863, 0.922, 1.0)         # #89dceb
    TEAL = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.580, 0.886, 0.835, 1.0)        # #94e2d5
    GREEN = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0)       # #a6e3a1
    YELLOW = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.976, 0.886, 0.686, 1.0)      # #f9e2af
    PEACH = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0)       # #fab387
    MAROON = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.922, 0.627, 0.675, 1.0)      # #eba0ac
    RED = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.953, 0.545, 0.659, 1.0)         # #f38ba8
    LAVENDER = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.706, 0.745, 0.996, 1.0)    # #b4befe

    @classmethod
    def get_color(cls, name: str, alpha: float = 1.0) -> AppKit.NSColor:
        color = getattr(cls, name.upper(), cls.TEXT)
        if alpha < 1.0:
            return color.colorWithAlphaComponent_(alpha)
        return color

    @classmethod
    def get_cgcolor(cls, name: str, alpha: float = 1.0):
        return cls.get_color(name, alpha).CGColor()
