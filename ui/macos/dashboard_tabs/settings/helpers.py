import AppKit
from ui.macos.theme import Theme
from ui.macos.components import (
    HairlineDivider,
    ModernButton,
    SectionHeaderView,
)


def add_section_header(parent, title, subtitle, h, w):
    SectionHeaderView.add_to_parent(parent, title, subtitle, h=h, w=w)


def add_hairline_divider(parent, y, w):
    div = HairlineDivider.create(16, y, w - 32.0)
    parent.addSubview_(div)


def create_pill_chip(
    parent,
    title,
    tag,
    is_checked,
    action_name,
    x,
    y,
    width=52.0,
    height=26.0,
    accent_type="mauve",
    target=None,
):
    """Creates a modern pill chip toggle button matching Qt."""
    btn = ModernButton.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, width, height))
    btn.setButtonType_(AppKit.NSButtonTypePushOnPushOff)
    btn.setBordered_(False)
    btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
    btn.setWantsLayer_(True)
    btn.layer().setCornerRadius_(7.0)
    btn.layer().setMasksToBounds_(True)
    btn.setTag_(tag)
    btn.setTitle_(title)
    if target is not None:
        btn.setTarget_(target)
    btn.setAction_(action_name)
    btn.setState_(AppKit.NSControlStateValueOn if is_checked else AppKit.NSControlStateValueOff)
    update_pill_chip_style(btn, is_checked, accent_type)
    parent.addSubview_(btn)
    return btn


def update_pill_chip_style(btn, is_checked, accent_type="mauve"):
    """Applies Catppuccin active/inactive styling matching Qt."""
    if accent_type == "blue":
        active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.706, 0.980, 1.0)
        border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.537, 0.706, 0.980, 1.0).CGColor()
    elif accent_type == "peach":
        active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0)
        border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.980, 0.702, 0.529, 1.0).CGColor()
    elif accent_type == "green":
        active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0)
        border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.651, 0.890, 0.631, 1.0).CGColor()
    else:
        active_bg = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0)
        border_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.796, 0.651, 0.969, 1.0).CGColor()

    if is_checked:
        btn.layer().setBackgroundColor_(active_bg.CGColor())
        btn.layer().setBorderWidth_(1.0)
        btn.layer().setBorderColor_(border_col)
        fg_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.067, 0.067, 0.106, 1.0)
        font = AppKit.NSFont.boldSystemFontOfSize_(11.5)
    else:
        btn.layer().setBackgroundColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.141, 0.141, 0.220, 1.0).CGColor())
        btn.layer().setBorderWidth_(1.0)
        btn.layer().setBorderColor_(AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.271, 0.278, 0.353, 1.0).CGColor())
        fg_color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.804, 0.839, 0.957, 1.0)
        font = AppKit.NSFont.systemFontOfSize_weight_(11.5, AppKit.NSFontWeightMedium)

    pstyle = AppKit.NSMutableParagraphStyle.alloc().init()
    pstyle.setAlignment_(AppKit.NSTextAlignmentCenter)
    attrs = {
        AppKit.NSFontAttributeName: font,
        AppKit.NSForegroundColorAttributeName: fg_color,
        AppKit.NSParagraphStyleAttributeName: pstyle
    }
    title_str = btn.title() or ""
    attr_str = AppKit.NSAttributedString.alloc().initWithString_attributes_(title_str, attrs)
    btn.setAttributedTitle_(attr_str)
