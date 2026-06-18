#!/bin/bash
# linebot_watchdog.sh — Check if LINE Bot is running, restart if not
# Designed to be called by Hermes cron every minute.

SCRIPT_DIR="/opt/data/skills/sanguo"
PID_FILE="/tmp/linebot.pid"
LOG_FILE="/tmp/linebot.log"
PYTHON="${SCRIPT_DIR}/.venv/bin/python"

# Check if venv exists
if [ ! -f "$PYTHON" ]; then
    echo "[watchdog] ERROR: ${PYTHON} not found. Run: cd ${SCRIPT_DIR} && uv venv .venv && uv pip install --python .venv/bin/python requests flask"
    exit 1
fi

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        # Process is alive
        exit 0
    else
        # Stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Not running — start it
echo "[watchdog] LINE Bot not running, starting..."
cd "$SCRIPT_DIR"
nohup "$PYTHON" main.py --monitor > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"
echo "[watchdog] Started (PID: $PID)"
