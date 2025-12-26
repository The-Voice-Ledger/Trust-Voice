# Pre-Demo Testing Guide

**Quick Reference for Demo Preparation**

## 🚀 Quick Start (5 minutes)

### 1. Activate Virtual Environment & Run Pre-Demo Check
```bash
source venv/bin/activate
python tests/pre_demo_check.py
```

This checks:
- ✅ Environment variables
- ✅ Redis connection
- ✅ Celery workers
- ✅ Database connectivity
- ✅ FFmpeg tools
- ✅ Test files availability

### 2. Start Required Services

```bash
# Terminal 1: Redis (if not running)
brew services start redis

# Terminal 2: Celery Worker
cd /Users/manu/Trust-Voice
source venv/bin/activate
celery -A voice.tasks.celery_app worker --loglevel=info

# Terminal 3: Telegram Bot
cd /Users/manu/Trust-Voice
source venv/bin/activate
python voice/telegram/bot.py
```

### 3. Run Automated Tests
```bash
source venv/bin/activate
python tests/test_voice_modules_automated.py
```

---

## 🧪 What the Automated Tests Do

### Phase 1: Service Verification
1. **Redis Connection** - Read/write test
2. **Celery Workers** - Active worker detection
3. **Database** - Connection + schema validation
4. **STT Provider** - AddisAI transcription test
5. **TTS Provider** - OpenAI speech generation test

### Phase 2: Module Testing

Each test:
1. Loads a test voice file from `documentation/testing/test_voice_messages/`
2. Submits it to Celery for processing
3. Waits for result (60s timeout)
4. Validates:
   - Voice processing succeeded
   - Intent was detected correctly
   - Database was updated
   - TTS audio was generated
5. Reports PASS/FAIL/WARN status

**Modules Tested:**
- ✅ Module 1: Campaign Creation
- ✅ Module 2: Donation Execution
- ✅ Module 3: Campaign Details
- ✅ Module 7: Donation Status
- ✅ Module 8: TTS Integration

---

## 🎯 Expected Output (All Passing)

```
================================================================================
  TrustVoice Voice Module Automated Testing
================================================================================

PHASE 1: Service Verification
================================================================================

✅ Redis connection - Connected to redis://localhost:6379/0
✅ Celery workers - Found workers: celery@localhost
✅ Database connection - Connected with 15 tables
✅ STT provider - Transcribed: 'I want to donate fifty dollars...'
✅ TTS provider (English) - Generated 45231 bytes

✅ All core services operational

PHASE 2: Module Testing
================================================================================

MODULE 1: Voice Campaign Creation
✅ Voice processing - Task completed successfully
✅ Intent detection - Detected: create_campaign
✅ Campaign creation - Created: Clean Water for Mwanza (status: pending)

MODULE 2: Voice Donation Execution
✅ Voice processing - Task completed successfully
✅ Intent detection - Detected: donate
✅ Donation creation - Amount: $50.0, Status: pending, Method: stripe

MODULE 3: Campaign Detail View
✅ Voice processing - Task completed successfully
✅ Campaign details - Response contains campaign information

MODULE 7: Donation Status Queries
✅ Voice processing - Task completed successfully
✅ Donation status - Response contains status information

MODULE 8: TTS Integration
✅ Voice processing - Task completed successfully
✅ TTS generation - Generated 38492 bytes (cache: False)

TEST SUMMARY
================================================================================

Services Status:
  ✅ redis: PASS
  ✅ celery: PASS
  ✅ database: PASS
  ✅ stt: PASS
  ✅ tts_en: PASS

Module Tests:
  ✅ module_1: PASS
  ✅ module_2: PASS
  ✅ module_3: PASS
  ✅ module_7: PASS
  ✅ module_8: PASS

Overall Results:
  Passed: 5
  Failed: 0
  Pass Rate: 100.0%

Recommendations for Demo:
  ✅ All services are operational - ready for demo!
```

---

## 🔍 Troubleshooting

### Redis Not Running
```bash
# Start Redis
brew services start redis

# Check status
redis-cli ping
# Should return: PONG
```

### Celery Workers Not Found
```bash
# Make sure you're in the right directory and venv is activated
cd /Users/manu/Trust-Voice
source venv/bin/activate

# Start worker with proper module path
celery -A voice.tasks.celery_app worker --loglevel=info

# In another terminal, verify workers:
cd /Users/manu/Trust-Voice
source venv/bin/activate
celery -A voice.tasks.celery_app inspect active
```

### Database Connection Failed
```bash
# Check DATABASE_URL is set
echo $DATABASE_URL

# Test connection
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✅ Connected')"
```

### STT/TTS Provider Failed
```bash
# Check API keys
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', '✅' if os.getenv('OPENAI_API_KEY') else '❌'); print('ADDISAI_STT_URL:', '✅' if os.getenv('ADDISAI_STT_URL') else '❌')"
```

### Voice Files Not Found
```bash
# Check test files exist
ls -la documentation/testing/test_voice_messages/*.mp3 | wc -l

# Should show multiple files
```

---

## 🎬 Demo Day Checklist

### Morning of Demo (30 minutes before)

1. **Run Pre-Demo Check**
   ```bash
   source venv/bin/activate
   python tests/pre_demo_check.py
   ```
   - All critical checks should pass

