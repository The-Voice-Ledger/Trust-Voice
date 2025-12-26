# Lab 5 Module Testing - Quick Reference

## 🚀 Services Status Check
```bash
ps aux | grep -E "telegram_bot|trustvoice_api|celery" | grep -v grep
./admin-scripts/START_SERVICES.sh  # If any service is down
```

## 📱 Test User Setup

### Register Test Users (in Telegram):
1. **Campaign Creator**: `/register` → Select "Campaign Creator"
2. **Donor**: `/register` → Select "Donor"
3. **Field Agent**: `/register` → Select "Field Agent"

## 🧪 Module Tests

### Module 1: Campaign Creation
**Voice Command**: "I want to create a campaign"
**Expected**: 9-step interview → Campaign created with status='pending'
**Verify**:
```sql
psql $DATABASE_URL -c "SELECT id, title, status FROM campaigns ORDER BY created_at DESC LIMIT 1;"
```

### Module 2: Donations
**Voice Command**: "I want to donate 50 dollars"
**Expected**: Donation created → M-Pesa/Stripe payment initiated
**Verify**:
```sql
psql $DATABASE_URL -c "SELECT id, amount_usd, status, payment_method FROM donations ORDER BY created_at DESC LIMIT 1;"
```

### Module 3: Campaign Details
**Voice Command**: "Tell me about [campaign name]"
**Expected**: Full details, progress bar, trust scores, recent donors
**Check**: Progress bar (█░░░░), amounts, verification status

### Module 4: Impact Reports
**Steps**:
1. Upload 3-5 photos to Telegram
2. **Voice**: "Report impact for [campaign name]"
**Expected**: Trust score 0-100, auto-approve if ≥80, $30 payout
**Verify**:
```sql
psql $DATABASE_URL -c "SELECT id, trust_score, status, agent_payout_status FROM impact_verifications ORDER BY created_at DESC LIMIT 1;"
```

### Module 5: Campaign Verification
**Steps**:
1. **Voice**: "Show campaigns needing verification"
2. **Voice**: "Verify [campaign name]"
3. Upload photos, share GPS, add observations
**Expected**: Campaign status pending→active if score ≥80, $30 agent payout
**Verify**:
```sql
psql $DATABASE_URL -c "SELECT title, status, avg_trust_score, verification_count FROM campaigns ORDER BY created_at DESC LIMIT 1;"
```

### Module 6: Payouts
**Voice Command**: "Request payout" or "Withdraw $100 from [campaign]"
**Requirements**: +254 phone (Kenya), campaign has funds, min $10
**Expected**: M-Pesa B2C initiated, campaign balance reduced
**Verify**:
```sql
psql $DATABASE_URL -c "SELECT title, raised_amount_usd, goal_amount_usd FROM campaigns ORDER BY created_at DESC LIMIT 1;"
```

### Module 7: Donation Status
**Voice Command**: "Check my donation status" or "Show my donations"
**Expected**: Latest donation details with status emoji (⏳/✅/❌)
**Verify**:
```sql
psql $DATABASE_URL -c "SELECT d.amount_usd, d.status, c.title FROM donations d JOIN campaigns c ON d.campaign_id = c.id ORDER BY d.created_at DESC LIMIT 3;"
```

### Module 8: TTS Integration
**Test**: Send any voice command
**Expected**: BOTH text reply + voice message (🎤 Voice version)
**Check**: 
- English uses OpenAI TTS (nova voice)
- Amharic uses AddisAI TTS
- Cache dir: `ls -lh voice/tts_cache/`
**Logs**: `tail -f logs/telegram_bot.log | grep -i tts`

## 🔍 Troubleshooting Commands

### View Logs
```bash
tail -f logs/telegram_bot.log          # Bot logs
tail -f logs/trustvoice_api.log        # API logs
tail -f logs/celery_worker.log         # Background tasks
```

### Database Quick Checks
```bash
# Check campaigns
psql $DATABASE_URL -c "SELECT id, title, status, raised_amount_usd, goal_amount_usd FROM campaigns ORDER BY created_at DESC LIMIT 5;"

# Check donations
psql $DATABASE_URL -c "SELECT id, amount_usd, status, payment_method, created_at FROM donations ORDER BY created_at DESC LIMIT 5;"

# Check impact verifications
psql $DATABASE_URL -c "SELECT id, trust_score, status, agent_payout_status, created_at FROM impact_verifications ORDER BY created_at DESC LIMIT 5;"
```

### Restart Services
```bash
./admin-scripts/STOP_SERVICES.sh && sleep 2 && ./admin-scripts/START_SERVICES.sh
```

## 🎯 Test Checklist

- [ ] **Module 1**: Campaign created with all 9 fields
- [ ] **Module 2**: Donation initiated (M-Pesa or Stripe)
- [ ] **Module 3**: Campaign details show correctly
- [ ] **Module 4**: Impact report with trust score calculated
- [ ] **Module 5**: Campaign verified and activated
- [ ] **Module 6**: Payout successful (M-Pesa B2C)
- [ ] **Module 7**: Donation status displayed
- [ ] **Module 8**: TTS voice replies working

## 📊 Success Criteria

### ✅ Module Pass
- Feature works as expected
- Database updated correctly
- No errors in logs
- TTS voice reply sent (Module 8)

### ❌ Module Fail
- Feature returns error
- Database inconsistent
- Logs show exceptions
- Missing expected output

## 💡 Test Tips

1. **Test in order**: Module 1 → 8 (dependencies exist)
2. **Check logs**: Always review logs after each test
3. **Verify database**: Use SQL queries to confirm changes
4. **Test edge cases**: Invalid amounts, missing fields, etc.
5. **Test both voice and text**: Both should work identically
6. **Check TTS**: Every response should include voice message

## 🐛 Common Issues

### FFmpeg Hanging
- **Fix**: Already applied (`stdin=subprocess.DEVNULL`)
- **Check**: Voice transcription works within 30s

### Payment Failures
- **M-Pesa**: Sandbox environment, may need real credentials
- **Stripe**: Test mode, use test card numbers

### TTS Not Working
- **Check**: OpenAI API key in `.env`
- **Check**: `logs/telegram_bot.log` for TTS errors
- **Non-critical**: System still works without TTS

### Database Connection
- **Check**: Neon Cloud connection string in `.env`
- **Test**: `psql $DATABASE_URL -c "SELECT 1;"`

## 🎉 All Tests Passing?

**Next Steps**:
1. Test edge cases and error handling
2. Load testing with multiple users
3. Security audit
4. Documentation updates
5. Production deployment preparation

---

**Happy Testing! 🚀**
