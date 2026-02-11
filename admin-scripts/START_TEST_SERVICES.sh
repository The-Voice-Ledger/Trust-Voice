#!/bin/bash
# ============================================
# TrustVoice - Start Local Test Services
# ============================================
# Starts ONLY: Redis, FastAPI, Celery
# Does NOT start: Telegram bot, ngrok
# (Telegram bot runs on Railway via webhooks)
# ============================================

set -e

echo ""
echo "🧪 Starting TrustVoice Test Services"
echo "====================================="
echo "   Redis + FastAPI + Celery (no bot, no ngrok)"
echo ""

# Navigate to project root
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# ---- Virtual environment ----
echo "1️⃣  Checking Python virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Activated venv ($(python --version))"
else
    echo "   ❌ No venv found. Run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# ---- Load .env ----
echo ""
echo "2️⃣  Loading environment variables..."
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "   ✅ Loaded .env"
else
    echo "   ❌ No .env file found"
    exit 1
fi

# Force development mode
export APP_ENV=development

# ---- Logs directory ----
mkdir -p logs

# ---- Redis ----
echo ""
echo "3️⃣  Checking Redis..."
if command -v redis-cli &> /dev/null && redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis already running"
else
    echo "   ⏳ Starting Redis..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes --loglevel warning
        sleep 1
        if redis-cli ping > /dev/null 2>&1; then
            echo "   ✅ Redis started"
        else
            echo "   ⚠️  Redis failed to start (sessions will fall back to in-memory)"
        fi
    else
        echo "   ⚠️  Redis not installed (brew install redis)"
        echo "   ℹ️  Continuing without Redis — sessions will use in-memory fallback"
    fi
fi

# ---- PostgreSQL (Neon) ----
echo ""
echo "4️⃣  Checking PostgreSQL (Neon)..."
if [ -z "$DATABASE_URL" ]; then
    echo "   ❌ DATABASE_URL not set in .env"
    exit 1
fi
python -c "
from sqlalchemy import create_engine, text
import os
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('   ✅ PostgreSQL (Neon) connected')
except Exception as e:
    print(f'   ⚠️  PostgreSQL connection issue: {e}')
    print('   ℹ️  Some features may not work')
" 2>/dev/null || echo "   ⚠️  Could not verify PostgreSQL connection"

# ---- FastAPI ----
echo ""
echo "5️⃣  Starting FastAPI server..."

# Kill any existing process on port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 1

nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    > logs/trustvoice_api.log 2>&1 &
API_PID=$!
sleep 3

if ps -p $API_PID > /dev/null 2>&1 && curl -s http://localhost:8001/docs > /dev/null 2>&1; then
    echo "   ✅ FastAPI started (PID: $API_PID)"
    echo "   📋 Logs: tail -f logs/trustvoice_api.log"
else
    echo "   ❌ FastAPI failed to start"
    echo "   📋 Check: tail -20 logs/trustvoice_api.log"
    exit 1
fi

# ---- Celery ----
echo ""
echo "6️⃣  Starting Celery worker..."

# Kill any existing Celery worker
if [ -f .celery_worker_pid ]; then
    OLD_PID=$(cat .celery_worker_pid)
    kill $OLD_PID 2>/dev/null || true
    sleep 1
fi

nohup "$PROJECT_DIR/venv/bin/python" -m celery -A voice.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=voice,notifications \
    > logs/celery_worker.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > .celery_worker_pid
sleep 3

if ps -p $CELERY_PID > /dev/null 2>&1; then
    echo "   ✅ Celery worker started (PID: $CELERY_PID)"
    echo "   📋 Logs: tail -f logs/celery_worker.log"
else
    echo "   ⚠️  Celery worker failed to start"
    echo "   📋 Check: tail -20 logs/celery_worker.log"
    echo "   ℹ️  API will still work, but async voice tasks won't process"
    CELERY_PID=""
fi

# ---- Save PIDs ----
echo "$API_PID ${CELERY_PID:-}" > .test_service_pids

# ---- Summary ----
echo ""
echo "====================================="
echo "✅ Test services ready!"
echo "====================================="
echo ""
echo "📝 Running Services:"
echo "   • Redis:         $(redis-cli ping 2>/dev/null && echo 'Running' || echo 'Not running')"
echo "   • PostgreSQL:    Neon Cloud"
echo "   • FastAPI:       PID $API_PID → http://localhost:8001"
if [ -n "$CELERY_PID" ]; then
    echo "   • Celery:        PID $CELERY_PID"
fi
echo ""
echo "🔗 Quick Links:"
echo "   • API Docs:      http://localhost:8001/docs"
echo "   • Mini Apps:     http://localhost:8001/index.html"
echo ""
echo "📋 Tail Logs:"
echo "   • API:     tail -f logs/trustvoice_api.log"
echo "   • Celery:  tail -f logs/celery_worker.log"
echo ""
echo "🧪 Run Tests:"
echo "   • pytest tests/ -v"
echo "   • curl http://localhost:8001/health"
echo ""
echo "🛑 Stop: ./admin-scripts/STOP_TEST_SERVICES.sh"
echo ""
