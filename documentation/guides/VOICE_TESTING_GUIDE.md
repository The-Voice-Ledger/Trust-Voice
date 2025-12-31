# Voice Enhancements Testing Guide

**Date:** 31 December 2025  
**Status:** Week 1 Complete - Ready for Testing  
**Version:** 1.0

---

## 🎯 Testing Overview

This guide covers testing for the Week 1 Voice Enhancements:
1. **Dynamic Context Updates** - Context-aware voice commands
2. **Silent Audio Detection** - Audio validation before upload
3. **Backend Context Integration** - Context processing in AI responses

---

## 🚀 Quick Start

### Prerequisites
```bash
# All services must be running:
# 1. FastAPI backend (port 8001)
# 2. ngrok tunnel
# 3. Celery workers
# 4. Telegram bot

# Verify services:
ps aux | grep -E "(uvicorn|celery|ngrok)" | grep -v grep
```

### Access Mini App
1. Open Telegram
2. Navigate to @TrustVoiceBot
3. Click "Mini Apps" button
4. Select "Campaigns"

---

## 📋 Test Scenarios

### Test Suite 1: Dynamic Context - List View

**Setup:**
- Open Campaigns mini app
- Ensure you're viewing the campaign list (not details)

**Test 1.1: General Search**
```
Voice Command: "show me water campaigns"
Expected Behavior:
✅ Search input populated with "water campaigns"
✅ Campaign list filters to matching campaigns
✅ Console shows: voiceContext with view='list'
✅ TTS response: "I found X campaigns for 'water'"
```

**Test 1.2: Keyword Search**
```
Voice Command: "health"
Expected Behavior:
✅ Filters campaigns containing "health"
✅ Context includes first 10 visible campaigns
✅ Response lists matching campaigns
```

### Test Suite 2: Dynamic Context - Detail View

**Setup:**
- Open a specific campaign (click on any campaign)
- Wait for detail alert to appear

**Test 2.1: Context-Aware Donation**
```
Voice Command: "donate to this campaign"
Expected Behavior:
✅ Console shows: voiceContext with view='detail'
✅ selected_campaign includes campaign ID, title, amounts
✅ Response: "To donate to [Campaign Name], tap the Donate button"
✅ Shows goal and raised amounts
```

**Test 2.2: Context-Aware Info Request**
```
Voice Command: "tell me about this"
Expected Behavior:
✅ Returns campaign description (first 200 chars)
✅ Uses selected campaign from context
```

**Test 2.3: Context Keywords**
Test with variations:
- "donate to the current campaign"
- "give to this one"
- "contribute to the shown campaign"
- "support the selected project"

All should resolve to the currently viewed campaign.

### Test Suite 3: Silent Audio Detection

**Test 3.1: Too Short Recording**
```
Action: Press and immediately release voice button (<0.5s)
Expected Behavior:
✅ Popup: "Recording Too Short"
✅ Message: "Your recording was less than 1 second"
✅ Suggestion: "Please hold the voice button and speak"
✅ No API call made
✅ Instant feedback (< 100ms)
```

**Test 3.2: Silent Recording**
```
Action: Hold voice button for 2s but don't speak
Expected Behavior:
✅ Shows: "🔍 Validating audio..."
✅ After validation: "🔇 No Speech Detected"
✅ Message: "I couldn't hear any speech in your recording"
✅ Tips for improvement shown
✅ No API call made
✅ Haptic error feedback
```

**Test 3.3: Noisy Environment**
```
Action: Record in noisy environment (music, traffic)
Expected Behavior:
✅ If amplitude > 0.01: Passes validation
✅ Proceeds to transcription
Note: Threshold 0.01 allows background noise
```

**Test 3.4: Normal Speech**
```
Action: Record clear speech "show campaigns"
Expected Behavior:
✅ Passes all validations (duration, size, sound)
✅ Shows: "Processing your voice command..."
✅ Uploads to backend
✅ Returns results
```

### Test Suite 4: Error Handling

**Test 4.1: Network Failure**
```
Setup: Disable network briefly
Action: Record voice command
Expected Behavior:
❌ Currently: Shows generic error (Week 2 will add retry)
📝 After Week 2: Exponential backoff retry
```

**Test 4.2: Invalid Audio Format**
```
Note: Browser MediaRecorder handles format
Expected Behavior:
✅ Always produces webm/ogg
✅ Backend accepts webm format
```

**Test 4.3: Backend Context Parsing Error**
```
Setup: Malformed context JSON (shouldn't happen)
Expected Behavior:
✅ Backend logs warning
✅ Continues without context
✅ Regular search functionality works
```

### Test Suite 5: Bilingual Support

**Test 5.1: English Commands**
```
Voice Commands:
- "show water campaigns"
- "donate to this"
- "tell me about this campaign"

Expected Behavior:
✅ English responses
✅ Proper formatting
```

**Test 5.2: Amharic Context** (if user language set)
```
Expected Behavior:
✅ Responses in Amharic
✅ Proper character encoding
✅ Context logic same as English
```

---

## 🔍 Debugging

### Console Logs to Check

