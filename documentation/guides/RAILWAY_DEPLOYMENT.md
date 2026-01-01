# Railway Deployment Guide for TrustVoice

## Overview
Railway provides stable public URLs, eliminating the need for ngrok. You can deploy via GitHub (recommended) or Railway CLI.

---

## ✅ Pre-Deployment Checklist

### 1. Your Current Setup (Already Good!)
- ✅ External PostgreSQL (Neon Cloud) - portable across environments
- ✅ `requirements.txt` exists
- ✅ `.env.example` for documentation
- ✅ Telegram bot uses polling (will change to webhooks)

### 2. What Needs to Change

**Critical Changes:**
1. **Telegram Bot**: Switch from polling → webhooks
2. **M-Pesa Callbacks**: Update URLs from ngrok → Railway
3. **Stripe Webhooks**: Update URLs from ngrok → Railway
4. **CORS Origins**: Add Railway domain

**Optional but Recommended:**
1. Add health check endpoint for Railway
2. Create `railway.json` for configuration
3. Add `Procfile` for explicit process definition

---

## 📋 Step-by-Step Deployment

### Option A: Deploy via GitHub (RECOMMENDED)

#### Step 1: Prepare Your Repository

1. **Create `.gitignore` additions** (if not already present):
```gitignore
.env
.celery_worker_pid
.fastapi_pid
.telegram_bot_pid
.service_pids
.test_chat_id
venv/
__pycache__/
*.pyc
logs/
uploads/
test_auth.db
```

2. **Create `Procfile`** (Railway auto-detects Python, but explicit is better):
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

3. **Create `railway.json`** (optional configuration):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

4. **Add health check endpoint to `main.py`**:
```python
@app.get("/health")
async def health_check():
    """Health check for Railway"""
    return {
        "status": "healthy",
        "service": "TrustVoice API",
        "timestamp": datetime.utcnow().isoformat()
    }
```

5. **Commit and push to GitHub**:
```bash
git add .
git commit -m "feat: prepare for Railway deployment"
git push origin main
```

#### Step 2: Deploy to Railway

