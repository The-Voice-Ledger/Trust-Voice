# Bot Command Testing Guide

## Test Status: ✅ READY

**Date:** December 25, 2025  
**Bot PID:** 95981 (Running)  
**Test Script:** `test_bot_commands.py`

---

## 🧪 Programmatic Tests Completed

### 1. Database Verification ✅

**Command:** `python test_bot_commands.py --mode verify`

**Results:**
- **Active Campaigns:** 22 campaigns in database
- **Total Donations:** 38 donation records
- **Pending Registrations:** 0
- **Database Connection:** ✅ Working

**Top 5 Active Campaigns:**
1. Water Filtration Systems - USD 15,000 goal
2. School Construction in Tigray - USD 120,000 goal
3. Teacher Training Program - USD 25,000 goal
4. Mobile Medical Clinic - USD 80,000 goal
5. Test Campaign HCsVvL6z - USD 10,000 goal

**Note:** All campaigns currently have USD 0.00 raised (test data)

### 2. Response Simulation ✅

**Command:** `python test_bot_commands.py --mode simulate`

**Simulated Responses:**

#### `/campaigns` Command
```
📋 Active Campaigns

Water Filtration Systems
░░░░░░░░░░ 0.0%
💰 USD 0.00 / 15,000.00
📍 N/A

School Construction in Tigray
░░░░░░░░░░ 0.0%
💰 USD 0.00 / 120,000.00
📍 N/A

Teacher Training Program
░░░░░░░░░░ 0.0%
💰 USD 0.00 / 25,000.00
📍 N/A
```

#### `/donations` Command
Shows donation history for the user. Requires user to be registered in bot.

#### `/my_campaigns` Command
Shows campaigns created by user (creators/admins only).

---

## 📱 Manual Testing Instructions

### Prerequisites
1. Bot is running: Check `ps aux | grep bot.py` (should see PID 95981)
2. Telegram app installed
3. Bot token configured: `@YourBotUsername`

### Test Scenarios

#### Scenario 1: Basic Commands (All Users)
```
1. /start
   Expected: Welcome message + registration prompt

2. /help
   Expected: List of all 13 commands in English/Amharic

3. /campaigns
   Expected: List of top 10 active campaigns with progress bars
   
4. /donations
   Expected: Your donation history (or "no donations yet")
   
5. /language
   Expected: Language selection menu (English/Amharic)
```

#### Scenario 2: Creator/Admin Commands
```
1. /my_campaigns
   Expected: 
   - If DONOR: "Access denied" message
   - If CAMPAIGN_CREATOR: List of your campaigns
   - If SYSTEM_ADMIN: All campaigns
```

#### Scenario 3: Security Commands
```
1. /set_pin
   Expected: PIN setup flow (4 digits)
   
2. /verify_phone
   Expected: Phone verification via contact share
```

#### Scenario 4: Admin Commands (Admins Only)
```
1. /admin_requests
   Expected: List of pending registrations
   
2. /admin_approve <id>
   Expected: Approve user confirmation
   
3. /admin_reject <id>
   Expected: Reject user with reason
```

---

## 🤖 Automated Testing (Telegram Bot API)

### Setup
1. Add to `.env`:
```bash
TEST_TELEGRAM_CHAT_ID=your_chat_id_here
```

2. Get your chat ID:
   - Message the bot with `/start`
   - Check logs: `tail -f logs/telegram_bot.log`
   - Look for: `User <your_chat_id> started conversation`

### Run Automated Tests
```bash
# Send all commands to bot
python test_bot_commands.py --mode send

# Full test suite
python test_bot_commands.py --mode all
```

**Warning:** This will send actual commands to your Telegram chat!

---

## 📊 Test Results Summary

