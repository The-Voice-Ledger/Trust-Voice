# TrustVoice Development Prompt

**Complete Build Instructions for AI Coding Assistant**

---

## Project Overview

Build a voice-first donation platform that connects European/US donors to African NGO projects through conversational AI. Donors use WhatsApp, Telegram, or phone calls to ask questions, donate, and track impact. Field officers verify project completion via voice, creating transparent blockchain receipts.

**Key Differentiator:** No apps or websites required. Pure conversational interface.

---

## Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL 15+ (Neon serverless)
- **Cache:** Redis
- **Task Queue:** Celery
- **ORM:** SQLAlchemy 2.0

### AI/ML
- **LLM:** OpenAI GPT-4 Turbo (European languages) + **Addis AI** (Amharic/Swahili native)
- **Speech-to-Text:** Whisper API (OpenAI) + Local Amharic model (Addis AI trained, 2000+ hours)
- **Text-to-Speech:** ElevenLabs (multi-language)
- **RAG:** LangChain + Pinecone (vector database)
- **Intent Classification:** GPT-4 function calling (EN) / Addis AI native (AM/SW)
- **Conversation State:** ConversationManager (proven with Voice Ledger - 1000+ concurrent users)

### Communication Channels
- **IVR:** Twilio Voice API
- **Telegram:** python-telegram-bot (async)
- **WhatsApp:** Twilio WhatsApp Business API
- **Webhooks:** ngrok (dev) / Cloudflare Tunnel (prod)

### Payments
- **Primary:** Stripe API (credit cards, bank transfers)
- **Secondary:** PayPal SDK
- **Crypto (Optional):** Web3.py (Polygon/Base)

### Blockchain
- **Networks:** Polygon (low gas), Base (Coinbase L2)
- **Smart Contracts:** Solidity 0.8.20
- **Storage:** IPFS (NFT.storage)
- **Framework:** Hardhat

### DevOps
- **Hosting:** Railway or Render
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry
- **Secrets:** Environment variables

---

## Architecture Blueprint

```
┌─────────────────────────────────────────────────┐
│         COMMUNICATION CHANNELS                   │
│  IVR (Phone) | Telegram Bot | WhatsApp          │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      MULTICHANNEL ROUTER                        │
│   voice/routers/channel_router.py               │
│   - Normalizes messages from all channels       │
│   - Routes to conversation handler              │
│   - Manages session state (Redis)               │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      LANGUAGE ROUTER                            │
│   Routes by donor.preferred_language            │
│   (Set during registration, NO auto-detection)  │
└─────┬──────────────────────────┬────────────────┘
      │                          │
┌─────▼────────┐        ┌────────▼──────────┐
│  GPT-4       │        │   ADDIS AI        │
│  (EU langs)  │        │   (AM/SW native)  │
│  EN/FR/DE/IT │        │   Amharic/Swahili │
└─────┬────────┘        └────────┬──────────┘
      │                          │
      └────────┬─────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│      CONVERSATION MANAGER                       │
│   voice/ai/conversation_manager.py              │
│   - Multi-turn dialogue state                   │
│   - Entity collection across turns              │
│   - Intent tracking                             │
│   - 5-minute conversation timeout               │
└─────┬──────────┬──────────┬────────────────────┘
      │          │          │
┌─────▼────┐ ┌──▼─────┐ ┌──▼──────────┐
│ CAMPAIGN │ │DONATION│ │   IMPACT    │
│  QUERY   │ │  FLOW  │ │ VERIFICATION│
│          │ │        │ │             │
│ RAG      │ │Stripe/ │ │Voice Record │
│(Pinecone)│ │PayPal  │ │+ Blockchain │
└──────────┘ └────────┘ └─────────────┘
      │          │          │
      └──────────┴──────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      POSTGRESQL DATABASE                        │
│   - Donors (with preferred_language)           │
│   - Campaigns                                   │
│   - Donations                                   │
│   - Impact Verifications                        │
│   - Conversation Logs                           │
└────────────────────────────────────────────────┘
```

---

## Phase 1: Core Infrastructure (Week 1-2)

### Step 1.1: Project Setup

```bash
# Initialize project
mkdir trustvoice && cd trustvoice
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic redis celery python-dotenv

# Create structure
mkdir -p {voice/{routers,ai,tasks},payments,blockchain,database/{models,migrations},tests}
touch {voice,payments,blockchain,database}/__init__.py
```

**Files to create:**

`main.py`:
```python
from fastapi import FastAPI
from voice.routers import ivr, telegram, whatsapp
from payments.routers import stripe_router, paypal_router

app = FastAPI(title="TrustVoice API")

# Include routers
app.include_router(ivr.router, prefix="/voice/ivr", tags=["IVR"])
app.include_router(telegram.router, prefix="/voice/telegram", tags=["Telegram"])
app.include_router(whatsapp.router, prefix="/voice/whatsapp", tags=["WhatsApp"])
app.include_router(stripe_router, prefix="/payments/stripe", tags=["Stripe"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

`.env`:
```bash
DATABASE_URL=postgresql://user:pass@db.neon.tech:5432/trustvoice
REDIS_URL=redis://localhost:6379

# OpenAI (European languages)
OPENAI_API_KEY=sk-...

# Addis AI (Amharic/Swahili) - CRITICAL for African language support
ADDIS_AI_API_KEY=sk_...
ADDIS_AI_URL=https://api.addisassistant.com/api/v1/chat_generate
ADDIS_TRANSLATE_URL=https://api.addisassistant.com/api/v1/translate

# Payments
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
TELEGRAM_BOT_TOKEN=...

# TTS
ELEVENLABS_API_KEY=...

# RAG
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-west1-gcp

# Blockchain
POLYGON_RPC_URL=https://polygon-rpc.com
IPFS_API_KEY=...
```

### Step 1.2: Database Models

`database/models.py`:
```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ARRAY, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Donor(Base):
    __tablename__ = "donors"
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, index=True)
    telegram_user_id = Column(String(50), unique=True, index=True)
    whatsapp_number = Column(String(20), unique=True, index=True)
    preferred_name = Column(String(100))
    preferred_language = Column(String(10), default="en")
    email = Column(String(255))
    country_code = Column(String(2))
    blockchain_wallet_address = Column(String(66))
    stripe_customer_id = Column(String(100))
    total_donated_usd = Column(Float, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime)
    
    donations = relationship("Donation", back_populates="donor")