**1. Context Updates:**
```javascript
// Should appear on every navigation
[Voice Context] Updated: {
    app: 'campaigns',
    view: 'list' | 'detail',
    selected_campaign: {...},  // when in detail view
    visible_campaigns: [...],   // when in list view
    available_actions: [...],
    timestamp: '...'
}
```

**2. Audio Validation:**
```javascript
// When validating audio
Audio validation result: {
    hasSound: true,
    maxAmplitude: 0.234,
    duration: 2.5,
    error: null
}
```

**3. Voice Command Processing:**
```javascript
// When sending to backend
Processing voice command with context: {view: 'detail', app: 'campaigns'}
```

### Backend Logs to Check

**1. Context Reception:**
```python
# voice/routers/miniapp_voice.py
INFO: Voice search with context: view=detail, app=campaigns
INFO: Context-aware: User referring to campaign 123
```

**2. Context-Aware Search:**
```python
INFO: Using context: Campaign 'Clean Water Project'
INFO: Found 1 campaigns matching 'donate to this'
```

### Common Issues

**Issue: Context not updating**
```
Check:
1. Browser console for updateVoiceContext() calls
2. Verify currentView and currentCampaign variables
3. Check if alert close callback fires
```

**Issue: Silent detection not working**
```
Check:
1. Browser supports Web Audio API (all modern browsers do)
2. AudioContext creation successful
3. Amplitude threshold (0.01) appropriate for environment
```

**Issue: Context not sent to backend**
```
Check:
1. FormData includes 'context' field
2. JSON.stringify works correctly
3. Backend receives context parameter
```

---

## 📊 Success Metrics

### Performance Benchmarks

**Audio Validation Speed:**
- ✅ Target: < 500ms for validation
- ✅ Target: < 100ms for duration/size checks
- ✅ Target: < 400ms for amplitude analysis

**Context Update Speed:**
- ✅ Target: < 50ms for context updates
- ✅ Target: Synchronous with navigation

**API Response Time:**
- ✅ Target: < 2s for transcription + search
- ✅ Target: < 1s for TTS generation

### Quality Metrics

**Context Accuracy:**
- ✅ Target: 95% correct campaign resolution
- ✅ Target: 100% view state tracking
- ✅ Target: 0% false positives on "this" keyword

**Silent Detection Accuracy:**
- ✅ Target: 98% true positive (catches silent audio)
- ✅ Target: < 2% false positive (rejects valid speech)
- ✅ Target: 100% fail-open (allows upload on validation error)

---

## 🧪 Automated Testing (Future)

### Unit Tests Needed

```javascript
// Test context updates
describe('updateVoiceContext', () => {
    it('should set view to detail when viewing campaign');
    it('should include selected campaign data');
    it('should reset to list on alert close');
    it('should include first 10 visible campaigns in list view');
});

// Test audio validation
describe('checkAudioHasSound', () => {
    it('should detect silent audio (amplitude < 0.01)');
    it('should pass normal speech (amplitude > 0.1)');
    it('should fail-open on AudioContext errors');
    it('should calculate duration correctly');
});
```

### Integration Tests Needed

```python
# Test backend context processing
def test_voice_search_with_context():
    """Test context-aware campaign resolution"""
    # Send voice command with detail view context
    # Verify selected campaign used for search

def test_voice_search_without_context():
    """Test fallback to regular search"""
    # Send voice command without context
    # Verify regular search across all campaigns

def test_context_keyword_detection():
    """Test 'this/current/shown' keyword detection"""
    # Send commands with context keywords
    # Verify correct campaign resolution
```

---

## 📈 Testing Checklist

Before marking Week 1 complete:

### Frontend Tests
- [ ] Context updates on campaign load
- [ ] Context updates on search/filter
- [ ] Context updates on view details
- [ ] Context resets on alert close
- [ ] Silent audio detected correctly
- [ ] Duration validation works
- [ ] Size validation works
- [ ] Error messages display correctly
- [ ] Context sent with FormData

### Backend Tests
- [ ] Context parameter received
- [ ] JSON parsing handles errors
- [ ] Context keywords detected
- [ ] Selected campaign resolved from context
- [ ] Regular search works without context
- [ ] Bilingual responses correct
- [ ] TTS generation works
- [ ] Error handling graceful

### End-to-End Tests
- [ ] "donate to this" works in detail view
- [ ] "donate to this" fails gracefully in list view
- [ ] Silent recording caught before API call
- [ ] Normal commands work as before
- [ ] Search still works without voice
- [ ] No regressions in existing functionality

---

## 🎉 Success Criteria

Week 1 is successful if:
1. ✅ Context-aware commands resolve correctly 95% of time
2. ✅ Silent audio caught before API call 98% of time
3. ✅ No increase in error rate for normal commands
4. ✅ User sees clear, actionable error messages
5. ✅ Bilingual support works for both English and Amharic
6. ✅ No breaking changes to existing functionality

---

## 🔜 Next Steps

After Week 1 testing complete:
1. Document any issues found
2. Fix critical bugs
3. Gather baseline metrics
4. Proceed to Week 2: Exponential Backoff Retry + TTS Controls
