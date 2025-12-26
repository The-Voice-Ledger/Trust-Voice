# Voice Interface Implementation Plan (v2.0)

## Current Status

**Date:** December 24, 2025  
**Version:** v1.8 (Backend Complete, Planning Bilingual Web UI)  
**Next Milestone:** v2.0 (Bilingual Web Voice Interface + Admin Dashboard)

### What's Already Working
- ✅ FastAPI installed and configured (`fastapi==0.104.1`)
- ✅ OpenAI client installed with Whisper API access (`openai==1.12.0`)
- ✅ Database layer complete (Neon PostgreSQL)
- ✅ EPCIS event generation working
- ✅ Blockchain anchoring working (Base Sepolia)
- ✅ IPFS storage working (Pinata)
- ✅ DPP generation working
- ✅ SSI (DIDs/VCs) working
- ✅ Telegram bot with voice commands working
- ✅ RFQ marketplace complete (Labs 12-15)
- ✅ Fractional ownership API working
- ✅ User language preference system (database: `user_identities.preferred_language`)
- ✅ Bilingual ASR: OpenAI Whisper (English) + Local Amharic model

### What's Missing
- ❌ Web UI for voice interactions
- ❌ AddisAI integration for Amharic TTS
- ❌ OpenAI TTS for English audio responses
- ❌ Admin dashboard for registration management
- ❌ JWT-based web authentication
- ❌ Mobile-responsive voice interface

---

## Phase 1: Minimal Voice API (1-2 Days)

**Goal:** Enable farmers to upload audio files and get EPCIS events created

### Step 1.1: Install Missing Dependencies

```bash
cd /Users/manu/Voice-Ledger
source venv/bin/activate

# Core audio processing (REQUIRED)
pip install pydub==0.25.1
pip install soundfile==0.12.1
pip install aiofiles==23.2.1

# System dependency
brew install ffmpeg

# Update requirements.txt
echo "" >> requirements.txt
echo "# -----------------------------" >> requirements.txt
echo "# Voice Interface (v1.5)" >> requirements.txt
echo "# -----------------------------" >> requirements.txt
echo "pydub==0.25.1" >> requirements.txt
echo "soundfile==0.12.1" >> requirements.txt
echo "aiofiles==23.2.1" >> requirements.txt
```

### Step 1.2: Review Existing Voice Modules

**Files that already exist:**
- `voice/asr/asr_infer.py` - Whisper ASR integration (complete)
- `voice/nlu/nlu_infer.py` - GPT NLU parser (complete)
- `voice/service/api.py` - FastAPI skeleton (needs completion)
- `voice/service/auth.py` - Authentication (needs completion)

**Action:** Read these files and understand current implementation state

```bash
# Check what's in the voice API
cat voice/service/api.py
cat voice/asr/asr_infer.py
cat voice/nlu/nlu_infer.py
```

### Step 1.3: Complete Voice API Endpoints

**File:** `voice/service/api.py`

**Add these endpoints:**

#### Endpoint 1: Upload Audio File
```python
@app.post("/voice/upload")
async def upload_audio(
    audio: UploadFile = File(...),
    farmer_id: str = Form(...)
):
    """
    Upload audio file, transcribe, parse, create EPCIS event.
    
    Steps:
    1. Save uploaded file to /tmp
    2. Call asr_infer.run_asr(file_path)
    3. Call nlu_infer.extract_event_data(transcript)
    4. Create batch + EPCIS event (use existing code)
    5. Return batch_id, event_id, transcript
    """
    pass
```

#### Endpoint 2: Health Check
```python
@app.get("/voice/health")
async def health_check():
    """Check if ASR and NLU services are available."""
    return {
        "status": "operational",
        "whisper_api": "connected",
        "database": "connected"
    }
```

#### Endpoint 3: Get Transcription Only (Testing)
```python
@app.post("/voice/transcribe")
async def transcribe_only(audio: UploadFile = File(...)):
    """Test endpoint - transcribe audio without creating events."""
    pass
```

### Step 1.4: Integrate with Existing Backend

**Connect to existing modules:**

```python
# In voice/service/api.py
from database import get_db, create_farmer, create_batch, create_event
from epcis.epcis_event import create_commissioning_event
from voice.asr.asr_infer import run_asr
from voice.nlu.nlu_infer import extract_event_data
from ipfs.ipfs_storage import pin_epcis_event
```

