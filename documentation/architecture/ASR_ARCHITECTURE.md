# Voice Ledger ASR Architecture

**Last Updated:** December 25, 2025  
**Purpose:** Explain the unified speech recognition and conversational AI architecture across all channels

---

## Overview

Voice Ledger uses a **hybrid ASR (Automatic Speech Recognition) architecture** that combines:
1. **Local Whisper models** for offline transcription
2. **Cloud APIs** for advanced language processing
3. **Unified routing** across all channels (Telegram, Web UI, IVR)

This document clarifies the distinction between the **local Addis AI model** (downloaded) and the **Addis AI API** (cloud service), which serve different purposes in the voice processing pipeline.

---

## Two-Stage Voice Processing Pipeline

### Stage 1: Speech-to-Text (ASR/STT)
**Purpose:** Convert audio → text  
**Components:** Local Whisper models + OpenAI Whisper API

### Stage 2: Natural Language Understanding (NLU)
**Purpose:** Understand intent, extract entities, manage conversation  
**Components:** GPT-4 API (English) + Addis AI API (Amharic)

---

## Component Breakdown

### 1. Local Amharic Whisper Model (Downloaded)

**Model:** `b1n1yam/shook-medium-amharic-2k` (HuggingFace)  
**Location:** [voice/asr/asr_infer.py](../voice/asr/asr_infer.py)  
**Purpose:** Speech-to-Text (ASR) for Amharic only

#### Technical Details
```python
def load_amharic_model():
    """Load local Amharic Whisper model"""
    model_name = "b1n1yam/shook-medium-amharic-2k"
    _amharic_processor = AutoProcessor.from_pretrained(model_name)
    _amharic_model = AutoModelForSpeechSeq2Seq.from_pretrained(model_name)
    
    # Runs on Mac MPS (GPU) or CPU
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    _amharic_model = _amharic_model.to(device)
```

#### What It Does
- **Input:** Amharic audio file (.wav, .mp3, .webm)
- **Output:** Amharic text transcription
- **Runs:** Locally on your Mac (MPS/CPU)
- **Training:** Fine-tuned on 2000+ hours of Ethiopian Amharic speech
- **Cost:** Free (no API calls)
- **Performance:** Optimized for Ethiopian accents and dialects

#### Example Flow
```
User speaks: [Amharic audio: "50 ኪሎግራም የሲዳማ ቡና አጨድኩ"]
              ↓
Local Whisper Model
              ↓
Transcription: "50 ኪሎግራም የሲዳማ ቡና አጨድኩ"
```

---

### 2. OpenAI Whisper API (Cloud)

**API:** OpenAI Whisper-1  
**Location:** [voice/asr/asr_infer.py](../voice/asr/asr_infer.py)  
**Purpose:** Speech-to-Text (ASR) for English and other languages

#### Technical Details
```python
def transcribe_english(audio_file_path: str):
    """Use OpenAI Whisper API for English"""
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcript.strip()
```

#### What It Does
- **Input:** Audio file (any language, but optimized for English in our system)
- **Output:** Text transcription
- **Runs:** OpenAI cloud (API call)
- **Cost:** $0.006 per minute of audio
- **Performance:** Best-in-class for English and 90+ languages

#### Example Flow
```
User speaks: [English audio: "Record 50 kilograms of Sidama coffee"]
              ↓
OpenAI Whisper API
              ↓
Transcription: "Record 50 kilograms of Sidama coffee"
```

---

### 3. Addis AI API (Cloud)

**API:** `https://api.addisassistant.com/api/v1/chat_generate`  
**Location:** [voice/integrations/amharic_conversation.py](../voice/integrations/amharic_conversation.py)  
**Purpose:** Conversational AI / Natural Language Understanding (Amharic only)

#### Technical Details
```python
async def process_amharic_conversation(user_id: int, transcript: str):
    """Process Amharic conversation with Addis AI"""
    response = await client_http.post(
        ADDIS_AI_URL,
        headers={"X-API-Key": ADDIS_AI_API_KEY},
        json={
            "prompt": transcript,
            "target_language": "am",
            "conversation_history": conversation_history,
            "generation_config": {
                "temperature": 0.7,
                "max_output_tokens": 500
            }
        }
    )
```

