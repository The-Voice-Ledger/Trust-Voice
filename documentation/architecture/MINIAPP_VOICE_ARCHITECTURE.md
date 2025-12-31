# Mini App Voice Architecture

**Document Version**: 1.0  
**Last Updated**: December 30, 2025  
**Author**: TrustVoice Engineering Team

---

## 📋 Overview

This document explains how voice search is implemented in TrustVoice Mini Apps. Unlike the Telegram bot which uses native voice messages, mini apps capture audio using browser APIs and process it through a dedicated backend endpoint.

**Key Difference from Bot:**
- **Telegram Bot**: Uses native voice messages (automatic file handling by Telegram)
- **Mini Apps**: Uses browser MediaRecorder API (manual audio capture and upload)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Mini App (Browser)                                │
│                                                                       │
│  📱 User Interface                                                   │
│    ├── Voice button (microphone icon)                               │
│    ├── Recording indicator (pulsing red)                            │
│    └── Response display (transcription + answer)                    │
│                                                                       │
│  🎤 Audio Capture (MediaRecorder API)                               │
│    ├── navigator.mediaDevices.getUserMedia()                        │
│    ├── MediaRecorder with ondataavailable                           │
│    ├── Blob creation from audioChunks                               │
│    └── webm format output                                           │
│                                                                       │
│  📤 Upload & Playback                                                │
│    ├── FormData with audio blob + user_id                           │
│    ├── POST /api/voice/search-campaigns                             │
│    ├── JSON response parsing                                        │
│    └── Audio API plays TTS response                                 │
└───────────────────────────┬───────────────────────────────────────┘
                             │
                             │ HTTPS POST
                             │ Content-Type: multipart/form-data
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│              Backend Voice Endpoint                                   │
│              voice/routers/miniapp_voice.py                          │
│                                                                       │
│  📥 Request Processing                                               │
│    ├── Save uploaded audio to tempfile                              │
│    ├── Extract user_id from form data                               │
│    └── Validate file format (webm, ogg, wav)                        │
│                                                                       │
│  🗣️ Voice Pipeline Integration                                      │
│    ├── 1. Get user language preference (DB lookup)                  │
│    ├── 2. Transcribe audio (voice.asr.asr_infer)                   │
│    ├── 3. Parse query (voice.workflows.search_flow)                │
│    ├── 4. Search campaigns (same as bot logic)                      │
│    ├── 5. Generate TTS response (voice.tts.tts_provider)           │
│    └── 6. Clean up temp file                                        │
│                                                                       │
│  📤 Response Format                                                  │
│    └── JSON: {transcription, response_text, audio_url, campaigns}   │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Frontend Implementation

### File Location
`frontend-miniapps/campaigns.html` (lines 540-663)

### 1. HTML Structure

```html
<!-- Voice Search Button -->
<button id="voice-btn" class="voice-btn" title="Voice Search">
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" 
         fill="currentColor" viewBox="0 0 16 16">
        <!-- Microphone icon SVG path -->
        <path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5z"/>
        <path d="M10 8a2 2 0 1 1-4 0V3a2 2 0 1 1 4 0v5zM8 0a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V3a3 3 0 0 0-3-3z"/>
    </svg>
</button>

<!-- Voice Response Display (initially hidden) -->
<div id="voice-response" class="voice-response">
    <div class="voice-response-content">
        <div id="voice-transcription" class="voice-transcription"></div>
        <div id="voice-answer" class="voice-answer"></div>
    </div>
</div>
```

### 2. CSS Styling

```css
/* Voice button default state */
.voice-btn {
    background: var(--tg-theme-button-color, #3390ec);
    color: var(--tg-theme-button-text-color, #ffffff);
    border: none;
    border-radius: 50%;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

/* Recording state with pulsing animation */
.voice-btn.recording {
    background: #ef4444; /* Red */
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* Voice response box (slides up from bottom) */
.voice-response {
    display: none;
    position: fixed;
    bottom: 80px;
    left: 16px;
    right: 16px;
    background: var(--tg-theme-secondary-bg-color, #f0f0f0);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    animation: slideUp 0.3s ease-out;
}

.voice-response.active {
    display: block;
}

@keyframes slideUp {
    from {
        transform: translateY(100%);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
```

### 3. Audio Capture Logic

**Key Technology**: Native Web APIs (no external libraries)

