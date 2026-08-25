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
PACKAGE_NAME="quakmeeting_${VERSION}_amd64"
BUILD_ROOT="$ROOT_DIR/deb_dist/$PACKAGE_NAME"
OUTPUT_DEB="$ROOT_DIR/deb_dist/${PACKAGE_NAME}.deb"

echo "🐧 Building Debian/Ubuntu .deb package for QuakMeeting v${VERSION} (Wayland & X11)..."

rm -rf "$ROOT_DIR/deb_dist"
mkdir -p "$BUILD_ROOT/DEBIAN"
mkdir -p "$BUILD_ROOT/opt/quakmeeting"
mkdir -p "$BUILD_ROOT/usr/bin"
mkdir -p "$BUILD_ROOT/usr/share/applications"
mkdir -p "$BUILD_ROOT/usr/share/icons/hicolor/512x512/apps"

# 1. Copy Application payload
cp -R "$ROOT_DIR/core" "$BUILD_ROOT/opt/quakmeeting/"
cp -R "$ROOT_DIR/ui" "$BUILD_ROOT/opt/quakmeeting/"
cp -R "$ROOT_DIR/assets" "$BUILD_ROOT/opt/quakmeeting/"
cp "$ROOT_DIR/main.py" "$BUILD_ROOT/opt/quakmeeting/"

# 2. Icon & Desktop integration
if [ -f "$ROOT_DIR/assets/icon.png" ]; then
    cp "$ROOT_DIR/assets/icon.png" "$BUILD_ROOT/usr/share/icons/hicolor/512x512/apps/quakmeeting.png"
fi

cat << 'DESKTOP_EOF' > "$BUILD_ROOT/usr/share/applications/quakmeeting.desktop"
[Desktop Entry]
Name=QuakMeeting
Comment=Smart Meeting Reminders & Flight Deck HUD for Wayland and macOS
Exec=/usr/bin/quakmeeting
Icon=quakmeeting
Terminal=false
Type=Application
Categories=Office;Calendar;Utility;
Keywords=Meeting;Calendar;Reminder;Timer;HUD;
StartupNotify=true
DESKTOP_EOF

# 3. Launcher executable script
cat << 'LAUNCHER_EOF' > "$BUILD_ROOT/usr/bin/quakmeeting"
#!/bin/bash
export PYTHONUNBUFFERED=1
cd /opt/quakmeeting
exec python3 /opt/quakmeeting/main.py "$@"
LAUNCHER_EOF
chmod +x "$BUILD_ROOT/usr/bin/quakmeeting"

# 4. Debian Control file
cat << CONTROL_EOF > "$BUILD_ROOT/DEBIAN/control"
Package: quakmeeting
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: QuakMeeting Team <support@quakmeeting.com>
Depends: python3 (>= 3.8), python3-gi, gir1.2-gtk-3.0, gir1.2-appindicator3-0.1 | gir1.2-ayatanaappindicator3-0.1, gir1.2-gtklayershell-0.1 | libcanberra-gtk3-module, gir1.2-edataserver-1.2, gir1.2-ecal-2.0
Description: Smart Meeting Reminders & Animated Flight Deck HUD
 QuakMeeting provides progressive multi-stage notifications, real-time Apple/Google
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
