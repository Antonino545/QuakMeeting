#!/bin/bash
set -e

echo "============================================================"
echo " 🐧 Installing QuakMeeting Linux Dependencies on Ubuntu"
echo "============================================================"
echo ""

if ! command -v apt > /dev/null 2>&1; then
    echo "❌ Error: 'apt' package manager not found. Please install PyGObject, GTK3 and AppIndicator manually."
    exit 1
fi

echo "📦 Step 1: Installing system GTK3, AppIndicator3 & Layer-Shell libraries..."
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                    gir1.2-appindicator3-0.1 gir1.2-gtklayershell-0.1 \
                    libgirepository1.0-dev libcairo2-dev pkg-config python3-dev

echo ""
echo "✅ All dependencies installed successfully!"
echo "🚀 You can now run: python3 main.py"
