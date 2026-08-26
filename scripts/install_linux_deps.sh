#!/bin/bash
set -e

echo "============================================================"
echo " 🐧 Installing QuakMeeting Linux Dependencies on Ubuntu"
echo "============================================================"
echo ""

if ! command -v apt > /dev/null 2>&1; then
    echo "❌ Error: 'apt' package manager not found. Please install PyQt6 and PyGObject manually."
    exit 1
fi

echo "📦 Step 1: Installing system PyQt6 & Evolution Data Server libraries..."
sudo apt update
sudo apt install -y python3-pyqt6 python3-gi \
                    gir1.2-edataserver-1.2 gir1.2-ecal-2.0 \
                    libgirepository1.0-dev pkg-config python3-dev

echo ""
echo "✅ All dependencies installed successfully!"
echo "🚀 You can now run: python3 main.py"