**Create full pipeline function:**

```python
async def process_voice_event(audio_file_path: str, farmer_id: str):
    """
    Complete pipeline: Audio → Transcript → Event → Blockchain
    
    Returns:
        {
            "transcript": str,
            "parsed_data": dict,
            "batch_id": str,
            "event_id": int,
            "blockchain_tx": str,
            "ipfs_cid": str
        }
    """
    # 1. ASR (2-5 seconds)
    transcript = run_asr(audio_file_path)
    
    # 2. NLU (1-2 seconds)
    event_data = extract_event_data(transcript)
    
    # 3. Create batch in database
    with get_db() as db:
        batch = create_batch(db, {
            'farmer_id': farmer_id,
            'quantity_kg': event_data['quantity'] * 60,  # bags to kg
            'batch_id': f"BATCH-VOICE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
        
        # 4. Create EPCIS event
        epcis_event = create_commissioning_event(batch)
        
        # 5. Store event (auto-pins to IPFS)
        stored_event = create_event(db, epcis_event, pin_to_ipfs=True)
        
        # 6. Anchor to blockchain (if Anvil running)
        from blockchain.anchor import anchor_event_hash
        tx_hash = anchor_event_hash(
            stored_event.event_hash,
            stored_event.event_type,
            stored_event.ipfs_cid
        )
    
    return {
        "transcript": transcript,
        "parsed_data": event_data,
        "batch_id": batch.batch_id,
        "event_id": stored_event.id,
        "blockchain_tx": tx_hash,
        "ipfs_cid": stored_event.ipfs_cid
    }
```

### Step 1.5: Create Test Audio Files

```bash
# Create test samples directory
mkdir -p tests/audio_samples

# Record test audio or use text-to-speech
# Example test phrases:
# - "I harvested 50 bags of washed coffee from my farm"
# - "Delivering 30 bags to Guzo cooperative warehouse"
# - "I processed 20 bags using wet processing method"
```

**Test script:**

```python
# tests/test_voice_api.py
import requests

def test_voice_upload():
    url = "http://localhost:8000/voice/upload"
    
    with open("tests/audio_samples/harvest_50bags.wav", "rb") as audio:
        files = {"audio": audio}
        data = {"farmer_id": "FARMER-001"}
        
        response = requests.post(url, files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        print("Transcript:", result['transcript'])
        print("Batch ID:", result['batch_id'])
        print("Event ID:", result['event_id'])
        print("Blockchain TX:", result['blockchain_tx'])
```

---

## Phase 0: Bilingual Voice Architecture (NEW - December 2025)

**Goal:** Establish language routing strategy for web voice UI

### Language Preference System

Voice Ledger uses a **database-driven language preference** system:

1. User selects language during registration (Telegram `/register`)
2. Preference stored in `user_identities.preferred_language` ('en' or 'am')
3. All voice interactions (Telegram + Web) respect this preference
4. User can change language anytime (persists across all platforms)
5. **No automatic language detection** to prevent errors

### Architecture Diagram

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

### Provider Comparison

| Feature | AddisAI (Amharic) | OpenAI (English) |
|---------|-------------------|------------------|
| **STT** | `/api/v2/stt` | Whisper API |
| **TTS** | `/api/v1/audio/speech` | TTS API (`tts-1`) |
| **Latency** | 300-800ms | 2-5s |
| **Language** | Amharic, Afan Oromo | 97+ languages |
| **Cost** | TBD | $0.006/min (STT), $15/1M chars (TTS) |
| **Quality** | Optimized for Ethiopian dialect | Excellent English |

### Implementation Requirements

**Backend APIs:**
- `GET /api/users/{user_id}/profile` - Get user language preference
- `PATCH /api/users/{user_id}/language` - Update language preference
- `POST /api/voice/process` - Process voice with automatic routing
- `POST /api/openai/transcribe` - OpenAI STT proxy (hides API key)
- `POST /api/openai/tts` - OpenAI TTS proxy
- `POST /api/addisai/transcribe` - AddisAI STT proxy
- `POST /api/addisai/tts` - AddisAI TTS proxy

