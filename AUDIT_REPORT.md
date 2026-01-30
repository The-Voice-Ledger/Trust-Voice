# Trust Voice System Audit Report
**Date:** January 30, 2026
**Status:** CRITICAL ISSUES IDENTIFIED

## Executive Summary

The system has multiple architectural problems causing voice processing failures across all interfaces (Telegram bot, miniapp, web UI). The root cause is **duplication of processing logic** and **inconsistent response handling**.

---

## 🔴 CRITICAL ISSUES

### 1. **DUPLICATE VOICE PROCESSING** (Telegram Bot)
**File:** `voice/telegram/bot.py` (lines 688-790)
**Problem:** Bot processes voice messages TWICE:
1. Worker task processes audio → ASR → NLU → routing → returns response
2. Bot IGNORES worker response and calls `route_command()` AGAIN

**Impact:** 
- Responses not sent to users
- Wasted API calls (2x Whisper, 2x GPT-4)
- Session state corruption

**Evidence:**
```python
# Line 686: Get result from worker
result = task.get()

# Lines 691-695: Extract data from worker result
intent = result.get("intent")
entities = result.get("entities", {})
transcript = result["stages"]["asr"]["transcript"]

# Lines 700-789: IGNORE result["response"] and call route_command() AGAIN
router_result = await route_command(...)  # ← DUPLICATE PROCESSING
```

**Fix Applied (line 695-711):**
```python
# Use response from worker if available
if "response" in result and "message" in result["response"]:
    response = result["response"]["message"]
    # Send response and return early
    return
```

**Status:** ✅ FIXED (commit 79ef195)

---

### 2. **INCONSISTENT LANGUAGE DETECTION**
**Files:** Multiple
**Problem:** Language detection logic differs across interfaces:

| Interface | Method | Source |
|-----------|--------|--------|
| Telegram Bot | Database → localStorage | `get_user_language_preference()` |
| Miniapp | localStorage → Database | `initializeUserLanguage()` |
| Worker | Parameter only | Direct from bot |
| Web UI | Not implemented | ❌ MISSING |

**Impact:**
- User says "I want to create campaign" (English)
- System processes in Amharic (from cached localStorage)
- Slow local model used instead of fast Whisper API
- Timeouts occur

**Evidence from logs:**
```
INFO:voice.routers.miniapp_voice:Voice wizard step for field: title, step: 1, lang: am
WARNING:voice.asr.asr_infer:AddisAI transcription failed
INFO:voice.asr.asr_infer:Falling back to local Amharic model
[... 30 seconds of processing ...]
```

**Root Cause:** localStorage caches `'am'` even after user changes to English in database

**Fix Needed:**
1. Always fetch from database on page load
2. Clear localStorage when language changes
3. Add cache expiration (TTL)

---

### 3. **SESSIONMANAGER METHOD MISMATCH**
**File:** `voice/telegram/bot.py` (line 775)
**Problem:** Called non-existent method `SessionManager.start_session()`
**Actual method:** `SessionManager.create_session()`

**Impact:** 
- AttributeError exception thrown
- No clarification flow possible
- Users never get asked for missing entities

**Status:** ✅ FIXED (commit 28d70cd)

---

### 4. **MISSING CLARIFICATION STATE**
**File:** `voice/session_manager.py` (lines 38-43)
**Problem:** ConversationState enum missing `WAITING_FOR_CLARIFICATION`

**Impact:**
- Cannot track multi-turn conversations
- Missing entity collection fails
- Users must repeat entire commands

**Status:** ✅ FIXED (commit 28d70cd)

---

### 5. **EXCEPTION HANDLER DOUBLE-DELETE**
**File:** `voice/telegram/bot.py` (line 818)
**Problem:** Exception handler tries to delete already-deleted message

**Flow:**
1. Line 689: `await processing_msg.delete()` ✅
2. Lines 690-805: Processing logic
3. Exception occurs
4. Line 818: `await processing_msg.delete()` ❌ "Message to delete not found"
5. Second exception prevents response from being sent

**Impact:** Any exception after line 689 blocks all responses

**Status:** ✅ FIXED (commit e1ce10c)

