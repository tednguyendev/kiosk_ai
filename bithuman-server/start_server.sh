#!/bin/bash
# Auto-restarting wrapper for the bitHuman kiosk server.
# The bithuman library has a segfault bug in its Cython async generator.
# This script automatically restarts the server when it crashes.
cd "$(dirname "$0")"
source venv/bin/activate
while true; do
    echo "[$(date)] Starting kiosk_server.py..."
    python kiosk_server.py
    EXIT_CODE=$?
    echo "[$(date)] Server exited with code $EXIT_CODE. Restarting in 2 seconds..."
    sleep 2
done