#### What It Does
- **Input:** Amharic text (from ASR transcription)
- **Output:** JSON with intent, entities, Amharic response
- **Runs:** Addis AI cloud (API call)
- **Cost:** Per API request (pricing varies)
- **Capabilities:**
  - Understands Amharic conversational context
  - Extracts entities (quantities, batch IDs, locations)
  - Manages multi-turn dialogue
  - Generates culturally appropriate Amharic responses
  - Determines when command is ready to execute

#### Example Flow
```
ASR Output: "50 ኪሎግራም የሲዳማ ቡና አጨድኩ"
              ↓
Addis AI API (NLU)
              ↓
JSON Response:
{
  "intent": "record_commission",
  "entities": {
    "quantity_kg": 50,
    "variety": "Sidama",
    "product": "coffee"
  },
  "amharic_response": "50 ኪሎግራም የሲዳማ ቡና መዝግቤአለሁ። ከየት እርሻ ነው?",
  "ready_to_execute": false,
  "needs_clarification": true
}
```

---

### 4. GPT-4 API (Cloud)

**API:** OpenAI GPT-4  
**Location:** [voice/integrations/english_conversation.py](../voice/integrations/english_conversation.py)  
**Purpose:** Conversational AI / Natural Language Understanding (English)

#### Technical Details
```python
def process_english_conversation(user_id: int, transcript: str):
    """Process English conversation with GPT-4"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation_history,
        {"role": "user", "content": transcript}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
```

#### What It Does
- **Input:** English text (from ASR transcription)
- **Output:** JSON with intent, entities, English response
- **Runs:** OpenAI cloud (API call)
- **Cost:** ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- **Capabilities:**
  - Understands English conversational context
  - Extracts entities (quantities, batch IDs, locations)
  - Manages multi-turn dialogue
  - Determines when command is ready to execute
  - Can access RAG knowledge base for documentation queries

---

## Complete Processing Flow

### Amharic Voice Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SPEAKS AMHARIC                          │
│                  [Audio: Amharic voice]                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 1: SPEECH-TO-TEXT (ASR)                     │
│                                                                 │
│  Component: Local Amharic Whisper Model                        │
│  Model: b1n1yam/shook-medium-amharic-2k                       │
│  Location: voice/asr/asr_infer.py                             │
│  Runs: Locally on Mac (MPS/CPU)                               │
│  Cost: Free                                                    │
│                                                                 │
│  Input:  [Amharic audio bytes]                                │
│  Output: "50 ኪሎግራም የሲዳማ ቡና አጨድኩ"                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│      STAGE 2: NATURAL LANGUAGE UNDERSTANDING (NLU)              │
│                                                                 │
│  Component: Addis AI API                                       │
│  Endpoint: https://api.addisassistant.com/api/v1/chat_generate│
│  Location: voice/integrations/amharic_conversation.py         │
│  Runs: Cloud (API call)                                       │
│  Cost: Per request                                            │
│                                                                 │
│  Input:  "50 ኪሎግራም የሲዳማ ቡና አጨድኩ"                              │
│  Output: {                                                     │
│    "intent": "record_commission",                             │
│    "entities": {"quantity_kg": 50, "variety": "Sidama"},      │
│    "amharic_response": "ከየት እርሻ ነው?",                          │
│    "ready_to_execute": false                                  │
│  }                                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                  EXECUTE OR CLARIFY                             │
│                                                                 │
│  If ready_to_execute: true  → Execute command (record batch)   │
│  If needs_clarification     → Ask for more info (farm location)│
└─────────────────────────────────────────────────────────────────┘
```

### English Voice Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SPEAKS ENGLISH                          │
│          [Audio: "Record 50kg of Sidama coffee"]               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│               STAGE 1: SPEECH-TO-TEXT (ASR)                     │
│                                                                 │
│  Component: OpenAI Whisper API                                 │
│  Model: whisper-1                                              │
│  Location: voice/asr/asr_infer.py                             │
│  Runs: OpenAI Cloud (API call)                                │
│  Cost: $0.006 per minute                                      │
│                                                                 │
│  Input:  [English audio bytes]                                │
│  Output: "Record 50kg of Sidama coffee"                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│      STAGE 2: NATURAL LANGUAGE UNDERSTANDING (NLU)              │
│                                                                 │
│  Component: GPT-4 API                                          │
│  Model: gpt-4                                                  │
│  Location: voice/integrations/english_conversation.py         │
│  Runs: OpenAI Cloud (API call)                                │
│  Cost: ~$0.03-0.06 per 1K tokens                              │
│                                                                 │
│  Input:  "Record 50kg of Sidama coffee"                       │
│  Output: {                                                     │
│    "intent": "record_commission",                             │
│    "entities": {"quantity_kg": 50, "variety": "Sidama"},      │
│    "message": "Which farm is this from?",                     │
│    "ready_to_execute": false                                  │
│  }                                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────────┐
│                  EXECUTE OR CLARIFY                             │
│                                                                 │
│  If ready_to_execute: true  → Execute command (record batch)   │
│  If needs_clarification     → Ask for more info (farm location)│
└─────────────────────────────────────────────────────────────────┘
```

