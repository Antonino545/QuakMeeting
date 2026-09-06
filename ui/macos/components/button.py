import AppKit
import objc
from ui.macos.theme import Theme


class ModernButton(AppKit.NSButton):
    """Modern macOS Button with pointing hand cursor, hover feedback, and tactile click animation."""

    def resetCursorRects(self):
        objc.super(ModernButton, self).resetCursorRects()
        cursor = (
            AppKit.NSCursor.pointingHandCursor()
            if self.isEnabled()
            else AppKit.NSCursor.arrowCursor()
        )
        self.addCursorRect_cursor_(self.bounds(), cursor)

    def updateTrackingAreas(self):
        objc.super(ModernButton, self).updateTrackingAreas()
        if hasattr(self, "_tracking_area") and self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
        self._tracking_area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            AppKit.NSTrackingMouseEnteredAndExited
            | AppKit.NSTrackingCursorUpdate
            | AppKit.NSTrackingActiveAlways
            | AppKit.NSTrackingInVisibleRect,
            self,
            None,
        )
        self.addTrackingArea_(self._tracking_area)

    def cursorUpdate_(self, event):
        cursor = (
            AppKit.NSCursor.pointingHandCursor()
            if self.isEnabled()
            else AppKit.NSCursor.arrowCursor()
        )
        if cursor is not None and hasattr(cursor, "set"):
            cursor.set()

    def mouseEntered_(self, event):
        try:
            AppKit.NSCursor.pointingHandCursor().set()
        except Exception:
            pass
        if self.layer() and self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.15)
            self.animator().setAlphaValue_(0.85)
            AppKit.NSAnimationContext.endGrouping()

    def mouseExited_(self, event):
        try:
            AppKit.NSCursor.arrowCursor().set()
        except Exception:
            pass
        if self.layer() and self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.15)
            self.animator().setAlphaValue_(1.0)
            AppKit.NSAnimationContext.endGrouping()

    def mouseDown_(self, event):
        if self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.06)
            self.animator().setAlphaValue_(0.55)
            AppKit.NSAnimationContext.endGrouping()
        objc.super(ModernButton, self).mouseDown_(event)
        if self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.15)
            self.animator().setAlphaValue_(1.0)
            AppKit.NSAnimationContext.endGrouping()


def style_button(
    btn,
    bg_color=None,
    text_color=None,
    border_color=None,
    corner_radius=7.0,
    font_size=12.0,
    bold=False,
):
    """Applies solid Catppuccin layer-backed styling to an NSButton."""
    btn.setWantsLayer_(True)
    btn.setBordered_(False)
    btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
    btn.setButtonType_(AppKit.NSButtonTypeMomentaryPushIn)
    bg = bg_color if bg_color is not None else Theme.SURFACE0
    btn.layer().setBackgroundColor_(bg.CGColor() if hasattr(bg, "CGColor") else bg)
    btn.layer().setCornerRadius_(corner_radius)
    btn.layer().setMasksToBounds_(True)
    if border_color is not None:
        btn.layer().setBorderWidth_(1.0)
        btn.layer().setBorderColor_(
            border_color.CGColor() if hasattr(border_color, "CGColor") else border_color
        )
    else:
        btn.layer().setBorderWidth_(0.0)

    fg = text_color if text_color is not None else Theme.TEXT
    fnt = (
        AppKit.NSFont.boldSystemFontOfSize_(font_size)
        if bold
        else AppKit.NSFont.systemFontOfSize_(font_size)
    )
    title_str = btn.title() or ""
    attrs = {
        AppKit.NSForegroundColorAttributeName: fg,
        AppKit.NSFontAttributeName: fnt,
    }
    attr_title = AppKit.NSAttributedString.alloc().initWithString_attributes_(title_str, attrs)
    btn.setAttributedTitle_(attr_title)


def create_button(
    frame,
    title="",
    bg_color=None,
    text_color=None,
    border_color=None,
    corner_radius=7.0,
    font_size=12.0,
    bold=False,
):
    """Instantiates a ModernButton with pointing hand cursor, hover and click animations."""
    btn = ModernButton.alloc().initWithFrame_(frame)
    btn.setTitle_(title)
    style_button(
        btn,
        bg_color=bg_color,
        text_color=text_color,
        border_color=border_color,
        corner_radius=corner_radius,
        font_size=font_size,
        bold=bold,
    )
    return btn


def create_gradient_button(
    frame,
    title="",
    start_color=None,
    end_color=None,
    text_color=None,
    corner_radius=8.0,
    font_size=12.0,
    bold=True,
):
    """Creates a modern button with horizontal Catppuccin color gradient."""
    btn = ModernButton.alloc().initWithFrame_(frame)
    btn.setTitle_(title)
    btn.setWantsLayer_(True)
    btn.setBordered_(False)
    btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
    btn.setButtonType_(AppKit.NSButtonTypeMomentaryPushIn)
    btn.layer().setCornerRadius_(corner_radius)
    btn.layer().setMasksToBounds_(True)

    try:
        import Quartz

        grad = Quartz.CAGradientLayer.layer()
        grad.setFrame_(AppKit.NSMakeRect(0, 0, frame.size.width, frame.size.height))
        c1 = (start_color if start_color is not None else Theme.GREEN).CGColor()
        c2 = (end_color if end_color is not None else Theme.TEAL).CGColor()
        grad.setColors_([c1, c2])
        grad.setStartPoint_(Quartz.CGPoint(0, 0))
        grad.setEndPoint_(Quartz.CGPoint(1, 0))
        btn.layer().insertSublayer_atIndex_(grad, 0)
    except Exception:
        btn.layer().setBackgroundColor_(
            (start_color if start_color else Theme.GREEN).CGColor()
        )

    fg = text_color if text_color is not None else Theme.CRUST
    fnt = (
        AppKit.NSFont.boldSystemFontOfSize_(font_size)
        if bold
        else AppKit.NSFont.systemFontOfSize_(font_size)
    )
    attrs = {
        AppKit.NSForegroundColorAttributeName: fg,
        AppKit.NSFontAttributeName: fnt,
    }
    attr_title = AppKit.NSAttributedString.alloc().initWithString_attributes_(title, attrs)
    btn.setAttributedTitle_(attr_title)
    return btn
