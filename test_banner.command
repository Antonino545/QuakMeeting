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
echo " 2) 🕵️‍♂️ Secret Agent Platypus (Secret Missions & Agile)"
echo " 3) 🐿️  Hyper Nut Explorer (Brainstorms & Sprints)"
echo " 4) 🍕 Chef Duck (Dinner / Restaurant & Food)"
echo " 5) ✈️  Jet Captain (Flights, Trains & Travel)"
echo " 6) 🎓 Academic Owl (University & Lectures)"
echo " 7) 🏋️‍♂️ Athlete Duck (Palestra / Gym & Sport)"
echo " 8) 🚗 Speed Racer (Driving / Real-Time Navigation)"
echo " 9) 🛋️  Zen Duck (Serenis & Wellness)"
echo "10) ⏱️  Quick Full Screen Test (with 4-second delay)"
echo "11) 🚪 Exit"
echo ""
read -p "Enter your choice [1-11] (default: 10): " CHOICE

if [ -z "$CHOICE" ]; then
    CHOICE="10"
fi

PILOT="duck"
DELAY=0

case "$CHOICE" in
    1)
        PILOT="duck"
        DELAY=1
        ;;
    2)
        PILOT="platypus"
        DELAY=1
        ;;
    3)
        PILOT="squirrel"
        DELAY=1
        ;;
    4)
        PILOT="chef"
        DELAY=1
        ;;
    5)
        PILOT="captain"
        DELAY=1
        ;;
    6)
        PILOT="owl"
        DELAY=1
        ;;
    7)
        PILOT="gym"
        DELAY=1
        ;;
    8)
        PILOT="driver"
        DELAY=1
        ;;
    9)
        PILOT="zen_duck"
        DELAY=1
        ;;
    10)
        echo ""
        echo "Choose the pilot character for the full-screen test:"
        echo " 1) Aviator Duck  2) Agent Platypus  3) Hyper Squirrel  4) Chef  5) Jet Captain  6) Owl  7) Gym  8) Driver  9) Zen Duck"
        read -p "Choice [1-9] (default: 1): " P_CHOICE
        case "$P_CHOICE" in
            2) PILOT="platypus" ;;
            3) PILOT="squirrel" ;;
            4) PILOT="chef" ;;
            5) PILOT="captain" ;;
            6) PILOT="owl" ;;
            7) PILOT="gym" ;;
            8) PILOT="driver" ;;
            9) PILOT="zen_duck" ;;
            *) PILOT="duck" ;;
        esac
        DELAY=4
        ;;
    11)
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