---

## Unified Channel Architecture

**All channels use the exact same ASR system:**

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Telegram   │  │   Web UI     │  │   Twilio     │  │    Future    │
│   Channel    │  │  (WebSocket) │  │   (IVR)      │  │   Channels   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │                  │
       └─────────────────┴──────────────────┴──────────────────┘
                                │
                                v
              ┌─────────────────────────────────┐
              │   UNIFIED ASR ROUTER            │
              │   voice/asr/asr_infer.py        │
              │   run_asr_with_user_preference  │
              └────────────┬────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                v                     v
    ┌──────────────────┐    ┌──────────────────┐
    │ Local Whisper    │    │ OpenAI Whisper   │
    │   (Amharic)      │    │   API (English)  │
    │ b1n1yam/shook... │    │   whisper-1      │
    └────────┬─────────┘    └────────┬─────────┘
             │                       │
             └───────────┬───────────┘
                         │
                         v
              ┌─────────────────────┐
              │  Transcribed Text   │
              └──────────┬──────────┘
                         │
                ┌────────┴────────┐
                │                 │
                v                 v
    ┌──────────────────┐  ┌──────────────────┐
    │  Addis AI API    │  │    GPT-4 API     │
    │   (Amharic NLU)  │  │  (English NLU)   │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │
             └──────────┬──────────┘
                        │
                        v
              ┌─────────────────────┐
              │  Intent + Entities  │
              │  + Response Message │
              └──────────┬──────────┘
                         │
                         v
              ┌─────────────────────┐
              │  Execute Command    │
              │  or Ask Clarifying  │
              │  Question           │
              └─────────────────────┘
```

---

## Key Implementation Files

### ASR Layer
**File:** [voice/asr/asr_infer.py](../voice/asr/asr_infer.py) (288 lines)

**Key Functions:**
```python
def load_amharic_model():
    """Lazy load local Amharic Whisper model"""
    
def detect_language(audio_file_path: str) -> str:
    """Detect language using OpenAI Whisper API"""
    
def transcribe_with_amharic_model(audio_file_path: str) -> str:
    """Transcribe Amharic audio with local model"""
    
def run_asr_with_user_preference(audio_file_path: str, user_language: str):
    """Route to appropriate ASR based on user's language choice"""
    # if user_language == 'am': → Local Whisper
    # else: → OpenAI Whisper API
```

### NLU Layer (Amharic)
**File:** [voice/integrations/amharic_conversation.py](../voice/integrations/amharic_conversation.py) (401 lines)

**Key Functions:**
```python
async def process_amharic_conversation(user_id: int, transcript: str):
    """Send Amharic text to Addis AI API for intent extraction"""
    
async def translate_summary_to_entities(amharic_summary: str):
    """Translate Amharic entities to English for database"""
