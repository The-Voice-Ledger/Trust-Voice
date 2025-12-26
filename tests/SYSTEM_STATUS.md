# Lab 5 Testing - System Status

**Date:** December 25, 2025  
**Status:** ✅ Ready for Testing

---

## 🎯 Quick Start

**Open your Telegram bot and start testing:**

```bash
# View this guide
cat tests/TESTING_GUIDE.md

# Monitor logs while testing
tail -f logs/telegram_bot.log

# Check database state anytime
python tests/check_db_state.py
```

---

## ✅ System Status

### Services Running
- **Telegram Bot**: PID 80256 ✅
- **FastAPI Server**: PID 80216 (http://localhost:8001) ✅
- **Celery Worker**: PID 80251 ✅
- **ngrok Tunnel**: PID 80232 (https://briary-torridly-raul.ngrok-free.dev) ✅
- **PostgreSQL**: Neon Cloud ✅
- **Redis**: localhost ✅

### Database Schema
- ✅ campaigns: All columns present (verification_count, avg_trust_score, etc.)
- ✅ donations: amount_usd, transaction_id migrated
- ✅ impact_verifications: All 14 new columns added
- ✅ users: phone_verified_at, is_phone_verified
- ✅ Indexes: 6 created (campaigns, donations, verifications)
- ✅ Constraints: trust_score (0-100) enforced

### Code Modules
- ✅ Module 1: campaign_builder.py (518 lines)
- ✅ Module 2: donation_handler.py (407 lines)
- ✅ Module 3: Campaign details (integrated in bot.py)
- ✅ Module 4: impact_handler.py (500+ lines)
- ✅ Module 5: verification_handler.py (500+ lines)
- ✅ Module 6: payout_handler.py (400+ lines)
- ✅ Module 7: Donation status (integrated)
- ✅ Module 8: tts_provider.py (300+ lines)

### Voice Processing
- ✅ FFmpeg fix applied (`stdin=subprocess.DEVNULL`)
- ✅ AddisAI STT integration working
- ✅ OpenAI TTS for English
- ✅ AddisAI TTS for Amharic
- ✅ Dual delivery (text + voice)

---

## 📝 Current Database State

**From last check:**
- Campaigns: 23 (22 active, 0 pending)
- Donations: 38 ($20,275 USD raised)
- Users: 3 (1 field agent, 1 creator, 1 admin)
- Impact Verifications: 0 (ready for testing)

---

## 🧪 Testing Order

1. **Module 1**: Create campaign (9-step interview)
2. **Module 5**: Verify campaign (field agent, activates campaign)
3. **Module 2**: Make donation (M-Pesa or Stripe)
4. **Module 3**: View campaign details
5. **Module 4**: Submit impact report (field agent)
6. **Module 7**: Check donation status
7. **Module 6**: Request payout (campaign creator)
8. **Module 8**: Verify TTS on all responses

**Why this order?**
- Module 5 before 2: Need active campaign to accept donations
- Module 4 needs active campaign with donations
- Module 6 needs raised funds
- Module 8 tests throughout all interactions

---

## 🎯 Testing Focus Areas

### Critical Paths
1. **Complete Campaign Lifecycle**: Create → Verify → Activate → Donate → Report → Payout
2. **Payment Integration**: M-Pesa STK Push, Stripe, B2C payouts
3. **Trust Scoring**: Field agent reports, auto-approval at 80+
4. **Voice Accessibility**: STT + NLU + TTS complete loop

### Edge Cases
- Invalid amounts (negative, zero, too large)
- Missing required fields
- Duplicate operations
- Non-Kenya phone numbers (no M-Pesa)
- Campaign without funds (payout should fail)

### Performance
- Voice transcription speed (should be < 30s)
- TTS cache hits (second identical message = instant)
- Database query performance
- Concurrent user handling

---

## 📊 Success Metrics

### Must Pass
- [ ] Voice messages transcribed in < 30 seconds
- [ ] Campaign creation completes all 9 steps
- [ ] Donations create valid records
- [ ] Trust scoring calculates correctly (0-100)
- [ ] Payouts initiate M-Pesa B2C
- [ ] TTS voice replies for every message
- [ ] No database errors
- [ ] No service crashes

### Nice to Have
- Campaign search by location working
- Multiple concurrent users supported
- Error messages helpful and clear
- TTS voices sound natural
- Cache reduces TTS API calls

---

## 🔧 Tools Available

### Database Queries
```bash
# Full report
python tests/check_db_state.py

# Specific campaign
python tests/check_db_state.py "Mwanza"

# Interactive SQL
python -c "from database.db import get_db; db = next(get_db()); ..."
```

### Log Monitoring
```bash
# All logs
tail -f logs/*.log

# Just bot
tail -f logs/telegram_bot.log

# Search for errors
grep -i error logs/telegram_bot.log

# TTS activity
tail -f logs/telegram_bot.log | grep -i tts
```

### Service Management
```bash
# Restart everything
./admin-scripts/STOP_SERVICES.sh && sleep 2 && ./admin-scripts/START_SERVICES.sh

# Check status
ps aux | grep -E "telegram_bot|trustvoice_api|celery" | grep -v grep

# View PIDs
cat .telegram_bot_pid .trustvoice_api_pid .celery_worker_pid
```

---

## 📱 Telegram Bot Testing

### Registration
```
/start → /register → Select role
```

### Test Commands
```
# Campaign Creation
"I want to create a campaign"
"Create a new project"

# Donations
"I want to donate 50 dollars"
"Donate to clean water project"

# Campaign Info
"Tell me about [campaign name]"
"Show campaign details"

# Field Agent
"Report impact for [campaign]"
"Verify [campaign name]"
"Show my verifications"

# Payouts
"Request payout"
"Withdraw $100"
"What's my campaign balance?"

# Status
"Check my donation status"
"Show my donations"
```

---

## 🐛 Known Issues & Workarounds

### Payment Sandbox Mode
- M-Pesa in test mode, may not process real transactions
- Stripe requires test card: 4242 4242 4242 4242
- B2C payouts may be delayed in sandbox

### TTS Limitations
- 1000 character limit (auto-truncated)
- English only for OpenAI (unless Amharic set)
- Requires OPENAI_API_KEY in .env

### Voice Transcription
- AddisAI STT accuracy varies with audio quality
- Background noise can affect results
- 30s timeout enforced

---

## 📈 What's Been Completed

✅ **Infrastructure**
- Database schema fully migrated
- All services running and stable
- Voice processing pipeline working
- Payment integrations configured

✅ **Voice Modules (8/8 core)**
- Module 1: Campaign Creation (9-step interview)
- Module 2: Donation Execution (M-Pesa + Stripe)
- Module 3: Campaign Details (rich display)
- Module 4: Impact Reports (trust scoring, $30 payouts)
- Module 5: Campaign Verification (activation, $30 payouts)
- Module 6: Payout Requests (M-Pesa B2C withdrawals)
- Module 7: Donation Status (query interface)
- Module 8: TTS Integration (complete voice loop)

✅ **Quality Assurance**
- Voice-Ledger ffmpeg fix applied
- Database consistency checks passed
- Schema validation complete
- Service health monitoring active

---

## 🚀 Next Actions

**Immediate:**
1. Open Telegram bot
2. Follow TESTING_GUIDE.md step by step
3. Document any issues or unexpected behavior
4. Check database state after each test

**After Initial Testing:**
1. Test edge cases and error handling
2. Load test with multiple concurrent users
3. Review logs for warnings/errors
4. Optimize slow queries if found

**Before Production:**
1. Security audit (payment validation, auth)
2. Environment variable documentation
3. Secrets management (API keys)
4. Monitoring and alerting setup
5. Backup strategies
6. Incident response procedures

---

## 📞 Support

**Logs:** `logs/telegram_bot.log`, `logs/trustvoice_api.log`  
**Database:** `python tests/check_db_state.py`  
**Restart:** `./admin-scripts/START_SERVICES.sh`

**Testing Guide:** `tests/TESTING_GUIDE.md`  
**Quick Reference:** `tests/TESTING_QUICK_REFERENCE.md`

---

**Status:** ✅ **READY FOR COMPREHENSIVE MODULE TESTING**

*Last Updated: 2025-12-25 (Lab 5 Complete)*
