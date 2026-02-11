#!/bin/bash
# ============================================
# TrustVoice - Stop Local Test Services
# ============================================
# Stops: FastAPI, Celery
# Leaves Redis running (lightweight, shared)
# ============================================

echo ""
echo "🛑 Stopping TrustVoice Test Services..."
echo "========================================="

cd "$(cd "$(dirname "$0")/.." && pwd)"

# ---- Read saved PIDs ----
if [ -f .test_service_pids ]; then
    read API_PID CELERY_PID < .test_service_pids
    echo "   📋 Found PIDs from startup"
else
    API_PID=""
    CELERY_PID=""
    echo "   ⚠️  No .test_service_pids found, will search for processes"
fi

# ---- Stop FastAPI ----
echo ""
echo "1️⃣  Stopping FastAPI server..."
STOPPED=false
if [ -n "$API_PID" ] && ps -p $API_PID > /dev/null 2>&1; then
    kill $API_PID 2>/dev/null
    STOPPED=true
    echo "   ✅ Stopped (PID: $API_PID)"
fi
# Also clean up anything on port 8001
if lsof -ti:8001 > /dev/null 2>&1; then
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    echo "   ✅ Killed process on port 8001"
    STOPPED=true
fi
if [ "$STOPPED" = false ]; then
    echo "   ℹ️  Not running"
fi

# ---- Stop Celery ----
echo ""
echo "2️⃣  Stopping Celery worker..."
STOPPED=false
if [ -n "$CELERY_PID" ] && ps -p $CELERY_PID > /dev/null 2>&1; then
    kill $CELERY_PID 2>/dev/null
    echo "   ✅ Stopped (PID: $CELERY_PID)"
    STOPPED=true
fi
# Also check .celery_worker_pid
if [ -f .celery_worker_pid ]; then
    CW_PID=$(cat .celery_worker_pid)
    if [ -n "$CW_PID" ] && ps -p $CW_PID > /dev/null 2>&1; then
        kill $CW_PID 2>/dev/null
        echo "   ✅ Stopped (PID: $CW_PID from .celery_worker_pid)"
        STOPPED=true
    fi
    rm -f .celery_worker_pid
fi
# Kill any remaining celery processes for this app
pkill -f "celery.*voice.tasks" 2>/dev/null && { echo "   ✅ Killed remaining Celery processes"; STOPPED=true; } || true
if [ "$STOPPED" = false ]; then
    echo "   ℹ️  Not running"
fi

# ---- Redis status ----
echo ""
echo "3️⃣  Redis..."
if command -v redis-cli &> /dev/null && redis-cli ping > /dev/null 2>&1; then
    echo "   ℹ️  Still running (left running intentionally)"
    echo "   💡 To stop: redis-cli shutdown"
else
    echo "   ℹ️  Not running"
fi

# ---- Cleanup ----
rm -f .test_service_pids

echo ""
echo "========================================="
echo "✅ Test services stopped"
echo ""
