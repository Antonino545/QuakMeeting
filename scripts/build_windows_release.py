"""
Build & Packaging script for FlightDeck on Windows.
Produces a portable standalone distribution (FlightDeck-Windows.zip) using PyInstaller.
"""
import os
import sys
import shutil
import zipfile
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ensure_ico():
    """Generates assets/icon.ico from assets/icon.png if needed."""
    png_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
    ico_path = os.path.join(PROJECT_ROOT, "assets", "icon.ico")
    if os.path.exists(ico_path):
        return ico_path
    if not os.path.exists(png_path):
        return None
    try:
        from PIL import Image
        img = Image.open(png_path)
        img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"Generated {ico_path}")
        return ico_path
    except Exception as e:
        print(f"Pillow not available to generate icon.ico ({e}), skipping ICO creation.")
        return None

def build():
    os.chdir(PROJECT_ROOT)
    version = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
    print(f"Building FlightDeck Windows release {version}...")

    ico_path = ensure_ico()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=FlightDeck",
        "--add-data", f"assets{os.pathsep}assets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--exclude-module=ui.macos",
        "main.py"
    ]
    if ico_path and os.path.exists(ico_path):
        cmd.extend(["--icon", ico_path])

    print("Running PyInstaller command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    dist_dir = os.path.join(PROJECT_ROOT, "dist", "FlightDeck")
    # Include runner batch script in the distribution
    shutil.copyfile(os.path.join(PROJECT_ROOT, "scripts", "run_windows.bat"), os.path.join(dist_dir, "run_windows.bat"))

    zip_name = "FlightDeck-Windows.zip"
    zip_path = os.path.join(PROJECT_ROOT, zip_name)
    print(f"Compressing distribution into {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.join(PROJECT_ROOT, "dist"))
                zf.write(full_path, rel_path)

    print(f"✅ Successfully built Windows release artifact: {zip_path}")

if __name__ == "__main__":
    build()
