#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "Avvio Test Banner Notifica QuakMeeting..."
python3 "$DIR/main.py" --test
