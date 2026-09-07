import AppKit
import objc
from ui.macos.theme import Theme


class ModernToggleSwitch(AppKit.NSControl):
    """Modern iOS/macOS styled Toggle Switch (44x24) matching Catppuccin Mocha theme."""

    def initWithFrame_(self, frame):
        self = objc.super(ModernToggleSwitch, self).initWithFrame_(frame)
        self._checked = False
        self._knob_x = 2.0
        self._target = None
        self._action = None
        self._callback = None
        return self

    def isChecked(self):
        return self._checked

    def setChecked_(self, val):
        self._checked = bool(val)
        self._knob_x = 22.0 if self._checked else 2.0
        self.setNeedsDisplay_(True)

    def state(self):
        return AppKit.NSControlStateValueOn if self._checked else AppKit.NSControlStateValueOff

    def setState_(self, val):
        self.setChecked_(val == AppKit.NSControlStateValueOn or bool(val))

    def setTarget_(self, target):
        self._target = target

    def setAction_(self, action):
        self._action = action

    def setCallback_(self, cb):
        self._callback = cb

    def acceptsFirstMouse_(self, event):
        return True

    def mouseDownCanMoveWindow(self):
        return False

    def resetCursorRects(self):
        cursor = (
            AppKit.NSCursor.pointingHandCursor()
            if self.isEnabled()
            else AppKit.NSCursor.arrowCursor()
        )
        self.addCursorRect_cursor_(self.bounds(), cursor)

    def mouseDown_(self, event):
        if not self.isEnabled():
            return
        self._checked = not self._checked
        self._knob_x = 22.0 if self._checked else 2.0
        self.setNeedsDisplay_(True)
        if self._action and self._target and hasattr(self._target, self._action):
            getattr(self._target, self._action)(self)
        elif self._callback:
            self._callback(self._checked)

    def mouseUp_(self, event):
        pass

    def drawRect_(self, dirtyRect):
        bounds = self.bounds()
        track_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            bounds, 12.0, 12.0
        )
        if not self.isEnabled():
            track_col = Theme.SURFACE0.colorWithAlphaComponent_(0.4)
            knob_col = Theme.SUBTEXT1.colorWithAlphaComponent_(0.4)
        elif self._checked:
            track_col = Theme.MAUVE
            knob_col = AppKit.NSColor.whiteColor()
        else:
            track_col = Theme.SURFACE0
            knob_col = Theme.SUBTEXT1

        track_col.setFill()
        track_path.fill()

        knob_rect = AppKit.NSMakeRect(self._knob_x, 2.0, 20.0, 20.0)
        knob_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(knob_rect)
        knob_col.setFill()
        knob_path.fill()