```javascript
// Global state
let mediaRecorder;
let audioChunks = [];

// Voice button click handler
document.getElementById('voice-btn').addEventListener('click', async () => {
    const voiceBtn = document.getElementById('voice-btn');
    
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        // ⏹️ Stop recording
        mediaRecorder.stop();
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '🎤';
    } else {
        // ▶️ Start recording
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: true 
            });
            
            // Create MediaRecorder instance
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            // Collect audio data chunks
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            // Process when recording stops
            mediaRecorder.onstop = async () => {
                // Create audio blob from chunks
                const audioBlob = new Blob(audioChunks, { 
                    type: 'audio/webm' 
                });
                
                // Send to backend
                await processVoiceCommand(audioBlob);
                
                // Release microphone
                stream.getTracks().forEach(track => track.stop());
            };
            
            // Start recording
            mediaRecorder.start();
            voiceBtn.classList.add('recording');
            voiceBtn.innerHTML = '⏹️';
            
            // Haptic feedback (if Telegram WebApp)
            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
            
        } catch (error) {
            console.error('Microphone access denied:', error);
            alert('Please allow microphone access to use voice search');
        }
    }
});
```

### 4. Upload and Response Processing

```javascript
async function processVoiceCommand(audioBlob) {
    try {
        // Show loading state
        const responseBox = document.getElementById('voice-response');
        const transcriptionEl = document.getElementById('voice-transcription');
        const answerEl = document.getElementById('voice-answer');
        
        responseBox.classList.add('active');
        transcriptionEl.textContent = 'Listening...';
        answerEl.textContent = 'Processing your request...';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice-search.webm');
        
        // Get user ID from Telegram WebApp
        const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 'anonymous';
        formData.append('user_id', userId);
        
        // Send to backend
        const response = await fetch(`${API_BASE}/voice/search-campaigns`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display transcription and response
        transcriptionEl.textContent = `You said: "${data.transcription}"`;
        answerEl.textContent = data.response_text;
        
        // Update search input with transcription
        document.getElementById('search-input').value = data.transcription;
        
        // Play TTS audio response
        if (data.has_audio && data.audio_url) {
            const audio = new Audio(data.audio_url);
            audio.play();
        }
        
        // Display campaigns
        if (data.campaigns && data.campaigns.length > 0) {
            displayCampaigns(data.campaigns);
        }
        
        // Auto-hide response box after 5 seconds
        setTimeout(() => {
            responseBox.classList.remove('active');
        }, 5000);
        
    } catch (error) {
        console.error('Voice search error:', error);
        const answerEl = document.getElementById('voice-answer');
        answerEl.textContent = 'Error processing voice command. Please try again.';
    }
}
```

---

## 🔧 Backend Implementation

### File Location
`voice/routers/miniapp_voice.py` (lines 1-80+)

### 1. Endpoint Definition

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import logging

# Import TrustVoice voice pipeline components
from voice.asr.asr_infer import transcribe_audio
from voice.telegram.voice_responses import get_user_language_preference
from voice.tts.tts_provider import TTSProvider
from voice.workflows.search_flow import SearchConversation
from database.db_utils import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["Mini App Voice"])

