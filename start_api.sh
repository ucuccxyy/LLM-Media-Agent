#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Project paths
PROJECT_ROOT="$SCRIPT_DIR"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
MAIN_SCRIPT="$PROJECT_ROOT/main.py"
PID_DIR="$PROJECT_ROOT/media_agent/pids"
PID_FILE="$PID_DIR/api.pid"
LOG_DIR="$PROJECT_ROOT/media_agent/logs"
LOG_FILE="$LOG_DIR/api.log"

# Change to the script's directory to ensure correct relative paths
cd "$SCRIPT_DIR" || exit

# Create directories if they don't exist
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

# Check if the service is already running
if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo "API service is already running with PID: $PID"
        exit 1
    else
        # The PID file exists but the process is dead, remove the stale file
        echo "Found stale PID file. Removing it."
        rm $PID_FILE
    fi
fi

# Start the API service in the background
echo "Starting API service..."
nohup $VENV_PYTHON -u $MAIN_SCRIPT --mode api > $LOG_FILE 2>&1 &

# Get the Process ID (PID) of the last background command
APP_PID=$!

# Save the PID to the file
echo $APP_PID > $PID_FILE

echo "API service started successfully."
echo "PID: $APP_PID"
echo "Logs are being written to: $LOG_FILE"
echo "To view logs in real-time, run: tail -f $LOG_FILE"
echo "To stop the service, run: ./stop_api.sh" 