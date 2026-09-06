import AppKit
import objc
from ui.macos.theme import Theme


class ChipDeleteButton(AppKit.NSButton):
    """Delete button for keyword chip with pointing hand cursor and hover feedback."""

    def resetCursorRects(self):
        self.addCursorRect_cursor_(self.bounds(), AppKit.NSCursor.pointingHandCursor())

    def updateTrackingAreas(self):
        objc.super(ChipDeleteButton, self).updateTrackingAreas()
        if hasattr(self, "_tracking_area") and self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
        self._tracking_area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            AppKit.NSTrackingMouseEnteredAndExited
            | AppKit.NSTrackingActiveAlways
            | AppKit.NSTrackingInVisibleRect
            | AppKit.NSTrackingCursorUpdate,
            self,
            None,
        )
        self.addTrackingArea_(self._tracking_area)

    def cursorUpdate_(self, event):
        try:
            AppKit.NSCursor.pointingHandCursor().set()
        except Exception:
            pass

    def mouseEntered_(self, event):
        try:
            AppKit.NSCursor.pointingHandCursor().set()
        except Exception:
            pass
        if self.layer() and self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.12)
            self.animator().setAlphaValue_(0.65)
            AppKit.NSAnimationContext.endGrouping()

    def mouseExited_(self, event):
        try:
            AppKit.NSCursor.arrowCursor().set()
        except Exception:
            pass
        if self.layer() and self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.12)
            self.animator().setAlphaValue_(1.0)
            AppKit.NSAnimationContext.endGrouping()


class KeywordChipView(AppKit.NSView):
    """Interactive keyword tag chip with text label and '✕' delete button."""

    def resetCursorRects(self):
        objc.super(KeywordChipView, self).resetCursorRects()

    @classmethod
    @objc.python_method
    def create(
        cls,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        target=None,
        action=None,
        tooltip: str = "",
    ):
        chip = cls.alloc().initWithFrame_(AppKit.NSMakeRect(x, y, width, height))
        chip.setWantsLayer_(True)
        chip.layer().setBackgroundColor_(Theme.SURFACE1.CGColor())
        chip.layer().setCornerRadius_(5.0)
        chip.layer().setBorderWidth_(1.0)
        chip.layer().setBorderColor_(Theme.SURFACE2.CGColor())

        lbl = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(6, 2, width - 24, height - 4)
        )
        lbl.setStringValue_(text)
        lbl.setFont_(
            AppKit.NSFont.systemFontOfSize_weight_(10.5, AppKit.NSFontWeightMedium)
        )
        lbl.setTextColor_(Theme.TEXT)
        lbl.setBezeled_(False)
        lbl.setDrawsBackground_(False)
        lbl.setEditable_(False)
        chip.addSubview_(lbl)

        del_btn = ChipDeleteButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(width - 20, 1, 18, height - 2)
        )
        del_btn.setTitle_("✕")
        del_btn.setBordered_(False)
        del_btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        if tooltip:
            del_btn.setToolTip_(tooltip)
        if target and action:
            del_btn.setTarget_(target)
            del_btn.setAction_(action)
        del_btn.setWantsLayer_(True)
        del_btn.layer().setBackgroundColor_(AppKit.NSColor.clearColor().CGColor())

        pstyle = AppKit.NSMutableParagraphStyle.alloc().init()
        pstyle.setAlignment_(AppKit.NSTextAlignmentCenter)
        del_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(10.0),
            AppKit.NSForegroundColorAttributeName: Theme.RED,
            AppKit.NSParagraphStyleAttributeName: pstyle,
        }
        del_btn.setAttributedTitle_(
            AppKit.NSAttributedString.alloc().initWithString_attributes_("✕", del_attrs)
        )
        chip.addSubview_(del_btn)
        return chip