@router.post("/search-campaigns")
async def voice_search_campaigns(
    audio: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Process voice search from mini app.
    
    Flow:
    1. Save uploaded audio to temp file
    2. Get user language preference
    3. Transcribe using Whisper ASR
    4. Search campaigns
    5. Generate TTS response
    6. Return JSON with results
    """
```

### 2. Audio Processing Pipeline

```python
try:
    # Step 1: Save audio to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
        audio_content = await audio.read()
        tmp_file.write(audio_content)
        audio_path = tmp_file.name
    
    try:
        # Step 2: Get user language preference from database
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            "SELECT language FROM users WHERE telegram_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        user_language = result[0] if result else 'en'
        cursor.close()
        db.close()
        
        # Step 3: Transcribe audio using Whisper
        # This is the ACTUAL TrustVoice ASR pipeline
        transcription = await transcribe_audio(
            audio_path=audio_path,
            language=user_language
        )
        
        if not transcription:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Could not transcribe audio",
                    "transcription": "",
                    "response_text": "I couldn't understand that. Please try again.",
                    "has_audio": False,
                    "audio_url": None,
                    "campaigns": []
                }
            )
        
        # Step 4: Search campaigns using SearchConversation
        # This is the SAME logic used by the Telegram bot
        search_conv = SearchConversation(session_manager)
        context = {
            "transcript": transcription,
            "user_id": user_id,
            "language": user_language
        }
        
        campaigns = await search_campaigns_by_query(transcription)
        
        # Step 5: Generate response text
        if campaigns:
            response_text = f"Found {len(campaigns)} campaign(s) matching your search."
        else:
            response_text = "No campaigns found matching your search."
        
        # Step 6: Generate TTS audio response
        # This is the ACTUAL TrustVoice TTS pipeline
        tts_provider = TTSProvider()
        audio_url = await tts_provider.generate_speech(
            text=response_text,
            language=user_language,
            user_id=user_id
        )
        
        # Step 7: Return complete response
        return JSONResponse(content={
            "transcription": transcription,
            "response_text": response_text,
            "has_audio": bool(audio_url),
            "audio_url": audio_url,
            "campaigns": [format_campaign(c) for c in campaigns]
        })
        
    finally:
        # Clean up temporary file
        if os.path.exists(audio_path):
            os.unlink(audio_path)

except Exception as e:
    logger.error(f"Voice search error: {e}")
    return JSONResponse(
        status_code=500,
        content={
            "error": str(e),
            "transcription": "",
            "response_text": "An error occurred. Please try again.",
            "has_audio": False,
            "audio_url": None,
            "campaigns": []
        }
    )
```

### 3. Campaign Formatting

```python
def format_campaign(campaign: dict) -> dict:
    """
    Format campaign data for mini app display.
    """
    return {
        "id": campaign.get("id"),
        "title": campaign.get("title"),
        "ngo_name": campaign.get("ngo_name"),
        "description": campaign.get("description"),
        "goal_amount": float(campaign.get("goal_amount", 0)),
        "current_amount": float(campaign.get("current_amount", 0)),
        "donor_count": campaign.get("donor_count", 0),
        "location": campaign.get("location"),
        "category": campaign.get("category"),
        "image_url": campaign.get("image_url"),
        "percentage": (
            (float(campaign.get("current_amount", 0)) / 
             float(campaign.get("goal_amount", 1))) * 100
        )
    }
```

---

## 🔄 Integration with Voice Pipeline

### Reusing Existing Components

The mini app voice endpoint **reuses the exact same voice processing pipeline** as the Telegram bot:

| Component | Module | Used By |
|-----------|--------|---------|
| **ASR** | `voice.asr.asr_infer.transcribe_audio` | Both |
| **NLU** | `voice.workflows.search_flow.SearchConversation` | Both |
| **TTS** | `voice.tts.tts_provider.TTSProvider` | Both |
| **Session** | `voice.workflows.session_manager.SessionManager` | Both |

**Why This Matters:**
- ✅ No code duplication
- ✅ Consistent behavior across interfaces
- ✅ Single pipeline to maintain and improve
- ✅ Same accuracy and quality

---

## 🆚 Telegram Bot vs Mini App Comparison

| Aspect | Telegram Bot | Mini App |
|--------|-------------|----------|
| **Audio Input** | Native voice message button | Custom record button + MediaRecorder |
| **File Format** | .ogg (Opus codec, Telegram's format) | .webm (browser default) |
| **Upload Method** | Automatic (Telegram handles it) | Manual (FormData POST) |
| **User ID** | From `update.message.from_user.id` | From `WebApp.initDataUnsafe.user.id` |
| **Handler** | `voice/telegram/bot.py` voice handler | `voice/routers/miniapp_voice.py` endpoint |
| **Processing Flow** | Bot receives file_id → Downloads → Processes | Browser uploads blob → Saves to temp → Processes |
| **Response Method** | `send_voice()` with audio file | JSON with audio_url |
| **Playback** | Native Telegram audio player | HTML5 `<audio>` element |
| **Session Context** | Automatic conversation thread | Manual session ID generation |
| **File Storage** | Telegram CDN (automatic) | Local temp file (manual cleanup) |

### Why Different Approaches?

**Telegram Bot:**
- Leverages Telegram's built-in voice message infrastructure
- File handling is abstracted by Telegram API
- Optimized for mobile messaging experience

**Mini App:**
- Runs in web context (no access to Telegram voice messages)
- Needs browser APIs for audio capture
- Optimized for in-app experience without leaving context

---

## 📊 Request/Response Flow

### Request Format

```
POST /api/voice/search-campaigns HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="audio"; filename="voice-search.webm"
Content-Type: audio/webm

[Binary audio data]
------WebKitFormBoundary
Content-Disposition: form-data; name="user_id"

123456789
------WebKitFormBoundary--
```

### Success Response

```json
{
    "transcription": "show me education campaigns in Kenya",
    "response_text": "Found 3 campaign(s) matching your search.",
    "has_audio": true,
    "audio_url": "https://api.trustvoice.org/audio/tts_12345.mp3",
    "campaigns": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Build Schools in Nairobi",
            "ngo_name": "Education For All Kenya",
            "description": "Help build 5 schools...",
            "goal_amount": 50000.0,
            "current_amount": 12500.0,
            "donor_count": 45,
            "location": "Nairobi, Kenya",
            "category": "education",
            "image_url": "https://...",
            "percentage": 25.0
        }
    ]
}
```

### Error Response

```json
{
    "error": "Could not transcribe audio",
    "transcription": "",
    "response_text": "I couldn't understand that. Please try again.",
    "has_audio": false,
    "audio_url": null,
    "campaigns": []
}
```

---

## 🔒 Security Considerations

### 1. Input Validation

```python
# File size limit (10MB max)
MAX_AUDIO_SIZE = 10 * 1024 * 1024

if len(audio_content) > MAX_AUDIO_SIZE:
    raise HTTPException(
        status_code=413,
        detail="Audio file too large. Max 10MB"
    )

# File type validation
ALLOWED_TYPES = ['audio/webm', 'audio/ogg', 'audio/wav']
if audio.content_type not in ALLOWED_TYPES:
    raise HTTPException(
        status_code=415,
        detail=f"Unsupported format. Allowed: {ALLOWED_TYPES}"
    )
```

### 2. User Authentication

```python
from voice.telegram.auth import verify_telegram_webapp_data

# Verify request came from Telegram
def verify_miniapp_request(init_data: str, bot_token: str) -> dict:
    """
    Verify Telegram WebApp init data signature.
    Returns user data if valid, raises HTTPException if not.
    """
    # Implementation validates HMAC signature
    pass
```

### 3. Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: request.client.host)

@router.post("/search-campaigns")
@limiter.limit("10/minute")  # Max 10 voice searches per minute per IP
async def voice_search_campaigns(...):
    pass
```

### 4. Temporary File Cleanup

```python
# Always use try/finally for temp file cleanup
try:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(audio_content)
        audio_path = tmp.name
    
    # Process audio...
    
finally:
    # Guaranteed cleanup even if processing fails
    if os.path.exists(audio_path):
        os.unlink(audio_path)
```

---

## 📱 Browser Compatibility

### MediaRecorder Support

| Browser | Min Version | Notes |
|---------|-------------|-------|
| **Chrome** | 49+ | ✅ Full support, best quality |
| **Firefox** | 25+ | ✅ Full support |
| **Safari** | 14.1+ | ✅ iOS 14.5+, webm support added |
| **Edge** | 79+ | ✅ Chromium-based, same as Chrome |
| **Opera** | 36+ | ✅ Chromium-based |

### Feature Detection

```javascript
// Check MediaRecorder support
if (!navigator.mediaDevices || !window.MediaRecorder) {
    console.warn('Voice recording not supported');
    document.getElementById('voice-btn').style.display = 'none';
}

// Check specific codec support
if (MediaRecorder.isTypeSupported('audio/webm')) {
    console.log('WebM supported');
} else if (MediaRecorder.isTypeSupported('audio/ogg')) {
    console.log('OGG supported');
}
```

### Graceful Degradation

```javascript
function initVoiceSearch() {
    if (!isVoiceSupported()) {
        // Hide voice button
        document.getElementById('voice-btn').style.display = 'none';
        
        // Show informational message
        console.log('Voice search not available in this browser');
        return;
    }
    
    // Initialize voice functionality
    setupVoiceRecording();
}

function isVoiceSupported() {
    return !!(
        navigator.mediaDevices &&
        navigator.mediaDevices.getUserMedia &&
        window.MediaRecorder
    );
}
```

---

## ⚡ Performance Optimization

### Frontend Optimizations

**1. Audio Compression**
```javascript
// Use lower bitrate for smaller files (speech doesn't need high quality)
const mediaRecorder = new MediaRecorder(stream, {
    mimeType: 'audio/webm;codecs=opus',
    audioBitsPerSecond: 16000  // 16kbps sufficient for voice
});
```

**2. Debounce Recording Button**
```javascript
let isProcessing = false;

voiceBtn.addEventListener('click', async () => {
    if (isProcessing) {
        console.log('Already processing, please wait');
        return;
    }
    
    isProcessing = true;
    try {
        await handleVoiceRecording();
    } finally {
        isProcessing = false;
    }
});
```

**3. Audio Preloading**
```javascript
// Preload TTS audio for faster playback
if (data.audio_url) {
    const audio = new Audio();
    audio.preload = 'auto';
    audio.src = data.audio_url;
    
    // Play when ready
    audio.addEventListener('canplaythrough', () => {
        audio.play();
    });
}
```

### Backend Optimizations

**1. Stream Processing**
```python
# Don't load entire audio file into memory
async def transcribe_audio_stream(audio_path: str):
    with open(audio_path, 'rb') as audio_file:
        # Process in chunks
        return await asr_model.transcribe_stream(audio_file)
```

**2. Response Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_tts(text: str, language: str):
    """Cache common TTS responses"""
    return tts_provider.generate_speech(text, language)
```

**3. Async Campaign Search**
```python
import asyncio

async def voice_search_campaigns(...):
    # Run transcription and DB query in parallel
    async with asyncio.TaskGroup() as tg:
        transcription_task = tg.create_task(transcribe_audio(audio_path))
        
    transcription = transcription_task.result()
    
    # Then search campaigns
    campaigns = await search_campaigns(transcription)
```

---

## 🧪 Testing Guide

### Manual Testing Checklist

**Recording:**
- [ ] Microphone permission requested on first use
- [ ] Button shows recording state (red, pulsing)
- [ ] Stop button appears while recording
- [ ] Can cancel recording
- [ ] Recording duration reasonable (5-30 seconds)

**Processing:**
- [ ] Loading indicator shown
- [ ] Transcription displayed correctly
- [ ] Response text appears
- [ ] Audio plays automatically
- [ ] Search results update

**Error Handling:**
- [ ] Graceful handling of permission denial
- [ ] Network error message shown
- [ ] Retry option available
- [ ] No JavaScript errors in console

### Browser Console Testing

```javascript
// Test MediaRecorder availability
console.log('MediaRecorder:', typeof MediaRecorder !== 'undefined');

// Test getUserMedia
navigator.mediaDevices.getUserMedia({ audio: true })
    .then(() => console.log('✅ Microphone access OK'))
    .catch(err => console.error('❌ Microphone error:', err));

// Test permissions API
navigator.permissions.query({ name: 'microphone' })
    .then(result => console.log('Mic permission:', result.state));

// Test audio playback
const audio = new Audio('https://example.com/test.mp3');
audio.play()
    .then(() => console.log('✅ Audio playback OK'))
    .catch(err => console.error('❌ Audio error:', err));
```

### Backend Testing with curl

```bash
# Record a test audio file
ffmpeg -f avfoundation -i ":0" -t 5 test_voice.webm

# Test the endpoint
curl -X POST https://your-api.com/api/voice/search-campaigns \
  -F "audio=@test_voice.webm" \
  -F "user_id=123456789" \
  | jq .

# Expected response structure
{
  "transcription": "...",
  "response_text": "...",
  "has_audio": true,
  "audio_url": "...",
  "campaigns": [...]
}
```

---

## 🎯 Best Practices

### Do's ✅

1. **Always request microphone permission explicitly**
   - Show purpose before requesting
   - Handle denial gracefully
   - Provide alternative (text search)

2. **Provide clear visual feedback**
   - Recording indicator (pulsing red)
   - Processing state
   - Transcription display

3. **Clean up resources**
   - Stop microphone stream after recording
   - Delete temp files on backend
   - Cancel pending requests on unmount

4. **Optimize audio quality vs size**
   - 16kbps is sufficient for speech
   - Use webm/opus for best compression
   - Limit recording duration (30 seconds max)

5. **Handle errors gracefully**
   - Show user-friendly messages
   - Log technical details for debugging
   - Provide retry mechanism

### Don'ts ❌

1. **Don't assume microphone access**
   - Always feature-detect MediaRecorder
   - Provide text fallback

2. **Don't keep microphone active unnecessarily**
   - Stop stream immediately after recording
   - Release permissions when done

3. **Don't ignore network conditions**
   - Show upload progress for large files
   - Handle timeout errors
   - Consider offline state

4. **Don't play audio without user interaction**
   - Browser autoplay policies may block
   - Provide manual play button fallback

5. **Don't store sensitive audio**
   - Delete temp files immediately
   - Don't log audio content
   - Respect user privacy

---

## 📚 Related Documentation

- **LAB_07_MINIAPPS_SETUP.md**: Mini app setup and navigation
- **LAB_07B_VOICE_INTEGRATION.md**: Extending voice to all mini apps
- **LAB_08_MULTI_TURN_CONVERSATIONS.md**: Bot voice message handling
- **voice/asr/README.md**: ASR pipeline documentation
- **voice/tts/README.md**: TTS pipeline documentation

---

## 🔗 External Resources

- [MDN: MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [MDN: getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

---

**Document Complete** | For Voice Ledger and TrustVoice reference
