#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Resolve version dynamically from argument $1, env var RELEASE_TAG/VERSION, or models.py
RAW_VER="${1:-${RELEASE_TAG:-${VERSION}}}"
if [ -z "$RAW_VER" ]; then
    RAW_VER=$(python3 -c "import re; m = re.search(r'__version__\s*=\s*[\"\']([^\"\']+)[\"\']', open('$ROOT_DIR/core/domain/models.py').read()); print(m.group(1) if m else '1.0.0')")
fi
# Strip any leading 'v'
VERSION="${RAW_VER#v}"
PACKAGE_NAME="flightdeck_${VERSION}_amd64"
BUILD_ROOT="$ROOT_DIR/deb_dist/$PACKAGE_NAME"
OUTPUT_DEB="$ROOT_DIR/deb_dist/${PACKAGE_NAME}.deb"

echo "🐧 Building Debian/Ubuntu .deb package for FlightDeck v${VERSION} (Wayland & X11)..."

rm -rf "$ROOT_DIR/deb_dist"
mkdir -p "$BUILD_ROOT/DEBIAN"
mkdir -p "$BUILD_ROOT/opt/flightdeck"
mkdir -p "$BUILD_ROOT/usr/bin"
mkdir -p "$BUILD_ROOT/usr/share/applications"
mkdir -p "$BUILD_ROOT/usr/share/icons/hicolor/512x512/apps"

# 1. Copy Application payload
cp -R "$ROOT_DIR/core" "$BUILD_ROOT/opt/flightdeck/"
cp -R "$ROOT_DIR/ui" "$BUILD_ROOT/opt/flightdeck/"
# Exclude macOS-specific UI files (AppKit/Quartz) and pycache from Linux package
rm -rf "$BUILD_ROOT/opt/flightdeck/ui/macos"
find "$BUILD_ROOT/opt/flightdeck" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
cp -R "$ROOT_DIR/assets" "$BUILD_ROOT/opt/flightdeck/"
cp "$ROOT_DIR/main.py" "$BUILD_ROOT/opt/flightdeck/"

# Stamp dynamic package version into payload
echo "$VERSION" > "$BUILD_ROOT/opt/flightdeck/VERSION"
sed -i "s/__version__ = .*/__version__ = \"$VERSION\"/" "$BUILD_ROOT/opt/flightdeck/core/domain/models.py" 2>/dev/null || true

# 2. Icon & Desktop integration
if [ -f "$ROOT_DIR/assets/icon.png" ]; then
    # Always install 512x512 base icon directly
    mkdir -p "$BUILD_ROOT/usr/share/icons/hicolor/512x512/apps"
    cp "$ROOT_DIR/assets/icon.png" "$BUILD_ROOT/usr/share/icons/hicolor/512x512/apps/flightdeck.png"

    # Generate multi-resolution icons (PIL -> PyQt6 fallback -> safe continue)
    python3 -c "
import os
src = '$ROOT_DIR/assets/icon.png'
sizes = [16, 24, 32, 48, 64, 128, 256, 512]

# 1. Try PIL (Pillow)
try:
    from PIL import Image
    im = Image.open(src)
    for sz in sizes:
        dest_dir = f'$BUILD_ROOT/usr/share/icons/hicolor/{sz}x{sz}/apps'
        os.makedirs(dest_dir, exist_ok=True)
        resized = im.resize((sz, sz), Image.Resampling.LANCZOS)
        resized.save(os.path.join(dest_dir, 'flightdeck.png'))
    exit(0)
except ImportError:
    pass

# 2. Try PyQt6 QImage
try:
    from PyQt6.QtGui import QImage
    from PyQt6.QtCore import Qt
    im = QImage(src)
    if not im.isNull():
        for sz in sizes:
            dest_dir = f'$BUILD_ROOT/usr/share/icons/hicolor/{sz}x{sz}/apps'
            os.makedirs(dest_dir, exist_ok=True)
            scaled = im.scaled(sz, sz, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            scaled.save(os.path.join(dest_dir, 'flightdeck.png'))
        exit(0)
except ImportError:
    pass

print('ℹ️ PIL and PyQt6 not available for multi-resolution scaling; base 512x512 icon preserved.')
" || true
fi

cat << 'DESKTOP_EOF' > "$BUILD_ROOT/usr/share/applications/flightdeck.desktop"
[Desktop Entry]
Name=FlightDeck
Comment=Smart Schedule & Travel Reminders & Flight Deck HUD for Wayland and macOS
Exec=/usr/bin/flightdeck
Icon=flightdeck
Terminal=false
Type=Application
Categories=Office;Calendar;Utility;
Keywords=Meeting;Calendar;Reminder;Timer;HUD;Travel;FlightDeck;
StartupNotify=true
StartupWMClass=flightdeck
DESKTOP_EOF

# 3. Launcher executable script
cat << 'LAUNCHER_EOF' > "$BUILD_ROOT/usr/bin/flightdeck"
#!/bin/bash
export PYTHONUNBUFFERED=1
cd /opt/flightdeck
exec /usr/bin/python3 /opt/flightdeck/main.py "$@"
LAUNCHER_EOF
chmod +x "$BUILD_ROOT/usr/bin/flightdeck"

# 4. Debian Control file
cat << CONTROL_EOF > "$BUILD_ROOT/DEBIAN/control"
Package: flightdeck
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: FlightDeck Team <support@flightdeck.com>
Depends: python3 (>= 3.10), python3-pyqt6, python3-gi, gir1.2-edataserver-1.2, gir1.2-ecal-2.0, gir1.2-ayatanaappindicator3-0.1
Description: Smart Schedule & Travel Reminders & Animated Flight Deck HUD
 FlightDeck provides progressive multi-stage notifications, real-time Apple/Google
 Maps travel ETAs, and pilot avatars floating smoothly over full-screen workspaces.
CONTROL_EOF

# 5. Post-install script
cat << 'POSTINST_EOF' > "$BUILD_ROOT/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi
exit 0
POSTINST_EOF
chmod 755 "$BUILD_ROOT/DEBIAN/postinst"

# 6. Build package using dpkg-deb if available or create tarball structure
if command -v dpkg-deb > /dev/null 2>&1; then
    echo "📦 Packaging .deb using dpkg-deb..."
    dpkg-deb --build "$BUILD_ROOT" "$OUTPUT_DEB"
    echo "✅ Debian package created: $OUTPUT_DEB"
else
    echo "ℹ️  dpkg-deb not present on this host (macOS). Package directory structured in: $BUILD_ROOT"
fi
