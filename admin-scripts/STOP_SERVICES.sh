#!/bin/bash
# TrustVoice - Stop All Services
# Run this script to cleanly stop all TrustVoice services

echo "🛑 Stopping TrustVoice Services..."
echo "===================================="

cd "$(dirname "$0")/.."

# Read PIDs from file if it exists
if [ -f .service_pids ]; then
    read API_PID NGROK_PID < .service_pids
    echo "📋 Found service PIDs from startup"
else
    echo "⚠️  No .service_pids file found, will search for processes"
    API_PID=""
    NGROK_PID=""
fi

# Stop FastAPI server
echo ""
echo "1️⃣  Stopping FastAPI server..."
if [ -n "$API_PID" ] && ps -p $API_PID > /dev/null 2>&1; then
    kill $API_PID
    echo "   ✅ FastAPI server stopped (PID: $API_PID)"
else
    # Fallback: kill by port
    if lsof -ti:8001 > /dev/null 2>&1; then
        lsof -ti:8001 | xargs kill -9
        echo "   ✅ FastAPI server stopped (port 8001)"
    else
        echo "   ℹ️  No FastAPI server running on port 8001"
    fi
fi

# Stop ngrok
echo ""
echo "2️⃣  Stopping ngrok tunnel..."
if [ -n "$NGROK_PID" ] && ps -p $NGROK_PID > /dev/null 2>&1; then
    kill $NGROK_PID
    echo "   ✅ ngrok tunnel stopped (PID: $NGROK_PID)"
else
    pkill ngrok && echo "   ✅ ngrok tunnel stopped" || echo "   ℹ️  No ngrok running"
fi

# Redis status (optional - usually leave running)
echo ""
echo "3️⃣  Redis status..."
if command -v redis-cli &> /dev/null && redis-cli ping > /dev/null 2>&1; then
    echo "   ℹ️  Redis still running (use 'redis-cli shutdown' to stop)"
else
    echo "   ℹ️  Redis not running"
fi

# PostgreSQL status (Neon cloud - always running)
echo ""
echo "4️⃣  PostgreSQL status..."
echo "   ℹ️  PostgreSQL (Neon Cloud) - managed service, always available"

# Clean up PID file
rm -f .service_pids

# Clean up old log files (optional)
echo ""
echo "5️⃣  Cleaning up old logs..."
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime +7 -delete 2>/dev/null && echo "   ✅ Old log files cleaned (>7 days)" || echo "   ℹ️  No old logs to clean"
else
    echo "   ℹ️  No logs directory"
fi

echo ""
echo "===================================="
echo "✅ All services stopped"
echo "===================================="
echo ""
echo "💡 To start services again, run: ./admin-scripts/START_SERVICES.sh"
echo ""
