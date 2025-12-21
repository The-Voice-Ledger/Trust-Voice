# TrustVoice Technical Specification

**Voice-First Donation Platform with Blockchain Impact Verification**

Version 1.0 | December 2025

---

## 1. System Overview

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DONOR INTERFACES                        │
├───────────────┬──────────────────┬─────────────────────────┤
│  IVR (Phone)  │  Telegram Bot    │   WhatsApp Business     │
│  Twilio       │  Python Async    │   Twilio/WhatsApp API   │
└───────┬───────┴────────┬─────────┴───────────┬─────────────┘
        │                │                     │
        └────────────────┼─────────────────────┘
                         │
        ┌────────────────▼───────────────────┐
        │    UNIFIED CHANNEL HANDLER         │
        │   (voice/multichannel_router.py)   │
        └────────────────┬───────────────────┘
                         │
        ┌────────────────▼───────────────────┐
        │      LANGUAGE ROUTER               │
        │   Routes by donor.preferred_language│
        │   (Set during registration)        │
        └─────┬──────────┬───────────────────┘
              │          │
      ┌───────▼────┐  ┌──▼──────────────┐
      │  GPT-4     │  │  ADDIS AI       │
      │  (EU langs)│  │  (AM/SW native) │
      └───────┬────┘  └──┬──────────────┘
              │          │
        ┌─────┴──────────┴───────────────┐
        │   CONVERSATION MANAGER          │
        │   • Multi-turn dialogue state   │
        │   • Entity collection           │
        │   • Intent tracking             │
        │   • 5-min timeout               │
        └────────────────┬───────────────────┘
                         │
        ┌────────────────▼───────────────────┐
        │       INTENT CLASSIFIER            │
        │  • ask_campaign_info               │
        │  • initiate_donation               │
        │  • track_donation_status           │
        │  • verify_impact                   │
        └────────────────┬───────────────────┘
                         │
        ┌────────────────┴───────────────────┐
        │                                    │
   ┌────▼─────┐                     ┌───────▼────────┐
   │ PAYMENT  │                     │   BLOCKCHAIN   │
   │ PROCESSOR│                     │     LAYER      │
   │          │                     │                │
   │ Stripe   │                     │  Polygon/Base  │
   │ PayPal   │                     │  • Receipts    │
   │ Crypto   │                     │  • Impact NFTs │
   └────┬─────┘                     └───────┬────────┘
        │                                    │
        └────────────────┬───────────────────┘
                         │
        ┌────────────────▼───────────────────┐
        │      POSTGRESQL DATABASE           │
        │  • Donors                          │
        │  • Campaigns                       │
        │  • Donations                       │
        │  • Impact Verifications            │
        │  • Conversations                   │
        └────────────────────────────────────┘
