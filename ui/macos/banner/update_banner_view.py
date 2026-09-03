import AppKit
import objc
import math
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from core.services.event_bus import event_bus
from core.services.updater_service import updater_service
from ui.macos.theme import Theme

CARD_W = 500.0
CARD_H = 148.0
CARD_R = 18.0
BTN_H = 32.0
BTN_JOIN_W = 170.0
BTN_SMALL_W = 100.0

def get_update_preset(version_str: str = "New Version", release_url: str = "") -> Dict[str, Any]:
    """Generates banner payload for QuakMeeting software updates."""
    return {
        "title": f"QuakMeeting {version_str} Ready!",
        "provider": "Software Update ✨",
        "pilot_type": "captain",
        "action_btn_text": "⚡ UPDATE NOW",
        "quote_text": f"🚀 {version_str} IS READY!",
        "action_url": release_url or "https://github.com/Antonino545/QuakMeeting/releases",
        "start_time": datetime.now(),
        "is_travel": False,
        "is_update_banner": True,
        "location": "Click to download & install update",
    }

class MacUpdateBannerView(AppKit.NSView):
    def initWithFrame_meetingData_controller_(self, frame, meeting_data: Dict[str, Any], controller):
        self = objc.super(MacUpdateBannerView, self).initWithFrame_(frame)
        if self is None:
            return None

        self.meeting_data = meeting_data
        self.controller = controller
        self.title = str(meeting_data.get("title", "Software Update"))
        self.provider = str(meeting_data.get("provider", "Software Update ✨"))
        self.btn_text = str(meeting_data.get("action_btn_text", "⚡ UPDATE NOW"))
        self.quote_text = str(meeting_data.get("quote_text", "🚀 QuakMeeting Update Ready!"))

        self.tick = 0
        self.is_paused = False
        self._hover_target = None  # "join" | "snooze" | "close"

        self.install_mode = False
        self.install_progress = 0.0
        self.install_step = "Downloading..."
        self.install_ready = False

        self._subscribe_updater_events()

        tracking_options = (
            AppKit.NSTrackingMouseEnteredAndExited |
            AppKit.NSTrackingMouseMoved |
            AppKit.NSTrackingActiveAlways |
            AppKit.NSTrackingInVisibleRect
        )
        self.tracking_area = AppKit.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            tracking_options,
            self,
            None
        )
        self.addTrackingArea_(self.tracking_area)

        return self

    @objc.python_method
    def _subscribe_updater_events(self):
        def _on_step(step_id=None, step_name=None, **kwargs):
            def _ui():
                if step_name:
                    self.install_step = step_name
                if step_id == "ready":
                    self.install_ready = True
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        def _on_progress(percent=0.0, **kwargs):
            def _ui():
                self.install_progress = float(percent)
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        def _on_downloading(file_name=None, url=None, **kwargs):
            def _ui():
                self.install_step = "Downloading..."
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        def _on_download_progress(percent=0.0, **kwargs):
            def _ui():
                self.install_progress = float(percent)
                self.install_step = "Downloading..."
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        def _on_downloaded(**kwargs):
            def _ui():
                self.install_step = "Installing..."
                self.install_progress = 100.0
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        def _on_installed(**kwargs):
            def _ui():
                self.install_ready = True
                self.install_step = "✅ Update Installed! Relaunching..."
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        def _on_failed(error=None, **kwargs):
            def _ui():
                self.install_step = f"❌ Update failed: {str(error or 'Error')[:40]}"
                self.setNeedsDisplay_(True)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_ui)

        event_bus.subscribe("UPDATE_STEP", _on_step)
        event_bus.subscribe("UPDATE_PROGRESS", _on_progress)
        event_bus.subscribe("UPDATE_DOWNLOADING", _on_downloading)
        event_bus.subscribe("UPDATE_DOWNLOAD_PROGRESS", _on_download_progress)
        event_bus.subscribe("UPDATE_DOWNLOADED", _on_downloaded)
        event_bus.subscribe("UPDATE_INSTALLED", _on_installed)
        event_bus.subscribe("UPDATE_FAILED", _on_failed)

    # ── Hit rects (AppKit coords: origin at bottom-left) ──────────────────────
    @objc.python_method
    def _card_rect(self) -> AppKit.NSRect:
        return AppKit.NSMakeRect(6.0, 6.0, CARD_W, CARD_H)

    @objc.python_method
    def _join_rect(self) -> AppKit.NSRect:
        if self.install_mode:
            return AppKit.NSMakeRect(0, 0, 0, 0)
        card_x = 6.0
        card_y = 6.0
        btn_y = card_y + 14.0
        btn_x0 = card_x + 16.0
        return AppKit.NSMakeRect(btn_x0, btn_y, BTN_JOIN_W, BTN_H)

    @objc.python_method
    def _snooze_rect(self) -> AppKit.NSRect:
        if self.install_mode:
            return AppKit.NSMakeRect(0, 0, 0, 0)
        card_x = 6.0
        card_y = 6.0
        btn_y = card_y + 14.0
        btn_x0 = card_x + 16.0
        return AppKit.NSMakeRect(btn_x0 + BTN_JOIN_W + 8.0, btn_y, BTN_SMALL_W, BTN_H)

    @objc.python_method
    def _close_rect(self) -> AppKit.NSRect:
        card_x = 6.0
        card_y = 6.0
        s = 22.0
        return AppKit.NSMakeRect(card_x + CARD_W - s - 10.0, card_y + CARD_H - s - 10.0, s, s)

    @objc.python_method
    def _progress_rect(self) -> AppKit.NSRect:
        card_x = 6.0
        card_y = 6.0
        return AppKit.NSMakeRect(card_x + 16.0, card_y + 14.0, CARD_W - 32.0, BTN_H)

    # ── Animation Timer Callback ──────────────────────────────────────────────
    def stepAnimation_(self, timer):
        self.tick += 1

        if self.controller and getattr(self.controller, "is_closing", False):
            # Smoothly slide UP out of the screen
            self.controller.curr_y += 18.0
            if self.controller.window:
                self.controller.window.setFrame_display_(
                    AppKit.NSMakeRect(self.controller.x_pos, self.controller.curr_y, self.controller.window_w, self.controller.window_h),
                    True
                )
            if self.controller.curr_y > getattr(self.controller, "screen_top", 1000.0) + 20.0:
                self.controller.finish_dismiss()
            return

        if self.controller and getattr(self.controller, "is_animating_in", False):
            # Smoothly slide DOWN onto the screen with responsive easing
            dist = self.controller.curr_y - self.controller.final_y
            step = max(3.0, dist * 0.22)
            self.controller.curr_y = max(self.controller.final_y, self.controller.curr_y - step)
            if self.controller.window:
                self.controller.window.setFrame_display_(
                    AppKit.NSMakeRect(self.controller.x_pos, self.controller.curr_y, self.controller.window_w, self.controller.window_h),
                    True
                )
            if self.controller.curr_y <= self.controller.final_y:
                self.controller.is_animating_in = False

        self.setNeedsDisplay_(True)

    # ── Mouse Tracking & Clicks ───────────────────────────────────────────────
    def _safe_set_cursor(self, pointing_hand: bool = False):
        try:
            cursor = AppKit.NSCursor.pointingHandCursor() if pointing_hand else AppKit.NSCursor.arrowCursor()
            if cursor is not None and hasattr(cursor, "set"):
                cursor.set()
        except Exception:
            pass

    def mouseMoved_(self, event):
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        old = self._hover_target
        if AppKit.NSPointInRect(p, self._close_rect()):
            self._hover_target = "close"
            self.is_paused = True
            self._safe_set_cursor(pointing_hand=True)
        elif AppKit.NSPointInRect(p, self._join_rect()):
            self._hover_target = "join"
            self.is_paused = True
            self._safe_set_cursor(pointing_hand=True)
        elif AppKit.NSPointInRect(p, self._snooze_rect()):
            self._hover_target = "snooze"
            self.is_paused = True
            self._safe_set_cursor(pointing_hand=True)
        elif AppKit.NSPointInRect(p, self._card_rect()):
            self._hover_target = None
            self.is_paused = True
            self._safe_set_cursor(pointing_hand=False)
        else:
            self._hover_target = None
            self.is_paused = False
            self._safe_set_cursor(pointing_hand=False)

        if hasattr(self.controller, "is_paused"):
            self.controller.is_paused = self.is_paused

        if old != self._hover_target:
            self.setNeedsDisplay_(True)

    def mouseEntered_(self, event):
        self.is_paused = True
        if hasattr(self.controller, "is_paused"):
            self.controller.is_paused = True
        self.setNeedsDisplay_(True)

    def mouseExited_(self, event):
        self.is_paused = False
        self._hover_target = None
        if hasattr(self.controller, "is_paused"):
            self.controller.is_paused = False
        self._safe_set_cursor(pointing_hand=False)
        self.setNeedsDisplay_(True)

    def mouseDown_(self, event):
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        if AppKit.NSPointInRect(p, self._close_rect()):
            self.controller.dismiss()
        elif AppKit.NSPointInRect(p, self._snooze_rect()):
            self.controller.dismiss()
        elif AppKit.NSPointInRect(p, self._join_rect()):
            if not self.install_mode:
                self.install_mode = True
                self.setNeedsDisplay_(True)
                updater_service.download_and_install_update(background=True)

    # ── Drawing ───────────────────────────────────────────────────────────────
    def drawRect_(self, dirtyRect):
        context = AppKit.NSGraphicsContext.currentContext().CGContext()
        card_rect = self._card_rect()
        cx = card_rect.origin.x
        cy = card_rect.origin.y

        # ── Card Background ──
        path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(card_rect, CARD_R, CARD_R)
        Theme.BASE.setFill()
        path.fill()

        # ── Animated Sweep Border (Blue to Mauve) ──
        speed_mult = 5.0 if self.install_mode else 1.0
        phase = (math.sin(self.tick * 0.04 * speed_mult) + 1.0) / 2.0  # 0.0 to 1.0

        c_blue = Theme.BLUE
        c_mauve = Theme.MAUVE
        r_blend = (1.0 - phase) * c_blue.redComponent() + phase * c_mauve.redComponent()
        g_blend = (1.0 - phase) * c_blue.greenComponent() + phase * c_mauve.greenComponent()
        b_blend = (1.0 - phase) * c_blue.blueComponent() + phase * c_mauve.blueComponent()
        sweep_col = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(r_blend, g_blend, b_blend, 1.0)

        sweep_col.setStroke()
        path.setLineWidth_(2.2)
        path.stroke()

        # ── Row 1: Provider Pill + Close Button ──
        pill_y = cy + CARD_H - 34.0
        pill_x = cx + 14.0
        prov_label = self.provider.upper()[:24]

        # Calculate pill width
        f_pill = AppKit.NSFont.boldSystemFontOfSize_(9.5)
        pill_attrs = {
            AppKit.NSFontAttributeName: f_pill,
            AppKit.NSForegroundColorAttributeName: Theme.TEXT
        }
        pill_str = AppKit.NSString.stringWithString_(prov_label)
        pill_text_sz = pill_str.sizeWithAttributes_(pill_attrs)
        pill_w = pill_text_sz.width + 36.0
        pill_h = 22.0

        pill_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            AppKit.NSMakeRect(pill_x, pill_y, pill_w, pill_h), 11.0, 11.0
        )
        Theme.SURFACE0.setFill()
        pill_path.fill()

        # Dot
        dot_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(
            AppKit.NSMakeRect(pill_x + 8.0, pill_y + 7.0, 8.0, 8.0)
        )
        Theme.BLUE.setFill()
        dot_path.fill()

        # Pill text
        pill_str.drawAtPoint_withAttributes_(
            AppKit.NSMakePoint(pill_x + 22.0, pill_y + 4.0),
            pill_attrs
        )

        # Close Button ✕
        cr = self._close_rect()
        close_hover = (self._hover_target == "close")
        close_path = AppKit.NSBezierPath.bezierPathWithOvalInRect_(cr)
        if close_hover:
            AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.95, 0.35, 0.45, 0.95).setFill()
        else:
            AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.8, 0.84, 0.96, 0.12).setFill()
        close_path.fill()

        c_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(10.5),
            AppKit.NSForegroundColorAttributeName: Theme.CRUST if close_hover else Theme.SUBTEXT0
        }
        c_str = AppKit.NSString.stringWithString_("✕")
        c_sz = c_str.sizeWithAttributes_(c_attrs)
        c_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(cr.origin.x + (cr.size.width - c_sz.width)/2.0, cr.origin.y + (cr.size.height - c_sz.height)/2.0), c_attrs)

        # ── Row 2: Title ──
        t_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(15.0),
            AppKit.NSForegroundColorAttributeName: Theme.TEXT
        }
        title_str = AppKit.NSString.stringWithString_(self.title)
        title_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(cx + 14.0, cy + CARD_H - 64.0), t_attrs)

        # ── Row 3: Subtitle ──
        s_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(10.5),
            AppKit.NSForegroundColorAttributeName: Theme.SUBTEXT0
        }
        sub_str = AppKit.NSString.stringWithString_("⚡ Ready to download & install update")
        sub_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(cx + 14.0, cy + CARD_H - 86.0), s_attrs)

        # ── Row 4: Action Buttons or Installation Mode Progress ──
        if self.install_mode:
            pr = self._progress_rect()
            p_bg = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(pr, 10.0, 10.0)
            Theme.MANTLE.setFill()
            p_bg.fill()

            if self.install_progress > 0:
                fill_w = (CARD_W - 32.0) * (self.install_progress / 100.0)
                fill_r = AppKit.NSMakeRect(pr.origin.x, pr.origin.y, fill_w, pr.size.height)
                p_fill = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(fill_r, 10.0, 10.0)
                
                # Gradient fill Blue -> Mauve
                grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(Theme.BLUE, Theme.MAUVE)
                grad.drawInBezierPath_angle_(p_fill, 0.0)

            # Centered status text
            stat_attrs = {
                AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(11.5),
                AppKit.NSForegroundColorAttributeName: Theme.CRUST if (self.install_progress >= 75 or self.install_ready) else Theme.TEXT
            }
            if self.install_ready:
                txt = "✅ Update Installed! Relaunching..."
            else:
                txt = f"{self.install_step} {int(self.install_progress)}%"
            stat_str = AppKit.NSString.stringWithString_(txt)
            stat_sz = stat_str.sizeWithAttributes_(stat_attrs)
            stat_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(pr.origin.x + (pr.size.width - stat_sz.width)/2.0, pr.origin.y + (pr.size.height - stat_sz.height)/2.0), stat_attrs)
            return

        # Normal Buttons Mode
        jr = self._join_rect()
        join_hover = (self._hover_target == "join")
        join_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(jr, 10.0, 10.0)

        # Gradient Join Button
        start_c = Theme.BLUE if join_hover else Theme.SAPPHIRE
        end_c = Theme.MAUVE if join_hover else Theme.BLUE
        btn_grad = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(start_c, end_c)
        btn_grad.drawInBezierPath_angle_(join_path, 0.0)

        j_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(11.5),
            AppKit.NSForegroundColorAttributeName: Theme.CRUST
        }
        btn_str = AppKit.NSString.stringWithString_(self.btn_text)
        btn_sz = btn_str.sizeWithAttributes_(j_attrs)
        btn_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(jr.origin.x + (jr.size.width - btn_sz.width)/2.0, jr.origin.y + (jr.size.height - btn_sz.height)/2.0), j_attrs)

        # Snooze Button (✕ Later)
        sr = self._snooze_rect()
        snz_hover = (self._hover_target == "snooze")
        snz_path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(sr, 10.0, 10.0)
        if snz_hover:
            AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.27, 0.28, 0.38, 0.7).setFill()
        else:
            Theme.SURFACE0.setFill()
        snz_path.fill()

        s_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(10.5),
            AppKit.NSForegroundColorAttributeName: Theme.TEXT if snz_hover else Theme.SUBTEXT0
        }
        snz_str = AppKit.NSString.stringWithString_("✕ Later")
        snz_sz = snz_str.sizeWithAttributes_(s_attrs)
        snz_str.drawAtPoint_withAttributes_(AppKit.NSMakePoint(sr.origin.x + (sr.size.width - snz_sz.width)/2.0, sr.origin.y + (sr.size.height - snz_sz.height)/2.0), s_attrs)
