#!/bin/bash
# Auto-restarting wrapper for the bitHuman kiosk server.
# The bithuman Cython runtime leaks frame buffers; we can't fix it (closed source).
# Strategy:
#   1. OUTPUT_WIDTH=640 + FPS=15  → smaller buffers, slower leak
#   2. Auto-restart on crash (segfault)
#   3. Proactive restart when RSS > 2.5GB (before macOS OOM-kills us)
# The frontend handles disconnects gracefully (index-bithuman.html).

cd "$(dirname "$0")"
source venv/bin/activate

# Tuning knobs that REDUCE footprint and slow the leak
export OUTPUT_WIDTH=640
export FPS=15
export PROCESS_IDLE_VIDEO=false
export PRELOAD_TO_MEMORY=false

# Avoid knobs that made things worse in experiments
# export LOADING_MODE=ON_DEMAND

RESTART_MB=3000   # RSS threshold in MB
CHECK_SEC=60      # how often to check memory

echo "[$(date)] Memory guard: restart if RSS > ${RESTART_MB}MB, check every ${CHECK_SEC}s"

while true; do
    echo "[$(date)] Starting kiosk_server.py..."
    python kiosk_server.py &
    PID=$!
    echo "[$(date)] Server PID $PID"

    # Background memory monitor
    while kill -0 $PID 2>/dev/null; do
        sleep $CHECK_SEC
        if ! kill -0 $PID 2>/dev/null; then
            break
        fi
        # Get RSS in KB, convert to MB
        RSS_KB=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
        if [ -n "$RSS_KB" ]; then
            RSS_MB=$((RSS_KB / 1024))
            if [ "$RSS_MB" -gt "$RESTART_MB" ]; then
                echo "[$(date)] RSS ${RSS_MB}MB > ${RESTART_MB}MB — proactively restarting..."
                kill $PID
                wait $PID 2>/dev/null
                break
            fi
        fi
    done

    # If monitor killed it, short pause before restart
    # If it crashed on its own, the wait already returned
    EXIT_CODE=$?
    echo "[$(date)] Server exited (code $EXIT_CODE). Restarting in 3 seconds..."
    sleep 3
done