2. **Start Services**
   ```bash
   # Terminal 1
   cd /Users/manu/Trust-Voice
   source venv/bin/activate
   celery -A voice.tasks.celery_app worker --loglevel=info
   
   # Terminal 2
   cd /Users/manu/Trust-Voice
   source venv/bin/activate
   python voice/telegram/bot.py
   ```

3. **Run Automated Tests**
   ```bash
   source venv/bin/activate
   python tests/test_voice_modules_automated.py
   ```
   - Should see 100% pass rate
   - If any failures, investigate immediately

4. **Manual Bot Test**
   - Open Telegram
   - Send a test voice message
   - Verify:
     - ✅ Bot responds quickly
     - ✅ Transcription is accurate
     - ✅ Voice reply is generated
     - ✅ Response is relevant

5. **Check Logs**
   ```bash
   # Check for errors in bot logs
   tail -f logs/bot.log
   
   # Check Celery worker logs
   # (visible in Terminal 1)
   ```

6. **Database Quick Check**
   ```bash
   source venv/bin/activate
   python -c "
   from sqlalchemy import create_engine, text
   import os
   from dotenv import load_dotenv
   load_dotenv()
   engine = create_engine(os.getenv('DATABASE_URL'))
   with engine.connect() as conn:
       campaigns = conn.execute(text('SELECT COUNT(*) FROM campaigns WHERE status=\\'active\\'')).scalar()
       donations = conn.execute(text('SELECT COUNT(*) FROM donations')).scalar()
       print(f'✅ Active campaigns: {campaigns}')
       print(f'✅ Total donations: {donations}')
   "
   ```

### During Demo

**Keep these terminals visible:**
1. Celery worker (shows real-time processing)
2. Bot logs (shows incoming requests)

**Have these ready:**
1. Test voice messages in Telegram (saved messages to self)
2. Example campaigns in database
3. Pre-written demo script with test phrases

**Emergency Commands:**
```bash
# Restart Celery if it hangs
pkill -f celery
celery -A voice.tasks.celery_app worker --loglevel=info

# Restart bot if it stops responding
pkill -f telegram_bot
python voice/telegram/bot.py

# Clear TTS cache if voice is stale
rm -rf voice/tts_cache/*

# Check Redis
redis-cli ping
```

---

## 📊 Understanding Test Results

### ✅ PASS
- Test completed successfully
- All validations passed
- System behaving as expected

### ❌ FAIL
- Test encountered an error
- Critical functionality broken
- **Must fix before demo**

### ⚠️ WARN (Warning)
- Test skipped or partially completed
- Non-critical issue
- System can function but investigate if time permits

---

## 🐛 Common Issues Found by Tests

### Issue: "No active workers found"
**Fix:** Start Celery worker
```bash
celery -A voice.tasks.celery_app worker --loglevel=info
```

### Issue: "Redis connection refused"
**Fix:** Start Redis
```bash
brew services start redis
```

### Issue: "Invalid audio file"
**Fix:** Ensure FFmpeg is installed and test files are valid
```bash
brew install ffmpeg
ffprobe documentation/testing/test_voice_messages/test_donate.mp3
```

### Issue: "No test voice files found"
**Fix:** Check test directory exists and has files
```bash
ls documentation/testing/test_voice_messages/*.mp3
```

### Issue: "Task timeout (>60s)"
**Possible causes:**
1. Celery worker overloaded
2. STT API slow/down
3. Network issues

**Fix:** Restart Celery and check logs

---

## 🎯 Success Criteria

Before demo starts, you should see:

- ✅ Pre-demo check: 0 critical failures
- ✅ Automated tests: 100% pass rate (or at least >80%)
- ✅ Manual test: Voice message → Voice reply works
- ✅ Celery worker: Running and processing tasks
- ✅ Redis: Responding to ping
- ✅ Database: Contains test campaigns
- ✅ TTS cache: Contains some files (shows caching works)

---

## 🚨 Last Resort (If Something Breaks)

### Nuclear Option: Full Restart
```bash
# Stop everything
pkill -f celery
pkill -f telegram_bot
brew services restart redis

# Wait 5 seconds
sleep 5

# Start fresh
celery -A voice.tasks.celery_app worker --loglevel=info &
python voice/telegram/bot.py &

# Wait 10 seconds
sleep 10

# Test
python tests/pre_demo_check.py
```

### Rollback to Text-Only Mode
If voice processing is completely broken, modify bot to respond with text only:
```python
# In voice/telegram/bot.py, temporarily disable voice processing
# Comment out the Celery task call and return a text response
```

---

## 📞 Quick Reference Commands

```bash
# Activate venv first
source venv/bin/activate

# Check everything
python tests/pre_demo_check.py

# Run full test suite
python tests/test_voice_modules_automated.py

# Start services (each in a separate terminal)
brew services start redis
cd /Users/manu/Trust-Voice && source venv/bin/activate && celery -A voice.tasks.celery_app worker --loglevel=info
cd /Users/manu/Trust-Voice && source venv/bin/activate && python voice/telegram/bot.py

# Check service status
ps aux | grep -E "celery|telegram_bot" | grep -v grep
redis-cli ping

# View logs
tail -f logs/bot.log
tail -f logs/celery.log

# Database query
python -c "from sqlalchemy import create_engine, text; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); result = conn.execute(text('SELECT COUNT(*) FROM campaigns')); print(f'Campaigns: {result.scalar()}')"
```

---

**Good luck with your demo! 🎉**