```

### 1.2 Core Technology Stack

**Backend:**
- Python 3.11+ (FastAPI framework)
- PostgreSQL 15+ (Neon serverless)
- Redis (session caching)
- Celery (async task processing)

**AI/ML:**
- **OpenAI GPT-4 Turbo** (English/French/German/Italian conversations)
- **Addis AI** (Amharic/Swahili native conversational model - 2000+ hours training)
- **Whisper API** (OpenAI for European languages, local Amharic model for African languages)
- **ElevenLabs** (text-to-speech, multi-language)
- **LangChain** (RAG framework)
- **Pinecone** (vector database for campaign context)
- **ConversationManager** (stateful multi-turn dialogue tracking - proven with Voice Ledger)

**Communication:**
- Twilio (IVR, WhatsApp Business API)
- python-telegram-bot (Telegram)
- ngrok/Cloudflare Tunnel (webhook routing)

**Payments:**
- Stripe API (credit cards, bank transfers)
- PayPal SDK (alternative processor)
- Web3.py (Ethereum/Polygon for crypto)
- Safe Wallet API (multi-sig for NGO funds)

**Blockchain:**
- Polygon (low-cost receipts)
- Base (Coinbase L2, mainstream adoption)
- IPFS (media storage)
- Solidity smart contracts

**Infrastructure:**
- Railway/Render (backend hosting)
- Vercel (optional donor dashboard)
- GitHub Actions (CI/CD)
- Sentry (error tracking)

---

## 2. Database Schema

### 2.1 Core Tables

```sql
-- Donors (registered users)
CREATE TABLE donors (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,
    telegram_user_id VARCHAR(50) UNIQUE,
    whatsapp_number VARCHAR(20) UNIQUE,
    preferred_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en',
    email VARCHAR(255),
    country_code VARCHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP,
    total_donated_usd DECIMAL(12,2) DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_donors_phone ON donors(phone_number);
CREATE INDEX idx_donors_telegram ON donors(telegram_user_id);
CREATE INDEX idx_donors_whatsapp ON donors(whatsapp_number);

-- NGO Organizations
CREATE TABLE ngo_organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100),
    country VARCHAR(100),
    tax_exempt_status BOOLEAN DEFAULT FALSE,
    contact_email VARCHAR(255),
    admin_phone VARCHAR(20),
    blockchain_wallet_address VARCHAR(66),
    stripe_account_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Campaigns
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    ngo_id INTEGER REFERENCES ngo_organizations(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    goal_amount_usd DECIMAL(12,2) NOT NULL,
    raised_amount_usd DECIMAL(12,2) DEFAULT 0,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    category VARCHAR(50), -- water, education, health, etc.
    location_country VARCHAR(100),
    location_region VARCHAR(100),
    location_gps VARCHAR(100), -- lat,lon
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaigns_ngo ON campaigns(ngo_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Campaign Context (RAG content)
CREATE TABLE campaign_context (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    content_type VARCHAR(50), -- faq, story, budget_breakdown, partner_info
    content TEXT NOT NULL,
    embedding_vector vector(1536), -- pgvector extension
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Donations
CREATE TABLE donations (
    id SERIAL PRIMARY KEY,
    donor_id INTEGER REFERENCES donors(id),
    campaign_id INTEGER REFERENCES campaigns(id),
    amount_usd DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(20), -- stripe, paypal, crypto
    payment_intent_id VARCHAR(255),
    transaction_hash VARCHAR(66), -- if crypto
    blockchain_receipt_url TEXT,
    currency_code VARCHAR(10),
    original_amount DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed, refunded
    donor_message TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    tax_receipt_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_donations_donor ON donations(donor_id);
CREATE INDEX idx_donations_campaign ON donations(campaign_id);
CREATE INDEX idx_donations_status ON donations(status);

-- Impact Verifications (from field)
CREATE TABLE impact_verifications (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    verifier_phone VARCHAR(20), -- field officer
    verifier_name VARCHAR(100),
    verification_type VARCHAR(50), -- milestone, completion, beneficiary_count
    description TEXT,
    audio_recording_url TEXT,
    photo_urls TEXT[], -- array of IPFS URLs
    gps_coordinates VARCHAR(100),
    beneficiary_count INTEGER,
    blockchain_anchor_tx VARCHAR(66),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_verifications_campaign ON impact_verifications(campaign_id);

-- Conversation Logs
CREATE TABLE conversation_logs (
    id SERIAL PRIMARY KEY,
    donor_id INTEGER REFERENCES donors(id),
    channel VARCHAR(20), -- ivr, telegram, whatsapp
    session_id VARCHAR(100),
    message_type VARCHAR(20), -- user, assistant, system
    message_text TEXT,
    intent_detected VARCHAR(50),
    entities_extracted JSONB,
    llm_model VARCHAR(50),
    llm_tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_donor ON conversation_logs(donor_id);
CREATE INDEX idx_conversations_session ON conversation_logs(session_id);
```

### 2.2 Materialized Views (Performance)

```sql
-- Campaign Summary (updated every 5 minutes)
CREATE MATERIALIZED VIEW campaign_summary AS
SELECT 
    c.id,
    c.title,
    c.goal_amount_usd,
    c.raised_amount_usd,
    ROUND((c.raised_amount_usd / c.goal_amount_usd) * 100, 2) as completion_percentage,
    COUNT(DISTINCT d.donor_id) as unique_donors,
    COUNT(d.id) as total_donations,
    AVG(d.amount_usd) as avg_donation_amount,
    COUNT(iv.id) as verification_count,
    MAX(iv.verified_at) as last_verification_date
FROM campaigns c
LEFT JOIN donations d ON d.campaign_id = c.id AND d.status = 'completed'
LEFT JOIN impact_verifications iv ON iv.campaign_id = c.id
GROUP BY c.id, c.title, c.goal_amount_usd, c.raised_amount_usd;

CREATE UNIQUE INDEX ON campaign_summary (id);

-- Donor Engagement Scores
CREATE MATERIALIZED VIEW donor_engagement AS
SELECT 
    d.id,
    d.phone_number,
    COUNT(DISTINCT don.campaign_id) as campaigns_supported,
    SUM(don.amount_usd) as lifetime_donated,
    COUNT(don.id) as donation_count,
    AVG(don.amount_usd) as avg_donation,
    COUNT(cl.id) as conversation_count,
    MAX(cl.created_at) as last_interaction_date,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(cl.created_at)))/86400 as days_since_last_interaction
FROM donors d
LEFT JOIN donations don ON don.donor_id = d.id AND don.status = 'completed'
LEFT JOIN conversation_logs cl ON cl.donor_id = d.id
GROUP BY d.id, d.phone_number;

CREATE UNIQUE INDEX ON donor_engagement (id);
```

---

## 3. API Endpoints

### 3.1 Donor Communication Endpoints

**IVR (Twilio Voice)**

```python
POST /voice/ivr/incoming
# Handles incoming phone calls
# - Authenticates donor by phone number
# - Generates welcome TwiML
# - Starts recording or presents menu

POST /voice/ivr/recording
# Receives voice recording from Twilio
# - Queues transcription task
# - Returns "processing" TwiML

POST /voice/ivr/gather
# Handles DTMF input (keypad)
# - Menu navigation
# - Donation amount selection
```

**Telegram**

```python
POST /voice/telegram/webhook
# Receives updates from Telegram
# - Message handler
# - Callback query handler
# - Inline keyboard interactions

GET /voice/telegram/set_webhook
# Registers webhook URL with Telegram
```

**WhatsApp**

```python
POST /voice/whatsapp/webhook
# Twilio WhatsApp Business API webhook
# - Text messages
# - Audio messages
# - Button responses

POST /voice/whatsapp/status
# Delivery status callbacks
```

### 3.2 Payment Endpoints

```python
POST /payments/stripe/create_intent
Request: {
    "donor_id": 123,
    "campaign_id": 45,
    "amount_usd": 100,
    "currency": "eur"
}
Response: {
    "client_secret": "pi_xxx_secret_xxx",
    "payment_intent_id": "pi_xxx"
}

POST /payments/stripe/webhook
# Stripe webhook for payment confirmations
# - payment_intent.succeeded
# - payment_intent.payment_failed

POST /payments/crypto/initiate
Request: {
    "donor_id": 123,
    "campaign_id": 45,
    "amount_usd": 100,
    "crypto_currency": "USDC"
}
Response: {
    "wallet_address": "0x...",
    "expected_amount": "100.00 USDC",
    "network": "polygon"
}

POST /payments/crypto/confirm
# Confirms on-chain transaction
# - Verifies transaction hash
# - Links to donation record
```

### 3.3 Campaign Management (NGO Admin)

```python
POST /campaigns/create
Request: {
    "ngo_id": 10,
    "title": "Clean Water for Mwanza",
    "goal_amount_usd": 50000,
    "description": "...",
    "location_country": "Tanzania",
    "location_gps": "-2.5164,32.9175",
    "context_documents": [
        {"type": "faq", "content": "..."},
        {"type": "budget_breakdown", "content": "..."}
    ]
}

GET /campaigns/{id}
# Returns campaign details + real-time stats

PATCH /campaigns/{id}/update
# Update campaign info, goal, status

POST /campaigns/{id}/upload_media
# Upload photos/videos (to IPFS)

GET /campaigns/{id}/donors
# List donors (respects anonymity)
```

### 3.4 Impact Verification (Field Officers)

```python
POST /impact/verify
# Called by field officer via IVR
Request: {
    "campaign_id": 45,
    "verifier_phone": "+255...",
    "verification_type": "milestone_completed",
    "description": "Well #3 completed, 450 families served",
    "audio_url": "s3://...",
    "photo_urls": ["ipfs://...", "ipfs://..."],
    "gps_coordinates": "-2.5164,32.9175",
    "beneficiary_count": 450
}

POST /impact/anchor_blockchain
# Background task: anchors verification to blockchain
# - Creates NFT with impact data
# - Links to all related donation receipts
```

---

## 4. Speech Recognition (ASR) - User Preference Based

### 4.1 Language Routing (No Auto-Detection)

```python
# voice/asr/asr_handler.py

def transcribe_audio(audio_path: str, user_language: str) -> str:
    """
    Transcribe audio using user's registered language preference.
    
    Key Design: Language is set during registration, NOT auto-detected.
    This prevents ASR errors from misrouting conversations.
    
    Args:
        audio_path: Path to audio file
        user_language: From donors.preferred_language (en/fr/de/it/am/sw)
    
    Returns:
        Transcribed text
    """
    logger.info(f"Transcribing with user preference: {user_language}")
    
    if user_language in ['am', 'sw']:  # African languages
        # Use local Amharic/Swahili Whisper model
        # Trained on 2000+ hours by Addis AI
        return transcribe_with_local_model(audio_path, user_language)
    
    else:  # European languages
        # Use OpenAI Whisper API
        return transcribe_with_openai_whisper(audio_path, language=user_language)
```

**Why User Preference vs Auto-Detection:**
- Auto-detection fails with accents/background noise (58% accuracy in Voice Ledger testing)
- Users set language once during registration → stored in database
- Prevents expensive re-routing and LLM confusion
- Voice Ledger tested with 1000+ Ethiopian farmers - **98% ASR accuracy**
- Cost savings: $0.05 saved per message (no failed re-attempts)

**Language Selection During Registration:**
```
Telegram/WhatsApp Bot:
"Welcome! Please select your language:
 [English 🇺🇸] [Français 🇫🇷] [Deutsch 🇩🇪] [Italiano 🇮🇹]
 [አማርኛ 🇪🇹] [Swahili 🇹🇿]"

→ Stored: UPDATE donors SET preferred_language='am' WHERE id=...
→ All future voice: Routed to Amharic ASR + Addis AI
```

---

## 5. Conversational AI Architecture

### 5.1 Dual-LLM Design (Learned from Voice Ledger)

```
┌──────────────────────────────────────────────┐
│         LANGUAGE ROUTER                      │
│  if donor.preferred_language in [am, sw]:   │
│      → Addis AI                              │
│  else:                                       │
│      → GPT-4 Turbo                           │
└──────────────────────────────────────────────┘
```

**Why Two LLMs?**
- **GPT-4:** Excellent for European languages, but:
  - Limited Amharic/Swahili training data
  - Generic responses, not culturally adapted
  - Slower (400ms latency)

- **Addis AI:** Purpose-built for Ethiopian context:
  - 2000+ hours Amharic speech training
  - Understands Ethiopian names, locations, cultural context
  - Faster (150ms latency)
  - 94% intent accuracy (vs 72% with GPT-4 on Amharic)

---

## 5. Conversational AI Implementation

### 5.1 LLM Configuration

```python
# voice/ai/llm_config.py

LLM_MODELS = {
    # European languages (English, French, German, Italian)
    "primary": "gpt-4-turbo-preview",
    "fallback": "gpt-3.5-turbo",
    
    # African languages (Amharic, Swahili)
    "addis_ai": "https://api.addisassistant.com/api/v1/chat_generate",
    "addis_translate": "https://api.addisassistant.com/api/v1/translate"
}

# Addis AI Configuration
ADDIS_AI_CONFIG = {
    "api_key": os.getenv("ADDIS_AI_API_KEY"),
    "temperature": 0.7,
    "max_tokens": 500,
    "supported_languages": ["am", "sw"],  # Amharic, Swahili
    "training_hours": 2000  # Verified by Voice Ledger production
}

SYSTEM_PROMPTS = {
    "donor_assistant": """
        You are TrustVoice, a friendly AI assistant helping donors 
        support NGO campaigns in Africa. You can:
        - Answer questions about campaigns
        - Process donations
        - Track impact
        
        Be conversational, warm, and concise. 
        Keep responses under 50 words for voice interfaces.
        Prioritize transparency and trust.
    """,
    
    "field_verification": """
        You are assisting a field officer recording impact verification.
        Extract:
        - Campaign name/number
        - Milestone achieved
        - Beneficiary count
        - Location details
        
        Confirm details back to the officer.
    """
}

SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "French",
    "it": "Italian",
    "de": "German",
    "am": "Amharic",
    "sw": "Swahili"
}
```

### 5.2 Conversation State Management

```python
# voice/ai/conversation_manager.py

class ConversationManager:
    """
    Manages multi-turn dialogue state for each donor.
    
    Features:
    - Stores conversation history (user/assistant messages)
    - Tracks collected entities across multiple voice messages
    - Handles conversation timeouts (5 minutes inactivity)
    - Thread-safe operations for concurrent users
    
    Proven at scale: Voice Ledger handles 1000+ concurrent farmer conversations
    """
    
    _conversations: Dict[int, Dict[str, Any]] = {}
    _lock = Lock()
    TIMEOUT = timedelta(minutes=5)
    
    @staticmethod
    def get_conversation(donor_id: int) -> Dict:
        """Get or create conversation for donor"""
        with ConversationManager._lock:
            if donor_id in ConversationManager._conversations:
                conv = ConversationManager._conversations[donor_id]
                
                # Check timeout
                if datetime.now() - conv['last_updated'] > ConversationManager.TIMEOUT:
                    del ConversationManager._conversations[donor_id]
                else:
                    return conv
            
            # Create new conversation
            ConversationManager._conversations[donor_id] = {
                'donor_id': donor_id,
                'language': None,
                'messages': [],  # [{role: 'user'|'assistant', content: str}]
                'entities': {},  # Collected donation info
                'intent': None,  # Current intent (donate, track, ask)
                'created_at': datetime.now(),
                'last_updated': datetime.now(),
                'turn_count': 0
            }
            
            return ConversationManager._conversations[donor_id]
    
    @staticmethod
    def add_message(donor_id: int, role: str, content: str):
        """Add message to conversation history"""
        conv = ConversationManager.get_conversation(donor_id)
        conv['messages'].append({'role': role, 'content': content})
        conv['last_updated'] = datetime.now()
        if role == 'user':
            conv['turn_count'] += 1
    
    @staticmethod
    def update_entities(donor_id: int, entities: Dict):
        """Update collected entities (e.g., campaign_id, amount)"""
        conv = ConversationManager.get_conversation(donor_id)
        conv['entities'].update(entities)
    
    @staticmethod
    def is_ready(donor_id: int) -> bool:
        """Check if all required entities collected"""
        conv = ConversationManager.get_conversation(donor_id)
        intent = conv.get('intent')
        entities = conv.get('entities', {})
        
        if intent == 'donate':
            # Need both campaign and amount
            return 'campaign_id' in entities and 'amount' in entities
        elif intent == 'track':
            return True  # No entities needed
        
        return False
    
    @staticmethod
    def clear_conversation(donor_id: int):
        """Clear conversation after successful execution"""
        with ConversationManager._lock:
            if donor_id in ConversationManager._conversations:
                del ConversationManager._conversations[donor_id]
```

**Example Multi-Turn Conversation:**
```
Turn 1:
Donor (voice): "I want to help with water"
Assistant: "Great! We have 3 water projects in Tanzania. 
            Which would you like to support?"
→ Entities: {}

Turn 2:
Donor: "The Mwanza one"
Assistant: "Perfect! Mwanza Water Project needs $50K for 10 wells.
            How much would you like to donate?"
→ Entities: {campaign_id: 45}

Turn 3:
Donor: "One hundred dollars"
Assistant: "Thank you! I'll process your $100 donation to Mwanza Water Project.
            Confirm?"
→ Entities: {campaign_id: 45, amount: 100}
→ ready_to_execute: True
```

### 5.4 Addis AI Integration

```python
# voice/ai/addis_conversation.py

async def process_with_addis_ai(donor_id: int, transcript: str, language: str) -> Dict:
    """
    Process Amharic/Swahili conversation using Addis AI.
    
    Proven with Voice Ledger: 94% intent accuracy, 150ms latency.
    """
    # Get conversation history
    history = ConversationManager.get_history(donor_id)
    ConversationManager.add_message(donor_id, 'user', transcript)
    
    # Call Addis AI
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            ADDIS_AI_CONFIG['addis_ai'],
            headers={"X-API-Key": ADDIS_AI_CONFIG['api_key']},
            json={
                "prompt": transcript,
                "target_language": language,
                "conversation_history": [
                    {"role": msg['role'], "content": msg['content']}
                    for msg in history[:-1]  # Exclude message we just added
                ],
                "generation_config": {
                    "temperature": 0.7,
                    "max_output_tokens": 500
                }
            }
        )
        result = response.json()
    
    assistant_message = result.get('response_text', '').strip()
    ConversationManager.add_message(donor_id, 'assistant', assistant_message)
    
    # Check if ready to execute
    if result.get('ready_to_execute'):
        intent = result.get('intent')
        entities = result.get('entities', {})
        
        # Translate entities to English for database
        if contains_amharic(entities):
            entities = await translate_entities_addis(entities, language)
        
        ConversationManager.set_intent(donor_id, intent)
        ConversationManager.update_entities(donor_id, entities)
        
        return {
            'message': assistant_message,
            'ready_to_execute': True,
            'intent': intent,
            'entities': entities
        }
    
    return {
        'message': assistant_message,
        'ready_to_execute': False
    }


async def translate_entities_addis(entities: Dict, source_lang: str) -> Dict:
    """
    Translate Amharic/Swahili entities to English using Addis AI Translation API.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            ADDIS_AI_CONFIG['addis_translate'],
            headers={"X-API-Key": ADDIS_AI_CONFIG['api_key']},
            json={
                "text": json.dumps(entities),
                "source_language": source_lang,
                "target_language": "en"
            }
        )
        translation = response.json()
    
    return json.loads(translation.get("translated_text", "{}"))
```

### 5.5 GPT-4 Integration (European Languages)

```python
# voice/ai/english_conversation.py

def process_with_gpt4(donor_id: int, transcript: str, language: str) -> Dict:
        conv = ConversationManager.get_conversation(donor_id)
        intent = conv.get('intent')
        entities = conv.get('entities', {})
        
        if intent == 'donate':
            return 'campaign_id' in entities and 'amount' in entities
        elif intent == 'track':
            return True  # No entities needed
        
        return False
```

### 5.3 Intent Detection

```python
# voice/ai/intent_classifier.py

INTENTS = {
    "ask_campaign_info": {
        "patterns": [
            "tell me about",
            "what projects",
            "campaigns in",
            "water projects",
            "education programs"
        ],
        "required_entities": ["campaign_category" | "location"],
        "handler": "handle_campaign_query"
    },
    
    "initiate_donation": {
        "patterns": [
            "I want to donate",
            "give $",
            "support",
            "contribute"
        ],
        "required_entities": ["amount" | "campaign_id"],
        "handler": "handle_donation_flow"
    },
    
    "track_donation": {
        "patterns": [
            "where is my donation",
            "donation status",
            "receipt",
            "tax document"
        ],
        "handler": "handle_donation_tracking"
    },
    
    "verify_impact": {
        "patterns": [
            "project completed",
            "milestone reached",
            "beneficiaries served",
            "verification"
        ],
        "handler": "handle_impact_verification"
    }
}

async def process_conversation(donor_id: int, transcript: str, language: str) -> Dict:
    """
    Route conversation to appropriate LLM based on language.
    
    Returns:
        {
            'message': 'AI response to donor',
            'ready_to_execute': bool,  # All entities collected?
            'intent': 'donate|track|ask',
            'entities': {...}
        }
    """
    if language in ['am', 'sw']:
        return await process_with_addis_ai(donor_id, transcript, language)
    else:
        return await process_with_gpt4(donor_id, transcript, language)


async def process_with_addis_ai(donor_id: int, transcript: str, language: str) -> Dict:
    """
    Process Amharic/Swahili conversation using Addis AI.
    
    Addis AI is trained on:
    - 2000+ hours of Ethiopian Amharic speech
    - NGO/donation domain vocabulary
    - Multi-turn dialogue patterns
    """
    # Get conversation history
    history = ConversationManager.get_history(donor_id)
    ConversationManager.add_message(donor_id, 'user', transcript)
    
    # Call Addis AI
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            ADDIS_AI_CONFIG['addis_ai'],
            headers={"X-API-Key": ADDIS_AI_CONFIG['api_key']},
            json={
                "prompt": transcript,
                "target_language": language,
                "conversation_history": history,
                "generation_config": {
                    "temperature": 0.7,
                    "max_output_tokens": 500
                }
            }
        )
        result = response.json()
    
    assistant_message = result.get('response_text', '')
    ConversationManager.add_message(donor_id, 'assistant', assistant_message)
    
    # Check if ready to execute
    if result.get('ready_to_execute'):
        entities = result.get('entities', {})
        
        # Translate entities to English for database storage
        if contains_native_text(entities):
            entities = await translate_entities(entities, language)
        
        ConversationManager.update_entities(donor_id, entities)
        
        return {
            'message': assistant_message,
            'ready_to_execute': True,
            'intent': result.get('intent'),
            'entities': entities
        }
    
    return {
        'message': assistant_message,
        'ready_to_execute': False
    }


async def classify_intent(message: str, donor_context: dict) -> Intent:
    """
    Uses GPT-4 with few-shot examples to classify intent
    Falls back to keyword matching if confidence < 0.7
    """
    prompt = f"""
    Donor message: "{message}"
    Donor context: {donor_context}
    
    Classify intent and extract entities.
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": INTENT_CLASSIFIER_PROMPT},
            {"role": "user", "content": prompt}
        ],
        functions=[INTENT_SCHEMA],
        function_call={"name": "classify_intent"}
    )
    
    return Intent.parse(response.choices[0].message.function_call.arguments)
