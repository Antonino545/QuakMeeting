#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Set PATH
export PATH="/opt/miniconda3/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

# Find Python interpreter with PyObjC / AppKit
PYTHON_BIN=""
for p in "/opt/miniconda3/bin/python3" "/usr/local/bin/python3" "/opt/homebrew/bin/python3" "$(which python3)"; do
    if [ -n "$p" ] && [ -x "$p" ] && "$p" -c "import AppKit" 2>/dev/null; then
        PYTHON_BIN="$p"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

clear
echo "============================================================"
echo " 🦆 QuakMeeting - Banner & Full Screen Overlay Test"
echo "============================================================"
echo ""
echo "Select which notification banner to test over your Full Screen apps:"
echo ""
echo " 1) 🦆 Classic Aviator Duck (Google Meet / Zoom)"
echo " 2) 🍕 Chef Duck (Dinner / Restaurant & Food)"
echo " 3) ✈️  Jet Captain (Flights, Trains & Travel)"
echo " 4) 🎓 Academic Owl (University & Lectures)"
echo " 5) 🚗 Speed Racer (Driving / Real-Time Navigation)"
echo " 6) 🛋️  Zen Duck (Serenis & Wellness)"
echo " 7) ⏱️  Quick Full Screen Test (with 4-second delay)"
echo " 8) 🚪 Exit"
echo ""
read -p "Enter your choice [1-8] (default: 7): " CHOICE

if [ -z "$CHOICE" ]; then
    CHOICE="7"
fi

PILOT="duck"
DELAY=0

case "$CHOICE" in
    1)
        PILOT="duck"
        DELAY=1
        ;;
    2)
        PILOT="chef"
        DELAY=1
        ;;
    3)
        PILOT="captain"
        DELAY=1
        ;;
    4)
        PILOT="owl"
        DELAY=1
        ;;
    5)
        PILOT="driver"
        DELAY=1
        ;;
    6)
        PILOT="zen_duck"
        DELAY=1
        ;;
    7)
        echo ""
        echo "Choose the pilot character for the full-screen test:"
        echo " 1) Aviator Duck  2) Chef  3) Jet Captain  4) Academic Owl  5) Speed Racer  6) Zen Duck"
        read -p "Choice [1-6] (default: 1): " P_CHOICE
        case "$P_CHOICE" in
            2) PILOT="chef" ;;
            3) PILOT="captain" ;;
            4) PILOT="owl" ;;
            5) PILOT="driver" ;;
            6) PILOT="zen_duck" ;;
            *) PILOT="duck" ;;
        esac
        DELAY=4
        ;;
    8)
        echo "Exiting..."
        exit 0
        ;;
    *)
        PILOT="duck"
        DELAY=1
        ;;
esac

echo ""
echo "💡 TIP:"
echo "Switch NOW to any Full Screen app (Safari, Chrome, YouTube, Keynote, etc.)!"
echo ""

"$PYTHON_BIN" "$DIR/main.py" --test --pilot "$PILOT" --delay "$DELAY"

echo ""
echo "✅ Test finished. Press Enter to close..."
read
