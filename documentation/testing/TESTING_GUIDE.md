# Lab 5 Module Testing Guide

## 🎯 Ready to Test!

All services are running and the database is properly configured. Let's test each module systematically in your Telegram bot.

---

## 📱 Test Environment

- **Telegram Bot**: @TrustVoiceBot (or your bot name)
- **Bot URL**: https://briary-torridly-raul.ngrok-free.dev
- **Database**: ✅ All schemas migrated
- **Services**: ✅ All running

**Check Service Status:**
```bash
ps aux | grep -E "telegram_bot|trustvoice_api|celery" | grep -v grep
```

---

## 🧪 Testing Sequence

### ✅ Module 1: Voice Campaign Creation

**Test Steps:**
1. Open Telegram and find your bot
2. Send `/start` then `/register`
3. Select role: `CAMPAIGN_CREATOR`
4. Send voice message: **"I want to create a campaign"**
5. Answer the 9 interview questions:
   - **Title**: "Clean Water for Mwanza Test"
   - **Category**: "Water and Sanitation"
   - **Problem**: "450 families lack clean water access"
   - **Solution**: "Build 10 water wells with filtration"
   - **Goal**: "50000 dollars"
   - **Beneficiaries**: "450 families in rural areas"
   - **Location**: "Mwanza, Tanzania"
   - **Timeline**: "6 months"
   - **Budget**: "Wells $30k, Filtration $10k, Maintenance $10k"

**Expected Result:**
- ✅ Campaign created with status='pending'
- ✅ Success message with campaign details
- ✅ TTS voice reply for each response

**Verify in Database:**
```bash
python tests/check_db_state.py "Mwanza Test"
```

---

### ✅ Module 2: Voice Donation Execution

**Test Steps:**
1. Register a new user as `DONOR` (use different phone in registration)
2. Send voice message: **"I want to donate 50 dollars"**
3. System should show available campaigns
4. Confirm donation
5. For Kenya (+254): M-Pesa STK Push prompt appears
6. For others: Stripe payment link provided

**Expected Result:**
- ✅ Donation record created
- ✅ Payment method auto-selected (M-Pesa or Stripe)
- ✅ Payment instructions with TTS voice
- ✅ Transaction ID generated

**Verify in Database:**
```bash
python -c "
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, amount_usd, status, payment_method FROM donations ORDER BY created_at DESC LIMIT 1'))
    print(result.fetchone())
"
```

---

### ✅ Module 3: Campaign Detail View

**Test Steps:**
1. Send voice/text: **"Tell me about Clean Water project"**
2. Or: **"Show campaign details"**

**Expected Result:**
- ✅ Campaign title and description
- ✅ Progress bar (█░░░░)
- ✅ Raised amount vs goal
- ✅ Donor count
- ✅ Verification status
- ✅ Recent supporters
- ✅ TTS voice reply

**Test Alternative Commands:**
- "Show me the Mwanza campaign"
- "What's the status of the water project?"
- "Campaign details"

---

### ✅ Module 4: Impact Reports (Field Agents)

**Test Steps:**
1. Register as `FIELD_AGENT`
2. **Upload 3-5 photos** to Telegram (any project-related images)
3. Send voice: **"Report impact for Clean Water project"**
4. Provide observations when prompted
5. Add testimonials
6. Share location (optional GPS)

**Expected Result:**
- ✅ Impact verification created
- ✅ Trust score calculated (0-100)
- ✅ Auto-approved if score ≥ 80
- ✅ $30 USD payout initiated (M-Pesa B2C)
- ✅ Payout confirmation with transaction ID

**Trust Score Breakdown:**
- Photos: 30 points (10 per photo, max 3)
- GPS: 25 points
- Testimonials: 20 points
- Description: 15 points
- Beneficiary count: 10 points

**Verify:**
```bash
python -c "
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT trust_score, status, agent_payout_status FROM impact_verifications ORDER BY created_at DESC LIMIT 1'))
    print(result.fetchone())
"
```

---

### ✅ Module 5: Campaign Verification (Field Agents)

**Test Steps:**
1. As `FIELD_AGENT`, send: **"Show campaigns needing verification"**
2. Send: **"Verify [campaign name]"**
3. Upload 3-5 photos of site visit
4. Share GPS location
5. Send observations via voice

**Expected Result:**
- ✅ Verification checklist provided
- ✅ Trust score calculated
- ✅ Campaign auto-activated if score ≥ 80
- ✅ Status changes: pending → active
- ✅ Agent receives $30 USD payout
- ✅ Campaign verification_count incremented

**Verify:**
```bash
python tests/check_db_state.py "Mwanza Test"
# Check status changed to 'active' and verification_count > 0
```

---

### ✅ Module 6: Payout Requests (Campaign Creators)

**Test Steps:**
1. As `CAMPAIGN_CREATOR`, send: **"Request payout"**
2. View available campaign balances
3. Send: **"Withdraw $100 from Clean Water project"**
4. Confirm phone number (+254 Kenya only for M-Pesa)

**Expected Result:**
- ✅ Campaign balance displayed (USD and KES)
- ✅ Minimum $10 enforced
- ✅ M-Pesa B2C payout initiated
- ✅ Campaign raised_amount_usd reduced
- ✅ Transaction ID provided
- ✅ Funds arrive in 1-5 minutes

