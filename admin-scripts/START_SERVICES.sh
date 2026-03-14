#!/bin/bash
# TrustVoice - Start All Services
# Run this script to start all required services for the NGO platform

set -e  # Exit on error

echo "🚀 Starting TrustVoice Services..."
echo "===================================="

# Navigate to project directory (parent of admin-scripts)
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"
echo "📂 Project directory: $PROJECT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment
echo ""
echo "1️⃣  Activating Python virtual environment..."
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    echo "   ✅ Virtual environment activated"
else
    echo "   ❌ ERROR: venv not found at $PROJECT_DIR/venv"
    echo "   Please run: python3 -m venv venv"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "   ❌ ERROR: .env file not found!"
    echo "   Please create .env with required variables"
    exit 1
fi

# Load environment variables using set -a
set -a
source .env
set +a
echo "   ✅ Environment variables loaded"

# Check PostgreSQL (Neon cloud database)
echo ""
echo "2️⃣  Checking PostgreSQL (Neon)..."
if python3 << EOF
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    conn.close()
    print("   ✅ PostgreSQL connected (Neon)")
    exit(0)
except Exception as e:
    print(f"   ❌ PostgreSQL connection failed: {e}")
    exit(1)
EOF
then
    :
else
    echo "   ⚠️  Please check DATABASE_URL in .env"
    exit 1
fi

# Check Redis (optional - not critical)
echo ""
echo "3️⃣  Checking Redis (optional)..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis running"
    else
        echo "   ⚠️  Redis not running. Starting Redis..."
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes
            sleep 2
            if redis-cli ping > /dev/null 2>&1; then
                echo "   ✅ Redis started"
            else
                echo "   ⚠️  Failed to start Redis (non-critical)"
            fi
        else
            echo "   ℹ️  Redis not installed (non-critical for development)"
        fi
    fi
else
    echo "   ℹ️  Redis not installed (non-critical for development)"
fi

# Start FastAPI server
echo ""
echo "4️⃣  Starting FastAPI server..."
# Kill any existing uvicorn processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Export all .env variables for uvicorn process
set -a
source .env
set +a

nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > logs/trustvoice_api.log 2>&1 &
API_PID=$!
sleep 3

if ps -p $API_PID > /dev/null && curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "   ✅ FastAPI server started (PID: $API_PID)"
    echo "   📋 Logs: logs/trustvoice_api.log"
    echo "   🌐 API docs: http://localhost:8000/docs"
    echo "   📱 Mini apps: http://localhost:8000/index.html"
else
    echo "   ❌ Failed to start FastAPI server"
    echo "   📋 Check logs: tail -f logs/trustvoice_api.log"
    exit 1
fi

# Start ngrok tunnel (for M-Pesa webhooks)
echo ""
echo "5️⃣  Starting ngrok tunnel..."
pkill ngrok 2>/dev/null || true
sleep 1

nohup ngrok http 8001 > logs/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 3

if ps -p $NGROK_PID > /dev/null; then
    echo "   ✅ ngrok tunnel started (PID: $NGROK_PID)"
    sleep 2
    
    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'ERROR')" 2>/dev/null || echo "ERROR")
    
    if [ "$NGROK_URL" != "ERROR" ] && [ -n "$NGROK_URL" ]; then
        echo "   🌐 Public URL: $NGROK_URL"
        echo "   📊 Dashboard: http://localhost:4040"
        
        # Update M-Pesa callback URLs in .env
        echo ""
        echo "6️⃣  Updating M-Pesa webhook URLs..."
        python3 << EOF
import os
import re

env_file = '.env'
ngrok_url = "${NGROK_URL}"
stk_webhook_url = f"{ngrok_url}/webhooks/mpesa"
b2c_result_url = f"{ngrok_url}/webhooks/mpesa/b2c/result"
b2c_timeout_url = f"{ngrok_url}/webhooks/mpesa/b2c/timeout"

# Read .env file
with open(env_file, 'r') as f:
    content = f.read()

# Update MPESA_CALLBACK_URL (STK Push)
if 'MPESA_CALLBACK_URL=' in content:
    content = re.sub(
        r'MPESA_CALLBACK_URL=.*',
        f'MPESA_CALLBACK_URL={stk_webhook_url}',
        content
    )
else:
    content += f'\nMPESA_CALLBACK_URL={stk_webhook_url}\n'

# Update MPESA_B2C_RESULT_URL
if 'MPESA_B2C_RESULT_URL=' in content:
    content = re.sub(
        r'MPESA_B2C_RESULT_URL=.*',
        f'MPESA_B2C_RESULT_URL={b2c_result_url}',
        content
    )