1. **Go to [Railway.app](https://railway.app)** and sign in with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `Trust-Voice` repository
   - Railway will auto-detect it's a Python app

3. **Configure Environment Variables** (Settings → Variables):
   Copy from your `.env` file:
   ```
   DATABASE_URL=postgresql://...your-neon-url...
   REDIS_URL=redis://...
   OPENAI_API_KEY=sk-proj-...
   ADDIS_AI_API_KEY=sk_...
   ADDIS_AI_URL=https://api.addisassistant.com/api/v1/chat_generate
   ADDIS_TRANSLATE_URL=https://api.addisassistant.com/api/v1/translate
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   TELEGRAM_BOT_TOKEN=1234567890:ABC...
   TWILIO_ACCOUNT_SID=AC...
   TWILIO_AUTH_TOKEN=...
   TWILIO_PHONE_NUMBER=+1234567890
   APP_ENV=production
   SECRET_KEY=generate-strong-random-key
   
   # Will be set after deployment:
   RAILWAY_PUBLIC_DOMAIN=your-app.railway.app
   MPESA_CALLBACK_URL=https://your-app.railway.app/webhooks/mpesa
   MPESA_B2C_RESULT_URL=https://your-app.railway.app/webhooks/mpesa/b2c/result
   MPESA_B2C_QUEUE_TIMEOUT_URL=https://your-app.railway.app/webhooks/mpesa/b2c/timeout
   TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/webhooks/telegram
   ```

4. **Generate Public Domain**:
   - Go to Settings → Networking
   - Click "Generate Domain"
   - You'll get: `your-app.railway.app`
   - Copy this URL

5. **Update Callback URLs**:
   - Go back to Variables
   - Update all webhook URLs with your Railway domain
   - Add to ALLOWED_ORIGINS: `https://your-app.railway.app`

6. **Deploy**:
   - Railway will automatically deploy
   - Watch logs in real-time
   - Wait for "Deployed successfully"

#### Step 3: Configure External Services

1. **Update Telegram Webhook**:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app.railway.app/webhooks/telegram"}'
   ```

   Verify it worked:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```

2. **Update M-Pesa Callback URLs**:
   - Login to [Safaricom Developer Portal](https://developer.safaricom.co.ke)
   - Update your app's callback URLs:
     - STK Push: `https://your-app.railway.app/webhooks/mpesa`
     - B2C Result: `https://your-app.railway.app/webhooks/mpesa/b2c/result`
     - B2C Timeout: `https://your-app.railway.app/webhooks/mpesa/b2c/timeout`

3. **Update Stripe Webhooks**:
   - Login to [Stripe Dashboard](https://dashboard.stripe.com)
   - Go to Developers → Webhooks
   - Add endpoint: `https://your-app.railway.app/webhooks/stripe`
   - Select events: `payment_intent.succeeded`, `payment_intent.failed`
   - Copy the signing secret and update `STRIPE_WEBHOOK_SECRET` in Railway

#### Step 4: Update Telegram Bot Code

You need to add webhook support to your bot. Create a new file:

**`voice/telegram/webhook.py`**:
```python
"""
Telegram Webhook Handler for Production
Replaces polling for Railway deployment
"""
from fastapi import APIRouter, Request, HTTPException
from telegram import Update
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Import your bot application
from voice.telegram.bot import application

@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.
    Railway will send POST requests here.
    """
    try:
        data = await request.json()
        logger.info(f"Received Telegram update: {data.get('update_id')}")
        
        # Create Update object from JSON
        update = Update.de_json(data, application.bot)
        
        # Process the update
        await application.process_update(update)
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Update `main.py`** to include webhook router:
```python
# Add this import at the top
from voice.telegram.webhook import router as telegram_webhook_router

# Add this after your other routers
app.include_router(telegram_webhook_router)
```

**Update `voice/telegram/bot.py`** - modify the `main()` function:
```python
def main():
    """Initialize bot based on environment."""
    import os
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ... (all your handlers) ...
    
    # Check environment
    app_env = os.getenv("APP_ENV", "development")
    
    if app_env == "production":
        # Production: Use webhooks (started by main.py)
        logger.info("🤖 Bot configured for webhooks (production mode)")
        # Don't call run_polling() - Railway will send webhook requests
    else:
        # Development: Use polling
        logger.info("🤖 Bot starting in polling mode (development)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
```

---

### Option B: Deploy via Railway CLI (Alternative)

1. **Install Railway CLI**:
```bash
npm i -g @railway/cli
# or
brew install railway
```

2. **Login and Link**:
```bash
railway login
cd /Users/manu/Trust-Voice
railway link
```

3. **Deploy**:
```bash
railway up
```

4. **Follow Step 2-4 from Option A** for configuration

---

## 🎯 Redis Setup (Optional but Recommended)

If you use Redis for caching/Celery:

1. **Add Redis to Railway**:
   - In your Railway project, click "New Service"
   - Select "Redis"
   - Railway will auto-generate `REDIS_URL`
   - It will be automatically added to your environment variables

2. **Update your code** to use `REDIS_URL` environment variable (already done in your code)

---

## 🧪 Testing Your Deployment

### 1. Test API Health
```bash
curl https://your-app.railway.app/health
```

### 2. Test Telegram Bot
- Send message to your bot on Telegram
- Check Railway logs for webhook activity

### 3. Test Miniapps
```bash
open https://your-app.railway.app/campaigns.html
open https://your-app.railway.app/donate.html
```

### 4. Test Voice Endpoints
```bash
curl -X POST https://your-app.railway.app/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Test deployment", "language": "en"}'
```

---

## 🔄 Continuous Deployment

Once deployed via GitHub:
- Every push to `main` branch automatically deploys
- Railway shows build logs in real-time
- Failed builds don't affect running app
- Rollback available in Railway dashboard

---

## 🚨 Important Notes

### Environment-Specific Behavior

**Development (localhost)**:
- Telegram: Polling mode
- Webhooks: ngrok URLs
- Port: 8001

**Production (Railway)**:
- Telegram: Webhook mode
- Webhooks: Railway URLs
- Port: Auto-assigned by Railway ($PORT)

### Railway Free Tier Limits
- $5 free credit/month
- Apps sleep after 30min inactivity (Pro plan removes this)
- 500MB RAM, 1GB storage
- Upgrade to Pro if you need 24/7 uptime

### Database Considerations
- Your Neon DB is already external ✅
- No migration needed
- Just ensure `DATABASE_URL` is set correctly

### File Uploads
- Railway has ephemeral filesystem
- Consider using S3/Cloudflare R2 for permanent storage
- Or use Railway Volumes (persistent storage)

---

## 📞 Support Checklist

Before going live, verify:
- [ ] Telegram bot responds to messages
- [ ] M-Pesa webhooks receive callbacks
- [ ] Stripe webhooks work
- [ ] Voice TTS/STT endpoints functional
- [ ] Miniapps load correctly
- [ ] Database migrations applied
- [ ] Environment variables all set
- [ ] CORS allows your domains
- [ ] Logs show no errors

---

## 🔐 Security Recommendations

1. **Use Railway Secrets** for sensitive data (auto-encrypted)
2. **Enable HTTPS** (Railway does this automatically)
3. **Restrict CORS** to your domains only
4. **Rotate secrets** regularly
5. **Monitor logs** for suspicious activity

---

## 🎉 Next Steps

After successful deployment:
1. Update your `.env.example` with Railway-specific notes
2. Document your Railway URL in README
3. Update Telegram Mini App URLs (if using)
4. Test end-to-end flows
5. Monitor Railway dashboard for errors
6. Set up custom domain (optional)

---

## 🆘 Troubleshooting

### Build Fails
- Check `requirements.txt` has all dependencies
- Verify Python version compatibility
- Check Railway build logs

### Bot Not Responding
- Verify `TELEGRAM_WEBHOOK_URL` is correct
- Check `getWebhookInfo` output
- Ensure webhook endpoint is `/webhooks/telegram`

### Database Connection Issues
- Verify `DATABASE_URL` format
- Check Neon DB allows Railway IPs
- Test connection from Railway shell

### Static Files Not Loading
- Ensure `static/` folder committed to Git
- Check Railway serves static files
- May need to configure nginx/static hosting

---

**You're ready to deploy! Start with Option A (GitHub) - it's the easiest and most maintainable approach.**