**Frontend Components:**
- Language switcher UI (🇺🇸 / 🇪🇹)
- Provider abstraction layer (`AddisAIProvider`, `OpenAIProvider`)
- Unified `BilingualVoiceController`
- Microphone recording
- Audio playback
- Conversation transcript

**Key Principles:**
- ✅ Single source of truth: Database stores preferred language
- ✅ Cross-platform consistency: Same language on Telegram and Web
- ✅ User control: Can change language anytime in settings
- ✅ No auto-detection: User explicitly chose their language
- ✅ Cost optimization: Route to appropriate provider per language

---

### Step 1.6: Run the Voice API

```bash
# Terminal 1: Start Anvil (blockchain)
anvil

# Terminal 2: Start Voice API
cd /Users/manu/Voice-Ledger
source venv/bin/activate
uvicorn voice.service.api:app --reload --port 8000

# Terminal 3: Test
curl -X POST http://localhost:8000/voice/upload \
  -F "audio=@tests/audio_samples/test.wav" \
  -F "farmer_id=FARMER-001"
```

---

## Phase 2: Production Enhancements (2-3 Days)

**Goal:** Make it production-ready with async processing, error handling, monitoring

### Step 2.1: Add Task Queue (Celery + Redis)

**Why needed:**
- ASR takes 2-5 seconds - blocks API response
- Multiple concurrent requests will overwhelm server
- Need to return immediately, process in background

**Install:**
```bash
pip install celery==5.3.4
pip install redis==5.0.1
brew install redis
brew services start redis
```

**Create task worker:**

```python
# voice/tasks/celery_app.py
from celery import Celery

app = Celery(
    'voice_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@app.task
def process_voice_event_task(audio_file_path, farmer_id):
    """Background task for voice processing."""
    from voice.service.api import process_voice_event
    return process_voice_event(audio_file_path, farmer_id)
```

**Update API to use async tasks:**

```python
@app.post("/voice/upload")
async def upload_audio(audio: UploadFile, farmer_id: str):
    # Save file
    file_path = f"/tmp/{audio.filename}"
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(await audio.read())
    
    # Queue task (returns immediately)
    task = process_voice_event_task.delay(file_path, farmer_id)
    
    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Your event is being processed. Check status at /voice/status/{task_id}"
    }

@app.get("/voice/status/{task_id}")
async def get_task_status(task_id: str):
    """Check processing status."""
    from voice.tasks.celery_app import app as celery_app
    task = celery_app.AsyncResult(task_id)
    
    if task.ready():
        return {
            "status": "completed",
            "result": task.result
        }
    else:
        return {
            "status": "processing",
            "progress": "Transcribing audio..."
        }
```

**Run workers:**
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery worker
celery -A voice.tasks.celery_app worker --loglevel=info

# Terminal 3: Voice API
uvicorn voice.service.api:app --reload
```

### Step 2.2: Add Error Handling

**Handle common errors:**
- Invalid audio format
- Corrupted audio file
- OpenAI API rate limits
- Whisper API timeout
- NLU parsing failures
- Database connection errors

```python
@app.post("/voice/upload")
async def upload_audio(audio: UploadFile, farmer_id: str):
    try:
        # Validate file format
        if not audio.filename.endswith(('.wav', '.mp3', '.m4a', '.ogg')):
            raise HTTPException(400, "Invalid audio format. Use WAV, MP3, M4A, or OGG")
        
        # Validate file size (max 25MB = Whisper API limit)
        if audio.size > 25 * 1024 * 1024:
            raise HTTPException(400, "Audio file too large (max 25MB)")
        
        # Process...
        
    except FileNotFoundError as e:
        raise HTTPException(404, f"File not found: {str(e)}")
    except openai.RateLimitError:
        raise HTTPException(429, "API rate limit reached. Try again in 60 seconds")
    except Exception as e:
        logger.error(f"Voice processing failed: {str(e)}")
        raise HTTPException(500, "Internal error processing audio")
```

### Step 2.3: Add Monitoring & Logging

```python
import logging
from prometheus_client import Counter, Histogram