else:
    content += f'\nMPESA_B2C_RESULT_URL={b2c_result_url}\n'

# Update MPESA_B2C_QUEUE_TIMEOUT_URL
if 'MPESA_B2C_QUEUE_TIMEOUT_URL=' in content:
    content = re.sub(
        r'MPESA_B2C_QUEUE_TIMEOUT_URL=.*',
        f'MPESA_B2C_QUEUE_TIMEOUT_URL={b2c_timeout_url}',
        content
    )
else:
    content += f'\nMPESA_B2C_QUEUE_TIMEOUT_URL={b2c_timeout_url}\n'

# Write back
with open(env_file, 'w') as f:
    f.write(content)

print(f"   ✅ M-Pesa STK Push webhook: {stk_webhook_url}")
print(f"   ✅ M-Pesa B2C Result URL: {b2c_result_url}")
print(f"   ✅ M-Pesa B2C Timeout URL: {b2c_timeout_url}")
EOF
    else
        echo "   ⚠️  Could not get ngrok URL - manual webhook setup required"
    fi
else
    echo "   ❌ Failed to start ngrok"
    echo "   ℹ️  You can start manually: ngrok http 8001"
fi

# Start Telegram Bot (enabled by default)
TELEGRAM_BOT_PID=""
echo ""
echo "7️⃣  Starting Celery worker for voice processing..."
# Kill any existing Celery worker
if [ -f .celery_worker_pid ]; then
    OLD_CELERY_PID=$(cat .celery_worker_pid)
    kill $OLD_CELERY_PID 2>/dev/null || true
fi

# Start Celery from project root with proper PYTHONPATH
cd "$PROJECT_DIR"
nohup venv/bin/python -m celery -A voice.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=voice,notifications \
    > logs/celery_worker.log 2>&1 &
CELERY_PID=$!
echo $CELERY_PID > .celery_worker_pid
sleep 3

if ps -p $CELERY_PID > /dev/null; then
    echo "   ✅ Celery worker started (PID: $CELERY_PID)"
    echo "   📋 Logs: logs/celery_worker.log"
else
    echo "   ❌ Failed to start Celery worker"
    echo "   📋 Check logs: tail -f logs/celery_worker.log"
    CELERY_PID=""
fi

echo ""
echo "8️⃣  Starting Telegram Bot..."
if [ "${START_TELEGRAM_BOT:-true}" = "true" ]; then
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        echo "   ⚠️  TELEGRAM_BOT_TOKEN not set in .env, skipping bot"
    elif [ -z "$OPENAI_API_KEY" ]; then
        echo "   ⚠️  OPENAI_API_KEY not set in .env, skipping bot"
    else
        # Kill any existing bot process
        if [ -f .telegram_bot_pid ]; then
            OLD_BOT_PID=$(cat .telegram_bot_pid)
            kill $OLD_BOT_PID 2>/dev/null || true
        fi
        
        nohup python voice/telegram/bot.py > logs/telegram_bot.log 2>&1 &
        TELEGRAM_BOT_PID=$!
        echo $TELEGRAM_BOT_PID > .telegram_bot_pid
        sleep 2
        
        if ps -p $TELEGRAM_BOT_PID > /dev/null; then
            echo "   ✅ Telegram bot started (PID: $TELEGRAM_BOT_PID)"
            echo "   📋 Logs: logs/telegram_bot.log"
        else
            echo "   ❌ Failed to start Telegram bot"
            echo "   📋 Check logs: tail -f logs/telegram_bot.log"
            TELEGRAM_BOT_PID=""
        fi
    fi
else
    echo "   ℹ️  Telegram bot disabled (set START_TELEGRAM_BOT=true in .env to enable)"
fi

# Start LiveKit voice agent worker
LIVEKIT_PID=""
echo ""
echo "9️⃣  Starting LiveKit voice agent..."
if [ -f "$PROJECT_DIR/venv-livekit/bin/activate" ]; then
    lsof -ti:8089 | xargs kill -9 2>/dev/null || true
    nohup "$PROJECT_DIR/venv-livekit/bin/python" -m voice.livekit_agent dev \
        > logs/livekit_agent.log 2>&1 &
    LIVEKIT_PID=$!
    sleep 3
    if ps -p $LIVEKIT_PID > /dev/null; then
        echo "   ✅ LiveKit agent started (PID: $LIVEKIT_PID)"
        echo "   📋 Logs: logs/livekit_agent.log"
    else
        echo "   ⚠️  Failed to start LiveKit agent"
        echo "   📋 Check logs: tail -f logs/livekit_agent.log"
        LIVEKIT_PID=""
    fi