class NGOOrganization(Base):
    __tablename__ = "ngo_organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100))
    country = Column(String(100))
    contact_email = Column(String(255))
    admin_phone = Column(String(20))
    blockchain_wallet_address = Column(String(66))
    stripe_account_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    campaigns = relationship("Campaign", back_populates="ngo")

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True)
    ngo_id = Column(Integer, ForeignKey("ngo_organizations.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    goal_amount_usd = Column(Float, nullable=False)
    raised_amount_usd = Column(Float, default=0)
    category = Column(String(50))  # water, education, health
    location_country = Column(String(100))
    location_region = Column(String(100))
    location_gps = Column(String(100))
    status = Column(String(20), default="active")  # active, paused, completed
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ngo = relationship("NGOOrganization", back_populates="campaigns")
    donations = relationship("Donation", back_populates="campaign")
    verifications = relationship("ImpactVerification", back_populates="campaign")

class CampaignContext(Base):
    __tablename__ = "campaign_context"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    content_type = Column(String(50))  # faq, story, budget
    content = Column(Text, nullable=False)
    language = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    amount_usd = Column(Float, nullable=False)
    payment_method = Column(String(20))  # stripe, paypal, crypto
    payment_intent_id = Column(String(255))
    transaction_hash = Column(String(66))  # if crypto
    blockchain_receipt_url = Column(Text)
    status = Column(String(20), default="pending")  # pending, completed, failed
    donor_message = Column(Text)
    is_anonymous = Column(Boolean, default=False)
    tax_receipt_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    donor = relationship("Donor", back_populates="donations")
    campaign = relationship("Campaign", back_populates="donations")

class ImpactVerification(Base):
    __tablename__ = "impact_verifications"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    verifier_phone = Column(String(20))
    verifier_name = Column(String(100))
    verification_type = Column(String(50))  # milestone, completion
    description = Column(Text)
    audio_recording_url = Column(Text)
    photo_urls = Column(ARRAY(Text))
    gps_coordinates = Column(String(100))
    beneficiary_count = Column(Integer)
    blockchain_anchor_tx = Column(String(66))
    verified_at = Column(DateTime, default=datetime.utcnow)
    
    campaign = relationship("Campaign", back_populates="verifications")

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    channel = Column(String(20))  # ivr, telegram, whatsapp
    session_id = Column(String(100))
    message_type = Column(String(20))  # user, assistant
    message_text = Column(Text)
    intent_detected = Column(String(50))
    llm_model = Column(String(50))
    llm_tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Create migration:**
```bash
alembic init database/migrations
# Edit alembic.ini: sqlalchemy.url = from .env
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Step 1.3: Database Utilities

`database/db.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

@contextmanager
def get_db() -> Session:
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

async def get_donor_by_phone(phone: str) -> Donor:
    with get_db() as db:
        return db.query(Donor).filter_by(phone_number=phone).first()

async def get_donor_by_telegram_id(telegram_id: str) -> Donor:
    with get_db() as db:
        return db.query(Donor).filter_by(telegram_user_id=telegram_id).first()

async def get_active_campaigns():
    with get_db() as db:
        return db.query(Campaign).filter_by(status="active").all()
```

---

## Phase 2: Speech Recognition (User Preference Based) (Week 2)

**CRITICAL LEARNING FROM VOICE LEDGER:** Do NOT use language auto-detection. Route based on user's registered language preference.

### Step 2.1: ASR Handler with Language Routing

`voice/asr/asr_handler.py`:
```python
import os
import logging
from pathlib import Path
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_path: str, user_language: str) -> Dict[str, str]:
    """
    Transcribe audio using user's registered language preference.
    
    **NO AUTO-DETECTION** - Language set during registration.
    
    Voice Ledger Design Choice:
    - Auto-detection can fail with accents and background noise
    - User preference is more reliable
    - Reduces re-attempts and costs
    
    Args:
        audio_path: Path to audio file
        user_language: From donors.preferred_language (en/fr/de/it/am/sw)
    
    Returns:
        {'text': transcript, 'language': user_language}
    """
    audio_file = Path(audio_path)
    
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    
    logger.info(f"Transcribing with user preference: {user_language}")
    
    if user_language in ['am', 'sw']:  # African languages
        # Use local Amharic/Swahili Whisper model
        # Trained on 2000+ hours by Addis AI
        transcript = transcribe_with_local_model(audio_path, user_language)
        logger.info(f"Local model ({user_language}): {transcript[:50]}...")
    
    else:  # European languages (en/fr/de/it)
        # Use OpenAI Whisper API
        with open(audio_path, "rb") as audio:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language=user_language,  # Hint improves accuracy
                response_format="text"
            )
        transcript = result.strip()
        logger.info(f"Whisper API ({user_language}): {transcript[:50]}...")
    
    return {
        'text': transcript,
        'language': user_language
    }


def transcribe_with_local_model(audio_path: str, language: str) -> str:
    """
    Transcribe using local Amharic/Swahili Whisper model.
    
    Model: whisper-large-v3-am (fine-tuned by Addis AI)
    Training: 2000+ hours of Ethiopian Amharic speech
    Based on Voice Ledger prototype architecture
    """
    import whisper
    
    # Load model (cached after first load)
    model_path = f"models/whisper-{language}"
    model = whisper.load_model(model_path)
    
    # Transcribe
    result = model.transcribe(
        audio_path,
        language=language,
        fp16=False  # CPU compatibility
    )
    
    return result["text"]
