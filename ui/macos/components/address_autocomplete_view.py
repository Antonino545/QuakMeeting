"""
Address Autocomplete Component for macOS AppKit (Google Maps style).
Provides continuous, non-interrupting search-as-you-type suggestions
using a non-activating floating overlay window, instant geocoding verification,
and direct Apple Maps preview.
"""
import threading
import logging
import AppKit
import objc
from typing import Optional, Callable, List

from core.services.address_service import address_service, AddressCandidate, AddressService
from core.services.language_service import t
from ui.macos.theme import Theme, ModernButton

logger = logging.getLogger("QuakMeeting.AddressAutocompleteView")


class NonActivatingSuggestionsWindow(AppKit.NSWindow):
    """
    Floating borderless window for suggestions that NEVER steals key or main focus,
    allowing the user to type continuously in the text field like Google Maps.
    """
    def canBecomeKeyWindow(self):
        return False

    def canBecomeMainWindow(self):
        return False


class SuggestionRowButton(ModernButton):
    """Sleek suggestion item row with primary street and secondary city/region."""
    def initWithCandidate_target_action_(self, candidate: AddressCandidate, target, action):
        self = objc.super(SuggestionRowButton, self).init()
        if self is None:
            return None
        self.candidate = candidate
        self.setTarget_(target)
        self.setAction_(action)
        self.setBordered_(False)
        self.setWantsLayer_(True)
        self.layer().setCornerRadius_(6.0)
        self.layer().setBackgroundColor_(Theme.MANTLE.CGColor())

        title_text = f"📍  {candidate.short_address}"
        secondary = []
        if candidate.city:
            secondary.append(candidate.city)
        if candidate.state:
            secondary.append(candidate.state)
        elif candidate.country:
            secondary.append(candidate.country)

        if secondary:
            title_text += f"   ({', '.join(secondary)})"

        self.setTitle_(title_text)
        self.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.setAlignment_(AppKit.NSTextAlignmentLeft)
        return self

    def mouseEntered_(self, event):
        if self.layer():
            self.layer().setBackgroundColor_(Theme.SURFACE1.CGColor())
        objc.super(SuggestionRowButton, self).mouseEntered_(event)

    def mouseExited_(self, event):
        if self.layer():
            self.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        objc.super(SuggestionRowButton, self).mouseExited_(event)


