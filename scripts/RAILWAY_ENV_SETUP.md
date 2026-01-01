# Setting Railway Environment Variables - Quick Guide

## Three Methods (Choose One):

### Method 1: Automated Script (RECOMMENDED) ⭐

**What it does:** Reads your `.env`, uploads all variables, sets Railway-specific URLs automatically

```bash
# Make sure Railway CLI is installed
railway --version

# Run the setup script
python scripts/setup-railway-env.py
```

**Benefits:**
- ✅ Automatic - no manual copying
- ✅ Sets production URLs automatically
- ✅ Generates strong SECRET_KEY
- ✅ One command

---

### Method 2: Railway CLI Bulk Import

**What it does:** Uploads your `.env` file directly to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli
# OR
brew install railway

# Login
railway login

# Link to project
railway link

# Bulk upload from .env
railway variables --set-from-file .env

# Then manually set production-specific vars
railway variables set APP_ENV=production
railway variables set ALLOWED_ORIGINS=https://your-app.railway.app
railway variables set TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/webhooks/telegram
railway variables set MPESA_CALLBACK_URL=https://your-app.railway.app/webhooks/mpesa
railway variables set SECRET_KEY=$(openssl rand -hex 32)
```

**Benefits:**
- ✅ Fast bulk upload
- ✅ Uses Railway CLI
- ⚠️ Needs manual URL updates

---

### Method 3: Railway Dashboard (Manual)

**What it does:** Copy/paste each variable in the web UI

1. Go to your Railway project
2. Click Settings → Variables
3. Click "New Variable"
4. Copy/paste from your `.env`
5. Repeat 30+ times 😅

**Benefits:**
- ✅ Visual interface
- ✅ No CLI needed
- ❌ Tedious
- ❌ Error-prone

---

## Comparison:

| Method | Speed | Automation | Difficulty |
|--------|-------|------------|------------|
| **Automated Script** | ⚡️⚡️⚡️ | 🤖 Full | ⭐️ Easy |
| **CLI Bulk** | ⚡️⚡️ | 🤖 Partial | ⭐️⭐️ Medium |
| **Manual** | 🐌 | ❌ None | ⭐️⭐️⭐️ Hard |

---

## What Gets Set:

### From Your `.env`:
- DATABASE_URL
- REDIS_URL
- OPENAI_API_KEY
- ADDIS_AI_API_KEY
- STRIPE_SECRET_KEY
- TELEGRAM_BOT_TOKEN
- etc. (all your existing variables)

### Production-Specific (Auto-generated):
- `APP_ENV=production`
- `SECRET_KEY=<random-32-byte-hex>`
- `ALLOWED_ORIGINS=https://your-app.railway.app`
- `TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/webhooks/telegram`
- `MPESA_CALLBACK_URL=https://your-app.railway.app/webhooks/mpesa`
- `MPESA_B2C_RESULT_URL=https://your-app.railway.app/webhooks/mpesa/b2c/result`
- `MPESA_B2C_QUEUE_TIMEOUT_URL=https://your-app.railway.app/webhooks/mpesa/b2c/timeout`

---

## After Setting Variables:

1. **Deploy:**
   ```bash
   railway up
   ```

2. **Verify:**
   ```bash
   railway logs
   railway open  # Opens your app
   ```

3. **Check Variables:**
   ```bash
   railway variables
   ```

---

## Troubleshooting:

**"Railway CLI not found"**
```bash
npm i -g @railway/cli
```

**"Not logged in"**
```bash
railway login
```

**"No project linked"**
```bash
railway link
# Select your project
```

**"Failed to set variable"**
- Check for special characters that need escaping
- Try setting manually: `railway variables set KEY="value"`

---

## Security Notes:

✅ **Safe:** `.env.example` → Git (has placeholders)
❌ **Never:** `.env` → Git (has real secrets)
✅ **Safe:** `.env` → Railway CLI (encrypted in transit)
✅ **Safe:** Railway Variables (encrypted at rest)

---

## TL;DR - Quick Start:

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login and link
railway login
railway link

# 3. Run automated setup
python scripts/setup-railway-env.py

# 4. Deploy
railway up

# 5. Done! ✨
```
