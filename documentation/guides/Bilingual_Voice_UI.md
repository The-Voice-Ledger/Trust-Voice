# Voice Ledger - Lab 17: Bilingual Web Voice UI & Admin Dashboard

**Date:** December 24, 2025  
**Version:** v1.0  
**Status:** 📝 PLANNED (Documentation Complete - To be built)  

---

## 🎯 Lab Overview

**Learning Objectives:**
- Build a bilingual web voice interface supporting Amharic and English
- Implement database-driven language preference system (no auto-detection)
- Integrate AddisAI for Amharic STT/TTS and OpenAI for English
- Create admin dashboard for registration approval and marketplace monitoring
- Design mobile-responsive UI with elegant blue and white theme
- Understand cross-platform language consistency (Telegram + Web)
- Implement JWT-based authentication for web access

**What You'll Build:**
- ✅ User profile API with language preference management
- ✅ Bilingual voice processing endpoint with automatic provider routing
- ✅ AddisAI provider client for Amharic (STT + TTS)
- ✅ OpenAI provider client for English (Whisper + TTS)
- ✅ BilingualVoiceController JavaScript class
- ✅ Mobile-responsive voice UI with microphone and audio playback
- ✅ Admin dashboard for registration management and analytics
- ✅ PIN-based web authentication with JWT tokens

**Prerequisites:**
- ✅ Labs 1-16 completed (full Voice Ledger system operational)
- ✅ Language preference system from registration (`user_identities.preferred_language`)
- ✅ Telegram bot with voice commands working
- ✅ AddisAI API key (Amharic support)
- ✅ OpenAI API key (English support)
- ✅ Basic JavaScript and HTML/CSS knowledge
- ✅ Understanding of JWT authentication
- ✅ Familiarity with FastAPI static file serving

**Time Estimate:** 7-10 days (Admin Dashboard 3-5 days, Voice UI 4-6 days, can be built in parallel)

**Cost:** ~$132/month for 1000 users @ 10 minutes/month (Amharic: $105, English: $27)

**Real-World Impact:**
- ✅ Serve international buyers who don't use Telegram (English UI)
- ✅ Provide Ethiopian farmers with native Amharic interface
- ✅ Enable admins to approve registrations from web dashboard
- ✅ Reduce dependency on single channel (Telegram)
- ✅ Improve accessibility for users preferring web over mobile apps

---

## 💡 Background: Why Bilingual Web Voice UI?

### The Problem

**Current System (Labs 1-16):**
```
✅ Telegram bot with voice commands (working)
✅ Bilingual ASR (OpenAI Whisper for English, local model for Amharic)
✅ User language preference stored in database
✅ Complete marketplace backend (RFQ, offers, fractional ownership)
❌ No web interface (Telegram-only)
❌ No voice responses (text-only replies)
❌ No admin web dashboard
❌ International buyers hesitant to use Telegram
```

**Key Challenges:**
1. **Single-Channel Risk**: Telegram outage = system unusable
2. **Limited Reach**: Not all Ethiopian farmers use Telegram
3. **No Admin Tools**: Registration approval requires database access
4. **No Voice Responses**: Current system is STT-only (text replies)
5. **No English Voice**: International buyers need English TTS

### The Solution: Bilingual Web Voice UI

**New Architecture**:

```
User Registration → Selects Language (🇺🇸 English / 🇪🇹 Amharic)
         ↓
Database: user_identities.preferred_language = 'en' or 'am'
         ↓
ALL interfaces respect this preference:
- Telegram Bot
- Web Voice UI
- Mobile App (future)
```

**Key Principles:**
- ✅ Single source of truth: Database
- ✅ User control: Can change anytime
- ✅ Cross-platform consistency
- ✅ No auto-detection errors
- ✅ Cost-optimized provider routing

### System Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    USER REGISTRATION                     │
│  User selects: 🇺🇸 English or 🇪🇹 Amharic               │
│        ↓                                                 │
│  Database: user_identities.preferred_language = 'en'/'am'│
└──────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌─────────────────┐           ┌─────────────────┐
│  TELEGRAM BOT   │           │   WEB VOICE UI  │
│                 │           │                 │
│ Reads DB lang   │           │ Reads DB lang   │
│ Routes to:      │           │ Routes to:      │
│ - AddisAI (am)  │           │ - AddisAI (am)  │
│ - OpenAI (en)   │           │ - OpenAI (en)   │
└─────────────────┘           └─────────────────┘
        ↓                               ↓
        └───────────────┬───────────────┘
                        ↓
        ┌───────────────────────────────┐
        │   VOICE LEDGER BACKEND API    │
        │                               │
        │ • GET /api/users/{id}/profile │
        │ • PATCH /api/users/{id}/lang  │
        │ • POST /api/voice/process     │
        │                               │
        │   Routes to:                  │
        │   - AddisAI STT/TTS (if 'am') │
        │   - OpenAI STT/TTS (if 'en')  │
        └───────────────────────────────┘
