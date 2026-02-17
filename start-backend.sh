#!/bin/bash
# Start the Beverage Social Listener Web Interface

cd /home/baill/.openclaw/workspace/web-interface/backend
source venv/bin/activate

echo "Starting backend server..."
uvicorn app:app --reload --port 8000 --host 0.0.0.0
