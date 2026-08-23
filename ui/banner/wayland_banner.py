"""
Wayland-Native Animated HUD Floating Banner for Ubuntu Linux.
Uses gtk-layer-shell (zwlr_layer_shell_v1) on LAYER_OVERLAY with Cairo rendering
for all 7 pilot mascots and airplanes.
"""
import sys
import os
import math
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("QuakMeeting.WaylandBanner")

def show_wayland_banner(event_data: Dict[str, Any]) -> None:
    """Spawns an animated floating HUD banner with Cairo pilot rendering on Ubuntu Wayland."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        try:
            gi.require_version('GtkLayerShell', '0.1')
            from gi.repository import GtkLayerShell
            has_layer_shell = True
        except (ValueError, ImportError):
            has_layer_shell = False

        from gi.repository import Gtk, Gdk, GLib, Pango
        import cairo
        from ui.banner.cairo_renderers import CairoPilotRenderer
    except Exception as e:
        logger.warning(f"PyGObject / GTK / Cairo not available on this host: {e}")
        return

    def _run():
        win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        win.set_title("QuakMeeting HUD")
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

        width, height = 540, 92
        win.set_default_size(width, height)

        title = event_data.get("title", "Upcoming Event")
        provider = event_data.get("provider", "Calendar")
        pilot_type = event_data.get("pilot_type", "duck")
        action_btn_text = event_data.get("action_btn_text", "🚀 JOIN")
        action_url = event_data.get("action_url")

        tick = [0]

        def draw_canvas(widget, ctx):
            w = widget.get_allocated_width()
            h = widget.get_allocated_height()

            # 1. Clear background
            ctx.set_source_rgba(0, 0, 0, 0)
            ctx.paint()

            # 2. Draw Translucent Frosted Glass Card (Banner)
            card_x = 90.0
            card_y = 6.0
            card_w = w - 100.0
            card_h = h - 12.0
            r = 14.0

            ctx.new_sub_path()
            ctx.arc(card_x + card_w - r, card_y + r, r, -1.570796, 0)
            ctx.arc(card_x + card_w - r, card_y + card_h - r, r, 0, 1.570796)
            ctx.arc(card_x + r, card_y + card_h - r, r, 1.570796, 3.141592)
            ctx.arc(card_x + r, card_y + r, r, 3.141592, 4.712388)
            ctx.close_path()

            # Slate Dark Glass Fill
            ctx.set_source_rgba(0.12, 0.14, 0.20, 0.92)
            ctx.fill_preserve()

            # Border Highlight
            ctx.set_source_rgba(1.0, 1.0, 1.0, 0.15)
            ctx.set_line_width(1.2)
            ctx.stroke()

            # 3. Draw Towing Cable
            ctx.set_source_rgba(0.9, 0.9, 0.95, 0.6)
            ctx.set_line_width(1.5)
            ctx.move_to(55.0, h * 0.5)
            ctx.line_to(card_x, h * 0.5)
            ctx.stroke()

            # 4. Draw Mascot Airplane & Pilot via CairoPilotRenderer
            CairoPilotRenderer.draw_pilot(ctx, pilot_type, 44.0, h * 0.5, tick[0])
            return False

        darea = Gtk.DrawingArea()
        darea.connect("draw", draw_canvas)

        overlay = Gtk.Overlay()
        overlay.add(darea)

        # Content Box positioned over the glass card
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(106)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        vbox.set_valign(Gtk.Align.CENTER)
        
        t_lbl = Gtk.Label()
        t_lbl.set_markup(f"<b>{GLib.markup_escape_text(title[:36])}</b>")
        t_lbl.set_xalign(0.0)
        vbox.pack_start(t_lbl, False, False, 0)

        s_lbl = Gtk.Label()
        s_lbl.set_markup(f"<small>{GLib.markup_escape_text(provider)}</small>")
        s_lbl.set_xalign(0.0)
        vbox.pack_start(s_lbl, False, False, 0)

        box.pack_start(vbox, True, True, 0)

        if action_url:
            btn = Gtk.Button(label=action_btn_text)
            btn.connect("clicked", lambda b: (import_webbrowser().open(action_url), win.destroy()))
            box.pack_end(btn, False, False, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.connect("clicked", lambda b: win.destroy())
        box.pack_end(close_btn, False, False, 0)

        overlay.add_overlay(box)
        win.add(overlay)
        win.show_all()

        # Animate propeller and wave
        def _step():
            tick[0] += 1
            darea.queue_draw()
            return True

        timer_id = GLib.timeout_add(40, _step) # ~25 FPS

        def _cleanup():
            GLib.source_remove(timer_id)
            win.destroy()

        # Auto-dismiss after 12 seconds
        GLib.timeout_add_seconds(12, _cleanup)

    def import_webbrowser():
        import webbrowser
        return webbrowser

    GLib.idle_add(_run)