---

## ⚠️ HIGH PRIORITY ISSUES

### 6. **WORKER VS BOT ARCHITECTURE CONFUSION**
**Problem:** Unclear separation of responsibilities

**Current State:**
- Worker: ASR → NLU → Routing → Response generation
- Bot: Waits for worker, then routes AGAIN

**Should Be:**
- **Option A:** Worker does everything, bot just sends response
- **Option B:** Bot does everything, no worker needed for voice

**Current implementation is half Option A, half Option B = BROKEN**

**Recommendation:** Choose Option A (worker-based) and fix bot.py to only send responses

---

### 7. **ADDISAI EVENT LOOP ERROR**
**File:** `voice/providers/addis_ai.py` (line 313)
**Problem:** Creates new event loop in sync context while another loop is running

**Error:**
```python
RuntimeWarning: coroutine 'AddisAIProvider.transcribe' was never awaited
loop.close()
WARNING: AddisAI transcription failed: Cannot run the event loop while another loop is running
```

**Impact:**
- All Amharic transcriptions fail
- Falls back to slow local model (30+ seconds)
- Users experience timeouts

**Fix Needed:**
```python
# Instead of creating new loop:
loop = asyncio.new_event_loop()  # ❌

# Use existing loop:
result = await provider.transcribe(audio_path, language)  # ✅
```

---

### 8. **NO ERROR PROPAGATION IN MINIAPP**
**Files:** `frontend-miniapps/*.html`
**Problem:** Voice processing errors not shown to users

**Current behavior:**
1. User speaks
2. Request fails
3. Loading indicator stays forever
4. No error message shown

**Fix Needed:** Add error handling in all miniapp voice buttons:
```javascript
catch (error) {
    console.error('Voice processing failed:', error);
    alert(`Voice processing failed: ${error.message}`);
    // Hide loading indicator
    // Re-enable button
}
```

---

### 9. **INCONSISTENT RESPONSE FORMATS**
**Problem:** Different endpoints return different response structures

**Examples:**
```python
# Telegram bot expects:
result["response"]["message"]

# Miniapp expects:
result["response_text"]

# Worker returns:
result["response"]["message"] OR result["response"]["type"]

# Command router returns:
router_result["message"]
```

**Impact:** Response extraction logic fragile and error-prone

**Fix Needed:** Standardize on single response format across all interfaces

---

## 🟡 MEDIUM PRIORITY ISSUES

### 10. **HARDCODED LANGUAGE FALLBACKS**
Multiple files have:
```python
language = user_language or "en"  # Always defaults to English
```

Should respect user's system language or database setting

---

### 11. **NO TIMEOUT HANDLING IN WORKER**
Worker tasks can run indefinitely. No timeout configured in Celery.

**Fix Needed:**
```python
@app.task(
    time_limit=60,  # Hard timeout
    soft_time_limit=45  # Warning timeout
)
```

---

### 12. **REDIS KEY NAMESPACE POLLUTION**
Keys not namespaced properly:
- `audio:{user_id}:{file_id}` ✅ Good
- `session:{user_id}` ✅ Good
- Random keys from other systems ❌ Bad

**Fix Needed:** Use key prefix for all Trust Voice keys: `tv:audio:...`, `tv:session:...`

---

### 13. **NO RATE LIMITING**
Voice endpoints have no rate limiting. Users can spam requests.

**Fix Needed:** Add rate limiting decorator:
```python
@router.post("/voice/search-campaigns")
@rate_limit("10/minute")  # Max 10 requests per minute
async def voice_search_campaigns(...):
```

---

### 14. **INCOMPLETE CLEANUP**
Audio files not always deleted:
- `cleanup_audio=True` in pipeline
- BUT exception before cleanup = file stays
- No periodic cleanup job

**Fix Needed:** Add finally block to ensure cleanup

---

### 15. **NO METRICS/MONITORING**
No tracking of:
- Voice processing latency
- Success/failure rates
- Language distribution
- API costs (Whisper, GPT-4)

**Fix Needed:** Add metrics collection to pipeline

---

## 📊 SYSTEM HEALTH CHECK