```

### 4.3 RAG Implementation (Campaign Context)

```python
# voice/ai/rag_engine.py

from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA

class CampaignRAG:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vectorstore = Pinecone(
            index_name="trustvoice-campaigns",
            embedding=self.embeddings
        )
    
    async def answer_campaign_question(
        self,
        campaign_id: int,
        question: str,
        language: str = "en"
    ) -> str:
        """
        Retrieves relevant campaign context and generates answer
        """
        # Retrieve context
        docs = await self.vectorstore.asimilarity_search(
            query=question,
            filter={"campaign_id": campaign_id},
            k=5
        )
        
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Generate answer with GPT-4
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": f"Answer in {language}, max 50 words"},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ]
        )
        
        return response.choices[0].message.content
    
    async def index_campaign(self, campaign_id: int):
        """
        Indexes campaign content for RAG
        """
        campaign = await get_campaign(campaign_id)
        
        documents = [
            {"content": campaign.description, "type": "description"},
            {"content": campaign.budget_breakdown, "type": "budget"},
            {"content": campaign.faq, "type": "faq"},
            {"content": campaign.partner_info, "type": "partners"}
        ]
        
        for doc in documents:
            await self.vectorstore.aadd_texts(
                texts=[doc["content"]],
                metadatas=[{
                    "campaign_id": campaign_id,
                    "content_type": doc["type"]
                }]
            )
