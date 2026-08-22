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
    print("🎨 Generating ICNS icon from assets/icon.png...")
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
    print(f"✅ AppIcon.icns successfully generated: {icns_path}")
    return icns_path

def check_python_code():
    print("🧪 Verifying and validating Python code syntax...")
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
            print(f"  ✓ {os.path.relpath(py_file, PROJECT_DIR)}: Syntax OK")
        except py_compile.PyCompileError as e:
            print(f"  ❌ SYNTAX ERROR in {py_file}: {e}")
            raise SystemExit(1)
                
    # Verify module imports
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
        print("  ✓ All core/ and ui/ modules imported cleanly!")
    except Exception as e:
        print(f"  ❌ IMPORT ERROR: {e}")
        raise SystemExit(1)
        
    # Run automated test suite
    print("  🧪 Running automated unit test suite...")
    res = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=PROJECT_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ❌ TEST SUITE FAILED:\n{res.stderr}\n{res.stdout}")
        raise SystemExit(1)
    print("  ✓ Test suite passed with 100% success!")
    print("✅ Python validation completed successfully (Zero Errors).\n")

def build_bundle():
    check_python_code()
    print(f"📦 Building macOS Native Bundle: {APP_DIR}...")
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
        
    os.makedirs(MACOS_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    
    # 1. Copy AppIcon.icns
    icns_path = generate_icns()
    shutil.copy2(icns_path, os.path.join(RESOURCES_DIR, "AppIcon.icns"))
    
    # 2. Copy assets/
    assets_dest = os.path.join(RESOURCES_DIR, "assets")
    os.makedirs(assets_dest, exist_ok=True)
    if os.path.exists(os.path.join(PROJECT_DIR, "assets", "icon.png")):
        shutil.copy2(os.path.join(PROJECT_DIR, "assets", "icon.png"), os.path.join(assets_dest, "icon.png"))
        
    # 3. Copy Python module directories (core/ and ui/) and main.py
    shutil.copytree(os.path.join(PROJECT_DIR, "core"), os.path.join(RESOURCES_DIR, "core"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(PROJECT_DIR, "ui"), os.path.join(RESOURCES_DIR, "ui"), dirs_exist_ok=True)
    shutil.copy2(os.path.join(PROJECT_DIR, "main.py"), os.path.join(RESOURCES_DIR, "main.py"))
            
    # 4. Create Info.plist
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
    <string>QuakMeeting requires Calendar access to display smart reminders and travel routes for your scheduled events.</string>
</dict>
</plist>
"""
    with open(os.path.join(CONTENTS_DIR, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(info_plist_content)
        
    # 5. Create Launcher Bash executable in MacOS/QuakMeeting
    launcher_content = """#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
LOG_DIR="$HOME/.quakmeeting"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/quakmeeting.log"
LAUNCHER_LOG="$LOG_DIR/launcher.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Launcher] QuakMeeting launching from $DIR..." >> "$LAUNCHER_LOG"

export PATH="/opt/miniconda3/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

PYTHON_BIN=""
for p in "/opt/miniconda3/bin/python3" "/usr/local/bin/python3" "/opt/homebrew/bin/python3" "$(which python3)"; do
    if [ -n "$p" ] && [ -x "$p" ] && "$p" -c "import AppKit" 2>/dev/null; then
        PYTHON_BIN="$p"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Launcher] Found Python with PyObjC: $PYTHON_BIN" >> "$LAUNCHER_LOG"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    ERR_MSG="Python 3 with PyObjC (AppKit) not found. Please install pyobjc: pip3 install pyobjc"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Launcher Error] $ERR_MSG" >> "$LAUNCHER_LOG"
    osascript -e "display alert \"QuakMeeting Launch Error\" message \"$ERR_MSG\" as critical"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Launcher] Executing $PYTHON_BIN $DIR/main.py --dashboard $@" >> "$LAUNCHER_LOG"
exec "$PYTHON_BIN" "$DIR/main.py" --dashboard "$@" >> "$LOG_FILE" 2>&1
"""
    launcher_path = os.path.join(MACOS_DIR, "QuakMeeting")
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(launcher_content)
        
    os.chmod(launcher_path, 0o755)
    print(f"🚀 QuakMeeting.app successfully created in: {APP_DIR}")
    
    # 6. Create Desktop shortcut
    desktop_app = os.path.expanduser("~/Desktop/QuakMeeting.app")
    try:
        if os.path.exists(desktop_app):
            if os.path.islink(desktop_app):
                os.unlink(desktop_app)
            else:
                shutil.rmtree(desktop_app)
        os.symlink(APP_DIR, desktop_app)
        print(f"📍 Shortcut created on Desktop: {desktop_app}")
    except Exception as e:
        print(f"Desktop note: {e}")

if __name__ == "__main__":
    build_bundle()