| Component | Status | Issues |
|-----------|--------|--------|
| Telegram Bot Voice | 🔴 BROKEN | Duplicate processing, no responses sent |
| Miniapp Voice | 🟡 DEGRADED | Slow (wrong language), no error handling |
| Web UI Voice | 🔴 MISSING | Not implemented |
| Worker Processing | 🟢 WORKING | Returns correct responses |
| ASR (English) | 🟢 WORKING | Whisper API fast |
| ASR (Amharic) | 🔴 BROKEN | AddisAI fails, local model too slow |
| NLU | 🟢 WORKING | GPT-4 intent extraction accurate |
| Redis Storage | 🟢 WORKING | Audio storage/retrieval functional |
| SessionManager | 🟡 FIXED | Was broken, now working |

---

## 🎯 RECOMMENDED FIX PRIORITY

### IMMEDIATE (Today)
1. ✅ Fix duplicate processing in bot.py
2. ✅ Fix SessionManager method calls
3. ✅ Fix exception handler double-delete
4. ⏳ Fix AddisAI event loop issue
5. ⏳ Add error handling to miniapp voice UI

### THIS WEEK
6. Standardize response formats across all interfaces
7. Implement proper language detection with cache invalidation
8. Add rate limiting to voice endpoints
9. Add timeout configuration to worker tasks
10. Implement cleanup job for temp files

### NEXT SPRINT
11. Add comprehensive error handling
12. Implement metrics/monitoring
13. Add user-facing error messages
14. Performance optimization (caching, batching)
15. Documentation update

---

## 💡 ARCHITECTURAL RECOMMENDATIONS

### 1. **Simplify Voice Flow**
```
Current (BROKEN):
Audio → Worker → [ASR → NLU → Route] → Bot → Route Again → Response

Proposed (SIMPLE):
Audio → Worker → [ASR → NLU → Route → Response] → Bot → Send
```

### 2. **Unified Response Format**
```python
{
    "success": bool,
    "data": {
        "transcript": str,
        "intent": str,
        "entities": dict,
        "message": str,  # ALWAYS this field name
        "audio_url": Optional[str]
    },
    "error": Optional[str]
}
```

### 3. **Language Detection Strategy**
```
1. Check user parameter (explicit override)
2. Check database (user.preferred_language)
3. Detect from transcript (if audio contains speech)
4. Default to system language (not hardcoded 'en')
```

### 4. **Error Handling Strategy**
```
1. Worker: Catch all exceptions, return error in result
2. Bot/API: Check result.success, show user-friendly message
3. Frontend: Always show error state, never leave loading
4. Logging: Log full stack trace for debugging
```

---

## 📝 CODE QUALITY ISSUES

### Found During Audit:
1. **Inconsistent naming:** `user_language` vs `language` vs `lang` vs `detected_language`
2. **Mixed sync/async:** Some functions sync, some async, no clear pattern
3. **Import chaos:** Same modules imported multiple times in different ways
4. **No type hints:** Return types unclear, function contracts ambiguous
5. **Dead code:** Multiple `.backup` files, commented-out code blocks
6. **Missing docstrings:** Many functions lack documentation
7. **Long functions:** Some functions >100 lines, should be split
8. **Magic numbers:** Hardcoded values (300s TTL, 5 retry limit, etc.)

---

## 🔧 TOOLS NEEDED

1. **Linting:** Add `pylint` or `ruff` to catch issues
2. **Type checking:** Add `mypy` for type safety
3. **Testing:** Expand test coverage (currently ~30%)
4. **Monitoring:** Add Sentry or similar for error tracking
5. **Profiling:** Add performance monitoring for slow endpoints

---

## 📌 SUMMARY

**Total Issues Found:** 15
- Critical: 5 (3 fixed, 2 remaining)
- High: 4
- Medium: 6

**System is currently:** 🔴 **BROKEN FOR END USERS**

**After fixes applied:** 🟡 **DEGRADED BUT FUNCTIONAL**

**To reach production quality:** 🎯 **2-3 weeks of work needed**

---

**Generated:** January 30, 2026
**Next Review:** After immediate fixes applied