class AddressAutocompleteView(AppKit.NSView):
    """
    Modern Google Maps-style address bar.
    - Full-width typing with continuous keystroke debouncing (350ms).
    - Floating suggestions overlay directly underneath that NEVER steals focus.
    - Integrated [🗺️ Map] and [💾 Save] action buttons.
    - Dynamic verification badge with canonical address.
    """

    def initWithFrame_placeholder_initialValue_onSave_btnColor_(
        self,
        frame,
        placeholder: str,
        initial_value: str,
        on_save_cb: Optional[Callable[[str, Optional[AddressCandidate]], None]] = None,
        btn_start_color=None,
        btn_end_color=None
    ):
        self = objc.super(AddressAutocompleteView, self).initWithFrame_(frame)
        if self is None:
            return None

        self.placeholder_str = placeholder
        self.initial_value_str = initial_value or ""
        self.on_save_cb = on_save_cb
        self.btn_start_color = btn_start_color or Theme.GREEN
        self.btn_end_color = btn_end_color or Theme.TEAL

        self.current_candidate: Optional[AddressCandidate] = None
        self._search_timer = None
        self._overlay_window: Optional[NonActivatingSuggestionsWindow] = None
        self._candidates: List[AddressCandidate] = []

        self._build_ui(frame)

        if self.initial_value_str:
            self._verify_initial_address(self.initial_value_str)

        return self

    def _build_ui(self, frame):
        w = frame.size.width
        h = frame.size.height

        btn_save_w = 88.0
        btn_map_w = 72.0
        gap = 8.0
        field_w = w - btn_save_w - btn_map_w - (gap * 2)

        # 1. Main Search Field (Google Maps style)
        field_y = max(20.0, h - 28.0)
        self.text_field = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(0, field_y, field_w, 28.0)
        )
        self.text_field.setStringValue_(self.initial_value_str)
        self.text_field.setPlaceholderString_(self.placeholder_str)
        self.text_field.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.text_field.setTextColor_(Theme.TEXT)
        self.text_field.setWantsLayer_(True)
        self.text_field.layer().setCornerRadius_(8.0)
        self.text_field.setBackgroundColor_(Theme.CRUST)
        self.text_field.setDrawsBackground_(True)
        self.text_field.layer().setBorderWidth_(1.0)
        self.text_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        self.text_field.setFocusRingType_(AppKit.NSFocusRingTypeNone)
        self.text_field.setTarget_(self)
        self.text_field.setAction_("onSaveClicked:")
        self.text_field.setDelegate_(self)
        self.addSubview_(self.text_field)

        # 2. View Map Button
        self.map_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(field_w + gap, field_y, btn_map_w, 28.0),
            title=t("settings_address_view_map"),
            start_color=Theme.SURFACE1,
            end_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            corner_radius=8.0,
            font_size=11.5,
            bold=False
        )
        self.map_btn.layer().setBorderWidth_(1.0)
        self.map_btn.layer().setBorderColor_(Theme.SURFACE2.CGColor())
        self.map_btn.setTarget_(self)
        self.map_btn.setAction_("onOpenMap:")
        self.addSubview_(self.map_btn)

        # 3. High-Contrast Save Button (Pure white text, saturated vibrant gradient + luminous border)
        if self.btn_start_color == Theme.MAUVE:
            # Saturated Violet/Purple for Exam Campus
            start_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.545, 0.361, 0.965, 1.0)  # #8b5cf6
            end_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.486, 0.227, 0.929, 1.0)    # #7c3aed
            border_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.655, 0.545, 0.980, 0.9)
        else:
            # Saturated Emerald/Green for Starting Address
            start_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.133, 0.773, 0.369, 1.0)  # #22c55e
            end_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.086, 0.639, 0.290, 1.0)    # #16a34a
            border_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.290, 0.871, 0.502, 0.9)

        self.save_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(field_w + gap + btn_map_w + gap, field_y, btn_save_w, 28.0),
            title=f"💾 {t('save')}",
            start_color=start_c,
            end_color=end_c,
            text_color=AppKit.NSColor.whiteColor(),
            corner_radius=8.0,
            font_size=11.5,
            bold=True
        )
        self.save_btn.layer().setBorderWidth_(1.0)
        self.save_btn.layer().setBorderColor_(border_c.CGColor())
        self.save_btn.setTarget_(self)
        self.save_btn.setAction_("onSaveClicked:")
        self.addSubview_(self.save_btn)
        self._set_save_btn_title(f"💾 {t('save')}")

        # 4. Status & Canonical Address Preview with High Contrast
        status_y = 0.0
        status_h = max(16.0, field_y - 2.0)
        self.status_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(2, status_y, w - 4, status_h)
        )
        self.status_label.setStringValue_(t("settings_address_suggest_hint"))
        self.status_label.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        self.status_label.setTextColor_(Theme.TEXT)
        self.status_label.setBezeled_(False)
        self.status_label.setDrawsBackground_(False)
        self.status_label.setEditable_(False)
        self.status_label.setSelectable_(True)
        self.status_label.setLineBreakMode_(AppKit.NSLineBreakByTruncatingTail)
        self.addSubview_(self.status_label)

    # Continuous keystroke delegate: user can keep typing without interruption!
    def controlTextDidChange_(self, notification):
        if self._search_timer:
            self._search_timer.invalidate()
            self._search_timer = None

        self._search_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.35, self, "onDebouncedSearch:", None, False
        )

    @objc.IBAction
    def onDebouncedSearch_(self, timer):
        query = str(self.text_field.stringValue() or "").strip()
        if len(query) < 3:
            self._close_overlay()
            self.status_label.setStringValue_(t("settings_address_suggest_hint"))
            self.status_label.setTextColor_(Theme.SUBTEXT0)
            return

        self.status_label.setStringValue_(t("settings_address_searching"))
        self.status_label.setTextColor_(Theme.BLUE)

        def _worker():
            candidates = address_service.search_suggestions(query, limit=4)

            def _update():
                # Make sure the query hasn't changed since request began
                curr = str(self.text_field.stringValue() or "").strip()
                if curr == query:
                    self._display_suggestions(candidates)

            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_update)

        threading.Thread(target=_worker, daemon=True).start()

    def _display_suggestions(self, candidates: List[AddressCandidate]):
        self._candidates = candidates
        if not candidates:
            self._close_overlay()
            self.status_label.setStringValue_(t("settings_address_not_found"))
            self.status_label.setTextColor_(Theme.PEACH)
            return

        parent_window = self.window()
        if not parent_window or not self.superview():
            return

        # Calculate exact screen coordinates for overlay placement directly beneath text field
        field_rect_in_window = self.convertRect_toView_(self.text_field.frame(), None)
        field_rect_on_screen = parent_window.convertRectToScreen_(field_rect_in_window)

        row_h = 32.0
        overlay_w = max(360.0, self.text_field.frame().size.width)
        overlay_h = max(38.0, len(candidates) * row_h + 8.0)

        overlay_x = field_rect_on_screen.origin.x
        overlay_y = field_rect_on_screen.origin.y - overlay_h - 4.0

        screen_rect = AppKit.NSMakeRect(overlay_x, overlay_y, overlay_w, overlay_h)

        if self._overlay_window is None:
            self._overlay_window = NonActivatingSuggestionsWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                screen_rect,
                AppKit.NSWindowStyleMaskBorderless,
                AppKit.NSBackingStoreBuffered,
                False
            )
            self._overlay_window.setOpaque_(False)
            self._overlay_window.setBackgroundColor_(AppKit.NSColor.clearColor())
            self._overlay_window.setHasShadow_(True)
            self._overlay_window.setLevel_(AppKit.NSFloatingWindowLevel)
            self._overlay_window.setIgnoresMouseEvents_(False)
        else:
            self._overlay_window.setFrame_display_(screen_rect, True)

        # Build clean Catppuccin Mocha container view
        content_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, overlay_w, overlay_h))
        content_view.setWantsLayer_(True)
        content_view.layer().setBackgroundColor_(Theme.CRUST.CGColor())
        content_view.layer().setCornerRadius_(10.0)
        content_view.layer().setBorderWidth_(1.0)
        content_view.layer().setBorderColor_(Theme.SURFACE1.CGColor())

        for idx, cand in enumerate(candidates):
            btn_y = overlay_h - ((idx + 1) * row_h) - 4.0
            row_btn = SuggestionRowButton.alloc().initWithCandidate_target_action_(
                cand, self, "onSelectSuggestionRow:"
            )
            row_btn.setFrame_(AppKit.NSMakeRect(6.0, btn_y, overlay_w - 12.0, row_h - 2.0))
            row_btn.tag = idx
            content_view.addSubview_(row_btn)

        self._overlay_window.setContentView_(content_view)
        parent_window.addChildWindow_ordered_(self._overlay_window, AppKit.NSWindowAbove)
        self._overlay_window.orderFront_(None)

    def _close_overlay(self):
        if self._overlay_window:
            parent_window = self.window()
            if parent_window and self._overlay_window in (parent_window.childWindows() or []):
                parent_window.removeChildWindow_(self._overlay_window)
            self._overlay_window.orderOut_(None)
            self._overlay_window = None

    @objc.IBAction
    def onSelectSuggestionRow_(self, sender):
        idx = getattr(sender, "tag", 0)
        if 0 <= idx < len(self._candidates):
            cand = self._candidates[idx]
            self.select_candidate(cand)

    def _set_save_btn_title(self, title_str: str, is_saved: bool = False):
        try:
            self.save_btn.setTitle_(title_str)
            text_color = AppKit.NSColor.whiteColor()
            fnt = AppKit.NSFont.boldSystemFontOfSize_(11.5)
            attrs = {
                AppKit.NSForegroundColorAttributeName: text_color,
                AppKit.NSFontAttributeName: fnt
            }
            attr_title = AppKit.NSAttributedString.alloc().initWithString_attributes_(title_str, attrs)
            self.save_btn.setAttributedTitle_(attr_title)
        except Exception:
            pass

    def _set_status(self, text: str, status_type: str = "hint"):
        self.status_label.setStringValue_(text)
        if status_type == "verified":
            self.status_label.setTextColor_(Theme.GREEN)
            self.status_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        elif status_type == "searching":
            self.status_label.setTextColor_(Theme.SKY)
            self.status_label.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))
        elif status_type == "error":
            self.status_label.setTextColor_(Theme.RED)
            self.status_label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(11.5))
        else:  # "hint"
            self.status_label.setTextColor_(Theme.TEXT)
            self.status_label.setFont_(AppKit.NSFont.systemFontOfSize_(11.5))

    def select_candidate(self, candidate: AddressCandidate):
        self._close_overlay()
        self.current_candidate = candidate

        # Use clean formatted address
        chosen_text = candidate.display_name or candidate.short_address
        self.text_field.setStringValue_(chosen_text)
        self.text_field.layer().setBorderColor_(Theme.GREEN.CGColor())

        status_text = f"🟢 {t('settings_address_verified')}: {candidate.display_name}"
        self._set_status(status_text, "verified")

        self._set_save_btn_title(f"✓ {t('saved')}", is_saved=True)

        def _reset_save_btn():
            try:
                self._set_save_btn_title(f"💾 {t('save')}")
            except Exception:
                pass

        def _delayed():
            import time
            time.sleep(1.5)
            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_reset_save_btn)

        threading.Thread(target=_delayed, daemon=True).start()

        if self.on_save_cb:
            try:
                self.on_save_cb(chosen_text, candidate)
            except Exception as e:
                logger.debug(f"Save callback error: {e}")

    @objc.IBAction
    def onSaveClicked_(self, sender):
        query = str(self.text_field.stringValue() or "").strip()
        self._close_overlay()

        if not query:
            self.current_candidate = None
            self._set_status(t("settings_address_suggest_hint"), "hint")
            self.text_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
            if self.on_save_cb:
                self.on_save_cb("", None)
            self._set_save_btn_title(f"✓ {t('saved')}", is_saved=True)
            return

        self._set_status(t("settings_address_searching"), "searching")
        self._set_save_btn_title("⏳ ...")

        def _verify():
            is_valid, cand, err = address_service.verify_address(query)

            def _done():
                self._set_save_btn_title(f"💾 {t('save')}")
                if is_valid and cand:
                    self.select_candidate(cand)
                elif is_valid and not query:
                    self._set_status(t("settings_address_suggest_hint"), "hint")
                else:
                    self.current_candidate = None
                    self._set_status(f"❌ {t('settings_address_not_found')}", "error")
                    self.text_field.layer().setBorderColor_(Theme.RED.CGColor())
                    if self.on_save_cb:
                        self.on_save_cb(query, None)

            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_done)

        threading.Thread(target=_verify, daemon=True).start()

    def _verify_initial_address(self, addr: str):
        def _verify():
            is_valid, cand, _ = address_service.verify_address(addr)

            def _update():
                if is_valid and cand:
                    self.current_candidate = cand
                    status_text = f"🟢 {t('settings_address_verified')}: {cand.display_name}"
                    self._set_status(status_text, "verified")
                    self.text_field.layer().setBorderColor_(Theme.GREEN.CGColor())

            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_update)

        threading.Thread(target=_verify, daemon=True).start()

    @objc.IBAction
    def onOpenMap_(self, sender):
        query = str(self.text_field.stringValue() or "").strip()
        if not query:
            return

        lat = self.current_candidate.lat if self.current_candidate else None
        lon = self.current_candidate.lon if self.current_candidate else None
        url_str = AddressService.get_map_url(query, lat=lat, lon=lon)

        url = AppKit.NSURL.URLWithString_(url_str)
        if url:
            AppKit.NSWorkspace.sharedWorkspace().openURL_(url)

    def get_address(self) -> str:
        return str(self.text_field.stringValue() or "").strip()

    def set_address(self, addr: str, trigger_save: bool = True):
        self.text_field.setStringValue_(addr or "")
        if trigger_save and addr:
            self.onSaveClicked_(None)
        elif addr:
            self._verify_initial_address(addr)
        else:
            self.current_candidate = None
            self._set_status(t("settings_address_suggest_hint"), "hint")
            self.text_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