# Metrics
voice_requests_total = Counter('voice_requests_total', 'Total voice requests')
voice_asr_duration = Histogram('voice_asr_duration_seconds', 'ASR processing time')
voice_nlu_duration = Histogram('voice_nlu_duration_seconds', 'NLU processing time')

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/voice/upload")
async def upload_audio(audio: UploadFile, farmer_id: str):
    voice_requests_total.inc()
    logger.info(f"Voice upload from farmer {farmer_id}")
    
    # Track ASR time
    with voice_asr_duration.time():
        transcript = run_asr(file_path)
    
    logger.info(f"ASR complete: {transcript[:50]}...")
    
    # Continue...
```

### Step 2.4: Add Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from cooperative/farmer app."""
    valid_keys = os.getenv("API_KEYS", "").split(",")
    
    if x_api_key not in valid_keys:
        raise HTTPException(401, "Invalid API key")
    
    return x_api_key

@app.post("/voice/upload")
async def upload_audio(
    audio: UploadFile,
    farmer_id: str,
    api_key: str = Depends(verify_api_key)
):
    # Process...
```

### Step 2.5: Create Farmer Mobile App Interface

**Simple HTML form for testing:**

```html
<!-- voice_upload.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Voice Ledger - Record Event</title>
</head>
<body>
    <h1>Record Coffee Event</h1>
    
    <form id="voiceForm" enctype="multipart/form-data">
        <label>Farmer ID:</label>
        <input type="text" name="farmer_id" required><br><br>
        
        <label>Audio Recording:</label>
        <input type="file" name="audio" accept="audio/*" required><br><br>
        
        <button type="button" onclick="recordAudio()">🎤 Record Audio</button>
        <button type="submit">📤 Upload</button>
    </form>
    
    <div id="result"></div>
    
    <script>
        document.getElementById('voiceForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            
            const response = await fetch('http://localhost:8000/voice/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            document.getElementById('result').innerHTML = `
                <h3>✅ Event Recorded!</h3>
                <p><strong>Transcript:</strong> ${result.transcript}</p>
                <p><strong>Batch ID:</strong> ${result.batch_id}</p>
                <p><strong>Event ID:</strong> ${result.event_id}</p>
                <p><strong>Blockchain TX:</strong> ${result.blockchain_tx}</p>
            `;
        };
    </script>
</body>
</html>
```

---

## Phase 3: IVR/Phone System (1 Week)

**Goal:** Enable farmers to call a toll-free number and record events via phone

### Step 3.1: Set Up Twilio Account

```bash
pip install twilio==8.13.0
```

**Configuration:**
1. Sign up at https://www.twilio.com
2. Buy toll-free number (~$2/month)
3. Configure webhook URL: `https://your-domain.com/voice/ivr`
4. Add credentials to `.env`:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+18001234567
```

### Step 3.2: Implement IVR Webhooks

```python
# voice/service/ivr.py
from twilio.twiml.voice_response import VoiceResponse, Gather

@app.post("/voice/ivr")
async def ivr_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    SpeechResult: str = Form(None)
):
    """
    Twilio IVR webhook.
    
    Flow:
    1. Farmer calls toll-free number
    2. System prompts in local language
    3. Farmer speaks event description
    4. System transcribes and parses
    5. System confirms via voice and SMS
    """
    response = VoiceResponse()
    
    if not SpeechResult:
        # First interaction - prompt for speech
        gather = Gather(
            input='speech',
            action='/voice/ivr',
            language='en-US',  # TODO: Support am-ET, om-ET
            speech_timeout='auto',
            timeout=5
        )
        
        gather.say(
            "Welcome to Voice Ledger. "
            "Please describe your coffee event after the beep. "
            "For example, say: I harvested 50 bags of washed coffee.",
            language='en-US'
        )
        
        response.append(gather)
        
    else:
        # Got speech - process it
        logger.info(f"IVR Speech from {From}: {SpeechResult}")
        
        # Get farmer from phone number
        with get_db() as db:
            farmer = db.query(FarmerIdentity)\
                .filter(FarmerIdentity.phone_number == From)\
                .first()
            
            if not farmer:
                response.say("Phone number not registered. Please contact your cooperative.")
                return str(response)
        
        # Parse speech with NLU
        try:
            event_data = extract_event_data(SpeechResult)
            
            # Create batch and event
            batch = create_batch(db, {
                'farmer_id': farmer.farmer_id,
                'quantity_kg': event_data['quantity'] * 60
            })
            
            # Confirm to farmer
            response.say(
                f"Event recorded. "
                f"Your batch ID is {batch.batch_id}. "
                f"You will receive an SMS confirmation. "
                f"Thank you for using Voice Ledger."
            )
            
            # Send SMS
            send_sms(
                From,
                f"✅ Event recorded!\n"
                f"Batch: {batch.batch_id}\n"
                f"Quantity: {event_data['quantity']} bags\n"
                f"View at: voiceledger.app/batch/{batch.batch_id}"
            )
            
        except Exception as e:
            logger.error(f"IVR processing failed: {str(e)}")
            response.say("Sorry, we couldn't process your event. Please try again.")
    
    return str(response)

