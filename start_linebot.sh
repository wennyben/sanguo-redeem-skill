#!/bin/bash
# start_linebot.sh — Start LINE Bot webhook server in background with nohup

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/tmp/linebot.log"
PID_FILE="/tmp/linebot.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "LINE Bot is already running (PID: $OLD_PID)"
        echo "Log: $LOG_FILE"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# Check env vars
if [ -z "$LINE_CHANNEL_SECRET" ] || [ -z "$LINE_CHANNEL_ACCESS_TOKEN" ]; then
    echo "Warning: LINE_CHANNEL_SECRET or LINE_CHANNEL_ACCESS_TOKEN not set"
    echo "Trying to load from line_config.json..."
    if [ ! -f "$SCRIPT_DIR/line_config.json" ]; then
        echo "Error: line_config.json not found. Create it from line_config.json.example"
        exit 1
    fi
fi

cd "$SCRIPT_DIR"

nohup /opt/hermes/.venv/bin/python3 main.py --monitor > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

echo "LINE Bot started (PID: $PID)"
echo "Log: $LOG_FILE"
echo ""
echo "To stop:  kill $PID  (or: bash start_linebot.sh stop)"
echo "To check: tail -f $LOG_FILE"
