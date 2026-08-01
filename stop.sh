#!/bin/bash

pkill -f uvicorn
pkill -f "vite --host"
pkill -f "npm run dev"

osascript -e 'display notification "Task Tracker has been stopped." with title "Task Tracker"'

exit 0