def send_sms(to_number: str, message: str):
    """Send SMS confirmation via Twilio."""
    from twilio.rest import Client
    
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    
    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=to_number
    )
```

### Step 3.3: Test IVR System

```bash
# Deploy to public URL (use ngrok for testing)
ngrok http 8000

# Update Twilio webhook to: https://your-ngrok-url.ngrok.io/voice/ivr

# Call the toll-free number and test
```

---

## Phase 4: Offline-First (2-3 Weeks)

**Goal:** Enable offline recording at cooperative offices with sync when internet available

### Step 4.1: Install Local Whisper

```bash
pip install openai-whisper==20231117
pip install torch==2.1.2
pip install torchaudio==2.1.2

# Download Whisper small model (244MB)
python -c "import whisper; whisper.load_model('small')"
```

### Step 4.2: Create Offline Queue

```python
# voice/offline/queue.py
from database.models import OfflineQueue

def queue_offline_event(audio_path: str, farmer_id: str):
    """Queue event for later processing when internet available."""
    with get_db() as db:
        queue_entry = OfflineQueue(
            audio_file_path=audio_path,
            farmer_id=farmer_id,
            status='pending',
            created_at=datetime.utcnow()
        )
        db.add(queue_entry)
        db.commit()

def sync_offline_events():
    """Process all queued events when internet restored."""
    with get_db() as db:
        pending = db.query(OfflineQueue)\
            .filter(OfflineQueue.status == 'pending')\
            .all()
        
        for entry in pending:
            try:
                # Process with local Whisper + GPT
                result = process_voice_event(
                    entry.audio_file_path,
                    entry.farmer_id
                )
                
                # Mark as synced
                entry.status = 'synced'
                entry.synced_at = datetime.utcnow()
                entry.batch_id = result['batch_id']
                
                # Send delayed SMS
                farmer = get_farmer_by_id(entry.farmer_id)
                send_sms(
                    farmer.phone_number,
                    f"✅ Offline event synced!\nBatch: {result['batch_id']}"
                )
                
            except Exception as e:
                entry.status = 'error'
                entry.error_message = str(e)
            
            db.commit()
