# Railway Deployment Checklist

Follow this step-by-step guide to deploy TrustVoice to Railway.

## ✅ Pre-Deployment Checklist

- [x] Procfile created
- [x] railway.json created
- [x] Health check endpoint exists in main.py
- [x] Telegram webhook handler created
- [x] Bot supports webhook mode
- [x] .env.example updated with Railway variables
- [ ] All changes committed to Git
- [ ] Changes pushed to GitHub

## 📋 Step 1: Commit and Push to GitHub

```bash
# Check status
git status

# Add all files
git add .

# Commit
git commit -m "feat: Railway deployment configuration

- Add Procfile for Railway
- Add railway.json for deployment config
- Add Telegram webhook support (production mode)
- Update bot.py to support webhook/polling modes
- Update .env.example with production variables
- Health check endpoint ready for Railway"

# Push to GitHub
git push origin main
```

## 📋 Step 2: Create Railway Project

1. Go to [Railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose `Trust-Voice` repository
6. Railway will automatically detect Python and start building

## 📋 Step 3: Configure Environment Variables

Go to Settings → Variables in Railway dashboard and add:

### Core Application
```
APP_ENV=production
SECRET_KEY=<generate-strong-random-key>
APP_HOST=0.0.0.0
```

### Database (Your existing Neon DB)
```
DATABASE_URL=<your-neon-postgresql-url>
```

### Redis (Optional - add if you use Celery)
```
REDIS_URL=<add-redis-service-in-railway>
```

### AI Services
```
OPENAI_API_KEY=<your-openai-key>
ADDIS_AI_API_KEY=<your-addis-key>
ADDIS_AI_URL=https://api.addisassistant.com/api/v1/chat_generate
ADDIS_TRANSLATE_URL=https://api.addisassistant.com/api/v1/translate
```

### Payment Services
```
STRIPE_SECRET_KEY=<your-stripe-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-pk>
STRIPE_WEBHOOK_SECRET=<your-webhook-secret>

MPESA_CONSUMER_KEY=<your-key>
MPESA_CONSUMER_SECRET=<your-secret>
MPESA_BUSINESS_SHORT_CODE=174379
MPESA_PASSKEY=<your-passkey>
MPESA_INITIATOR_NAME=testapi
MPESA_SECURITY_CREDENTIAL=<your-credential>
MPESA_ENVIRONMENT=production
```

### Telegram
```
TELEGRAM_BOT_TOKEN=<your-bot-token>
```

### Twilio (if using phone)
```
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
TWILIO_PHONE_NUMBER=<your-phone>
```

## 📋 Step 4: Generate Public Domain

1. Go to Settings → Networking in Railway
2. Click "Generate Domain"
3. You'll get: `your-app-name.railway.app`
4. Copy this URL

## 📋 Step 5: Update Webhook Environment Variables

Go back to Variables and add (using your Railway domain):

```
# CORS - Add your Railway domain
ALLOWED_ORIGINS=https://your-app-name.railway.app

# Telegram Webhook
TELEGRAM_WEBHOOK_URL=https://your-app-name.railway.app/webhooks/telegram

# M-Pesa Callbacks
MPESA_CALLBACK_URL=https://your-app-name.railway.app/webhooks/mpesa
MPESA_B2C_RESULT_URL=https://your-app-name.railway.app/webhooks/mpesa/b2c/result
MPESA_B2C_QUEUE_TIMEOUT_URL=https://your-app-name.railway.app/webhooks/mpesa/b2c/timeout
```

## 📋 Step 6: Deploy and Monitor

1. Railway will automatically deploy after adding variables
2. Watch the deployment logs
3. Wait for "✅ Deployed successfully"
4. Check health endpoint: `https://your-app-name.railway.app/health`

## 📋 Step 7: Configure External Services

### Telegram Webhook

```bash
# Set webhook (Railway does this automatically, but verify)
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app-name.railway.app/webhooks/telegram"}'

# Verify webhook is set
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Expected response:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-app-name.railway.app/webhooks/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### Stripe Webhooks

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to Developers → Webhooks
3. Click "Add endpoint"
4. Endpoint URL: `https://your-app-name.railway.app/webhooks/stripe`
5. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.failed`
   - `payment_intent.payment_failed`
6. Copy the webhook signing secret
7. Update `STRIPE_WEBHOOK_SECRET` in Railway

### M-Pesa Callbacks

1. Log in to [Safaricom Developer Portal](https://developer.safaricom.co.ke)
2. Go to your app settings
3. Update callback URLs:
   - STK Push Callback: `https://your-app-name.railway.app/webhooks/mpesa`
   - B2C Result URL: `https://your-app-name.railway.app/webhooks/mpesa/b2c/result`
   - B2C Timeout URL: `https://your-app-name.railway.app/webhooks/mpesa/b2c/timeout`
4. Save changes

## 📋 Step 8: Test Your Deployment

### Test Health Check
```bash
curl https://your-app-name.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "TrustVoice API",
  "version": "1.0.0",
  "environment": "production"
}
```

### Test API Endpoints
```bash
# List campaigns
curl https://your-app-name.railway.app/api/campaigns/

# Test TTS endpoint
curl -X POST https://your-app-name.railway.app/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Test deployment", "language": "en"}'
```

### Test Miniapps
Open in browser:
- `https://your-app-name.railway.app/campaigns.html`
- `https://your-app-name.railway.app/donate.html`
- `https://your-app-name.railway.app/create-campaign-wizard.html`
- `https://your-app-name.railway.app/ngo-register-wizard.html`

### Test Telegram Bot
1. Open Telegram
2. Send a message to your bot
3. Check Railway logs for webhook activity
4. Verify bot responds

### Test Voice Features
1. Open a miniapp
2. Click voice button
3. Speak a command
4. Verify TTS response plays
5. Check Railway logs

## 📋 Step 9: Monitor Logs

In Railway dashboard:
1. Click on your deployment
2. View "Logs" tab
3. Watch for:
   - ✅ Bot initialized and ready for webhooks
   - ✅ Telegram webhook router registered
   - ✅ Received Telegram webhook update
   - ❌ Any error messages

## 🚨 Troubleshooting

### Bot Not Responding

**Check webhook status:**
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

**If webhook is not set:**
```bash
# Manually set webhook
curl -X POST https://your-app-name.railway.app/webhooks/telegram/set
```

**If webhook has errors:**
```bash
# Remove and reset webhook
curl -X DELETE https://your-app-name.railway.app/webhooks/telegram/unset
# Then set it again
curl -X POST https://your-app-name.railway.app/webhooks/telegram/set
```

### Database Connection Issues

1. Check `DATABASE_URL` is correct in Railway variables
2. Verify Neon DB allows Railway IP addresses
3. Test connection from Railway shell:
   ```bash
   # In Railway dashboard, open Shell
   python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print('Connected!' if engine.connect() else 'Failed')"
   ```

### Static Files Not Loading

1. Verify `frontend-miniapps/` folder is in Git
2. Check Railway build logs for errors
3. Test direct file access: `https://your-app-name.railway.app/campaigns.html`

### M-Pesa Webhooks Not Working

1. Verify callback URLs are correct in Safaricom portal
2. Test webhook manually:
   ```bash
   curl -X POST https://your-app-name.railway.app/webhooks/mpesa \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```
3. Check Railway logs for webhook requests

## ✅ Post-Deployment Checklist

- [ ] Health check responds with 200 OK
- [ ] All miniapps load correctly
- [ ] Telegram bot responds to messages
- [ ] Voice features work (TTS/STT)
- [ ] Language toggle saves to database
- [ ] M-Pesa webhooks configured
- [ ] Stripe webhooks configured
- [ ] Database migrations applied (if any)
- [ ] No errors in Railway logs
- [ ] CORS allows your domain

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ `https://your-app-name.railway.app/health` returns healthy
2. ✅ Miniapps load and are functional
3. ✅ Telegram bot responds to text messages
4. ✅ Telegram bot responds to voice messages
5. ✅ Voice TTS/STT works in miniapps
6. ✅ Language toggle works
7. ✅ No errors in Railway logs for 5 minutes

## 📝 Next Steps

After successful deployment:

1. **Custom Domain (Optional):**
   - Add custom domain in Railway settings
   - Update DNS records
   - Update all webhook URLs

2. **Monitoring:**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure alerts for downtime
   - Monitor error logs daily

3. **Optimization:**
   - Review Railway usage
   - Upgrade to Pro if needed (removes sleep)
   - Optimize slow endpoints

4. **Documentation:**
   - Update README with production URL
   - Document deployment process
   - Create runbook for common issues

## 🆘 Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check Railway logs first
- Test locally with `APP_ENV=production` to simulate

---

**You're ready to deploy! 🚀**