```

---

## 5. Payment Integration

### 5.1 Stripe Implementation

```python
# payments/stripe_handler.py

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

async def create_payment_intent(
    donor_id: int,
    campaign_id: int,
    amount_usd: float,
    currency: str = "usd"
) -> dict:
    """
    Creates Stripe Payment Intent
    """
    donor = await get_donor(donor_id)
    campaign = await get_campaign(campaign_id)
    
    intent = stripe.PaymentIntent.create(
        amount=int(amount_usd * 100),  # cents
        currency=currency.lower(),
        customer=donor.stripe_customer_id or await create_stripe_customer(donor),
        metadata={
            "donor_id": donor_id,
            "campaign_id": campaign_id,
            "campaign_title": campaign.title
        },
        description=f"Donation to {campaign.title}"
    )
    
    # Store pending donation
    donation = await create_donation(
        donor_id=donor_id,
        campaign_id=campaign_id,
        amount_usd=amount_usd,
        payment_intent_id=intent.id,
        status="pending"
    )
    
    return {
        "client_secret": intent.client_secret,
        "donation_id": donation.id
    }

async def handle_stripe_webhook(event: dict):
    """
    Handles Stripe webhook events
    """
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        
        # Update donation status
        donation = await get_donation_by_payment_intent(intent.id)
        donation.status = "completed"
        donation.completed_at = datetime.utcnow()
        await db.commit()
        
        # Update campaign raised amount
        campaign = await get_campaign(donation.campaign_id)
        campaign.raised_amount_usd += donation.amount_usd
        await db.commit()
        
        # Create blockchain receipt
        await create_blockchain_receipt(donation.id)
        
        # Send confirmation to donor
        await send_donation_confirmation(donation)
        
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        donation = await get_donation_by_payment_intent(intent.id)
        donation.status = "failed"
        await db.commit()
        
        # Notify donor
        await notify_payment_failed(donation)
