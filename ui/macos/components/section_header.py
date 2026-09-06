import AppKit
import objc
from ui.macos.theme import Theme


class HairlineDivider(AppKit.NSView):
    """Subtle 1px horizontal divider line matching Catppuccin Mocha SURFACE0."""

    @classmethod
    @objc.python_method
    def create(cls, x: float, y: float, width: float, color=None):
        div = cls.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, width, 1.0))
        div.setWantsLayer_(True)
        c = color if color is not None else Theme.SURFACE0
        div.layer().setBackgroundColor_(c.CGColor() if hasattr(c, "CGColor") else c)
        return div


class SectionHeaderView(AppKit.NSView):
    """Section header with optional accent pill, bold title, and subtitle."""

    @classmethod
    @objc.python_method
    def add_to_parent(
        cls,
        parent,
        title: str,
        subtitle: str = "",
        h: float = 0.0,
        w: float = 0.0,
        x: float = 18.0,
        top_offset: float = 34.0,
        accent_color=None,
    ):
        """Helper to append section header labels directly to a parent card."""
        if accent_color is not None:
            pill = AppKit.NSView.alloc().initWithFrame_(
                AppKit.NSMakeRect(x, h - top_offset - 2, 4, 20)
            )
            pill.setWantsLayer_(True)
            pill.layer().setBackgroundColor_(
                accent_color.CGColor() if hasattr(accent_color, "CGColor") else accent_color
            )
            pill.layer().setCornerRadius_(2.0)
            parent.addSubview_(pill)
            x += 10.0

        t_lbl = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(x, h - top_offset, w - x - 18, 22)
        )
        t_lbl.setStringValue_(title)
        t_lbl.setFont_(AppKit.NSFont.boldSystemFontOfSize_(14.5))
        t_lbl.setTextColor_(Theme.TEXT)
        t_lbl.setBezeled_(False)
        t_lbl.setDrawsBackground_(False)
        t_lbl.setEditable_(False)
        parent.addSubview_(t_lbl)

        if subtitle:
            s_lbl = AppKit.NSTextField.alloc().initWithFrame_(
                AppKit.NSMakeRect(x, h - top_offset - 18, w - x - 18, 16)
            )
            s_lbl.setStringValue_(subtitle)
            s_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
            s_lbl.setTextColor_(Theme.SUBTEXT0)
            s_lbl.setBezeled_(False)
            s_lbl.setDrawsBackground_(False)
            s_lbl.setEditable_(False)
            parent.addSubview_(s_lbl)
