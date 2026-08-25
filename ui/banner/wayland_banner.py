"""
Wayland & X11 Animated Floating HUD Banner for Ubuntu Linux.
Features:
- Cairo-rendered frosted glass card with glowing border
- Animated aircraft tow cable with pilot mascot rendering
- Speech bubble pilot quotes & vibrant action buttons
- Clean window destruction & GTK main quit handling
"""
import sys
import os
import math
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("QuakMeeting.WaylandBanner")

PILOT_QUOTES = {
    "duck": "🚀 Buckle up! Video call starting soon!",
    "chef": "🍕🍽️ Time for dinner & drinks!",
    "captain": "✈️ Prepare for departure & flight!",
    "owl": "📚 University lecture starting!",
    "gym": "🏋️‍♂️ Time to hit the gym & workout!",
    "driver": "🚗 Time to leave for your meeting!",
    "zen_duck": "🌸 Take a deep breath & relax"
}

BANNER_CSS = b"""
.hud-title-lbl {
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
}

.hud-sub-lbl {
    font-size: 12px;
    color: #94a3b8;
}

.hud-btn {
    background: linear-gradient(135deg, #0284c7, #2563eb);
    color: #ffffff;
    font-weight: 800;
    font-size: 12px;
    border-radius: 8px;
    border: none;
    padding: 6px 14px;
}

.hud-btn:hover {
    background: linear-gradient(135deg, #38bdf8, #3b82f6);
}

.hud-close {
    background: rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    font-weight: bold;
    padding: 2px 8px;
}

.hud-close:hover {
    background: rgba(239, 68, 68, 0.4);
    color: #ffffff;
}
"""

_banner_css_loaded = False

