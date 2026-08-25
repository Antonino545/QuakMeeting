import re

with open('ui/banner/wayland_banner.py', 'r') as f:
    content = f.read()

snooze_logic = """
        if not is_update_banner and (reminder_stage is None or reminder_stage > 0):
            skip_btn = Gtk.Button(label="⏭️ Skip")
            skip_btn.get_style_context().add_class("hud-btn")
            def _on_skip(b):
                from core.services.reminder_engine import reminder_engine
                m_id = event_data.get("id")
                if not m_id:
                    m_title = event_data.get("title", "")
                    m_start = event_data.get("start_time")
                    time_str = m_start.strftime("%Y%m%d%H%M") if hasattr(m_start, "strftime") else "000000000000"
                    m_id = f"{m_title}_{time_str}"
                reminder_engine.mark_arrived(m_id)
                _close_and_quit()
            skip_btn.connect("clicked", _on_skip)
            box.pack_end(skip_btn, False, False, 0)
            
            snooze_btn = Gtk.Button(label="💤 Snooze 5m")
            snooze_btn.get_style_context().add_class("hud-btn")
            def _on_snooze(b):
                import threading
                import time
                def _re_notify():
                    time.sleep(300)
                    from ui.banner.wayland_banner import show_wayland_banner
                    GLib.idle_add(lambda: show_wayland_banner(event_data))
                threading.Thread(target=_re_notify, daemon=True).start()
                _close_and_quit()
            snooze_btn.connect("clicked", _on_snooze)
            box.pack_end(snooze_btn, False, False, 0)
"""

content = content.replace('        close_btn = Gtk.Button(label="✕")', snooze_logic + '\n        close_btn = Gtk.Button(label="✕")')

with open('ui/banner/wayland_banner.py', 'w') as f:
    f.write(content)