```

### Step 2.2: Language Selection During Registration

**Telegram/WhatsApp Registration Flow:**

`voice/telegram/register_handler.py`:
```python
async def handle_language_selection(update: Update, context):
    """
    Present language options to new donor.
    """
    keyboard = [
        [
            InlineKeyboardButton("English 🇺🇸", callback_data="lang_en"),
            InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")
        ],
        [
            InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de"),
            InlineKeyboardButton("Italiano 🇮🇹", callback_data="lang_it")
        ],
        [
            InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am"),
            InlineKeyboardButton("Swahili 🇹🇿", callback_data="lang_sw")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Welcome to TrustVoice! 🌍\n\n"
        "Please select your preferred language.\n"
        "This will be used for all voice interactions:",
        reply_markup=reply_markup
    )

async def handle_language_callback(update: Update, context):
    """
    Store language preference in database.
    """
    query = update.callback_query
    await query.answer()
    
    language = query.data.split('_')[1]  # Extract 'en' from 'lang_en'
    user_id = update.effective_user.id
    
    # Save to database
    with get_db() as db:
        donor = db.query(Donor).filter_by(telegram_user_id=str(user_id)).first()
        if donor:
            donor.preferred_language = language
            db.commit()
    
    lang_names = {
        'en': 'English', 'fr': 'Français', 'de': 'Deutsch',
        'it': 'Italiano', 'am': 'አማርኛ', 'sw': 'Swahili'
    }
    
    await query.edit_message_text(
        f"✅ Language set to: {lang_names[language]}\n\n"
        f"All voice messages will be processed in {lang_names[language]}.\n"
        f"You can change this anytime in settings."
    )
```

---

## Phase 3: Communication Channels (Week 3-4)

### Step 2.1: IVR (Twilio Voice)

`voice/routers/ivr.py`:
```python
from fastapi import APIRouter, Form, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from database.db import get_donor_by_phone, get_db
from voice.ai.conversation_handler import process_voice_input
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/incoming")
async def handle_incoming_call(From: str = Form(...)):
    """Handles incoming phone call"""
    response = VoiceResponse()
    
    # Authenticate donor
    donor = await get_donor_by_phone(From)
    
    if not donor:
        response.say(
            "Thank you for calling TrustVoice. This phone number is not registered. "
            "Please sign up via WhatsApp or Telegram first. Goodbye.",
            language="en"
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    
    # Welcome message
    greeting = f"Hello {donor.preferred_name}! Welcome to TrustVoice. "
    greeting += "You can ask about campaigns, make a donation, or track your impact. "
    greeting += "What would you like to do?"
    
    response.say(greeting, language=donor.preferred_language or "en")
    response.record(
        action="/voice/ivr/recording",
        method="POST",
        max_length=60,
        transcribe=False  # We use Whisper instead
    )
    
    return Response(content=str(response), media_type="application/xml")

@router.post("/recording")
async def handle_recording(
    From: str = Form(...),
    RecordingUrl: str = Form(...),
    CallSid: str = Form(...)
):
    """Processes recorded audio"""
    response = VoiceResponse()
    
    response.say("Processing your request, please wait.", language="en")
    
    # Queue transcription + AI processing
    from voice.tasks.voice_tasks import process_ivr_recording
    process_ivr_recording.delay(
        phone_number=From,
        recording_url=RecordingUrl,
        call_sid=CallSid
    )
    
    response.pause(length=3)
    response.say("We'll call you back shortly with a response.", language="en")
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")

@router.post("/respond")
async def respond_to_donor(
    To: str = Form(...),
    Message: str = Form(...)
):
    """Calls donor back with AI response"""
    from twilio.rest import Client
    import os
    
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    
    # Generate TTS
    from voice.tts.speech_generator import text_to_speech
    audio_bytes = await text_to_speech(Message, "en")
    
    # Upload to S3/Twilio
    audio_url = await upload_audio(audio_bytes)
    
    # Make outbound call
    call = client.calls.create(
        to=To,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"/voice/ivr/play?audio_url={audio_url}"
    )
    
    return {"call_sid": call.sid}

@router.post("/play")
async def play_audio(audio_url: str):
    """Plays AI-generated audio to donor"""
    response = VoiceResponse()
    response.play(audio_url)
    response.hangup()
    return Response(content=str(response), media_type="application/xml")
```

### Step 2.2: Telegram Bot

Install: `pip install python-telegram-bot`

`voice/routers/telegram.py`:
```python
from fastapi import APIRouter, Request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database.db import get_donor_by_telegram_id, get_db
from database.models import Donor
from voice.ai.conversation_handler import process_text_input
import os

router = APIRouter()

# Initialize bot
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(BOT_TOKEN).build()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receives updates from Telegram"""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@router.get("/set_webhook")
async def set_webhook():
    """Registers webhook with Telegram"""
    webhook_url = f"{os.getenv('BASE_URL')}/voice/telegram/webhook"
    await application.bot.set_webhook(webhook_url)
    return {"webhook_set": webhook_url}

# Command handlers
async def start_handler(update: Update, context):
    """Handles /start command"""
    user = update.effective_user
    
    # Get or create donor
    donor = await get_donor_by_telegram_id(str(user.id))
    
    if not donor:
        # New user - create donor record
        with get_db() as db:
            donor = Donor(
                telegram_user_id=str(user.id),
                preferred_name=user.first_name,
                preferred_language="en"
            )
            db.add(donor)
            db.commit()
        
        await update.message.reply_text(
            f"Welcome to TrustVoice, {user.first_name}! 👋\n\n"
            "I can help you:\n"
            "• Find campaigns to support\n"
            "• Make donations\n"
            "• Track your impact\n\n"
            "Just ask me anything, like 'Tell me about water projects in Tanzania'"
        )
    else:
        await update.message.reply_text(
            f"Welcome back, {donor.preferred_name}!\n\n"
            "What would you like to do today?"
        )

async def message_handler(update: Update, context):
    """Handles all text messages"""
    user = update.effective_user
    message = update.message.text
    
    # Get donor
    donor = await get_donor_by_telegram_id(str(user.id))
    if not donor:
        await update.message.reply_text("Please use /start first")
        return
    
    # Process with AI
    ai_response = await process_text_input(
        donor_id=donor.id,
        message=message,
        channel="telegram",
        session_id=f"tg_{user.id}"
    )
    
    # Send response
    if ai_response.get("buttons"):
        keyboard = [[InlineKeyboardButton(btn["text"], callback_data=btn["data"])]
                   for btn in ai_response["buttons"]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(ai_response["text"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(ai_response["text"])

# Register handlers
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
```

### Step 2.3: WhatsApp

`voice/routers/whatsapp.py`:
```python
from fastapi import APIRouter, Form, Response
from database.db import get_donor_by_phone
from voice.ai.conversation_handler import process_text_input
from twilio.rest import Client
import os

router = APIRouter()

@router.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """Handles incoming WhatsApp messages"""
    
    # Get donor (WhatsApp number format: whatsapp:+1234567890)
    phone = From.replace("whatsapp:", "")
    donor = await get_donor_by_phone(phone)
    
    if not donor:
        await send_whatsapp_message(
            to=From,
            message="Welcome to TrustVoice! Please register first by sending your name."
        )
        return {"status": "pending_registration"}
    
    # Process with AI
    ai_response = await process_text_input(
        donor_id=donor.id,
        message=Body,
        channel="whatsapp",
        session_id=f"wa_{phone}"
    )
    
    # Send response
    await send_whatsapp_message(
        to=From,
        message=ai_response["text"]
    )
    
    return {"status": "processed"}

async def send_whatsapp_message(to: str, message: str):
    """Sends WhatsApp message via Twilio"""
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    
    client.messages.create(
        from_=f"whatsapp:{os.getenv('TWILIO_PHONE_NUMBER')}",
        to=to,
        body=message
    )
```

---

## Phase 3: AI Conversation Engine (Week 3-4)

### Step 3.1: Intent Classification

Install: `pip install openai langchain pinecone-client`

`voice/ai/conversation_handler.py`:
```python
import openai
import os
from database.db import get_db, get_donor_by_id
from database.models import ConversationLog, Campaign
from typing import Dict

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are TrustVoice, an AI assistant helping donors support NGO campaigns in Africa.

You can:
1. Answer questions about campaigns (water, education, health projects)
2. Help donors make donations
3. Track donation impact
4. Provide campaign updates

Be warm, concise (max 50 words for voice), and transparent. 
Always mention how funds are used.

Available functions:
- get_campaigns: List active campaigns (filter by category, location)
- initiate_donation: Start donation process
- track_donations: Show donor's donation history
- get_impact: Show verified impact from field
"""

INTENT_SCHEMA = {
    "name": "classify_intent",
    "description": "Classifies user intent and extracts entities",
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [
                    "ask_campaign_info",
                    "initiate_donation",
                    "track_donation",
                    "get_impact",
                    "general_question"
                ]
            },
            "entities": {
                "type": "object",
                "properties": {
                    "campaign_category": {"type": "string"},
                    "location": {"type": "string"},
                    "amount": {"type": "number"},
                    "campaign_id": {"type": "integer"}
                }
            },
            "confidence": {"type": "number"}
        },
        "required": ["intent", "confidence"]
    }
}

