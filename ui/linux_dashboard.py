"""
GTK3 Flight Deck Dashboard Window for Ubuntu Linux.
Provides Today's Agenda, Pilot Hangar test buttons, and Settings & Preferences.
"""
import os
import sys
import threading
import logging
from datetime import datetime
from typing import Optional

from core.services.config_service import config
from core.services.calendar_service import calendar_service
from core.services.updater_service import updater_service
from core.services.event_bus import event_bus
from core.domain.models import format_duration
from core.logger import open_log_file, open_log_folder

logger = logging.getLogger("QuakMeeting.LinuxDashboard")

def show_linux_dashboard(tab_index: int = 0):
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, Gdk, GLib
    except Exception as e:
        logger.warning(f"GTK3 not available: {e}")
        return

    win = Gtk.Window(title="QuakMeeting — Flight Deck")
    win.set_default_size(780, 560)
    win.set_position(Gtk.WindowPosition.CENTER)

    notebook = Gtk.Notebook()
    notebook.set_tab_pos(Gtk.PositionType.TOP)

    # 1. Agenda Tab
    agenda_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    agenda_box.set_margin_start(16)
    agenda_box.set_margin_end(16)
    agenda_box.set_margin_top(16)
    agenda_box.set_margin_bottom(16)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    list_box = Gtk.ListBox()
    list_box.set_selection_mode(Gtk.SelectionMode.NONE)

    now = datetime.now()
    meetings = calendar_service.get_upcoming_meetings()
    today_meets = [m for m in meetings if m.start_time and m.start_time.date() == now.date()]

    if not today_meets:
        empty_lbl = Gtk.Label(label="🧘‍♂️ No events scheduled for today.\nRelax or add an event in your calendar!")
        empty_lbl.set_margin_top(40)
        list_box.add(empty_lbl)
    else:
        for m in today_meets:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row_box.set_margin_start(12)
            row_box.set_margin_end(12)
            row_box.set_margin_top(10)
            row_box.set_margin_bottom(10)

            icon_lbl = Gtk.Label(label="🦆")
            row_box.pack_start(icon_lbl, False, False, 0)

            st = m.start_time.strftime("%H:%M") if m.start_time else "--:--"
            t_lbl = Gtk.Label()
            t_lbl.set_markup(f"<b>{st}</b>  •  {GLib.markup_escape_text(m.title)}")
            t_lbl.set_xalign(0.0)
            row_box.pack_start(t_lbl, True, True, 0)

            if m.action_url:
                btn = Gtk.Button(label="🚀 Join")
                btn.connect("clicked", lambda b, u=m.action_url: import_webbrowser().open(u))
                row_box.pack_end(btn, False, False, 0)

            list_box.add(row_box)

    scroll.add(list_box)
    agenda_box.pack_start(scroll, True, True, 0)
    notebook.append_page(agenda_box, Gtk.Label(label="📅 Today's Agenda"))

    # 2. Pilot Hangar Tab
    hangar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    hangar_box.set_margin_start(16)
    hangar_box.set_margin_end(16)
    hangar_box.set_margin_top(16)
    hangar_box.set_margin_bottom(16)

    pilots = [
        ("duck", "🦆 Aviator Duck (Google Meet / Zoom)", "https://meet.google.com/test"),
        ("chef", "👨‍🍳 Chef Duck (Dinner / Restaurant)", "https://maps.google.com/?q=Pizzeria"),
        ("captain", "🧑‍✈️ Jet Captain (Flight / Transit)", "https://maps.google.com/?q=Airport"),
        ("owl", "🦉 Academic Owl (University / Study)", "https://calendar.google.com"),
        ("gym", "🏋️‍♂️ Athlete Duck (Palestra / Gym / Sport)", "https://maps.google.com/?daddr=Gym"),
        ("driver", "🏎️ Speed Racer Driver (In Person)", "https://maps.google.com/?daddr=Office"),
        ("zen_duck", "🦆🌸 Zen Duck (Therapy / Wellness)", "https://app.serenis.it")
    ]

    for p_id, p_name, p_url in pilots:
        p_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        p_lbl = Gtk.Label()
        p_lbl.set_markup(f"<b>{p_name}</b>")
        p_lbl.set_xalign(0.0)
        p_row.pack_start(p_lbl, True, True, 0)

        t_btn = Gtk.Button(label="🚀 Test Flight")
        t_btn.connect("clicked", lambda b, i=p_id, u=p_url: event_bus.publish("TRIGGER_BANNER", event_dict={
            "title": f"QuakMeeting {i.capitalize()} Test",
            "provider": "Manual Test 🚀",
            "pilot_type": i,
            "action_btn_text": "🚀 OPEN LINK",
            "action_url": u,
            "start_time": datetime.now(),
            "is_travel": False
        }))
        p_row.pack_end(t_btn, False, False, 0)
        hangar_box.pack_start(p_row, False, False, 4)

    notebook.append_page(hangar_box, Gtk.Label(label="🦆 Pilot Hangar"))

    # 3. Preferences Tab
    pref_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    pref_box.set_margin_start(16)
    pref_box.set_margin_end(16)
    pref_box.set_margin_top(16)
    pref_box.set_margin_bottom(16)

    # Starting address
    addr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    addr_lbl = Gtk.Label(label="🏠 Home / Starting Address:")
    addr_entry = Gtk.Entry()
    addr_entry.set_text(config.get("home_address", "") or "")
    addr_entry.set_placeholder_text("e.g. 24 Oxford Street, London")
    save_btn = Gtk.Button(label="💾 Save")
    save_btn.connect("clicked", lambda b: config.set("home_address", addr_entry.get_text().strip()))

    addr_row.pack_start(addr_lbl, False, False, 0)
    addr_row.pack_start(addr_entry, True, True, 0)
    addr_row.pack_end(save_btn, False, False, 0)
    pref_box.pack_start(addr_row, False, False, 0)

    # System Buttons
    sys_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    edit_btn = Gtk.Button(label="📝 Edit Rules")
    edit_btn.connect("clicked", lambda b: config.open_config_in_editor())
    log_btn = Gtk.Button(label="📄 View Logs")
    log_btn.connect("clicked", lambda b: open_log_file())
    up_btn = Gtk.Button(label="🔍 Check for Updates")
    up_btn.connect("clicked", lambda b: updater_service.check_for_updates(background=True))

    sys_row.pack_start(edit_btn, True, True, 0)
    sys_row.pack_start(log_btn, True, True, 0)
    sys_row.pack_start(up_btn, True, True, 0)
    pref_box.pack_start(sys_row, False, False, 0)

    notebook.append_page(pref_box, Gtk.Label(label="⚙️ Preferences"))

    notebook.set_current_page(tab_index)
    win.add(notebook)
    win.show_all()

def import_webbrowser():
    import webbrowser
    return webbrowser
