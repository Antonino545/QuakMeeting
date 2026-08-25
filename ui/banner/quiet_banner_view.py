import AppKit
import objc
from datetime import datetime

class QuietReminderView(AppKit.NSView):
    def initWithFrame_meetingData_controller_(self, frame, meeting_data, controller):
        self = objc.super(QuietReminderView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.meeting_data = meeting_data
        self.controller = controller
        
        self.title = str(meeting_data.get("title") or "Upcoming Meeting")
        self.stage = meeting_data.get("reminder_stage", 10)
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
        self.controller.dismiss()
        
    def stepAnimation_(self, timer):
        pass

    def drawRect_(self, dirtyRect):
        ctx = AppKit.NSGraphicsContext.currentContext().CGContext()
        rect = self.bounds()
        
        path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 12.0, 12.0)
        
        if self.hovered:
            AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.15, 0.95).setFill()
        else:
            AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.1, 0.9).setFill()
            
        path.fill()
        
        # Draw border
        AppKit.NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.2).setStroke()
        path.setLineWidth_(1.0)
        path.stroke()
        
        # Draw icon
        icon_str = AppKit.NSString.stringWithString_("🦆")
        icon_attrs = {AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(24)}
        icon_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(15, rect.size.height/2 - 15), icon_attrs)
        
        # Draw title
        title_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(14),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.whiteColor()
        }
        title_str = AppKit.NSString.stringWithString_(self.title)
        title_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(55, rect.size.height - 25), title_attrs)
        
        # Draw subtitle
        sub_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(12),
            AppKit.NSForegroundColorAttributeName: AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.8, 1.0)
        }
        if self.stage == 0:
            subtitle = f"Starts NOW at {self.time_str}"
        else:
            subtitle = f"Starts in {self.stage}m (at {self.time_str})"
        sub_str = AppKit.NSString.stringWithString_(subtitle)
        sub_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(55, rect.size.height - 45), sub_attrs)
