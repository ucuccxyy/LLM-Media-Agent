#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT="$SCRIPT_DIR"

# Define the path to the PID file relative to the script's location
PID_DIR="$PROJECT_ROOT/media_agent/pids"
PID_FILE="$PID_DIR/api.pid"

# Change to the script's directory to ensure the PID file is found correctly
cd "$PROJECT_ROOT" || exit

# Check if the PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo "API service is not running (or PID file not found)."
    exit 1
fi

# Read the PID from the file
PID=$(cat "$PID_FILE")

# Check if the process is actually running
if ! ps -p "$PID" > /dev/null; then
    echo "API service with PID $PID is not running (stale PID file)."
    # Clean up the stale PID file
    rm "$PID_FILE"
    exit 1
fi

# Try to stop the process gracefully
echo "Stopping API service with PID: $PID..."
kill "$PID"

# Wait a moment and check if the process has stopped
sleep 2
if ps -p "$PID" > /dev/null; then
    echo "Service did not stop gracefully. Forcing shutdown (kill -9)..."
    kill -9 "$PID"
fi

# Remove the PID file
rm "$PID_FILE"

echo "API service stopped successfully." 