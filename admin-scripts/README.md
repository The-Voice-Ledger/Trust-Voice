# TrustVoice Admin Scripts

Scripts for managing TrustVoice services during development and testing.

## Available Scripts

### START_SERVICES.sh
Starts all required services for TrustVoice platform:
- PostgreSQL connection check (Neon Cloud)
- Redis check (optional)
- FastAPI server (port 8001)
- ngrok tunnel (for M-Pesa webhooks)

**Usage:**
```bash
./admin-scripts/START_SERVICES.sh
```

**What it does:**
1. Activates Python virtual environment
2. Loads environment variables from `.env`
3. Checks database connectivity
4. Starts FastAPI server on http://localhost:8001
5. Creates ngrok tunnel with public URL
6. Automatically updates `MPESA_CALLBACK_URL` in `.env`
7. Saves process IDs for clean shutdown

**Output:**
```
🚀 Starting TrustVoice Services...
====================================
📂 Project directory: /Users/manu/Trust-Voice

1️⃣  Activating Python virtual environment...
   ✅ Virtual environment activated
   ✅ Environment variables loaded

2️⃣  Checking PostgreSQL (Neon)...
   ✅ PostgreSQL connected (Neon)

3️⃣  Checking Redis (optional)...
   ✅ Redis running

4️⃣  Starting FastAPI server...
   ✅ FastAPI server started (PID: 12345)
   📋 Logs: logs/trustvoice_api.log
   🌐 API docs: http://localhost:8001/docs

5️⃣  Starting ngrok tunnel...
   ✅ ngrok tunnel started (PID: 12346)
   🌐 Public URL: https://abc123.ngrok.io
   📊 Dashboard: http://localhost:4040

6️⃣  Updating M-Pesa webhook URL...
   ✅ M-Pesa webhook URL updated: https://abc123.ngrok.io/webhooks/mpesa

====================================
✅ All services started successfully!
====================================

📝 Service Status:
   • PostgreSQL:    Running (Neon Cloud)
   • Redis:         Running (localhost)
   • FastAPI:       PID 12345 (http://localhost:8001)
   • ngrok:         PID 12346 (https://abc123.ngrok.io)

📋 Logs:
   • API:     tail -f logs/trustvoice_api.log
   • ngrok:   tail -f logs/ngrok.log

🔗 Quick Links:
   • API Docs:       http://localhost:8001/docs
   • ngrok Dashboard: http://localhost:4040
   • Public API:     https://abc123.ngrok.io/docs
   • M-Pesa Webhook: https://abc123.ngrok.io/webhooks/mpesa

🛑 To stop all services, run: ./admin-scripts/STOP_SERVICES.sh
```

---

### STOP_SERVICES.sh
Cleanly stops all running TrustVoice services.

**Usage:**
```bash
./admin-scripts/STOP_SERVICES.sh
```

**What it does:**
1. Reads saved process IDs from `.service_pids`
2. Stops FastAPI server gracefully
3. Stops ngrok tunnel
4. Cleans up old log files (>7 days)
5. Removes PID tracking file

**Output:**
```
🛑 Stopping TrustVoice Services...
====================================
📋 Found service PIDs from startup

1️⃣  Stopping FastAPI server...
   ✅ FastAPI server stopped (PID: 12345)

2️⃣  Stopping ngrok tunnel...
   ✅ ngrok tunnel stopped (PID: 12346)

3️⃣  Redis status...
   ℹ️  Redis still running (use 'redis-cli shutdown' to stop)

4️⃣  PostgreSQL status...
   ℹ️  PostgreSQL (Neon Cloud) - managed service, always available

5️⃣  Cleaning up old logs...
   ✅ Old log files cleaned (>7 days)

====================================
✅ All services stopped
====================================

💡 To start services again, run: ./admin-scripts/START_SERVICES.sh
```

---

## Service Details

### FastAPI Server
- **Port:** 8001
- **Logs:** `logs/trustvoice_api.log`
- **API Docs:** http://localhost:8001/docs
- **Auto-reload:** Enabled (watches for code changes)

### ngrok Tunnel
- **Purpose:** Expose localhost to internet for M-Pesa webhooks
- **Logs:** `logs/ngrok.log`
- **Dashboard:** http://localhost:4040
- **Public URL:** Changes each time you restart (free tier)

### PostgreSQL (Neon)
- **Type:** Cloud-hosted managed database
- **Always Running:** No need to start/stop
- **Connection:** Via `DATABASE_URL` in `.env`

### Redis (Optional)
- **Purpose:** Session caching, rate limiting
- **Status:** Optional for development
- **Default:** localhost:6379

---

## Monitoring & Debugging

### View Logs in Real-Time
```bash
# FastAPI server logs
tail -f logs/trustvoice_api.log

# ngrok tunnel logs
tail -f logs/ngrok.log
```

### Check Service Status
```bash
# Check if FastAPI is running
curl http://localhost:8001/docs

# Check if ngrok is running
curl http://localhost:4040/api/tunnels

# Check Redis
redis-cli ping
```

### Manual Service Control
```bash
# Start FastAPI manually
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
uvicorn main:app --reload --port 8001

# Start ngrok manually
ngrok http 8001

# Stop services by port
lsof -ti:8001 | xargs kill -9  # Stop FastAPI
pkill ngrok                     # Stop ngrok
```

---

## Troubleshooting

### "Port 8001 already in use"
```bash
# Find and kill process using port 8001
lsof -ti:8001 | xargs kill -9

# Or use the stop script
./admin-scripts/STOP_SERVICES.sh
```

### "ngrok: command not found"
```bash
# Install ngrok
brew install ngrok

# Or download from: https://ngrok.com/download
```

### "Database connection failed"
1. Check `DATABASE_URL` in `.env`
2. Verify Neon database is accessible
3. Check internet connection

### "Redis connection failed"
Redis is optional. To install:
```bash
# macOS
brew install redis
redis-server --daemonize yes

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
```

### ngrok URL keeps changing
This is normal for free tier. Each time you restart, you get a new URL.

**Solutions:**
- Upgrade to ngrok paid plan ($10/month) for static domains
- Use a VPS with public IP for production
- Deploy to cloud platform (Heroku, Railway, Render)

---

## Production Deployment

These scripts are for **development only**. For production:

1. **Don't use ngrok** - Deploy to a platform with static IP
2. **Use systemd/supervisor** - For process management
3. **Use proper logging** - Sentry, CloudWatch, etc.
4. **Set up monitoring** - Uptime checks, error tracking
5. **Use environment-specific configs** - Separate .env files

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `./admin-scripts/START_SERVICES.sh` | Start all services |
| `./admin-scripts/STOP_SERVICES.sh` | Stop all services |
| `tail -f logs/trustvoice_api.log` | View API logs |
| `curl http://localhost:8001/docs` | Check if API is running |
| `curl http://localhost:4040/api/tunnels` | Get ngrok URL |
| `redis-cli ping` | Check Redis status |

---

## Next Steps

After starting services:
1. Visit http://localhost:8001/docs to see API documentation
2. Check ngrok dashboard at http://localhost:4040
3. Test M-Pesa donations (webhook will work through ngrok)
4. Monitor logs for any errors

**M-Pesa Webhook URL** is automatically updated in `.env` when you start services.