```

### Step 4.3: Deploy Edge Devices

**Hardware:**
- Raspberry Pi 5 (8GB RAM)
- USB microphone
- Local WiFi/Ethernet

**Software stack:**
- Raspbian OS
- Python 3.9+
- Whisper-Small model
- Local PostgreSQL (sync to Neon periodically)

---

## Testing Checklist

### Unit Tests
- [ ] `test_asr_infer.py` - ASR with sample audio files
- [ ] `test_nlu_infer.py` - NLU with sample transcripts
- [ ] `test_voice_api.py` - API endpoints with mocked audio
- [ ] `test_voice_pipeline.py` - End-to-end audio → blockchain

### Integration Tests
- [ ] Upload real audio file via API
- [ ] Call IVR toll-free number and record event
- [ ] Verify batch created in database
- [ ] Verify event anchored on blockchain
- [ ] Verify IPFS upload successful
- [ ] Verify SMS confirmation sent
- [ ] Test offline queue and sync

### Performance Tests
- [ ] ASR latency < 5 seconds
- [ ] NLU latency < 2 seconds
- [ ] Total pipeline < 15 seconds
- [ ] Concurrent uploads (10 simultaneous farmers)
- [ ] Offline queue processing rate (100 events/minute)

---

## Deployment Checklist

### Environment Setup
- [ ] Set `OPENAI_API_KEY` in production `.env`
- [ ] Set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
- [ ] Configure Neon database connection
- [ ] Set up Redis for Celery
- [ ] Configure IPFS Pinata keys
- [ ] Set up blockchain RPC endpoint (Polygon mainnet)

### Infrastructure
- [ ] Deploy FastAPI to cloud (AWS/Digital Ocean/Render)
- [ ] Set up HTTPS with SSL certificate
- [ ] Configure Twilio webhook URL
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation (Papertrail/Loggly)
- [ ] Set up error tracking (Sentry)

### Documentation
- [ ] API documentation (FastAPI auto-docs at /docs)
- [ ] Farmer onboarding guide (how to call toll-free number)
- [ ] Cooperative admin guide (how to use offline queue)
- [ ] Troubleshooting guide (common errors)

---

## Cost Estimates (100 Farmers, 10 Events/Month Each)

### API-Based (Cloud)
- Whisper API: 1000 events × 30s × $0.006/min = **$3/month**
- GPT-3.5 NLU: 1000 events × $0.002 = **$2/month**
- Twilio calls: 1000 × 0.5min × $0.0085 = **$4.25/month**
- Twilio SMS: 1000 × $0.0075 = **$7.50/month**
- Blockchain gas: 1000 × $0.01 = **$10/month**
- Server (2GB RAM): **$12/month**
- **Total: ~$39/month ($0.039/event)**

### Offline-First (Edge)
- Raspberry Pi 5: **$100 one-time**
- SMS only: **$7.50/month**
- Blockchain: **$10/month**
- **Total: ~$18/month after hardware amortized ($0.018/event)**

---

## Success Metrics

### Technical
- [ ] ASR accuracy > 90% for English
- [ ] NLU parsing success rate > 85%
- [ ] API uptime > 99.5%
- [ ] End-to-end latency < 15 seconds
- [ ] Zero data loss (all events eventually synced)

### Business
- [ ] 50+ farmers using voice interface in first month
- [ ] 500+ events recorded via voice
- [ ] < 5% farmer support requests
- [ ] 100% EUDR compliance for voice-recorded events
- [ ] Average farmer satisfaction score > 4/5

---

## Next Steps (Immediate)

1. **Install missing packages** (5 minutes)
   ```bash
   pip install pydub soundfile aiofiles
   brew install ffmpeg
   ```

2. **Review existing voice code** (30 minutes)
   - Read `voice/asr/asr_infer.py`
   - Read `voice/nlu/nlu_infer.py`
   - Read `voice/service/api.py`

3. **Create test audio file** (10 minutes)
   - Record: "I harvested 50 bags of washed coffee"
   - Save as `tests/audio_samples/test_harvest.wav`

4. **Test ASR module** (5 minutes)
   ```python
   from voice.asr.asr_infer import run_asr
   transcript = run_asr("tests/audio_samples/test_harvest.wav")
   print(transcript)
   ```

5. **Complete voice API endpoint** (1-2 hours)
   - Implement `/voice/upload` in `voice/service/api.py`
   - Integrate with existing database/blockchain code
   - Test with curl or Postman

6. **Deploy locally and test end-to-end** (30 minutes)
   - Start Anvil blockchain
   - Start Voice API
   - Upload test audio
   - Verify batch in database
   - Check dashboard for new event

---

## Resources

### Documentation
- OpenAI Whisper API: https://platform.openai.com/docs/guides/speech-to-text
- Twilio Voice: https://www.twilio.com/docs/voice
- FastAPI File Upload: https://fastapi.tiangolo.com/tutorial/request-files/
- Celery: https://docs.celeryq.dev/

### Code Examples
- `tests/test_end_to_end_workflow.py` - Reference for creating events
- `voice/asr/asr_infer.py` - ASR implementation
- `voice/nlu/nlu_infer.py` - NLU implementation
- `database/crud.py` - Database operations

### Support
- OpenAI API support: https://help.openai.com
- Twilio support: https://support.twilio.com
- GitHub Issues: https://github.com/The-Voice-Ledger/Voice-Ledger/issues

---

**Status:** Ready to implement  
**Estimated Time:** 1-2 days for basic API, 1 week for production-ready system  
**Dependencies:** None blocking (all packages available)  
**Risk Level:** Low (well-defined scope, proven technologies)

**Next Session:** Start with Phase 1, Step 1.1 (install packages)