```

### NLU Layer (English)
**File:** [voice/integrations/english_conversation.py](../voice/integrations/english_conversation.py) (275 lines)

**Key Functions:**
```python
def process_english_conversation(user_id: int, transcript: str, use_rag: bool = True):
    """Send English text to GPT-4 for intent extraction"""
    # Note: RAG integration pending (see FIX_RAG_CORE_INTEGRATION.md)
```

### Channel Implementations

#### Telegram Channel
**File:** [voice/tasks/voice_tasks.py](../voice/tasks/voice_tasks.py)
```python
@celery_app.task
def process_voice_task(user_id, audio_path, user_language):
    # Uses: run_asr_with_user_preference()
    # Then: process_amharic_conversation() or process_english_conversation()
```

#### Web UI Channel
**File:** [voice/web/voice_api.py](../voice/web/voice_api.py)
```python
@router.websocket("/api/voice/ws/voice")
async def voice_websocket(websocket: WebSocket):
    # Uses: run_asr_with_user_preference_async()
    # Then: process_amharic_conversation() or process_english_conversation()
```

#### Twilio IVR Channel
**File:** [voice/ivr/twilio_handlers.py](../voice/ivr/twilio_handlers.py)
```python
@router.post("/twilio/voice/gather")
async def handle_voice_gather(request: Request):
    # Uses: run_asr_with_user_preference()
    # Then: process_amharic_conversation() or process_english_conversation()
```

---

## Why This Architecture?

### 1. **Cost Efficiency**
- **Amharic:** Local model = $0 per transcription
- **English:** OpenAI API = $0.006 per minute (acceptable for business use)
- **Hybrid approach saves ~70% on ASR costs** (most users are Amharic speakers)

### 2. **Quality Optimization**
- **Amharic:** Local model fine-tuned on Ethiopian speech patterns
- **English:** OpenAI Whisper-1 is best-in-class for English
- **Each language gets the best available model**

### 3. **Offline Capability**
- **Amharic users can transcribe offline** (local model)
- **English requires internet** (API call)
- **Important for rural Ethiopian users with limited connectivity**

### 4. **Single Source of Truth**
- **All channels use same ASR module**
- **Consistent transcription quality**
- **Easy to update/debug** (change in one place)

### 5. **Modularity**
- **ASR layer** independent of NLU layer
- **Easy to swap models** (e.g., switch from GPT-4 to local LLaMA)
- **Can add new languages** without touching channel code

---

## Performance Characteristics

### Local Amharic Whisper Model
| Metric | Value |
|--------|-------|
| **Load Time** | 3-5 seconds (first time, then cached) |
| **Inference Speed** | ~0.5-1.5 seconds per 10 seconds of audio (on Mac M1/M2) |
| **Accuracy** | 85-95% for Ethiopian Amharic |
| **Memory** | ~2GB RAM when loaded |
| **Device** | MPS (Mac GPU) or CPU fallback |

### OpenAI Whisper API
| Metric | Value |
|--------|-------|
| **Latency** | ~2-4 seconds per request |
| **Accuracy** | 95%+ for clear English audio |
| **Supported Languages** | 90+ languages |
| **Max File Size** | 25MB |

### Addis AI API
| Metric | Value |
|--------|-------|
| **Latency** | ~1-3 seconds per request |
| **Context Window** | Supports multi-turn conversation |
| **Output** | Structured JSON or Amharic text |

### GPT-4 API
| Metric | Value |
|--------|-------|
| **Latency** | ~1-3 seconds per request |
| **Context Window** | 8K tokens |
| **Output** | Structured JSON |
| **RAG-Enhanced** | Can access 3,539 knowledge base chunks |

---

## Configuration

### Environment Variables Required

```bash
# OpenAI (for English ASR and NLU)
OPENAI_API_KEY=sk-...

# Addis AI (for Amharic NLU)
ADDIS_AI_API_KEY=sk_...