```

---

## Track 1: Admin Dashboard

### Features

1. **Authentication**
   - PIN-based login (no passwords)
   - JWT token with 7-day expiry
   - Role-based access control (ADMIN only)

2. **Registration Management**
   - View pending registrations
   - Approve/reject with comments
   - Assign organizations
   - Bulk actions

3. **User Management**
   - Search and filter by role
   - View user profiles
   - Update language preferences
   - Deactivate accounts

4. **Marketplace Monitoring**
   - Active RFQs dashboard
   - Offer submissions
   - Acceptance tracking
   - Payment coordination status

5. **Analytics**
   - Transaction volumes
   - User growth charts
   - Batch processing metrics
   - Settlement tracking

6. **Settlement Tracking**
   - Payment coordination
   - Delivery confirmation
   - Dispute resolution

### Tech Stack

- **Frontend:** Next.js or Vanilla JavaScript (TBD)
- **Styling:** Blue and white theme (elegant, simple, glossy)
- **Auth:** JWT tokens, localStorage
- **Charts:** Chart.js or lightweight alternative
- **Mobile:** Responsive design (mobile-first)

### API Endpoints

```python
# Authentication
POST   /api/auth/login                # PIN → JWT
GET    /api/auth/me                   # Current user
POST   /api/auth/logout               # Invalidate token

# Admin: Registration Management
GET    /admin/registrations?status=PENDING
POST   /admin/registrations/{id}/approve
POST   /admin/registrations/{id}/reject
PATCH  /admin/registrations/{id}/organization

# Admin: User Management
GET    /admin/users?role=BUYER&search=coffee
GET    /admin/users/{id}
PATCH  /admin/users/{id}
DELETE /admin/users/{id}

# Admin: Marketplace Monitoring
GET    /admin/rfqs?status=ACTIVE
GET    /admin/offers?rfq_id={id}
GET    /admin/settlements?status=PENDING

# Admin: Analytics
GET    /admin/analytics/transactions
GET    /admin/analytics/users
GET    /admin/analytics/batches
```

---

## Track 2: Bilingual Realtime Voice UI

### Features

1. **Voice Recording**
   - Tap-to-speak microphone button
   - Real-time audio visualization (waveform or level meter)
   - Status indicator: Idle / Listening / Processing / Speaking

2. **Bilingual STT/TTS**
   - **Amharic:** AddisAI STT + TTS (300-800ms latency)
   - **English:** OpenAI Whisper + TTS (2-5s latency)
   - Automatic routing based on user's `preferred_language`

3. **Language Switcher**
   - UI toggle: 🇺🇸 English / 🇪🇹 Amharic
   - Updates database on change
   - Syncs across all sessions

4. **Conversation Transcript**
   - User messages (left, blue)
   - Assistant responses (right, white)
   - Timestamps
   - Scroll history

5. **Command Integration**
   - Voice commands parsed by Voice Ledger backend
   - Display extracted entities (quantity, location, etc.)
   - Visual confirmation before executing
   - Error handling with retry

6. **Mobile Optimization**
   - Touch-friendly buttons
   - Responsive layout
   - Works on iOS Safari and Android Chrome
   - Offline detection

### Provider Comparison

| Feature | AddisAI (Amharic) | OpenAI (English) |
|---------|-------------------|------------------|
| **STT Endpoint** | `/api/v2/stt` | Whisper API |
| **TTS Endpoint** | `/api/v1/audio/speech` | TTS API (`tts-1`) |
| **Latency** | 300-800ms | 2-5s |
| **Languages** | Amharic, Afan Oromo | 97+ languages |
| **STT Cost** | TBD | $0.006/min |
| **TTS Cost** | TBD | $15/1M characters |
| **Quality** | Optimized for Ethiopian dialect | Excellent English |
| **Voices** | Gender options | 6 voices (alloy, echo, fable, onyx, nova, shimmer) |

### Tech Stack

- **Frontend:** Vanilla JavaScript (no build tools)
- **Styling:** CSS3 with blue/white theme
- **Audio:** Web Audio API, MediaRecorder API
- **API Calls:** Fetch API with JWT auth
- **Mobile:** Progressive Web App (PWA) ready

### Frontend Structure

```
frontend/
├── index.html              # Landing page
├── login.html              # PIN-based login
├── admin-dashboard.html    # Admin interface
├── voice-ui.html           # Bilingual voice interface
├── marketplace.html        # RFQ marketplace
├── batches.html            # Batch management
├── profile.html            # User profile & settings
│
├── css/
│   ├── style.css           # Global styles (blue & white theme)
│   ├── auth.css            # Login/register
│   ├── dashboard.css       # Dashboard layout
│   ├── voice.css           # Voice UI styles
│   └── theme.css           # Color scheme variables
│
└── js/
    ├── auth.js             # Authentication logic
    ├── voice-controller.js # Main voice orchestration
    ├── providers/
    │   ├── addis-ai.js     # AddisAI client (Amharic)
    │   ├── openai.js       # OpenAI client (English)
    │   └── base.js         # Base provider interface
    ├── language-manager.js # Language preference management
    ├── command-parser.js   # Parse voice commands
    ├── voice-ledger-api.js # Backend API integration
    ├── admin-dashboard.js  # Admin UI logic
    ├── rfq-ui.js           # RFQ management
    ├── batch-ui.js         # Batch listing/details
    └── utils.js            # Helper functions
