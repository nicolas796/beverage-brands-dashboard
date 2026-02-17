#!/bin/bash
# Start Web Interface - Persistent Version

echo "Starting Web Interface Services..."
echo "=================================="

# Kill any existing processes
pkill -f "uvicorn" 2>/dev/null
pkill -f "npm start" 2>/dev/null
sleep 2

# Get WSL IP
WSL_IP=$(hostname -I | awk '{print $1}')
echo "WSL IP: $WSL_IP"
echo ""

# Start Backend
echo "Starting Backend on port 8000..."
cd /home/baill/.openclaw/workspace/web-interface/backend
source venv/bin/activate
nohup uvicorn app:app --port 8000 --host 0.0.0.0 > server.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

# Test backend
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✓ Backend running on http://$WSL_IP:8000"
else
    echo "✗ Backend failed to start"
fi

# Start Frontend
echo ""
echo "Starting Frontend on port 3000..."
cd /home/baill/.openclaw/workspace/web-interface/frontend
nohup npm start -- --host 0.0.0.0 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
sleep 10

# Test frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ Frontend running on http://$WSL_IP:3000"
else
    echo "✗ Frontend failed to start"
fi

echo ""
echo "=================================="
echo "Access URLs:"
echo "  Frontend: http://$WSL_IP:3000"
echo "  Backend:  http://$WSL_IP:8000"
echo "=================================="
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