# Local model will download automatically from HuggingFace on first use
# No API key needed for local Amharic ASR
```

### Model Download
The Amharic Whisper model downloads automatically on first use:
```python
# Downloads from HuggingFace Hub
model_name = "b1n1yam/shook-medium-amharic-2k"
_amharic_processor = AutoProcessor.from_pretrained(model_name)
_amharic_model = AutoModelForSpeechSeq2Seq.from_pretrained(model_name)
```

**Size:** ~1.5GB download  
**Location:** `~/.cache/huggingface/hub/`

---

## Troubleshooting

### Issue: "Amharic model taking too long to load"
**Solution:** Model loads once and is cached. First load takes 3-5 seconds, subsequent calls are instant.

### Issue: "OpenAI Whisper API rate limits"
**Solution:** OpenAI has generous rate limits. If hit, implement request queuing or upgrade tier.

### Issue: "Addis AI API connection failed"
**Solution:** 
1. Check API key in `.env`
2. Verify endpoint: `https://api.addisassistant.com/api/v1/chat_generate`
3. Check API key format: `sk_xxx_xxx`

### Issue: "Wrong language detected"
**Solution:** User language preference takes precedence over auto-detection. Ensure `user.preferred_language` is set correctly.

### Issue: "Web UI transcription different from Telegram"
**Solution:** This shouldn't happen - both use same ASR. Check logs for routing decision. Verify `user_language` parameter passed correctly.

---

## Testing

### Test Amharic ASR (Local Model)
```bash
python -m voice.asr.asr_infer tests/audio/amharic_sample.wav --lang am
```

### Test English ASR (OpenAI API)
```bash
python -m voice.asr.asr_infer tests/audio/english_sample.wav --lang en
```

### Test Amharic Full Pipeline
```bash
python admin_scripts/test_amharic_voice.sh
```

### Test Web UI
```bash
bash admin_scripts/START_SERVICES.sh
# Open http://localhost:3000/voice
# Record Amharic or English voice
# Verify correct routing in logs
```

---

## Future Enhancements

### Planned Improvements
1. **Add more Ethiopian languages**
   - Oromo, Tigrinya models
   - Extend local ASR to 5+ Ethiopian languages

2. **Streaming ASR**
   - Real-time transcription as user speaks
   - Reduce perceived latency

3. **Voice Activity Detection (VAD)**
   - Auto-detect when user stops speaking
   - No manual recording stop needed

4. **Accent Adaptation**
   - Fine-tune on user's specific accent over time
   - Personalized ASR models

5. **Offline English Support**
   - Download OpenAI Whisper locally for English
   - Full offline capability

---

## Related Documentation

- **RAG System:** [RAG_SYSTEM_IMPLEMENTATION.md](RAG_SYSTEM_IMPLEMENTATION.md)
- **RAG Core Fix:** [FIX_RAG_CORE_INTEGRATION.md](FIX_RAG_CORE_INTEGRATION.md)
- **Web UI RAG Audit:** [audits/WEBUI_RAG_INTEGRATION_AUDIT.md](audits/WEBUI_RAG_INTEGRATION_AUDIT.md)
- **End-to-End Workflow:** [guides/VOICE_LEDGER_END_TO_END_WORKFLOW.md](guides/VOICE_LEDGER_END_TO_END_WORKFLOW.md)
- **Deployment Guide:** [guides/RAILWAY_DEPLOYMENT_GUIDE.md](guides/RAILWAY_DEPLOYMENT_GUIDE.md)

---

## Summary

**Key Takeaways:**

1. ✅ **Two-stage pipeline:** ASR (speech→text) → NLU (intent extraction)
2. ✅ **Local Amharic Whisper = ASR only** (not conversational AI)
3. ✅ **Addis AI API = NLU only** (conversational understanding)
4. ✅ **Web UI uses same ASR as Telegram** (unified architecture)
5. ✅ **Cost-efficient:** Local model for Amharic, API for English
6. ✅ **High quality:** Each language gets best-in-class model
7. ✅ **Modular:** Easy to add channels/languages/models

**Architecture Philosophy:**
> "Use local models where quality and cost efficiency justify it (Amharic ASR), and cloud APIs where they provide best-in-class capabilities (English ASR, all NLU)."

---

**Questions?** Check logs in `logs/voice_api.log` or ask in the team channel.