def _apply_banner_css():
    global _banner_css_loaded
    if _banner_css_loaded:
        return
    try:
        from gi.repository import Gtk, Gdk
        provider = Gtk.CssProvider()
        provider.load_from_data(BANNER_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        _banner_css_loaded = True
    except Exception:
        pass

def show_wayland_banner(event_data: Dict[str, Any]) -> None:
    """Spawns an animated floating HUD banner with Qt/Cairo pilot rendering on Ubuntu."""
    try:
        from ui.banner.qt_banner import show_qt_banner
        show_qt_banner(event_data)
        return
    except Exception as qt_err:
        logger.info(f"PyQt6 banner unavailable ({qt_err}), falling back to GTK...")

    try:
        import gi
        gi.require_version('Gtk', '3.0')
        try:
            gi.require_version('GtkLayerShell', '0.1')
            from gi.repository import GtkLayerShell
            has_layer_shell = hasattr(GtkLayerShell, 'is_supported') and GtkLayerShell.is_supported()
        except (ValueError, ImportError):
            has_layer_shell = False

        from gi.repository import Gtk, Gdk, GLib
        import cairo
        from ui.banner.cairo_renderers import CairoPilotRenderer
    except Exception as e:
        logger.warning(f"PyGObject / GTK / Cairo not available on this host: {e}")
        return

    _apply_banner_css()

    def _run():
        win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        win.set_title("QuakMeeting HUD Banner")
        win.set_decorated(False)
        win.set_app_paintable(True)

        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual() if screen else None
        if visual and screen.is_composited():
            win.set_visual(visual)

        if has_layer_shell:
            GtkLayerShell.init_for_window(win)
            GtkLayerShell.set_layer(win, GtkLayerShell.Layer.OVERLAY)
            GtkLayerShell.set_anchor(win, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_margin(win, GtkLayerShell.Edge.TOP, 16)
            GtkLayerShell.set_keyboard_mode(win, GtkLayerShell.KeyboardMode.NONE)
        else:
            win.set_keep_above(True)
            win.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
            win.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
            win.set_skip_taskbar_hint(True)
            win.set_skip_pager_hint(True)

        width, height = 580, 96
        win.set_default_size(width, height)

        title = event_data.get("title", "Upcoming Event")
        provider = event_data.get("provider", "Calendar")
        pilot_type = event_data.get("pilot_type", "duck")
        action_btn_text = event_data.get("action_btn_text", "🚀 JOIN")
        action_url = event_data.get("action_url")
        is_update_banner = bool(event_data.get("is_update_banner", False))
        quote_text = event_data.get("quote_text") or PILOT_QUOTES.get(pilot_type, "🚀 Meeting starting soon!")

        tick = [0]

        def draw_canvas(widget, ctx):
            w = widget.get_allocated_width()
            h = widget.get_allocated_height()

            # Clear background
            ctx.set_source_rgba(0, 0, 0, 0)
            ctx.paint()

            # Glass Card Dimensions
            card_x = 10.0 if is_update_banner else 94.0
            card_y = 6.0
            card_w = (w - 20.0) if is_update_banner else (w - 104.0)
            card_h = h - 12.0
            r = 14.0

            # Card Path
            ctx.new_sub_path()
            ctx.arc(card_x + card_w - r, card_y + r, r, -1.570796, 0)
            ctx.arc(card_x + card_w - r, card_y + card_h - r, r, 0, 1.570796)
            ctx.arc(card_x + r, card_y + card_h - r, r, 1.570796, 3.141592)
            ctx.arc(card_x + r, card_y + r, r, 3.141592, 4.712388)
            ctx.close_path()

            # Dark Frosted Glass Fill
            ctx.set_source_rgba(0.09, 0.11, 0.17, 0.94)
            ctx.fill_preserve()

            # Border Glowing Highlight
            ctx.set_source_rgba(0.22, 0.74, 0.97, 0.45)
            ctx.set_line_width(1.4)
            ctx.stroke()

            if not is_update_banner:
                # Towing Cable Line with Dynamic Bounce
                cable_y = h * 0.5 + math.sin(tick[0] * 0.15) * 1.5
                ctx.set_source_rgba(0.9, 0.92, 0.98, 0.7)
                ctx.set_line_width(1.5)
                ctx.move_to(56.0, cable_y)
                ctx.line_to(card_x, cable_y)
                ctx.stroke()

                # Draw Mascot Aircraft & Animated Propeller
                CairoPilotRenderer.draw_pilot(ctx, pilot_type, 44.0, cable_y, tick[0])
            return False

        darea = Gtk.DrawingArea()
        darea.connect("draw", draw_canvas)

        overlay = Gtk.Overlay()
        overlay.add(darea)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        box.set_margin_start(24 if is_update_banner else 110)
        box.set_margin_end(18)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_valign(Gtk.Align.CENTER)
        
        t_lbl = Gtk.Label()
        t_lbl.get_style_context().add_class("hud-title-lbl")
        t_lbl.set_markup(f"<b>{GLib.markup_escape_text(title[:34])}</b>")
        t_lbl.set_xalign(0.0)
        vbox.pack_start(t_lbl, False, False, 0)

        s_lbl = Gtk.Label()
        s_lbl.get_style_context().add_class("hud-sub-lbl")
        s_lbl.set_markup(f"{GLib.markup_escape_text(provider)}  •  <i>{GLib.markup_escape_text(quote_text)}</i>")
        s_lbl.set_xalign(0.0)
        vbox.pack_start(s_lbl, False, False, 0)

        box.pack_start(vbox, True, True, 0)

        def _close_and_quit():
            try:
                GLib.source_remove(timer_id)
            except Exception:
                pass
            win.destroy()
            if "--test" in sys.argv and Gtk.main_level() > 0:
                Gtk.main_quit()

        if action_url or is_update_banner:
            btn = Gtk.Button(label=action_btn_text)
            btn.get_style_context().add_class("hud-btn")
            if is_update_banner:
                def _on_up_click(b):
                    from core.services.updater_service import updater_service
                    updater_service.download_and_install_update(background=True)
                    _close_and_quit()
                btn.connect("clicked", _on_up_click)
            else:
                btn.connect("clicked", lambda b: (import_webbrowser().open(action_url), _close_and_quit()))
            box.pack_end(btn, False, False, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("hud-close")
        close_btn.connect("clicked", lambda b: _close_and_quit())
        box.pack_end(close_btn, False, False, 0)

        overlay.add_overlay(box)
        win.add(overlay)
        win.show_all()

        def _step():
            tick[0] += 1
            darea.queue_draw()
            return True

        timer_id = GLib.timeout_add(40, _step) # ~25 FPS

        # Auto-dismiss pre-event banners after 12 seconds (stage 0 remains persistent until acknowledged)
        reminder_stage = event_data.get("reminder_stage")
        if reminder_stage is None or reminder_stage > 0:
            GLib.timeout_add_seconds(12, _close_and_quit)

    def import_webbrowser():
        import webbrowser
        return webbrowser

    GLib.idle_add(_run)