async def process_text_input(
    donor_id: int,
    message: str,
    channel: str,
    session_id: str
) -> Dict:
    """
    Main conversation handler
    """
    # Get donor context
    donor = await get_donor_by_id(donor_id)
    
    # Get conversation history
    history = await get_conversation_history(donor_id, session_id)
    
    # Classify intent
    response = await openai.ChatCompletion.acreate(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": message}
        ],
        functions=[INTENT_SCHEMA],
        function_call={"name": "classify_intent"}
    )
    
    intent_data = eval(response.choices[0].message.function_call.arguments)
    intent = intent_data["intent"]
    entities = intent_data.get("entities", {})
    
    # Log conversation
    await log_conversation(donor_id, session_id, message, "user", intent, channel)
    
    # Route to handler
    if intent == "ask_campaign_info":
        ai_response = await handle_campaign_query(entities, donor.preferred_language)
    elif intent == "initiate_donation":
        ai_response = await handle_donation_flow(donor_id, entities)
    elif intent == "track_donation":
        ai_response = await handle_donation_tracking(donor_id)
    elif intent == "get_impact":
        ai_response = await handle_impact_query(donor_id, entities)
    else:
        ai_response = await handle_general_question(message, donor.preferred_language)
    
    # Log AI response
    await log_conversation(
        donor_id, session_id, ai_response["text"], 
        "assistant", intent, channel
    )
    
    return ai_response

async def handle_campaign_query(entities: Dict, language: str) -> Dict:
    """
    Answers questions about campaigns using RAG
    """
    from voice.ai.rag_engine import answer_campaign_question
    
    # Get campaigns matching criteria
    with get_db() as db:
        query = db.query(Campaign).filter_by(status="active")
        
        if entities.get("campaign_category"):
            query = query.filter_by(category=entities["campaign_category"])
        if entities.get("location"):
            query = query.filter(
                Campaign.location_country.ilike(f"%{entities['location']}%")
            )
        
        campaigns = query.limit(3).all()
    
    if not campaigns:
        return {
            "text": f"No active campaigns found. Try asking about water, education, or health projects.",
            "buttons": []
        }
    
    # Format response
    response_text = "Here are matching campaigns:\n\n"
    buttons = []
    
    for campaign in campaigns:
        progress = (campaign.raised_amount_usd / campaign.goal_amount_usd) * 100
        response_text += f"📍 {campaign.title}\n"
        response_text += f"   {campaign.location_country} • {progress:.0f}% funded\n"
        response_text += f"   ${campaign.raised_amount_usd:,.0f} / ${campaign.goal_amount_usd:,.0f}\n\n"
        
        buttons.append({
            "text": f"Donate to {campaign.title}",
            "data": f"donate_{campaign.id}"
        })
    
    return {"text": response_text.strip(), "buttons": buttons}

async def handle_donation_flow(donor_id: int, entities: Dict) -> Dict:
    """
    Initiates donation process
    """
    campaign_id = entities.get("campaign_id")
    amount = entities.get("amount", 50)  # Default $50
    
    if not campaign_id:
        return {
            "text": "Which campaign would you like to support? Please specify the campaign name.",
            "buttons": []
        }
    
    # Generate payment link
    from payments.stripe_handler import create_payment_intent
    
    payment_data = await create_payment_intent(
        donor_id=donor_id,
        campaign_id=campaign_id,
        amount_usd=amount
    )
    
    payment_url = f"https://trustvoice.org/pay/{payment_data['client_secret']}"
    
    return {
        "text": f"Great! To donate ${amount:.2f}, click here:\n{payment_url}\n\nOr reply with a different amount.",
        "buttons": [
            {"text": "Pay Now", "data": payment_url}
        ]
    }

async def handle_donation_tracking(donor_id: int) -> Dict:
    """
    Shows donor's donation history
    """
    from database.models import Donation
    
    with get_db() as db:
        donations = db.query(Donation).filter_by(
            donor_id=donor_id,
            status="completed"
        ).order_by(Donation.completed_at.desc()).limit(5).all()
    
    if not donations:
        return {
            "text": "You haven't made any donations yet. Ask me about campaigns to get started!",
            "buttons": []
        }
    
    response_text = f"Your donations ({len(donations)} total):\n\n"
    
    for donation in donations:
        response_text += f"• ${donation.amount_usd:.2f} to {donation.campaign.title}\n"
        response_text += f"  {donation.completed_at.strftime('%b %d, %Y')}\n\n"
    
    return {"text": response_text.strip(), "buttons": []}

