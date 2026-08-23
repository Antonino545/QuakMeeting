"""
Wayland-Native Animated HUD Floating Banner for Ubuntu Linux.
Uses gtk-layer-shell (zwlr_layer_shell_v1) on LAYER_OVERLAY with Cairo rendering.
"""
import sys
import os
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("QuakMeeting.WaylandBanner")

def show_wayland_banner(event_data: Dict[str, Any]) -> None:
    """Spawns an animated floating HUD banner on Ubuntu Wayland."""
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
    except Exception as e:
        logger.warning(f"PyGObject / GTK not available on this environment: {e}")
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

        width, height = 480, 84
        win.set_default_size(width, height)

        title = event_data.get("title", "Upcoming Event")
        provider = event_data.get("provider", "Calendar")
        pilot_type = event_data.get("pilot_type", "duck")
        action_btn_text = event_data.get("action_btn_text", "🚀 JOIN")
        action_url = event_data.get("action_url")

        icon_map = {"chef": "🍕", "captain": "✈️", "owl": "🎓", "driver": "🚗", "zen_duck": "🛋️", "duck": "🦆"}
        icon_str = icon_map.get(pilot_type, "🦆")

        def draw_bg(widget, ctx):
            ctx.set_source_rgba(0.12, 0.14, 0.20, 0.92)
            # Rounded rectangle
            r = 14.0
            w, h = widget.get_allocated_width(), widget.get_allocated_height()
            ctx.new_sub_path()
            ctx.arc(w - r, r, r, -1.570796, 0)
            ctx.arc(w - r, h - r, r, 0, 1.570796)
            ctx.arc(r, h - r, r, 1.570796, 3.141592)
            ctx.arc(r, r, r, 3.141592, 4.712388)
            ctx.close_path()
            ctx.fill_preserve()
            ctx.set_source_rgba(1.0, 1.0, 1.0, 0.12)
            ctx.set_line_width(1.5)
            ctx.stroke()
            return False

        win.connect("draw", draw_bg)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        icon_lbl = Gtk.Label(label=icon_str)
        icon_lbl.modify_font(Pango.FontDescription("24"))
        box.pack_start(icon_lbl, False, False, 0)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        vbox.set_valign(Gtk.Align.CENTER)
        
        t_lbl = Gtk.Label()
        t_lbl.set_markup(f"<b>{GLib.markup_escape_text(title[:40])}</b>")
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

        win.add(box)
        win.show_all()

        # Auto-dismiss after 12 seconds
        GLib.timeout_add_seconds(12, win.destroy)

    def import_webbrowser():
        import webbrowser
        return webbrowser

    GLib.idle_add(_run)
