import AppKit
import objc
from datetime import datetime
try:
    from ui.macos.theme import Theme
except ImportError:
    from theme import Theme

class QuietReminderView(AppKit.NSView):
    def initWithFrame_meetingData_controller_(self, frame, meeting_data, controller):
        self = objc.super(QuietReminderView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.meeting_data = meeting_data
        self.controller = controller

        self.title = str(meeting_data.get("title") or "Upcoming Meeting")
        self.stage = meeting_data.get("reminder_stage", 10)
        self.is_update = bool(meeting_data.get("is_update_banner"))
        start_time = meeting_data.get("start_time")
        if start_time and hasattr(start_time, "strftime"):
            self.time_str = start_time.strftime("%H:%M")
        else:
            self.time_str = ""

        self.hovered = False

        tracking_options = (
            AppKit.NSTrackingMouseEnteredAndExited |
            AppKit.NSTrackingActiveAlways
        )
        self.tracking_area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            tracking_options,
            self,
            None
        )
        self.addTrackingArea_(self.tracking_area)

        return self

    def mouseEntered_(self, event):
        self.hovered = True
        self.setNeedsDisplay_(True)

    def mouseExited_(self, event):
        self.hovered = False
        self.setNeedsDisplay_(True)

    def mouseDown_(self, event):
        if self.is_update:
            self.controller.trigger_action()
        else:
            self.controller.dismiss()

    def stepAnimation_(self, timer):
        pass

    def drawRect_(self, dirtyRect):
        rect = self.bounds()
        path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 14.0, 14.0)

        if self.hovered:
            Theme.SURFACE0.setFill()
        else:
            Theme.BASE.setFill()

        path.fill()

        # Draw border
        if self.is_update:
            Theme.SAPPHIRE.setStroke()
            path.setLineWidth_(1.5)
        else:
            Theme.SURFACE1.setStroke()
            path.setLineWidth_(1.0)
        path.stroke()

        # Draw icon
        icon_symbol = "🚀" if self.is_update else "🦆"
        icon_str = AppKit.NSString.stringWithString_(icon_symbol)
        icon_attrs = {AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(26)}
        icon_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(16, rect.size.height/2 - 16), icon_attrs)

        # Draw title
        title_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(14),
            AppKit.NSForegroundColorAttributeName: Theme.TEXT
        }
        title_str = AppKit.NSString.stringWithString_(self.title)
        title_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(58, rect.size.height - 28), title_attrs)

        # Draw subtitle
        sub_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(12),
            AppKit.NSForegroundColorAttributeName: Theme.SAPPHIRE if self.is_update else Theme.SUBTEXT0
        }
        if self.is_update:
            subtitle = "⚡ Click to download & install update"
        elif self.stage == 0:
            subtitle = f"Starts NOW at {self.time_str}"
        else:
            subtitle = f"In {self.stage} minutes • {self.time_str}"
        sub_str = AppKit.NSString.stringWithString_(subtitle)
        sub_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(58, 12), sub_attrs)