async def handle_impact_query(donor_id: int, entities: Dict) -> Dict:
    """
    Shows verified impact for donor's campaigns
    """
    from database.models import Donation, ImpactVerification
    
    with get_db() as db:
        # Get campaigns donor has supported
        campaign_ids = db.query(Donation.campaign_id).filter_by(
            donor_id=donor_id,
            status="completed"
        ).distinct().all()
        
        campaign_ids = [cid[0] for cid in campaign_ids]
        
        # Get recent verifications
        verifications = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id.in_(campaign_ids)
        ).order_by(ImpactVerification.verified_at.desc()).limit(3).all()
    
    if not verifications:
        return {
            "text": "No impact updates yet for your campaigns. We'll notify you when field officers verify progress!",
            "buttons": []
        }
    
    response_text = "Recent impact updates:\n\n"
    
    for verification in verifications:
        response_text += f"✅ {verification.campaign.title}\n"
        response_text += f"   {verification.description}\n"
        if verification.beneficiary_count:
            response_text += f"   {verification.beneficiary_count} people served\n"
        response_text += f"   {verification.verified_at.strftime('%b %d, %Y')}\n\n"
    
    return {"text": response_text.strip(), "buttons": []}

async def log_conversation(
    donor_id: int,
    session_id: str,
    message: str,
    message_type: str,
    intent: str,
    channel: str
):
    """Logs conversation to database"""
    with get_db() as db:
        log = ConversationLog(
            donor_id=donor_id,
            session_id=session_id,
            message_text=message,
            message_type=message_type,
            intent_detected=intent,
            channel=channel,
            llm_model="gpt-4-turbo-preview"
        )
        db.add(log)
        db.commit()
```

### Step 3.2: RAG Implementation

`voice/ai/rag_engine.py`:
```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone
import os

# Initialize Pinecone
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENVIRONMENT")
)

INDEX_NAME = "trustvoice-campaigns"

class CampaignRAG:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vectorstore = Pinecone.from_existing_index(
            INDEX_NAME,
            self.embeddings
        )
    
    async def index_campaign(self, campaign_id: int):
        """
        Indexes campaign content for semantic search
        """
        from database.db import get_db
        from database.models import Campaign, CampaignContext
        
        with get_db() as db:
            campaign = db.query(Campaign).get(campaign_id)
            contexts = db.query(CampaignContext).filter_by(
                campaign_id=campaign_id
            ).all()
        
        # Prepare documents
        documents = [
            f"Campaign: {campaign.title}\nDescription: {campaign.description}",
        ]
        
        for context in contexts:
            documents.append(context.content)
        
        # Add to Pinecone
        self.vectorstore.add_texts(
            texts=documents,
            metadatas=[{"campaign_id": campaign_id}] * len(documents)
        )
    
    async def search(self, query: str, campaign_id: int = None, k: int = 5):
        """
        Searches campaign content
        """
        filter_dict = {"campaign_id": campaign_id} if campaign_id else {}
        
        results = self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter_dict
        )
        
        return [doc.page_content for doc in results]
```

---

## Phase 4: Payment Integration (Week 5)

### Step 4.1: Stripe

Install: `pip install stripe`

`payments/stripe_handler.py`:
```python
import stripe
import os
from database.db import get_db
from database.models import Donation, Donor, Campaign
from datetime import datetime

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def create_payment_intent(
    donor_id: int,
    campaign_id: int,
    amount_usd: float
) -> dict:
    """
    Creates Stripe Payment Intent
    """
    with get_db() as db:
        donor = db.query(Donor).get(donor_id)
        campaign = db.query(Campaign).get(campaign_id)
        
        # Create or get Stripe customer
        if not donor.stripe_customer_id:
            customer = stripe.Customer.create(
                email=donor.email,
                name=donor.preferred_name,
                phone=donor.phone_number
            )
            donor.stripe_customer_id = customer.id
            db.commit()
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(amount_usd * 100),  # Convert to cents
            currency="usd",
            customer=donor.stripe_customer_id,
            metadata={
                "donor_id": donor_id,
                "campaign_id": campaign_id,
                "campaign_title": campaign.title
            },
            description=f"Donation to {campaign.title}"
        )
        
        # Create pending donation record
        donation = Donation(
            donor_id=donor_id,
            campaign_id=campaign_id,
            amount_usd=amount_usd,
            payment_method="stripe",
            payment_intent_id=intent.id,
            status="pending"
        )
        db.add(donation)
        db.commit()
    
    return {
        "client_secret": intent.client_secret,
        "donation_id": donation.id
    }

async def handle_webhook_event(event: dict):
    """
    Processes Stripe webhook events
    """
    event_type = event["type"]
    
    if event_type == "payment_intent.succeeded":
        intent = event["data"]["object"]
        await process_successful_payment(intent)
    
    elif event_type == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        await process_failed_payment(intent)

async def process_successful_payment(intent: dict):
    """
    Handles successful payment
    """
    with get_db() as db:
        donation = db.query(Donation).filter_by(
            payment_intent_id=intent["id"]
        ).first()
        
        if donation:
            # Update donation
            donation.status = "completed"
            donation.completed_at = datetime.utcnow()
            
            # Update campaign raised amount
            campaign = donation.campaign
            campaign.raised_amount_usd += donation.amount_usd
            
            # Update donor total
            donor = donation.donor
            donor.total_donated_usd += donation.amount_usd
            
            db.commit()
            
            # Create blockchain receipt
            from blockchain.receipt_manager import create_receipt
            await create_receipt(donation.id)
            
            # Send confirmation
            await send_confirmation_message(donation)

async def send_confirmation_message(donation: Donation):
    """
    Sends donation confirmation to donor
    """
    message = f"Thank you for your ${donation.amount_usd:.2f} donation to {donation.campaign.title}! 🎉\n\n"
    message += f"Your impact receipt: {donation.blockchain_receipt_url}\n\n"
    message += "We'll send you updates as the project progresses."
    
    # Send via appropriate channel
    donor = donation.donor
    
    if donor.telegram_user_id:
        from voice.routers.telegram import send_telegram_message
        await send_telegram_message(donor.telegram_user_id, message)
    elif donor.whatsapp_number:
        from voice.routers.whatsapp import send_whatsapp_message
        await send_whatsapp_message(f"whatsapp:{donor.whatsapp_number}", message)
```

`payments/routers.py`:
```python
from fastapi import APIRouter, Request, Header
import stripe
import os

router = APIRouter()

