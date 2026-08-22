import os
import subprocess
import sys

PLIST_PATH = os.path.expanduser("~/Library/LaunchAgents/com.quakmeeting.app.plist")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_SCRIPT_PATH = os.path.join(PROJECT_DIR, "main.py")
PYTHON_EXEC = sys.executable
LOG_OUT = os.path.join(PROJECT_DIR, "quakmeeting.log")
LOG_ERR = os.path.join(PROJECT_DIR, "quakmeeting_error.log")

def get_plist_content():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.quakmeeting.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PYTHON_EXEC}</string>
        <string>{MAIN_SCRIPT_PATH}</string>
        <string>--autostart</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>StandardOutPath</key>
    <string>{LOG_OUT}</string>
    <key>StandardErrorPath</key>
    <string>{LOG_ERR}</string>
</dict>
</plist>
"""

def is_autostart_enabled():
    return os.path.exists(PLIST_PATH)

def enable_autostart():
    try:
        os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)
        with open(PLIST_PATH, "w", encoding="utf-8") as f:
            f.write(get_plist_content().strip())
        subprocess.run(["launchctl", "unload", PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["launchctl", "load", PLIST_PATH], check=True)
        print("✅ Avvio automatico al login configurato con successo!")
        return True
    except Exception as e:
        print(f"Errore attivazione avvio automatico: {e}")
        return False

def disable_autostart():
    try:
        if os.path.exists(PLIST_PATH):
            subprocess.run(["launchctl", "unload", PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(PLIST_PATH)
        print("❌ Avvio automatico disattivato.")
        return True
    except Exception as e:
        print(f"Errore disattivazione avvio automatico: {e}")
        return False

if __name__ == "__main__":
    if "--enable" in sys.argv:
        enable_autostart()
    elif "--disable" in sys.argv:
        disable_autostart()
    else:
        print("Stato avvio automatico:", "ATTIVO" if is_autostart_enabled() else "DISATTIVO")