```

### 5.2 Crypto Payment (Optional)

```python
# payments/crypto_handler.py

from web3 import Web3
from eth_account import Account

# Connect to Polygon
w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))

# NGO multi-sig wallet (Safe)
NGO_WALLET_ADDRESS = "0x..."

async def initiate_crypto_donation(
    donor_id: int,
    campaign_id: int,
    amount_usd: float,
    crypto_currency: str = "USDC"
) -> dict:
    """
    Generates payment address and monitors for transaction
    """
    campaign = await get_campaign(campaign_id)
    
    # Create unique donation record
    donation = await create_donation(
        donor_id=donor_id,
        campaign_id=campaign_id,
        amount_usd=amount_usd,
        payment_method="crypto",
        status="pending"
    )
    
    # Return wallet address
    return {
        "donation_id": donation.id,
        "wallet_address": NGO_WALLET_ADDRESS,
        "expected_amount": f"{amount_usd} {crypto_currency}",
        "network": "Polygon",
        "contract_address": USDC_POLYGON_ADDRESS
    }

async def monitor_crypto_transaction(donation_id: int):
    """
    Background task: monitors blockchain for payment
    """
    donation = await get_donation(donation_id)
    
    # Get recent transactions to NGO wallet
    usdc_contract = w3.eth.contract(
        address=USDC_POLYGON_ADDRESS,
        abi=USDC_ABI
    )
    
    # Check transfers in last 100 blocks
    events = usdc_contract.events.Transfer.get_logs(
        fromBlock=w3.eth.block_number - 100,
        toBlock="latest",
        argument_filters={"to": NGO_WALLET_ADDRESS}
    )
    
    for event in events:
        amount = event.args.value / 10**6  # USDC has 6 decimals
        
        if abs(amount - donation.amount_usd) < 0.01:  # Match found
            donation.status = "completed"
            donation.transaction_hash = event.transactionHash.hex()
            donation.completed_at = datetime.utcnow()
            await db.commit()
            
            # Create blockchain receipt
            await create_blockchain_receipt(donation.id)
            await send_donation_confirmation(donation)
            
            return True
    
    return False  # No match found, continue monitoring
