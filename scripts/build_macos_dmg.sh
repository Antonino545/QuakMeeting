#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DMG_NAME="QuakMeeting-macOS.dmg"
OUTPUT_DMG="$ROOT_DIR/$DMG_NAME"
TEMP_DMG_DIR="$ROOT_DIR/dmg_temp"

echo "📦 Packaging QuakMeeting into macOS .dmg..."

# 1. Build .app bundle first
cd "$ROOT_DIR"
PYTHON_CMD="python3"
if [ -n "$PYTHON" ]; then
    PYTHON_CMD="$PYTHON"
elif [ -x "/opt/miniconda3/bin/python3" ]; then
    PYTHON_CMD="/opt/miniconda3/bin/python3"
fi
RAW_VER="${1:-${RELEASE_TAG:-${VERSION}}}"
"$PYTHON_CMD" build_macos_app.py "$RAW_VER"

APP_PATH="$ROOT_DIR/QuakMeeting.app"
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: QuakMeeting.app not found in $ROOT_DIR"
    exit 1
fi

# 2. Prepare temporary directory
rm -rf "$TEMP_DMG_DIR" "$OUTPUT_DMG"
mkdir -p "$TEMP_DMG_DIR"

cp -R "$APP_PATH" "$TEMP_DMG_DIR/"
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# Clear quarantine flags and ad-hoc sign the bundle with designated requirement
echo "✍️ Applying ad-hoc codesign signature with designated requirement..."
xattr -cr "$TEMP_DMG_DIR/QuakMeeting.app" 2>/dev/null || true
codesign --force --deep -s - -i "com.quakmeeting.app" -r '=designated => identifier "com.quakmeeting.app"' "$TEMP_DMG_DIR/QuakMeeting.app" 2>/dev/null || true

# 3. Create DMG using hdiutil
echo "💽 Creating disk image: $OUTPUT_DMG..."
hdiutil create -volname "QuakMeeting Installer" \
    -srcfolder "$TEMP_DMG_DIR" \
    -ov -format UDZO \
    "$OUTPUT_DMG"

rm -rf "$TEMP_DMG_DIR"

# Ad-hoc sign the DMG image
codesign --force --sign - "$OUTPUT_DMG" 2>/dev/null || true

echo "✅ DMG successfully built & signed: $OUTPUT_DMG"
shasum -a 256 "$OUTPUT_DMG"