**Requirements:**
- Phone must be +254 (Kenya)
- Campaign must have raised funds
- Minimum $10 withdrawal

**Verify:**
```bash
python tests/check_db_state.py "Mwanza Test"
# Check raised_amount_usd was reduced
```

---

### ✅ Module 7: Donation Status Check

**Test Steps:**
1. As `DONOR`, send: **"Check my donation status"**
2. Or: **"Show my donations"**

**Expected Result:**
- ✅ Most recent donation shown
- ✅ Status with emoji (⏳ pending / ✅ completed / ❌ failed)
- ✅ Amount and currency
- ✅ Campaign name
- ✅ Payment method
- ✅ Transaction ID
- ✅ Date and time
- ✅ TTS voice reply

**Alternative Commands:**
- "What's my donation status?"
- "Show donation history"
- "List my contributions"

---

### ✅ Module 8: TTS Integration

**Test Every Module:**
1. Send any command from modules above
2. Check you receive **BOTH**:
   - Text message (immediate)
   - Voice message marked "🎤 Voice version"

**What to Verify:**
- ✅ Audio is clear and natural
- ✅ English uses OpenAI TTS (warm voice)
- ✅ Amharic uses AddisAI TTS (if language set to 'am')
- ✅ Same message = instant audio (cache working)
- ✅ Long messages truncated properly

**Check TTS Cache:**
```bash
ls -lh voice/tts_cache/
# Should see .mp3 files with MD5 hash names
```

**Check TTS Logs:**
```bash
tail -f logs/telegram_bot.log | grep -i tts
```

---

## 🔍 Monitoring & Debugging

### View Live Logs

**Telegram Bot:**
```bash
tail -f logs/telegram_bot.log
```

**API Server:**
```bash
tail -f logs/trustvoice_api.log
```

**Celery Worker:**
```bash
tail -f logs/celery_worker.log
```

**All Services:**
```bash
tail -f logs/*.log
```

### Database Queries

**Full Report:**
```bash
python tests/check_db_state.py
```

**Specific Campaign:**
```bash
python tests/check_db_state.py "Mwanza"
```

**Custom SQL:**
```python
python -c "
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    # Your SQL here
    result = conn.execute(text('SELECT * FROM campaigns LIMIT 5'))
    for row in result:
        print(row)
"
```

### Restart Services

If anything goes wrong:
```bash
./admin-scripts/STOP_SERVICES.sh && sleep 2 && ./admin-scripts/START_SERVICES.sh
```

---

## ✅ Test Completion Checklist

Mark each module as tested:

- [ ] **Module 1**: Campaign created with all 9 fields
- [ ] **Module 2**: Donation initiated (M-Pesa or Stripe)
- [ ] **Module 3**: Campaign details displayed correctly
- [ ] **Module 4**: Impact report with trust score
- [ ] **Module 5**: Campaign verified and activated
- [ ] **Module 6**: Payout successful (if +254 phone)
- [ ] **Module 7**: Donation status displayed
- [ ] **Module 8**: TTS voice replies working

---

## 🐛 Common Issues & Solutions

### Issue: Voice transcription fails
**Solution:** Already fixed with `stdin=subprocess.DEVNULL`. If still failing:
```bash
# Check logs
tail -f logs/telegram_bot.log | grep -i "ffmpeg\|audio"
```

### Issue: Payment failures
**M-Pesa:** Sandbox environment - may need real credentials  
**Stripe:** Use test card: 4242 4242 4242 4242

### Issue: TTS not generating audio
**Check:** OpenAI API key in `.env`
```bash
grep OPENAI_API_KEY .env
```
Note: TTS is non-critical - text messages still work

### Issue: Database connection errors
**Check:** Neon Cloud connection
```bash
python -c "from database.db import get_db; next(get_db()); print('✅ Connected')"
```

### Issue: Bot not responding
**Check:** Services running
```bash
ps aux | grep telegram_bot | grep -v grep
```
**Restart:** `./admin-scripts/START_SERVICES.sh`

---

## 🎉 Success Criteria

### All Tests Passing When:
- ✅ Voice transcription works (< 30s)
- ✅ Campaign creation completes 9-step interview
- ✅ Donations create records with payment methods
- ✅ Campaign details show progress and verification
- ✅ Impact reports calculate trust scores
- ✅ Campaign verification activates campaigns
- ✅ Payouts initiate M-Pesa B2C
- ✅ Donation status queries work
- ✅ Every response includes TTS voice message
- ✅ Database stays consistent
- ✅ No errors in logs

---

## 📊 Next Steps After Testing

1. **Document Issues**: Note any failures or unexpected behavior
2. **Edge Cases**: Test invalid inputs, missing fields, boundary conditions
3. **Load Testing**: Multiple simultaneous users
4. **Security Audit**: Payment validation, user authentication
5. **Production Prep**: Environment variables, secrets management
6. **Beta Testing**: Real users, real Telegram accounts
7. **Monitoring Setup**: Alerts, metrics, error tracking

---

**Happy Testing! 🚀**

For help: Check logs, review code, or run database queries above.