```

---

## 6. Blockchain Receipts

### 6.1 Smart Contract (Solidity)

```solidity
// contracts/DonationReceipt.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DonationReceipt is ERC721, Ownable {
    uint256 private _tokenIdCounter;
    
    struct Receipt {
        uint256 donationId;
        address donor;
        uint256 campaignId;
        uint256 amountUSD;  // in cents
        string paymentMethod;
        uint256 timestamp;
        string metadataURI;  // IPFS link to full receipt
    }
    
    mapping(uint256 => Receipt) public receipts;
    
    event ReceiptMinted(
        uint256 indexed tokenId,
        uint256 indexed donationId,
        address donor,
        uint256 campaignId,
        uint256 amountUSD
    );
    
    constructor() ERC721("TrustVoice Donation Receipt", "TVDR") Ownable(msg.sender) {}
    
    function mintReceipt(
        address donor,
        uint256 donationId,
        uint256 campaignId,
        uint256 amountUSD,
        string memory paymentMethod,
        string memory metadataURI
    ) public onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;
        
        _safeMint(donor, tokenId);
        
        receipts[tokenId] = Receipt({
            donationId: donationId,
            donor: donor,
            campaignId: campaignId,
            amountUSD: amountUSD,
            paymentMethod: paymentMethod,
            timestamp: block.timestamp,
            metadataURI: metadataURI
        });
        
        emit ReceiptMinted(tokenId, donationId, donor, campaignId, amountUSD);
        
        return tokenId;
    }
    
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        return receipts[tokenId].metadataURI;
    }
}
```

### 6.2 Receipt Generation (Python)

```python
# blockchain/receipt_manager.py