else
    echo "   ⚠️  venv-livekit not found, skipping LiveKit agent"
fi

# Start Vite dev server for React frontend
VITE_PID=""
echo ""
echo "🔟  Starting Vite dev server (React frontend)..."
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1
if [ -d "$PROJECT_DIR/web-frontend" ] && [ -f "$PROJECT_DIR/web-frontend/package.json" ]; then
    cd "$PROJECT_DIR/web-frontend"
    nohup npx vite --host > "$PROJECT_DIR/logs/vite_dev.log" 2>&1 &
    VITE_PID=$!
    cd "$PROJECT_DIR"
    sleep 3
    if ps -p $VITE_PID > /dev/null; then
        echo "   ✅ Vite dev server started (PID: $VITE_PID)"
        echo "   📋 Logs: logs/vite_dev.log"
        echo "   🌐 Frontend: http://localhost:5173"
    else
        echo "   ⚠️  Failed to start Vite dev server"
        echo "   📋 Check logs: tail -f logs/vite_dev.log"
        VITE_PID=""
    fi
else
    echo "   ⚠️  web-frontend not found, skipping Vite"
fi

# Save PIDs to file for shutdown
echo "$API_PID $NGROK_PID $TELEGRAM_BOT_PID $CELERY_PID $LIVEKIT_PID $VITE_PID" > .service_pids

echo ""
echo "===================================="
echo "✅ All services started successfully!"
echo "===================================="
echo ""
echo "📝 Service Status:"
echo "   • PostgreSQL:    Running (Neon Cloud)"
if redis-cli ping > /dev/null 2>&1; then
    echo "   • Redis:         Running (localhost)"
else
    echo "   • Redis:         Not running (optional)"
fi
echo "   • FastAPI:       PID $API_PID (http://localhost:8000)"
if [ "$NGROK_URL" != "ERROR" ] && [ -n "$NGROK_URL" ]; then
    echo "   • ngrok:         PID $NGROK_PID ($NGROK_URL)"
fi
if [ -n "$TELEGRAM_BOT_PID" ]; then
    echo "   • Telegram Bot:  PID $TELEGRAM_BOT_PID"
fi
if [ -n "$CELERY_PID" ]; then
    echo "   • Celery Worker: PID $CELERY_PID"
fi
if [ -n "$LIVEKIT_PID" ]; then
    echo "   • LiveKit Agent: PID $LIVEKIT_PID"
fi
if [ -n "$VITE_PID" ]; then
    echo "   • Vite Frontend: PID $VITE_PID (http://localhost:5173)"
fi
echo ""
echo "📋 Logs:"
echo "   • API:     tail -f logs/trustvoice_api.log"
echo "   • ngrok:   tail -f logs/ngrok.log"
if [ -n "$TELEGRAM_BOT_PID" ]; then
    echo "   • Bot:     tail -f logs/telegram_bot.log"
fi
if [ -n "$CELERY_PID" ]; then
    echo "   • Celery:  tail -f logs/celery_worker.log"
fi
if [ -n "$LIVEKIT_PID" ]; then
    echo "   • LiveKit: tail -f logs/livekit_agent.log"
fi
if [ -n "$VITE_PID" ]; then
    echo "   • Vite:    tail -f logs/vite_dev.log"
fi
echo ""
echo "🔗 Quick Links:"
echo "   • API Docs:      http://localhost:8000/docs"
echo "   • Mini Apps Menu: http://localhost:8000/index.html"
echo "   • ngrok Dashboard: http://localhost:4040"
if [ "$NGROK_URL" != "ERROR" ] && [ -n "$NGROK_URL" ]; then
    echo "   • Public API:    $NGROK_URL/docs"
    echo "   • Public Mini Apps: $NGROK_URL/index.html"
    echo "   • M-Pesa Webhook: $NGROK_URL/webhooks/mpesa"
    echo ""
    echo "📱 Telegram Mini Apps:"
    echo "   • Analytics:    $NGROK_URL/analytics.html"
    echo "   • Campaigns:    $NGROK_URL/campaigns.html"
    echo "   • Admin:        $NGROK_URL/admin.html"
    echo "   • Donate:       $NGROK_URL/donate.html"
    echo "   • NGO Register: $NGROK_URL/ngo-register.html"
fi
echo ""
echo "🛑 To stop all services, run: ./admin-scripts/STOP_SERVICES.sh"
echo ""
