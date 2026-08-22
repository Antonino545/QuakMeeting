#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Imposta il PATH
export PATH="/opt/miniconda3/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

# Cerca l'interprete Python con PyObjC/AppKit
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
echo " 🦆 QuakMeeting - Test Banner & Full Screen Overlay"
echo "============================================================"
echo ""
echo "Scegli che tipo di banner testare sopra le tue app a Schermo Intero:"
echo ""
echo " 1) 🦆 Papero Aviatore Classico (Google Meet / Zoom)"
echo " 2) 🍕 Chef Duck (Cena in Pizzeria / Cibo)"
echo " 3) ✈️  Capitano Jet (Volo Aereo / Viaggio)"
echo " 4) 🎓 Gufo Accademico (Studio / Lezione Universitaria)"
echo " 5) 🚗 Speed Racer (Auto / Navigazione Mappe)"
echo " 6) 🛋️  Zen Duck (Serenis / Benessere)"
echo " 7) ⏱️  Test Schermo Intero Rapido (con countdown di 4 sec)"
echo " 8) 🚪 Esci"
echo ""
read -p "Inserisci la tua scelta [1-8] (default: 7): " CHOICE

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
        echo "Scegli il pilota per il test a schermo intero:"
        echo " 1) Papero Aviatore  2) Chef  3) Capitano Jet  4) Gufo  5) Driver  6) Zen Duck"
        read -p "Scelta [1-6] (default: 1): " P_CHOICE
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
        echo "Uscita..."
        exit 0
        ;;
    *)
        PILOT="duck"
        DELAY=1
        ;;
esac

echo ""
echo "💡 SUGGERIMENTO:"
echo "Passa ORA all'app a Schermo Intero (Safari, Chrome, YouTube, Keynote, ecc.)!"
echo ""

"$PYTHON_BIN" "$DIR/main.py" --test --pilot "$PILOT" --delay "$DELAY"

echo ""
echo "✅ Test completato. Premi Invio per chiudere..."
read