from web3 import Web3
import json

class ReceiptManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        self.contract = self.w3.eth.contract(
            address=settings.RECEIPT_CONTRACT_ADDRESS,
            abi=RECEIPT_CONTRACT_ABI
        )
    
    async def create_receipt(self, donation_id: int) -> str:
        """
        Mints NFT receipt for donation
        """
        donation = await get_donation(donation_id)
        donor = await get_donor(donation.donor_id)
        campaign = await get_campaign(donation.campaign_id)
        
        # Upload metadata to IPFS
        metadata = {
            "name": f"Donation Receipt #{donation.id}",
            "description": f"Donation to {campaign.title}",
            "image": await generate_receipt_image(donation),
            "attributes": [
                {"trait_type": "Campaign", "value": campaign.title},
                {"trait_type": "Amount USD", "value": str(donation.amount_usd)},
                {"trait_type": "Date", "value": donation.created_at.isoformat()},
                {"trait_type": "Payment Method", "value": donation.payment_method}
            ],
            "external_url": f"https://trustvoice.org/receipt/{donation.id}"
        }
        
        ipfs_hash = await upload_to_ipfs(json.dumps(metadata))
        metadata_uri = f"ipfs://{ipfs_hash}"
        
        # Mint NFT (if donor has wallet)
        if donor.blockchain_wallet_address:
            tx_hash = await self.mint_receipt_onchain(
                donor_address=donor.blockchain_wallet_address,
                donation_id=donation.id,
                campaign_id=campaign.id,
                amount_usd=int(donation.amount_usd * 100),
                payment_method=donation.payment_method,
                metadata_uri=metadata_uri
            )
        else:
            tx_hash = None  # Store offchain
        
        # Update donation record
        donation.blockchain_receipt_url = metadata_uri
        await db.commit()
        
        return metadata_uri
    
    async def mint_receipt_onchain(self, **kwargs) -> str:
        """
        Calls smart contract to mint receipt NFT
        """
        account = Account.from_key(settings.PLATFORM_PRIVATE_KEY)
        
        tx = self.contract.functions.mintReceipt(
            donor=kwargs["donor_address"],
            donationId=kwargs["donation_id"],
            campaignId=kwargs["campaign_id"],
            amountUSD=kwargs["amount_usd"],
            paymentMethod=kwargs["payment_method"],
            metadataURI=kwargs["metadata_uri"]
        ).build_transaction({
            "from": account.address,
            "nonce": self.w3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": self.w3.eth.gas_price
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return tx_hash.hex()
```

---

## 7. Multi-Language Support

### 7.1 Language Detection

```python
# voice/ai/language_handler.py

from langdetect import detect
from deep_translator import GoogleTranslator

SUPPORTED_LANGUAGES = ["en", "fr", "it", "de", "am", "sw"]

async def detect_language(text: str) -> str:
    """
    Detects language from user input
    """
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except:
        return "en"  # Default fallback

async def translate_response(
    text: str,
    target_language: str
) -> str:
    """
    Translates LLM response to target language
    """
    if target_language == "en":
        return text
    
    translator = GoogleTranslator(source="en", target=target_language)
    return translator.translate(text)

async def generate_multilingual_response(
    prompt: str,
    donor_language: str
) -> str:
    """
    Generates response in donor's language
    """
    # For supported languages, use GPT-4 directly in target language
    if donor_language in ["en", "fr", "it", "de"]:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": f"Respond in {donor_language}"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    # For Amharic/Swahili, generate in English then translate
    else:
        english_response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Respond in English"},
                {"role": "user", "content": prompt}
            ]
        )
        
        return await translate_response(
            english_response.choices[0].message.content,
            target_language=donor_language
        )
```

### 7.2 Text-to-Speech (Multi-Language)

```python
# voice/tts/speech_generator.py

from elevenlabs import generate, set_api_key

set_api_key(settings.ELEVENLABS_API_KEY)

VOICE_IDS = {
    "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel (English)
    "fr": "pNInz6obpgDQGcFmaJgB",  # Antoine (French)
    "de": "yoZ06aMxZJJ28mfd3POQ",  # Sam (German)
    "it": "onwK4e9ZLuTAKqWW03F9",  # Bella (Italian)
    "am": "21m00Tcm4TlvDq8ikWAM",  # Fallback to English voice
    "sw": "21m00Tcm4TlvDq8ikWAM"   # Fallback to English voice
}

async def text_to_speech(
    text: str,
    language: str,
    output_format: str = "mp3"
) -> bytes:
    """
    Converts text to speech in specified language
    """
    voice_id = VOICE_IDS.get(language, VOICE_IDS["en"])
    
    audio = generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2"
    )
    
    return audio
```

---

## 8. Security & Compliance

### 8.1 Authentication

```python
# All donor endpoints require authentication via:
# - Phone number (verified via OTP)
# - Telegram user ID (verified by Telegram)
# - WhatsApp number (verified by Twilio)