@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None)
):
    """
    Receives Stripe webhook events
    """
    payload = await request.body()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError:
        return {"error": "Invalid payload"}, 400
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}, 400
    
    # Process event
    from payments.stripe_handler import handle_webhook_event
    await handle_webhook_event(event)
    
    return {"status": "success"}
```

---

## Phase 5: Blockchain Receipts (Week 6)

### Step 5.1: Smart Contract

Install: `npm install --save-dev hardhat @openzeppelin/contracts`

`contracts/DonationReceipt.sol`:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DonationReceipt is ERC721, Ownable {
    uint256 private _tokenIdCounter;
    
    struct Receipt {
        uint256 donationId;
        uint256 campaignId;
        uint256 amountUSD;
        uint256 timestamp;
        string metadataURI;
    }
    
    mapping(uint256 => Receipt) public receipts;
    
    event ReceiptMinted(
        uint256 indexed tokenId,
        uint256 donationId,
        uint256 campaignId,
        uint256 amountUSD
    );
    
    constructor() ERC721("TrustVoice Receipt", "TVDR") Ownable(msg.sender) {}
    
    function mintReceipt(
        address donor,
        uint256 donationId,
        uint256 campaignId,
        uint256 amountUSD,
        string memory metadataURI
    ) public onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;
        
        _safeMint(donor, tokenId);
        
        receipts[tokenId] = Receipt({
            donationId: donationId,
            campaignId: campaignId,
            amountUSD: amountUSD,
            timestamp: block.timestamp,
            metadataURI: metadataURI
        });
        
        emit ReceiptMinted(tokenId, donationId, campaignId, amountUSD);
        
        return tokenId;
    }
    
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        return receipts[tokenId].metadataURI;
    }
}
```

Deploy:
```bash
npx hardhat run scripts/deploy.js --network polygon
# Save contract address to .env: RECEIPT_CONTRACT_ADDRESS=0x...
```

### Step 5.2: Receipt Manager

Install: `pip install web3 nft-storage`

`blockchain/receipt_manager.py`:
```python
from web3 import Web3
from eth_account import Account
import os
import json

class ReceiptManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("POLYGON_RPC_URL")))
        self.contract_address = os.getenv("RECEIPT_CONTRACT_ADDRESS")
        
        with open("contracts/artifacts/DonationReceipt.json") as f:
            abi = json.load(f)["abi"]
        
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=abi
        )
        
        self.account = Account.from_key(os.getenv("PLATFORM_PRIVATE_KEY"))
    
    async def create_receipt(self, donation_id: int) -> str:
        """
        Mints blockchain receipt for donation
        """
        from database.db import get_db
        from database.models import Donation
        
        with get_db() as db:
            donation = db.query(Donation).get(donation_id)
            
            # Upload metadata to IPFS
            metadata = {
                "name": f"Donation Receipt #{donation.id}",
                "description": f"${donation.amount_usd} donation to {donation.campaign.title}",
                "image": "ipfs://QmReceipt...",  # Generate receipt image
                "attributes": [
                    {"trait_type": "Campaign", "value": donation.campaign.title},
                    {"trait_type": "Amount USD", "value": str(donation.amount_usd)},
                    {"trait_type": "Date", "value": donation.created_at.isoformat()}
                ]
            }
            
            ipfs_url = await self.upload_to_ipfs(metadata)
            
            # Mint NFT (if donor has wallet)
            if donation.donor.blockchain_wallet_address:
                tx_hash = await self.mint_onchain(
                    donor_address=donation.donor.blockchain_wallet_address,
                    donation_id=donation.id,
                    campaign_id=donation.campaign_id,
                    amount_usd=int(donation.amount_usd * 100),
                    metadata_uri=ipfs_url
                )
            
            # Update donation record
            donation.blockchain_receipt_url = ipfs_url
            db.commit()
        
        return ipfs_url
    
    async def mint_onchain(self, **kwargs) -> str:
        """
        Mints receipt NFT on Polygon
        """
        tx = self.contract.functions.mintReceipt(
            donor=kwargs["donor_address"],
            donationId=kwargs["donation_id"],
            campaignId=kwargs["campaign_id"],
            amountUSD=kwargs["amount_usd"],
            metadataURI=kwargs["metadata_uri"]
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gas": 200000,
            "gasPrice": self.w3.eth.gas_price
        })
        
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        return tx_hash.hex()
    
    async def upload_to_ipfs(self, metadata: dict) -> str:
        """
        Uploads metadata to IPFS via NFT.Storage
        """
        from nft_storage import upload
        
        ipfs_hash = await upload(
            data=json.dumps(metadata),
            api_key=os.getenv("IPFS_API_KEY")
        )
        
        return f"ipfs://{ipfs_hash}"
```

---

## Phase 6: Background Tasks (Week 6)

### Celery Setup

`voice/tasks/voice_tasks.py`:
```python
from celery import Celery
import os

celery_app = Celery(
    "trustvoice",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

@celery_app.task
def process_ivr_recording(phone_number: str, recording_url: str, call_sid: str):
    """
    Background task: Transcribes IVR recording and generates response
    """
    import asyncio
    from voice.ai.speech_handler import transcribe_audio
    from voice.ai.conversation_handler import process_text_input
    from database.db import get_donor_by_phone
    
    # Download audio
    audio_bytes = download_audio(recording_url)
    
    # Transcribe
    transcript = asyncio.run(transcribe_audio(audio_bytes))
    
    # Get donor
    donor = asyncio.run(get_donor_by_phone(phone_number))
    
    # Process with AI
    ai_response = asyncio.run(process_text_input(
        donor_id=donor.id,
        message=transcript,
        channel="ivr",
        session_id=call_sid
    ))
    
    # Call donor back with response
    from voice.routers.ivr import respond_to_donor
    asyncio.run(respond_to_donor(
        To=phone_number,
        Message=ai_response["text"]
    ))

@celery_app.task
def send_impact_notifications(campaign_id: int, verification_id: int):
    """
    Background task: Notifies all donors when impact is verified
    """
    from database.db import get_db
    from database.models import Donation, ImpactVerification
    
    with get_db() as db:
        verification = db.query(ImpactVerification).get(verification_id)
        donations = db.query(Donation).filter_by(
            campaign_id=campaign_id,
            status="completed"
        ).all()
        
        for donation in donations:
            message = f"✅ Impact Update: {verification.description}\n\n"
            message += f"{verification.beneficiary_count} people served!"
            
            # Send notification
            if donation.donor.telegram_user_id:
                send_telegram_message(donation.donor.telegram_user_id, message)

def download_audio(url: str) -> bytes:
    import requests
    response = requests.get(url)
    return response.content
```

