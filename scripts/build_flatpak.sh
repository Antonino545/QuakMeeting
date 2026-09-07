#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MANIFEST="$ROOT_DIR/packaging/flatpak/com.quakmeeting.QuakMeeting.yaml"
BUILD_DIR="$ROOT_DIR/build/flatpak"
REPO_DIR="$ROOT_DIR/build/flatpak_repo"
DIST_DIR="$ROOT_DIR/flatpak_dist"

echo "📦 QuakMeeting Flatpak Builder"
echo "=============================="

if ! command -v flatpak &>/dev/null; then
    echo "❌ Error: 'flatpak' command not found. Please install flatpak first."
    exit 1
fi

if ! command -v flatpak-builder &>/dev/null; then
    echo "⚠️  'flatpak-builder' is not installed."
    echo "To build flatpaks locally, install it via:"
    echo "   sudo apt-get install -y flatpak-builder"
    echo "and ensure the KDE runtime is installed:"
    echo "   flatpak install -y flathub org.kde.Platform//6.8 org.kde.Sdk//6.8"
    exit 1
fi

mkdir -p "$DIST_DIR"
mkdir -p "$BUILD_DIR"

echo "🔨 Building Flatpak package using manifest: $MANIFEST..."
flatpak-builder --force-clean --repo="$REPO_DIR" "$BUILD_DIR" "$MANIFEST"

BUNDLE_NAME="quakmeeting.flatpak"
echo "📦 Exporting standalone Flatpak bundle: $DIST_DIR/$BUNDLE_NAME..."
flatpak build-bundle "$REPO_DIR" "$DIST_DIR/$BUNDLE_NAME" com.quakmeeting.QuakMeeting

echo "✅ Flatpak bundle successfully created at $DIST_DIR/$BUNDLE_NAME"
echo "To test run locally:"
echo "   flatpak install --user $DIST_DIR/$BUNDLE_NAME"
echo "   flatpak run com.quakmeeting.QuakMeeting"