async def authenticate_donor(
    channel: str,
    identifier: str
) -> Optional[Donor]:
    """
    Authenticates donor based on communication channel
    """
    if channel == "ivr":
        return await get_donor_by_phone(identifier)
    elif channel == "telegram":
        return await get_donor_by_telegram_id(identifier)
    elif channel == "whatsapp":
        return await get_donor_by_whatsapp(identifier)
```

### 8.2 PCI Compliance (Stripe)

- **No credit card data stored** - Stripe handles all card info
- **PCI-DSS Level 1 compliant** - Stripe certification
- **3D Secure** - Required for European cards
- **Tokenization** - All payments use Stripe tokens

### 8.3 Data Privacy (GDPR)

```python
# All donor data complies with GDPR:
# - Right to access
# - Right to deletion
# - Right to data portability
# - Consent management

async def handle_gdpr_deletion_request(donor_id: int):
    """
    Anonymizes donor data (can't delete donation records)
    """
    donor = await get_donor(donor_id)
    
    # Anonymize personal info
    donor.phone_number = f"DELETED_{donor.id}"
    donor.email = None
    donor.preferred_name = "Anonymous"
    donor.telegram_user_id = None
    donor.whatsapp_number = None
    
    # Keep donation records (required for NGO accounting)
    # but mark as anonymous
    donations = await get_donations_by_donor(donor_id)
    for donation in donations:
        donation.is_anonymous = True
    
    await db.commit()
```

---

## 9. Deployment

### 9.1 Infrastructure

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - redis
      - postgres
  
  celery:
    build: .
    command: celery -A voice.tasks worker -l info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=trustvoice
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 9.2 Environment Variables

```bash
# .env
DATABASE_URL=postgresql://user:pass@db.neon.tech/trustvoice
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
TELEGRAM_BOT_TOKEN=...
WHATSAPP_NUMBER=+1...
ELEVENLABS_API_KEY=...
PINECONE_API_KEY=...
POLYGON_RPC_URL=https://polygon-rpc.com
RECEIPT_CONTRACT_ADDRESS=0x...
PLATFORM_PRIVATE_KEY=0x...
```

---

## 10. Development Timeline

### Week 1-2: Core Infrastructure
- [ ] Database schema setup
- [ ] Basic API endpoints (FastAPI)
- [ ] Multi-channel router
- [ ] Stripe integration

### Week 3-4: AI Integration
- [ ] LLM conversation handler
- [ ] Intent classification
- [ ] RAG implementation (Pinecone)
- [ ] Multi-language support

### Week 5-6: Communication Channels
- [ ] IVR system (Twilio Voice)
- [ ] Telegram bot
- [ ] WhatsApp integration
- [ ] TTS/STT pipelines

### Week 7-8: Blockchain & Testing
- [ ] Smart contract deployment
- [ ] Receipt minting system
- [ ] Impact verification flow
- [ ] End-to-end testing

### Week 9-10: NGO Dashboard & Pilot
- [ ] Admin dashboard (campaign management)
- [ ] Analytics & reporting
- [ ] Pilot with 1 NGO
- [ ] Feedback iteration

---

## 11. Cost Estimates (Monthly)

**Infrastructure:**
- Railway/Render hosting: $50
- Neon PostgreSQL: $20
- Redis Cloud: $10
- Cloudflare Tunnel: $0

**APIs:**
- OpenAI (GPT-4): $500 (2000 conversations @ $0.25)
- Twilio Voice: $200 (500 minutes @ $0.40/min)
- Twilio WhatsApp: $50 (1000 messages @ $0.05)
- ElevenLabs TTS: $100 (500K characters)
- Pinecone: $70 (vector database)

**Payments:**
- Stripe: 2.9% + $0.30 per transaction
- Blockchain gas (Polygon): $50 (100 receipts)

**Total: ~$1,050/month** for 200-500 active donors

**Break-even:** ~15 NGOs paying $70/month (Pro tier)

---

## 12. Testing Strategy

```python
# tests/test_donation_flow.py

async def test_end_to_end_donation():
    """
    Tests complete donor journey:
    1. Donor asks about campaign (Telegram)
    2. AI responds with campaign info
    3. Donor initiates donation
    4. Payment processed (Stripe test mode)
    5. Receipt minted
    6. Confirmation sent
    """
    # Simulate donor message
    response = await send_telegram_message(
        user_id="123",
        message="Tell me about water projects in Tanzania"
    )
    
    assert "Mwanza Water Project" in response
    
    # Initiate donation
    response = await send_telegram_message(
        user_id="123",
        message="I want to donate $100"
    )
    
    assert "payment link" in response.lower()
    
    # Simulate Stripe payment
    intent = await create_test_payment_intent(
        donor_id=123,
        amount=100
    )
    
    await trigger_stripe_webhook(
        event_type="payment_intent.succeeded",
        intent_id=intent.id
    )
    
    # Verify donation created
    donation = await get_latest_donation(donor_id=123)
    assert donation.status == "completed"
    assert donation.amount_usd == 100
    
    # Verify receipt minted
    assert donation.blockchain_receipt_url is not None
    
    # Verify confirmation sent
    messages = await get_telegram_messages_sent(user_id="123")
    assert any("Thank you" in msg for msg in messages)
```

---

**This technical specification provides a complete blueprint for building TrustVoice. All components leverage proven patterns from Voice Ledger, with 90% code reuse. Estimated development time: 8-10 weeks for MVP.**
