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
from ui.macos.theme import Theme
from ui.macos.components.button import ModernButton

logger = logging.getLogger("FlightDeck.AddressAutocompleteView")


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

        self.is_editing = not bool(self.initial_value_str)
        self._build_ui(frame)

        if self.initial_value_str:
            self._update_confirmed_row(None, self.initial_value_str)
            self.set_editing(False)
            self._verify_initial_address(self.initial_value_str)
        else:
            self.set_editing(True)

        return self

    def _build_ui(self, frame):
        w = frame.size.width
        h = frame.size.height

        row_h = 28.0
        row_y = max(0.0, (h - row_h) * 0.5)

        # =========================================================================
        # 1. EDITING CONTAINER (Shown when editing or no address saved)
        # =========================================================================
        self.edit_container = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, w, h))
        self.addSubview_(self.edit_container)

        btn_save_w = 80.0
        btn_map_w = 32.0
        gap = 8.0
        field_w = w - btn_save_w - btn_map_w - (gap * 2)

        # 1A. Text input field
        field_y = row_y
        self.text_field = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(0, field_y, field_w, row_h)
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
        self.edit_container.addSubview_(self.text_field)

        # 1B. Icon-only Map Button (subdued secondary action)
        self.map_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(field_w + gap, field_y, btn_map_w, row_h),
            title="🗺️",
            start_color=Theme.SURFACE1,
            end_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            corner_radius=8.0,
            font_size=12.0,
            bold=False
        )
        self.map_btn.layer().setBorderWidth_(1.0)
        self.map_btn.layer().setBorderColor_(Theme.SURFACE2.CGColor())
        self.map_btn.setTarget_(self)
        self.map_btn.setAction_("onOpenMap:")
        self.edit_container.addSubview_(self.map_btn)

        # 1C. High-Contrast Save Button (primary action)
        if self.btn_start_color == Theme.MAUVE:
            start_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.545, 0.361, 0.965, 1.0)  # #8b5cf6
            end_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.486, 0.227, 0.929, 1.0)    # #7c3aed
            border_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.655, 0.545, 0.980, 0.9)
        else:
            start_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.133, 0.773, 0.369, 1.0)  # #22c55e
            end_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.086, 0.639, 0.290, 1.0)    # #16a34a
            border_c = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(0.290, 0.871, 0.502, 0.9)

        self.save_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(field_w + gap + btn_map_w + gap, field_y, btn_save_w, row_h),
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
        self.edit_container.addSubview_(self.save_btn)
        self._set_save_btn_title(f"💾 {t('save')}")

        # 1D. Status line kept hidden for backwards-compatibility; status messages render in floating overlay
        self.status_label = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSZeroRect)
        self.status_label.setHidden_(True)

        # =========================================================================
        # 2. CONFIRMED CONTAINER (Compact single-row result card when saved)
        # =========================================================================
        self.confirmed_container = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, row_y, w, row_h))
        self.confirmed_container.setWantsLayer_(True)
        self.confirmed_container.layer().setBackgroundColor_(Theme.MANTLE.CGColor())
        self.confirmed_container.layer().setCornerRadius_(8.0)
        self.confirmed_container.layer().setBorderWidth_(1.0)
        self.confirmed_container.layer().setBorderColor_(Theme.SURFACE0.CGColor())
        self.addSubview_(self.confirmed_container)

        btn_edit_w = 58.0
        c_map_w = 28.0
        c_gap = 6.0
        label_w = w - btn_edit_w - c_map_w - (c_gap * 3) - 10.0

        # Confirmed label: "✓ Politecnico (Corso Duca degli Abruzzi) · Torino, 10129"
        self.confirmed_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(10, 4, label_w, 20.0)
        )
        self.confirmed_label.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        self.confirmed_label.setBezeled_(False)
        self.confirmed_label.setDrawsBackground_(False)
        self.confirmed_label.setEditable_(False)
        self.confirmed_label.setSelectable_(False)
        self.confirmed_label.setLineBreakMode_(AppKit.NSLineBreakByTruncatingTail)
        self.confirmed_container.addSubview_(self.confirmed_label)

        # Quick Map Icon button on confirmed row
        self.confirmed_map_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(w - btn_edit_w - c_map_w - c_gap - 4, 3, c_map_w, 22.0),
            title="🗺️",
            start_color=Theme.SURFACE0,
            end_color=Theme.CRUST,
            text_color=Theme.TEXT,
            corner_radius=6.0,
            font_size=11.0,
            bold=False
        )
        self.confirmed_map_btn.layer().setBorderWidth_(1.0)
        self.confirmed_map_btn.layer().setBorderColor_(Theme.SURFACE1.CGColor())
        self.confirmed_map_btn.setTarget_(self)
        self.confirmed_map_btn.setAction_("onOpenMap:")
        self.confirmed_container.addSubview_(self.confirmed_map_btn)

        # Edit text button: "✏️ Edit"
        edit_title = f"✏️ {t('settings_address_edit')}"
        self.edit_btn = Theme.create_gradient_button(
            AppKit.NSMakeRect(w - btn_edit_w - 4, 3, btn_edit_w, 22.0),
            title=edit_title,
            start_color=Theme.SURFACE1,
            end_color=Theme.SURFACE0,
            text_color=Theme.TEXT,
            corner_radius=6.0,
            font_size=11.0,
            bold=False
        )
        self.edit_btn.layer().setBorderWidth_(1.0)
        self.edit_btn.layer().setBorderColor_(Theme.SURFACE2.CGColor())
        self.edit_btn.setTarget_(self)
        self.edit_btn.setAction_("onEditClicked:")
        self.confirmed_container.addSubview_(self.edit_btn)

    # Continuous keystroke delegate: user can keep typing without interruption!
    def controlTextDidChange_(self, notification):
        if self._search_timer:
            self._search_timer.invalidate()
            self._search_timer = None

        self._search_timer = AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.35, self, "onDebouncedSearch:", None, False
        )

    def _display_message_overlay(self, message: str, is_error: bool = False):
        parent_window = self.window()
        if not parent_window or not self.superview():
            return

        field_rect_in_window = self.convertRect_toView_(self.text_field.frame(), None)
        field_rect_on_screen = parent_window.convertRectToScreen_(field_rect_in_window)

        overlay_w = max(360.0, self.text_field.frame().size.width)
        overlay_h = 36.0

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
        else:
            self._overlay_window.setFrame_display_(screen_rect, True)

        self._overlay_window.setIgnoresMouseEvents_(True)

        content_view = AppKit.NSView.alloc().initWithFrame_(AppKit.NSMakeRect(0, 0, overlay_w, overlay_h))
        content_view.setWantsLayer_(True)
        content_view.layer().setBackgroundColor_(Theme.CRUST.CGColor())
        content_view.layer().setCornerRadius_(8.0)
        content_view.layer().setBorderWidth_(1.0)
        border_col = Theme.PEACH if is_error else Theme.SURFACE1
        content_view.layer().setBorderColor_(border_col.CGColor())

        msg_lbl = AppKit.NSTextField.alloc().initWithFrame_(AppKit.NSMakeRect(12.0, 8.0, overlay_w - 24.0, 20.0))
        msg_lbl.setStringValue_(message)
        msg_lbl.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
        msg_lbl.setTextColor_(Theme.PEACH if is_error else Theme.BLUE)
        msg_lbl.setBezeled_(False)
        msg_lbl.setDrawsBackground_(False)
        msg_lbl.setEditable_(False)
        msg_lbl.setSelectable_(False)
        content_view.addSubview_(msg_lbl)

        self._overlay_window.setContentView_(content_view)
        parent_window.addChildWindow_ordered_(self._overlay_window, AppKit.NSWindowAbove)
        self._overlay_window.orderFront_(None)

    @objc.IBAction
    def onDebouncedSearch_(self, timer):
        query = str(self.text_field.stringValue() or "").strip()
        if len(query) < 3:
            self._close_overlay()
            return

        self._display_message_overlay(t("settings_address_searching"), is_error=False)

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
            self._display_message_overlay(t("settings_address_not_found"), is_error=True)
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
            self._overlay_window.setIgnoresMouseEvents_(False)

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

    def viewWillMoveToWindow_(self, new_window):
        if new_window is None:
            self._close_overlay()
        objc.super(AddressAutocompleteView, self).viewWillMoveToWindow_(new_window)


    def close_suggestions(self):
        self._close_overlay()

    def _close_overlay(self):
        if self._search_timer:
            self._search_timer.invalidate()
            self._search_timer = None
        if self._overlay_window:
            parent_window = self.window()
            if parent_window and self._overlay_window in (parent_window.childWindows() or []):
                try:
                    parent_window.removeChildWindow_(self._overlay_window)
                except Exception:
                    pass
            try:
                self._overlay_window.orderOut_(None)
            except Exception:
                pass
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

    @objc.python_method
    def set_editing(self, is_editing: bool):
        self.is_editing = is_editing
        self.edit_container.setHidden_(not is_editing)
        self.confirmed_container.setHidden_(is_editing)
        if not is_editing:
            self._close_overlay()
            self._set_status("")

    @objc.IBAction
    def onEditClicked_(self, sender):
        self.set_editing(True)
        w = self.window()
        if w:
            w.makeFirstResponder_(self.text_field)
            self.text_field.selectText_(None)

    def _update_confirmed_row(self, candidate: Optional[AddressCandidate], raw_text: str = ""):
        short_addr = ""
        secondary = ""
        if candidate:
            short_addr = candidate.short_address or candidate.display_name or raw_text
            parts = []
            if candidate.city:
                parts.append(candidate.city)
            if candidate.postcode:
                parts.append(candidate.postcode)
            secondary = ", ".join(parts)
        elif raw_text:
            short_addr = raw_text.split(",")[0].strip()
            parts = [p.strip() for p in raw_text.split(",")[1:] if p.strip()]
            secondary = ", ".join(parts[:2])

        attr_str = AppKit.NSMutableAttributedString.alloc().init()

        # 1. Green checkmark
        check_attrs = {
            AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(12.0),
            AppKit.NSForegroundColorAttributeName: Theme.GREEN
        }
        attr_str.appendAttributedString_(
            AppKit.NSAttributedString.alloc().initWithString_attributes_("✓  ", check_attrs)
        )

        # 2. Venue / Street Name (Bold text)
        if short_addr:
            main_attrs = {
                AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(12.0),
                AppKit.NSForegroundColorAttributeName: Theme.TEXT
            }
            attr_str.appendAttributedString_(
                AppKit.NSAttributedString.alloc().initWithString_attributes_(short_addr, main_attrs)
            )

        # 3. Secondary City / Postcode (Dimmed subtext)
        if secondary:
            sub_attrs = {
                AppKit.NSFontAttributeName: AppKit.NSFont.systemFontOfSize_(11.0),
                AppKit.NSForegroundColorAttributeName: Theme.SUBTEXT0
            }
            attr_str.appendAttributedString_(
                AppKit.NSAttributedString.alloc().initWithString_attributes_(f"  ·  {secondary}", sub_attrs)
            )

        self.confirmed_label.setAttributedStringValue_(attr_str)

    def _set_status(self, text: str, status_type: str = "hint"):
        if not text:
            self._close_overlay()
            return

        if status_type == "searching":
            self._display_message_overlay(text, is_error=False)
        elif status_type == "error":
            self._display_message_overlay(text, is_error=True)
            self.text_field.layer().setBorderColor_(Theme.RED.CGColor())
        else:
            self._close_overlay()

    def select_candidate(self, candidate: AddressCandidate):
        self._close_overlay()
        self.current_candidate = candidate

        chosen_text = candidate.short_address or candidate.display_name
        self.text_field.setStringValue_(chosen_text)
        self.text_field.layer().setBorderColor_(Theme.GREEN.CGColor())

        self._update_confirmed_row(candidate, chosen_text)
        self._set_save_btn_title(f"✓ {t('saved')}", is_saved=True)

        def _transition_to_confirmed():
            self._set_save_btn_title(f"💾 {t('save')}")
            self.set_editing(False)

        AppKit.NSTimer.scheduledTimerWithTimeInterval_repeats_block_(
            0.5, False, lambda timer: _transition_to_confirmed()
        )

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
            self._set_status("")
            self.text_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
            self._update_confirmed_row(None, "")
            self.set_editing(True)
            if self.on_save_cb:
                self.on_save_cb("", None)
            return

        self._set_status(t("settings_address_searching"), "searching")
        self._set_save_btn_title("⏳ ...")

        def _verify():
            is_valid, cand, err = address_service.verify_address(query)

            def _done():
                self._set_save_btn_title(f"💾 {t('save')}")
                if is_valid and cand:
                    self.select_candidate(cand)
                else:
                    self.current_candidate = None
                    self._set_status(f"❌ {t('settings_address_not_found')}", "error")
                    self.text_field.layer().setBorderColor_(Theme.RED.CGColor())
                    self.set_editing(True)
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
                    self._update_confirmed_row(cand, addr)
                    self.text_field.layer().setBorderColor_(Theme.GREEN.CGColor())
                    if not self.is_editing:
                        self.set_editing(False)

            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_update)

        threading.Thread(target=_verify, daemon=True).start()

    @objc.IBAction
    def onOpenMap_(self, sender):
        query = str(self.text_field.stringValue() or "").strip()
        if not query and self.current_candidate:
            query = self.current_candidate.display_name or self.current_candidate.short_address
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
            self._update_confirmed_row(None, addr)
            self.set_editing(False)
            self._verify_initial_address(addr)
        else:
            self.current_candidate = None
            self._update_confirmed_row(None, "")
            self.set_editing(True)
            self._set_status("")
            self.text_field.layer().setBorderColor_(Theme.SURFACE0.CGColor())