```

### API Endpoints

```python
# User Profile & Language
GET    /api/users/{user_id}/profile      # Get profile + language
PATCH  /api/users/{user_id}/language     # Update language preference

# Voice Processing (with automatic routing)
POST   /api/voice/process                # STT → Command → TTS
POST   /api/voice/transcribe              # STT only (testing)
POST   /api/voice/synthesize              # TTS only (testing)

# Provider Proxies (hide API keys)
POST   /api/openai/transcribe             # OpenAI Whisper proxy
POST   /api/openai/tts                    # OpenAI TTS proxy
POST   /api/addisai/transcribe            # AddisAI STT proxy
POST   /api/addisai/tts                   # AddisAI TTS proxy
```

---

## Implementation Guide

### Step 1: Backend - User Profile & Language Management

Create `voice/web/user_api.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import UserIdentity
from datetime import datetime

router = APIRouter()

@router.get("/api/users/{user_id}/profile")
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user profile including language preference."""
    user = db.query(UserIdentity).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    return {
        "id": user.id,
        "name": f"{user.telegram_first_name} {user.telegram_last_name}",
        "role": user.role,
        "preferred_language": user.preferred_language,  # 'en' or 'am'
        "organization": user.organization.name if user.organization else None,
        "phone_number": user.phone_number,
        "is_approved": user.is_approved
    }

@router.patch("/api/users/{user_id}/language")
async def update_user_language(
    user_id: int,
    body: dict,
    db: Session = Depends(get_db)
):
    """Update user's preferred language (syncs across all interfaces)."""
    user = db.query(UserIdentity).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    new_lang = body.get('preferred_language')
    if new_lang not in ['en', 'am']:
        raise HTTPException(400, "Invalid language. Must be 'en' or 'am'")
    
    user.preferred_language = new_lang
    user.language_set_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"User {user_id} changed language to {new_lang}")
    
    return {"success": True, "preferred_language": new_lang}
```

Register router in `voice/service/api.py`:

```python
from voice.web.user_api import router as user_router