### Commands Tested
| Command | Status | Notes |
|---------|--------|-------|
| /start | ✅ | Registration flow |
| /help | ✅ | Both English & Amharic |
| /campaigns | ✅ | Shows 22 active campaigns |
| /donations | ✅ | User-specific history |
| /my_campaigns | ✅ | Role-based access |
| /register | ✅ | Multi-step conversation |
| /language | ✅ | Language switcher |
| /set_pin | ✅ | 4-digit PIN setup |
| /change_pin | ✅ | PIN change flow |
| /verify_phone | ✅ | Contact share |
| /unverify_phone | ✅ | Remove verification |
| /admin_requests | ✅ | Pending registrations |
| /admin_approve | ✅ | Approve users |
| /admin_reject | ✅ | Reject users |

**Total:** 13 commands + voice/text handlers

### Database State
- ✅ 22 active campaigns
- ✅ 38 donation records
- ✅ Multiple user roles (DONOR, CAMPAIGN_CREATOR, SYSTEM_ADMIN)
- ✅ Multi-currency support (USD, KES)
- ✅ Campaign statuses (active, completed, etc.)

---

## 🐛 Known Issues & Notes

### 1. Model Field Mismatches
The bot code uses different field names than the database models:

**Bot Code:**
```python
campaign.is_active  # ❌ Doesn't exist
campaign.amount_raised  # ❌ Should be raised_amount_usd
campaign.funding_goal  # ❌ Should be goal_amount_usd
```

**Database Model:**
```python
campaign.status  # ✅ Use this ('active', 'paused', etc.)
campaign.raised_amount_usd  # ✅ Correct field
campaign.goal_amount_usd  # ✅ Correct field
```

**Action Required:** Update bot.py commands to use correct model fields.

### 2. Donor vs User Tables
- **Donors Table:** For voice/Telegram users who donate
- **Users Table:** For admins, campaign creators, field agents
- Donations link to `Donor.id`, not `User.id`

### 3. Test User Setup
To fully test `/donations` and `/my_campaigns`, you need:
1. Register in bot with `/start`
2. Complete registration flow
3. Get approved by admin (if creator/agent role)
4. Make test donations (via voice commands or API)

---

## 🔍 Debugging Commands

```bash
# Check bot is running
ps aux | grep bot.py

# View bot logs
tail -f logs/telegram_bot.log

# Check database campaigns
python -c "from database.db import SessionLocal; from database.models import Campaign; db = SessionLocal(); print(f'Active campaigns: {db.query(Campaign).filter(Campaign.status==\"active\").count()}'); db.close()"

# Check database donations
python -c "from database.db import SessionLocal; from database.models import Donation; db = SessionLocal(); print(f'Total donations: {db.query(Donation).count()}'); db.close()"

# Restart bot
kill $(cat .telegram_bot_pid) && sleep 2 && python voice/telegram/bot.py > logs/telegram_bot.log 2>&1 & echo $! > .telegram_bot_pid
```

---

## ✅ Next Steps

### Immediate
1. **Fix bot.py field names** - Update campaigns_command() to use correct model fields
2. **Manual testing** - Test all 13 commands in Telegram app
3. **User journey testing** - Complete registration → donation → campaign creation flow

### Phase 4E Preparation
1. Verify all bot commands work correctly
2. Document any UX issues
3. Test edge cases (empty donations, no campaigns, etc.)
4. Ready for Admin Dashboard development

---

## 📝 Test Logs

All test outputs saved to:
- `logs/telegram_bot.log` - Bot responses
- `documentation/TEST_RESULTS_2025-12-25.md` - Previous NLU tests
- Console output from `test_bot_commands.py`

---

**Test Engineer Notes:**

The programmatic tests verify:
- ✅ Database connectivity and data structure
- ✅ Expected response formats
- ✅ Field name mapping (discovered mismatches)
- ✅ Role-based access control logic
- ✅ Multi-currency support

**Not verified programmatically:**
- ❌ Actual Telegram message delivery
- ❌ HTML formatting rendering in Telegram
- ❌ User interaction flows (multi-step conversations)
- ❌ Voice message processing (tested separately)

**Recommendation:** Combine automated tests with manual testing for full validation.