Run Celery:
```bash
celery -A voice.tasks.voice_tasks worker -l info
```

---

## Phase 7: Testing & Deployment (Week 7-8)

### Testing

`tests/test_donation_flow.py`:
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_campaign_query():
    """Test campaign information retrieval"""
    response = client.post(
        "/voice/telegram/webhook",
        json={
            "message": {
                "from": {"id": 123, "first_name": "Test"},
                "text": "Tell me about water projects"
            }
        }
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_donation_flow():
    """Test end-to-end donation"""
    from payments.stripe_handler import create_payment_intent
    from database.db import get_db
    from database.models import Donor, Campaign
    
    # Create test donor
    with get_db() as db:
        donor = Donor(telegram_user_id="test_123", preferred_name="Test")
        campaign = Campaign(title="Test Campaign", goal_amount_usd=1000)
        db.add_all([donor, campaign])
        db.commit()
    
    # Create payment intent
    intent = await create_payment_intent(
        donor_id=donor.id,
        campaign_id=campaign.id,
        amount_usd=50
    )
    
    assert intent["client_secret"] is not None
```

Run tests:
```bash
pytest tests/ -v
```

### Deployment

`Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy to Railway:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init

# Add environment variables
railway variables set DATABASE_URL=...
railway variables set OPENAI_API_KEY=...

# Deploy
railway up
```

---

## Success Metrics

**Week 8 MVP should support:**
- ✅ 3 communication channels (IVR, Telegram, WhatsApp)
- ✅ 6 languages (EN, FR, IT, DE, AM, SW)
- ✅ Stripe payments (credit card)
- ✅ Blockchain receipts (Polygon)
- ✅ Impact verification flow
- ✅ Admin dashboard (campaign creation)

**Test with:**
- 1 NGO partner
- 50 test donors
- 3 campaigns
- End-to-end donation + verification

---

## Next Steps After MVP

1. **Analytics Dashboard** - Track donor engagement, campaign performance
2. **Crypto Payments** - Add USDC/ETH support
3. **Video Verification** - Field officers upload videos to IPFS
4. **Recurring Donations** - Stripe subscriptions
5. **WhatsApp Voice** - Support voice messages
6. **Mobile App** (Optional) - React Native for power users

---

## Lab System: Educational Documentation Pattern

**CRITICAL:** TrustVoice should include comprehensive lab guides following the Voice Ledger pattern. Labs serve as:
- Step-by-step implementation guides
- Design decision documentation
- Best practices and gotchas
- Testing and validation procedures

### Lab Structure Template

Each lab should follow this format (4000-6000 lines per major lab):

```markdown
# TrustVoice - Lab X: [Topic Name]

**Learning Objectives:**
- Objective 1 with clear outcome
- Objective 2 with measurable result
- Objective 3 with practical application

**Prerequisites:**
- Previous labs completed
- Required knowledge/tools
- External services needed

**Time Estimate:** X-Y hours
**Difficulty:** Beginner/Intermediate/Advanced

---

## 🎯 Lab Overview: The Problem We're Solving

[Detailed problem description with real-world context]

**What We Had:**
[Description of previous state with limitations]

**The Problem:**
[Clear articulation of issues with examples]

**What We're Building:**
[Solution overview with expected outcomes]

---

## 📋 System Architecture

[Architecture diagrams showing data flow]

### Component Breakdown

[Detailed component explanations]

---

## Step-by-Step Implementation

### Step 1: [Component Name]

**File Created:** `path/to/file.py`

#### 📚 Background: [Conceptual Explanation]

[Why this component exists, design decisions]

#### 💻 Complete Implementation

[Full code with extensive comments]

#### 🧪 Testing

[Test cases and validation steps]

### Step 2: [Next Component]

[Repeat pattern]

---

## Integration & Testing

[How components work together]

---

## Why This Design?

[Design decisions, alternatives considered, trade-offs]

---

## Production Considerations

[Security, scaling, monitoring, costs]

---

## Common Gotchas

[Pitfalls and how to avoid them]
```

### Recommended Lab Sequence for TrustVoice

**Lab 1-2: Foundation (Campaign & Donor Management)**
- Database schema design
- Campaign creation API
- Donor registration flow
- Why PostgreSQL over NoSQL
- Data modeling best practices
- ~5000 lines

**Lab 3: Payment Integration (Stripe)**
- Payment Intent creation
- Webhook handling
- Idempotency keys
- PCI compliance considerations
- Testing with Stripe test mode
- ~3500 lines

**Lab 4: Speech Recognition (User Preference Based)**
- ASR implementation (OpenAI + local models)
- Language routing logic
- Why user preference vs auto-detection
- Cost optimization strategies
- Testing with audio samples
- ~4000 lines

**Lab 5: Conversational AI (Dual-LLM)**
- ConversationManager implementation
- GPT-4 integration (European languages)
- Addis AI integration (Amharic/Swahili)
- Multi-turn dialogue patterns
- Entity collection strategies
- Why two LLMs instead of one
- ~6000 lines

**Lab 6: Multi-Channel Interface**
- IVR implementation (Twilio)
- Telegram bot setup
- WhatsApp Business API
- Channel abstraction layer
- Why phone-based systems matter
- Accessibility considerations
- ~4500 lines

**Lab 7: RAG Implementation (Campaign Context)**
- Pinecone vector database setup
- Campaign content indexing
- Semantic search implementation
- LangChain integration
- Context retrieval strategies
- ~3500 lines

**Lab 8: Blockchain Receipts**
- Smart contract deployment (Polygon)
- NFT minting for donations
- IPFS metadata storage
- Web3.py integration
- Gas optimization techniques
- ~4000 lines

**Lab 9: Impact Verification**
- Field officer voice recording
- GPS verification
- Photo upload to IPFS
- Blockchain anchoring
- Donor notification system
- ~3500 lines

**Lab 10: Testing & Deployment**
- End-to-end test scenarios
- Load testing strategies
- Railway/Render deployment
- Environment configuration
- Monitoring setup (Sentry)
- ~3000 lines

**Lab 11: Analytics & Reporting**
- Donor engagement metrics
- Campaign performance tracking
- Database views and aggregations
- Dashboard API endpoints
- ~2500 lines

**Lab 12: Security & Compliance**
- GDPR implementation
- PCI-DSS considerations
- Data anonymization
- Audit logging
- Penetration testing
- ~3000 lines

### Lab Writing Guidelines

**1. Start with Context (The "Why")**

Bad:
```markdown
## Install Stripe

pip install stripe
```

Good:
```markdown
## Why Stripe for Donation Processing

In TrustVoice, we need a payment processor that:
- Supports international donors (Europe/US)
- Handles multiple currencies (USD, EUR, GBP)
- Provides PCI-DSS Level 1 compliance (so we don't handle card data)
- Offers transparent pricing ($0.30 + 2.9% per transaction)

Alternatives considered:
- PayPal: Higher fees (3.49% + $0.49)
- Braintree: Complex integration
- Direct card processing: Requires PCI compliance (expensive)

Stripe wins because...

Now let's install it:
pip install stripe
```

**2. Include Real-World Scenarios**

```markdown
## Example: Donor Journey from Berlin

Sarah in Berlin wants to donate €100 to Mwanza Water Project:

1. Opens WhatsApp, sends: "Tell me about water projects"
2. AI responds in German (her registered language): "..."
3. Sarah: "Ich möchte 100 Euro spenden"
4. AI: "Perfekt! Hier ist der Zahlungslink..."
5. Stripe processes €100 → $108.50 USD
6. System mints blockchain receipt NFT
7. Sarah receives WhatsApp confirmation with receipt link

Let's implement this flow...
```

**3. Show Design Alternatives**

```markdown
## Design Decision: Language Routing

**Option 1: Auto-Detection**
Pros: No user input needed
Cons: Lower accuracy (testing showed issues), costly re-attempts
Cost: Higher due to detection + potential re-transcription

**Option 2: User Preference (CHOSEN)**
Pros: More reliable, set once during registration
Cons: Requires one-time language selection
Cost: Lower (single transcription)

We chose Option 2 because...
```

**4. Include Troubleshooting**

```markdown
## Common Gotchas

### Problem: Twilio webhook returns 500 error

**Symptom:**
Donor calls IVR, hears "An application error occurred"

**Cause:**
Database connection not closed properly

**Solution:**
Always use context manager:
```python
with get_db() as db:
    donor = db.query(Donor).filter_by(phone=phone).first()
# Connection auto-closed here
```

Don't do this:
```python
db = SessionLocal()
donor = db.query(Donor).filter_by(phone=phone).first()
# Connection never closed! Memory leak!
```
```

**5. Emphasize Production Readiness**

```markdown
## Production Considerations

**Security:**
- ✅ All API keys in environment variables (never committed)
- ✅ Stripe webhook signature verification
- ✅ HTTPS only for all endpoints
- ✅ Rate limiting on donation endpoints (10/min per donor)

**Scalability:**
- Conversation state in Redis (not in-memory)
- Database connection pooling (10 connections)
- Celery for async tasks (receipt minting)
- Can handle 1000 concurrent donors

**Monitoring:**
- Sentry for error tracking
- Stripe dashboard for payment monitoring
- Custom metrics for donor engagement
- Alert on failed donations
```

**6. Include Cost Analysis**

```markdown
## Cost Breakdown (500 Active Donors/Month)

**Infrastructure:**
- Railway hosting: $50/month
- Neon PostgreSQL: $20/month
- Redis Cloud: $10/month

**APIs:**
- OpenAI GPT-4: $300 (1500 conversations @ $0.20)
- Addis AI: $100 (500 Amharic conversations @ $0.20)
- Whisper ASR: $150 (3000 transcriptions @ $0.05)
- Twilio Voice: $200 (500 minutes @ $0.40/min)
- ElevenLabs TTS: $80 (400K characters)

**Payments:**
- Stripe: 2.9% + $0.30 per donation (variable)
- Polygon gas: $30 (100 receipt NFTs @ $0.30)

**Total Fixed: ~$940/month**
**Break-even: 15 NGOs @ $70/month**
```

### Lab Distribution Strategy

**Phase 1 (Week 1-2): Foundation Labs**
- Labs 1-2: Database & API basics
- Get developers familiar with stack
- Establish patterns

**Phase 2 (Week 3-5): Core Features**
- Labs 3-6: Payments, voice, AI
- Build the MVP functionality
- Test with real audio

**Phase 3 (Week 6-7): Blockchain & Verification**
- Labs 7-9: IPFS, blockchain, impact tracking
- Complete the trust layer

**Phase 4 (Week 8): Production**
- Labs 10-12: Deployment, security, monitoring
- Launch-ready system

### Documentation Standards

**Code Comments:**
```python
def create_payment_intent(donor_id: int, amount: float) -> Dict:
    """
    Create Stripe Payment Intent for donation.
    
    This function generates a payment intent that the donor client
    uses to collect payment information securely. We never handle
    raw card data - Stripe does that (PCI compliance).
    
    Args:
        donor_id: Database ID of donor
        amount: Donation amount in USD
    
    Returns:
        {
            'client_secret': 'pi_xxx_secret_xxx',
            'donation_id': 123
        }
    
    Raises:
        stripe.error.StripeError: If Stripe API fails
        
    Example:
        >>> intent = create_payment_intent(donor_id=5, amount=100.0)
        >>> print(intent['client_secret'])
        pi_1A2B3C_secret_4D5E6F
    
    Security:
        - Client secret is single-use
        - Expires after 24 hours
        - Can only be used with matching payment method
    """
```

**Section Headers:**
- 🎯 = Lab objective/goal
- 📚 = Background/theory
- 💻 = Code implementation
- 🧪 = Testing/validation
- ⚠️ = Warning/gotcha
- ✅ = Verification/success criteria
- 🔒 = Security consideration
- 💰 = Cost implication
- 🚀 = Performance optimization

### Lab Review Checklist

Before marking a lab complete:

- [ ] All code is production-ready (no TODOs)
- [ ] Design decisions explained
- [ ] Alternatives discussed with trade-offs
- [ ] Real-world examples included
- [ ] Common errors documented
- [ ] Security considerations covered
- [ ] Cost analysis provided
- [ ] Testing procedures complete
- [ ] Integration with other labs verified
- [ ] Accessibility implications discussed (if applicable)

---

**This prompt provides complete instructions to build TrustVoice MVP in 8 weeks, including comprehensive lab documentation following the Voice Ledger pattern. Total documentation: ~45,000 lines across 12 labs. Estimated cost: $1,000/month for 500 active donors.**