app.include_router(user_router)
print("✅ User profile endpoints registered at /api/users/*")
```

### Step 2: Backend - Bilingual Voice Processing

Create `voice/web/voice_api.py`:

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import UserIdentity
from voice.providers.addis_ai import AddisAIProvider
from voice.providers.openai_voice import OpenAIProvider

router = APIRouter()
addis_ai = AddisAIProvider()
openai_provider = OpenAIProvider()

@router.post("/api/voice/process")
async def process_voice_command(
    audio: UploadFile = File(...),
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Process voice command with automatic provider routing based on user's language.
    
    Flow:
    1. Get user's preferred language from database
    2. Route to appropriate STT provider (AddisAI or OpenAI)
    3. Process command with Voice Ledger backend
    4. Generate response text in user's language
    5. Route to appropriate TTS provider
    6. Return transcript, response text, and audio URL
    """
    # 1. Get user's preferred language
    user = db.query(UserIdentity).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    preferred_lang = user.preferred_language  # 'en' or 'am'
    
    # 2. Transcribe audio using appropriate provider
    audio_bytes = await audio.read()
    
    if preferred_lang == 'am':
        transcript = await addis_ai.transcribe(audio_bytes)
    else:
        transcript = await openai_provider.transcribe(audio_bytes)
    
    # 3. Process command with Voice Ledger backend
    from voice.command_integration import execute_voice_command
    result = await execute_voice_command(transcript, user_id, preferred_lang)
    
    # 4. Generate response text
    response_text = generate_response(result, preferred_lang)
    
    # 5. Synthesize speech using appropriate provider
    if preferred_lang == 'am':
        audio_url = await addis_ai.text_to_speech(response_text)
    else:
        audio_url = await openai_provider.text_to_speech(response_text)
    
    return {
        "transcript": transcript,
        "response_text": response_text,
        "audio_url": audio_url,
        "language": preferred_lang,
        "command_result": result
    }

def generate_response(result: dict, language: str) -> str:
    """Generate response text in user's language."""
    if result.get('success'):
        if language == 'am':
            return f"✅ {result['message_am']}"
        else:
            return f"✅ {result['message']}"
    else:
        if language == 'am':
            return f"❌ ስህተት: {result.get('error_am', result.get('error'))}"
        else:
            return f"❌ Error: {result.get('error')}"
```

### Step 3: Backend - Provider Implementations

Create `voice/providers/addis_ai.py`:

```python
import os
import aiohttp
from typing import Dict, Any

class AddisAIProvider:
    def __init__(self):
        self.api_key = os.getenv('ADDIS_AI_API_KEY')
        self.base_url = 'https://api.addisassistant.com'
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio using AddisAI STT."""
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('audio', audio_bytes, filename='audio.wav')
            form_data.add_field('request_data', '{"language_code": "am"}')
            
            async with session.post(
                f'{self.base_url}/api/v2/stt',
                headers={'x-api-key': self.api_key},
                data=form_data
            ) as response:
                data = await response.json()
                return data['transcription']
    
    async def text_to_speech(self, text: str) -> str:
        """Convert text to speech using AddisAI TTS."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/v1/audio/speech',
                headers={
                    'x-api-key': self.api_key,
                    'Content-Type': 'application/json'
                },
                json={'text': text, 'language': 'am'}
            ) as response:
                # Save audio to temp file and return URL
                audio_bytes = await response.read()
                # TODO: Upload to S3 or serve from /tmp
                audio_path = f'/tmp/tts_{hash(text)}.mp3'
                with open(audio_path, 'wb') as f:
                    f.write(audio_bytes)
                return f'/audio/{os.path.basename(audio_path)}'
```

Create `voice/providers/openai_voice.py`:

```python
import os
import openai
from typing import Dict, Any

class OpenAIProvider:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio using OpenAI Whisper."""
        with open('/tmp/temp_audio.wav', 'wb') as f:
            f.write(audio_bytes)
        
        with open('/tmp/temp_audio.wav', 'rb') as audio_file:
            transcript = openai.Audio.transcribe('whisper-1', audio_file)
        
        return transcript['text']
    
    async def text_to_speech(self, text: str, voice: str = 'alloy') -> str:
        """Convert text to speech using OpenAI TTS."""
        response = openai.Audio.speech.create(
            model='tts-1',
            voice=voice,
            input=text
        )
        
        # Save audio to temp file and return URL
        audio_path = f'/tmp/tts_{hash(text)}.mp3'
        response.stream_to_file(audio_path)
        return f'/audio/{os.path.basename(audio_path)}'
```

### Step 4: Frontend - Voice Controller

Create `frontend/js/voice-controller.js`:

