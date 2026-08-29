import AppKit
import objc
from ui.common.theme import CatppuccinMocha

class ModernButton(AppKit.NSButton):
    """Modern macOS Button with pointing hand cursor, hover feedback, and tactile click animation."""
    def resetCursorRects(self):
        self.addCursorRect_cursor_(self.bounds(), AppKit.NSCursor.pointingHandCursor())

    def updateTrackingAreas(self):
        objc.super(ModernButton, self).updateTrackingAreas()
        if hasattr(self, "_tracking_area") and self._tracking_area:
            self.removeTrackingArea_(self._tracking_area)
        self._tracking_area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            AppKit.NSTrackingMouseEnteredAndExited | AppKit.NSTrackingActiveAlways | AppKit.NSTrackingInVisibleRect,
            self,
            None
        )
        self.addTrackingArea_(self._tracking_area)

    def mouseEntered_(self, event):
        if self.layer() and self.isEnabled():
            AppKit.NSAnimationContext.beginGrouping()
            AppKit.NSAnimationContext.currentContext().setDuration_(0.15)
            self.animator().setAlphaValue_(0.85)
            AppKit.NSAnimationContext.endGrouping()

    def mouseExited_(self, event):
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
    def create_button(cls, frame, title="", bg_color=None, text_color=None, border_color=None, corner_radius=7.0, font_size=12.0, bold=False):
        """Instantiates a ModernButton with pointing hand cursor, hover and click animations."""
        btn = ModernButton.alloc().initWithFrame_(frame)
        btn.setTitle_(title)
        cls.style_button(btn, bg_color=bg_color, text_color=text_color, border_color=border_color, corner_radius=corner_radius, font_size=font_size, bold=bold)
        return btn

    @classmethod
    def style_button(cls, btn, bg_color=None, text_color=None, border_color=None, corner_radius=7.0, font_size=12.0, bold=False):
        """Applies solid Catppuccin layer-backed styling to NSButton."""
        btn.setWantsLayer_(True)
        btn.setBordered_(False)
        btn.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        btn.setButtonType_(AppKit.NSButtonTypeMomentaryPushIn)
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

    @classmethod
    def create_gradient_button(cls, frame, title="", start_color=None, end_color=None, text_color=None, corner_radius=8.0, font_size=12.0, bold=True):
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
            c1 = (start_color if start_color is not None else cls.GREEN).CGColor()
            c2 = (end_color if end_color is not None else cls.TEAL).CGColor()
            grad.setColors_([c1, c2])
            grad.setStartPoint_(Quartz.CGPoint(0, 0))
            grad.setEndPoint_(Quartz.CGPoint(1, 0))
            btn.layer().insertSublayer_atIndex_(grad, 0)
        except Exception:
            btn.layer().setBackgroundColor_((start_color if start_color else cls.GREEN).CGColor())

        fg = text_color if text_color is not None else cls.CRUST
        fnt = AppKit.NSFont.boldSystemFontOfSize_(font_size) if bold else AppKit.NSFont.systemFontOfSize_(font_size)
        attrs = {
            AppKit.NSForegroundColorAttributeName: fg,
            AppKit.NSFontAttributeName: fnt
        }
        attr_title = AppKit.NSAttributedString.alloc().initWithString_attributes_(title, attrs)
        btn.setAttributedTitle_(attr_title)
        return btn


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

    def setTarget_(self, target):
        self._target = target

    def setAction_(self, action):
        self._action = action

    def setCallback_(self, cb):
        self._callback = cb

    def resetCursorRects(self):
        self.addCursorRect_cursor_(self.bounds(), AppKit.NSCursor.pointingHandCursor())

    def mouseUp_(self, event):
        self._checked = not self._checked
        self._knob_x = 22.0 if self._checked else 2.0
        self.setNeedsDisplay_(True)
        if self._action and self._target and hasattr(self._target, self._action):
            getattr(self._target, self._action)(self)
        elif self._callback:
            self._callback(self._checked)

    def drawRect_(self, dirtyRect):
        bounds = self.bounds()
        track_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 12.0, 12.0)
        if self._checked:
            Theme.MAUVE.setFill()
        else:
            Theme.SURFACE0.setFill()
        track_path.fill()

        knob_rect = AppKit.NSMakeRect(self._knob_x, 2.0, 20.0, 20.0)
        knob_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(knob_rect)
        if self._checked:
            Theme.CRUST.setFill()
        else:
            Theme.TEXT.setFill()
        knob_path.fill()

