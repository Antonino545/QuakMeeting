import os
import shutil
import subprocess

APP_NAME = "QuakMeeting.app"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(PROJECT_DIR, APP_NAME)
CONTENTS_DIR = os.path.join(APP_DIR, "Contents")
MACOS_DIR = os.path.join(CONTENTS_DIR, "MacOS")
RESOURCES_DIR = os.path.join(CONTENTS_DIR, "Resources")

def generate_icns():
    print("🎨 Generazione file icns da assets/icon.png...")
    icon_src = os.path.join(PROJECT_DIR, "assets", "icon.png")
    if not os.path.exists(icon_src):
        from generate_app_icon import create_app_icon
        create_app_icon(icon_src, 1024)
        
    iconset_dir = os.path.join(PROJECT_DIR, "assets", "AppIcon.iconset")
    os.makedirs(iconset_dir, exist_ok=True)
    
    sizes = [16, 32, 128, 256, 512]
    for sz in sizes:
        # Standard 1x
        out_1x = os.path.join(iconset_dir, f"icon_{sz}x{sz}.png")
        subprocess.run(["sips", "-z", str(sz), str(sz), icon_src, "--out", out_1x], capture_output=True)
        # Retina 2x
        out_2x = os.path.join(iconset_dir, f"icon_{sz}x{sz}@2x.png")
        subprocess.run(["sips", "-z", str(sz * 2), str(sz * 2), icon_src, "--out", out_2x], capture_output=True)
        
    # Generate ICNS
    icns_path = os.path.join(PROJECT_DIR, "assets", "AppIcon.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path], check=True)
    shutil.rmtree(iconset_dir, ignore_errors=True)
    print(f"✅ AppIcon.icns generata con successo: {icns_path}")
    return icns_path

def check_python_code():
    print("🧪 Controllo e validazione del codice Python in corso...")
    import py_compile
    
    py_files = []
    for root, _, files in os.walk(PROJECT_DIR):
        if ".git" in root or "QuakMeeting.app" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    
    for py_file in py_files:
        try:
            py_compile.compile(py_file, doraise=True)
            print(f"  ✓ {os.path.relpath(py_file, PROJECT_DIR)}: Sintassi OK")
        except py_compile.PyCompileError as e:
            print(f"  ❌ ERRORE SINTASSI in {py_file}: {e}")
            raise SystemExit(1)
                
    # Verifica import dei moduli
    try:
        import sys
        if PROJECT_DIR not in sys.path:
            sys.path.insert(0, PROJECT_DIR)
        import core.domain
        import core.services
        import core.providers
        import core.config_manager
        import core.calendar_scanner
        import core.autostart
        import ui.banner
        import ui.dashboard_window
        import ui.menu_bar_app
        print("  ✓ Tutti i moduli core/ e ui/ importati correttamente!")
    except Exception as e:
        print(f"  ❌ ERRORE IMPORT: {e}")
        raise SystemExit(1)
        
    # Esegui suite di test automatici
    print("  🧪 Esecuzione test suite automatica...")
    res = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=PROJECT_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ❌ TEST SUITE FALLITA:\n{res.stderr}")
        raise SystemExit(1)
    print("  ✓ Test suite superata al 100%!")
    print("✅ Controllo Python completato con successo (Zero Errori).\n")

def build_bundle():
    check_python_code()
    print(f"📦 Creazione del bundle macOS nativo: {APP_DIR}...")
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
        
    os.makedirs(MACOS_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    
    # 1. Copia AppIcon.icns
    icns_path = generate_icns()
    shutil.copy2(icns_path, os.path.join(RESOURCES_DIR, "AppIcon.icns"))
    
    # 2. Copia assets/
    assets_dest = os.path.join(RESOURCES_DIR, "assets")
    os.makedirs(assets_dest, exist_ok=True)
    if os.path.exists(os.path.join(PROJECT_DIR, "assets", "icon.png")):
        shutil.copy2(os.path.join(PROJECT_DIR, "assets", "icon.png"), os.path.join(assets_dest, "icon.png"))
        
    # 3. Copia directory di moduli Python (core/ e ui/) e main.py
    shutil.copytree(os.path.join(PROJECT_DIR, "core"), os.path.join(RESOURCES_DIR, "core"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(PROJECT_DIR, "ui"), os.path.join(RESOURCES_DIR, "ui"), dirs_exist_ok=True)
    shutil.copy2(os.path.join(PROJECT_DIR, "main.py"), os.path.join(RESOURCES_DIR, "main.py"))
            
    # 4. Crea Info.plist
    info_plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>QuakMeeting</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.quakmeeting.app</string>
    <key>CFBundleName</key>
    <string>QuakMeeting</string>
    <key>CFBundleDisplayName</key>
    <string>QuakMeeting</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCalendarsUsageDescription</key>
    <string>QuakMeeting necessita dell'accesso ai calendari per mostrarti promemoria intelligenti e indicazioni per i tuoi eventi.</string>
</dict>
</plist>
"""
    with open(os.path.join(CONTENTS_DIR, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(info_plist_content)
        
    # 5. Crea eseguibile Launcher Bash in MacOS/QuakMeeting
    launcher_content = """#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
export PATH="/opt/miniconda3/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

PYTHON_BIN=""
for p in "/opt/miniconda3/bin/python3" "/usr/local/bin/python3" "/opt/homebrew/bin/python3" "$(which python3)"; do
    if [ -x "$p" ] && "$p" -c "import AppKit" 2>/dev/null; then
        PYTHON_BIN="$p"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$DIR/main.py" --dashboard "$@"
"""
    launcher_path = os.path.join(MACOS_DIR, "QuakMeeting")
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_content)
        
    os.chmod(launcher_path, 0o755)
    print(f"🚀 QuakMeeting.app creato con successo in: {APP_DIR}")
    
    # 6. Crea collegamento simbolico sul Desktop per comodità immediata dell'utente
    desktop_app = os.path.expanduser("~/Desktop/QuakMeeting.app")
    try:
        if os.path.exists(desktop_app):
            if os.path.islink(desktop_app):
                os.unlink(desktop_app)
            else:
                shutil.rmtree(desktop_app)
        os.symlink(APP_DIR, desktop_app)
        print(f"📍 Collegamento creato sulla Scrivania (Desktop): {desktop_app}")
    except Exception as e:
        print(f"Nota desktop: {e}")

if __name__ == "__main__":
    build_bundle()