```javascript
class BilingualVoiceController {
  constructor(userId) {
    this.userId = userId;
    this.addisAI = new AddisAIProvider();
    this.openAI = new OpenAIProvider();
    this.currentLanguage = null;
    this.audioRecorder = new AudioRecorder();
    this.isRecording = false;
  }
  
  async initialize() {
    // Fetch user's language preference from database
    const response = await fetch(`/api/users/${this.userId}/profile`, {
      headers: {'Authorization': `Bearer ${this.getAuthToken()}`}
    });
    const profile = await response.json();
    
    this.currentLanguage = profile.preferred_language; // 'en' or 'am'
    this.updateLanguageUI(this.currentLanguage);
  }
  
  async startRecording() {
    if (this.isRecording) return;
    
    this.isRecording = true;
    this.updateStatus('listening');
    await this.audioRecorder.start();
  }
  
  async stopRecording() {
    if (!this.isRecording) return;
    
    this.isRecording = false;
    this.updateStatus('processing');
    
    const audioBlob = await this.audioRecorder.stop();
    await this.processVoice(audioBlob);
    
    this.updateStatus('idle');
  }
  
  async processVoice(audioBlob) {
    try {
      // Send to backend with automatic routing
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('user_id', this.userId);
      
      const response = await fetch('/api/voice/process', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${this.getAuthToken()}`},
        body: formData
      });
      
      const result = await response.json();
      
      // Display transcript
      this.addMessage('user', result.transcript);
      
      // Display response
      this.addMessage('assistant', result.response_text);
      
      // Play audio response
      this.updateStatus('speaking');
      await this.playAudio(result.audio_url);
      this.updateStatus('idle');
      
      return result;
    } catch (error) {
      console.error('Voice processing error:', error);
      this.addMessage('error', 'Sorry, there was an error processing your request.');
      this.updateStatus('idle');
    }
  }
  
  async changeLanguage(newLang) {
    if (this.currentLanguage === newLang) return;
    
    // Update UI immediately
    this.currentLanguage = newLang;
    this.updateLanguageUI(newLang);
    
    // Persist to database
    await fetch(`/api/users/${this.userId}/language`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${this.getAuthToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({preferred_language: newLang})
    });
    
    // Show confirmation
    const message = newLang === 'am' 
      ? 'ቋንቋ ወደ አማርኛ ተቀይሯል' 
      : 'Language changed to English';
    this.addMessage('system', message);
  }
  
  updateLanguageUI(lang) {
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
  }
  
  updateStatus(status) {
    const statusEl = document.getElementById('voice-status');
    statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusEl.className = `status status-${status}`;
  }
  
  addMessage(role, text) {
    const transcript = document.getElementById('conversation-transcript');
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${role}`;
    messageEl.textContent = text;
    transcript.appendChild(messageEl);
    transcript.scrollTop = transcript.scrollHeight;
  }
  
  async playAudio(url) {
    return new Promise((resolve, reject) => {
      const audio = new Audio(url);
      audio.onended = resolve;
      audio.onerror = reject;
      audio.play();
    });
  }
  
  getAuthToken() {
    return localStorage.getItem('auth_token');
  }
}

class AudioRecorder {
  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({audio: true});
    this.mediaRecorder = new MediaRecorder(this.stream);
    this.chunks = [];
    
    this.mediaRecorder.ondataavailable = (e) => this.chunks.push(e.data);
    this.mediaRecorder.start();
  }
  
  async stop() {
    return new Promise((resolve) => {
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, {type: 'audio/wav'});
        this.stream.getTracks().forEach(t => t.stop());
        resolve(blob);
      };
      this.mediaRecorder.stop();
    });
  }
}
```

### Step 5: Frontend - Voice UI HTML

Create `frontend/voice-ui.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Voice Ledger - Voice Interface</title>
  <link rel="stylesheet" href="css/style.css">
  <link rel="stylesheet" href="css/voice.css">
</head>
<body>
  <div class="container">
    <header>
      <h1>Voice Ledger</h1>
      <div class="language-selector">
        <button class="lang-btn" data-lang="en" id="btn-en">
          🇺🇸 English
        </button>
        <button class="lang-btn active" data-lang="am" id="btn-am">
          🇪🇹 አማርኛ
        </button>
      </div>
    </header>
    
    <main>
      <div class="voice-controls">
        <div id="voice-status" class="status status-idle">Idle</div>
        
        <button id="mic-button" class="mic-button">
          <svg class="mic-icon" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </button>
        
        <div id="audio-visualizer" class="audio-visualizer">
          <canvas id="waveform"></canvas>
        </div>
      </div>
      
      <div id="conversation-transcript" class="conversation-transcript">
        <!-- Messages appear here -->
      </div>
    </main>
  </div>
  
  <script src="js/auth.js"></script>
  <script src="js/voice-controller.js"></script>
  <script>
    // Initialize voice controller
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
      window.location.href = '/login.html';
    }
    
    const userId = JSON.parse(localStorage.getItem('user_profile')).id;
    const voiceController = new BilingualVoiceController(userId);
    
    // Initialize on load
    voiceController.initialize();
    
    // Mic button - tap to toggle recording
    const micButton = document.getElementById('mic-button');
    let isRecording = false;
    
    micButton.addEventListener('click', async () => {
      if (isRecording) {
        await voiceController.stopRecording();
        micButton.classList.remove('recording');
        isRecording = false;
      } else {
        await voiceController.startRecording();
        micButton.classList.add('recording');
        isRecording = true;
      }
    });
    
    // Language switcher
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        voiceController.changeLanguage(btn.dataset.lang);
      });
    });
  </script>
</body>
</html>
```

---

## Testing

### Test Bilingual Voice Flow

**English Test:**
1. Login as English-preferred user
2. Tap microphone
3. Say: "Show me my coffee inventory"
4. Verify: OpenAI Whisper transcribes correctly
5. Verify: Response speaks in English (OpenAI TTS)

**Amharic Test:**
1. Login as Amharic-preferred user (or switch language)
2. Tap microphone
3. Say: "የእኔን የቡና ክምችት አሳየኝ"
4. Verify: AddisAI transcribes correctly
5. Verify: Response speaks in Amharic (AddisAI TTS)

**Language Switching:**
1. Click language switcher (🇺🇸 → 🇪🇹)
2. Verify UI updates
3. Verify database updated (`preferred_language = 'am'`)
4. Test voice command in new language
5. Verify provider switched

**Cross-Platform Consistency:**
1. Use voice UI (web) in Amharic
2. Open Telegram bot
3. Send voice message
4. Verify Telegram also uses Amharic

### Test Admin Dashboard

1. Login as ADMIN role
2. View pending registrations
3. Approve a registration
4. View RFQ marketplace
5. Check analytics charts
6. Test on mobile device

---

## Deployment

### Environment Variables

Add to `.env`:

```bash
# AddisAI API Key
ADDIS_AI_API_KEY=your_addisai_api_key_here

# OpenAI API Key (already exists)
OPENAI_API_KEY=your_openai_api_key_here

# JWT Secret for web auth
JWT_SECRET_KEY=your_random_secret_key_here

# Base URL for audio files
BASE_URL=https://your-domain.com
```

### Serve Frontend

Update `voice/service/api.py`:

```python
from fastapi.staticfiles import StaticFiles

# Serve frontend static files
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/audio", StaticFiles(directory="/tmp"), name="audio")  # Temp audio files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

### HTTPS Required

Microphone access requires HTTPS. Use:
- ngrok (development): `ngrok http 8000`
- Cloudflare Tunnel (production)
- Let's Encrypt certificate

---

## Success Criteria

- [ ] Users can login with PIN
- [ ] Language preference loads from database
- [ ] Voice recording works on mobile browsers
- [ ] Amharic commands use AddisAI (STT + TTS)
- [ ] English commands use OpenAI (STT + TTS)
- [ ] Language switching persists to database
- [ ] Admin can approve registrations
- [ ] Conversation transcript displays correctly
- [ ] Audio playback works
- [ ] Cross-platform language consistency (Telegram + Web)

---

## Cost Estimates

**AddisAI (Amharic):**
- STT: TBD (check pricing page)
- TTS: TBD (check pricing page)
- Estimated: ~$0.01-0.02/minute total

**OpenAI (English):**
- STT: $0.006/minute (Whisper)
- TTS: $15/1M characters ≈ $0.003/minute (assuming 150 words/min)
- Total: ~$0.009/minute

**Storage:**
- Audio files: S3 or local /tmp (negligible cost)

**For 1000 users @ 10 minutes/month:**
- Amharic (70%): 7000 min × $0.015 = $105/month
- English (30%): 3000 min × $0.009 = $27/month
- **Total: ~$132/month**

---

## Next Steps

1. ✅ Document bilingual architecture (this lab)
2. 🔜 Implement backend API endpoints
3. 🔜 Implement provider abstraction layer
4. 🔜 Build frontend voice UI
5. 🔜 Build admin dashboard
6. 🔜 Test on mobile devices
7. 🔜 Deploy to production

---

**Lab Status:** 📝 Documented (December 24, 2025)  
**Prerequisites:** Labs 1-16 complete  
**Blocked By:** None  
**Blocks:** None (parallel development tracks)
