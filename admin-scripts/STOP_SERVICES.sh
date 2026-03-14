#!/bin/bash
# TrustVoice - Stop All Services
# Run this script to cleanly stop all TrustVoice services

echo "🛑 Stopping TrustVoice Services..."
echo "===================================="

cd "$(dirname "$0")/.."

# Read PIDs from file if it exists
if [ -f .service_pids ]; then
    read API_PID NGROK_PID TELEGRAM_BOT_PID CELERY_PID LIVEKIT_PID VITE_PID < .service_pids
    echo "📋 Found service PIDs from startup"
else
    echo "⚠️  No .service_pids file found, will search for processes"
    API_PID=""
    NGROK_PID=""
    TELEGRAM_BOT_PID=""
    CELERY_PID=""
    LIVEKIT_PID=""
    VITE_PID=""
fi

# Stop FastAPI server
echo ""
echo "1️⃣  Stopping FastAPI server..."
if [ -n "$API_PID" ] && ps -p $API_PID > /dev/null 2>&1; then
    kill $API_PID
    echo "   ✅ FastAPI server stopped (PID: $API_PID)"
else
    # Fallback: kill by port
    if lsof -ti:8000 > /dev/null 2>&1; then
        lsof -ti:8000 | xargs kill -9
        echo "   ✅ FastAPI server stopped (port 8000)"
    else
        echo "   ℹ️  No FastAPI server running on port 8000"
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

# Stop Telegram Bot
echo ""
echo "5️⃣  Stopping Telegram bot..."
# First try PID from startup
BOT_STOPPED=false
if [ -n "$TELEGRAM_BOT_PID" ] && ps -p $TELEGRAM_BOT_PID > /dev/null 2>&1; then
    kill $TELEGRAM_BOT_PID
    echo "   ✅ Telegram bot stopped (PID: $TELEGRAM_BOT_PID)"
    BOT_STOPPED=true
fi

# Also check .telegram_bot_pid file
if [ -f .telegram_bot_pid ]; then
    BOT_PID=$(cat .telegram_bot_pid)
    if [ -n "$BOT_PID" ] && ps -p $BOT_PID > /dev/null 2>&1; then
        kill $BOT_PID
        echo "   ✅ Telegram bot stopped (PID: $BOT_PID from .telegram_bot_pid)"
        BOT_STOPPED=true
    fi
    rm -f .telegram_bot_pid
fi

if [ "$BOT_STOPPED" = false ]; then
    # Fallback: kill by process name
    if pgrep -f "voice/telegram/bot.py" > /dev/null; then
        pkill -f "voice/telegram/bot.py"
        echo "   ✅ Telegram bot stopped (by process name)"
    else
        echo "   ℹ️  No Telegram bot running"
    fi
fi

# Stop Celery Worker
echo ""
echo "6️⃣  Stopping Celery worker..."
CELERY_STOPPED=false
if [ -n "$CELERY_PID" ] && ps -p $CELERY_PID > /dev/null 2>&1; then
    kill $CELERY_PID
    echo "   ✅ Celery worker stopped (PID: $CELERY_PID)"
    CELERY_STOPPED=true
fi

# Also check .celery_worker_pid file
if [ -f .celery_worker_pid ]; then
    CELERY_PID_FILE=$(cat .celery_worker_pid)
    if [ -n "$CELERY_PID_FILE" ] && ps -p $CELERY_PID_FILE > /dev/null 2>&1; then
        kill $CELERY_PID_FILE
        echo "   ✅ Celery worker stopped (PID: $CELERY_PID_FILE from .celery_worker_pid)"
        CELERY_STOPPED=true
    fi
    rm -f .celery_worker_pid
fi

if [ "$CELERY_STOPPED" = false ]; then
    # Fallback: kill by process name
    if pgrep -f "celery.*worker" > /dev/null; then
        pkill -f "celery.*worker"
        echo "   ✅ Celery worker stopped (by process name)"
    else
        echo "   ℹ️  No Celery worker running"
    fi
fi

# Clean up PID file
rm -f .service_pids

# Stop LiveKit voice agent
echo ""
echo "8️⃣  Stopping LiveKit voice agent..."
LK_STOPPED=false
if [ -n "$LIVEKIT_PID" ] && ps -p $LIVEKIT_PID > /dev/null 2>&1; then
    kill $LIVEKIT_PID
    echo "   ✅ LiveKit agent stopped (PID: $LIVEKIT_PID)"
    LK_STOPPED=true
fi
if [ "$LK_STOPPED" = false ]; then
    if pgrep -f "voice.livekit_agent" > /dev/null; then
        pkill -f "voice.livekit_agent"
        echo "   ✅ LiveKit agent stopped (by process name)"
    else
        echo "   ℹ️  No LiveKit agent running"
    fi
fi

# Stop Vite dev server
echo ""
echo "9️⃣  Stopping Vite dev server..."
VITE_STOPPED=false
if [ -n "$VITE_PID" ] && ps -p $VITE_PID > /dev/null 2>&1; then
    kill $VITE_PID
    echo "   ✅ Vite dev server stopped (PID: $VITE_PID)"
    VITE_STOPPED=true
fi
if [ "$VITE_STOPPED" = false ]; then
    if lsof -ti:5173 > /dev/null 2>&1; then
        lsof -ti:5173 | xargs kill -9
        echo "   ✅ Vite dev server stopped (port 5173)"
    else
        echo "   ℹ️  No Vite dev server running"
    fi
fi

# Clean up old log files (optional)
echo ""
echo "7️⃣  Cleaning up old logs..."
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
