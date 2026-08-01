#!/bin/bash

PROJECT="$HOME/GitHub/task-tracker-api"

# Splash screen
osascript <<EOF &
display dialog "Starting Task Tracker..." with title "Task Tracker" buttons {} giving up after 4
EOF

# Create logs directory
mkdir -p "$PROJECT/logs"

# Start backend
cd "$PROJECT"
source venv/bin/activate
nohup uvicorn main:app --reload > "$PROJECT/logs/backend.log" 2>&1 < /dev/null &

# Start frontend
cd "$PROJECT/frontend"
nohup npm run dev -- --host > "$PROJECT/logs/frontend.log" 2>&1 < /dev/null &

# Wait for servers
sleep 5

# Open app
open http://localhost:5173
open http://127.0.0.1:8000/docs

exit 0
