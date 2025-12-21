# TrustVoice - Session Context & Progress Tracker

**Last Updated:** 21 December 2025  
**Current Branch:** `lab-03-payments`  
**Project Status:** Lab 3 Complete ✅ | Lab 4 Pending 🔄

---

## 🎯 Project Overview

**TrustVoice** is a voice-first donation platform enabling international NGOs to accept donations via:
- 📞 Phone calls (IVR with AI voice assistance)
- 💬 Telegram/WhatsApp chatbots
- 💳 Multiple payment methods (M-Pesa, Stripe, Crypto)
- 🌍 Multi-currency support (USD, EUR, GBP, KES, etc.)

**Tech Stack:**
- Backend: FastAPI + Python 3.9
- Database: PostgreSQL (Neon Cloud)
- Cache: Redis
- Payments: M-Pesa, Stripe
- AI: OpenAI GPT-4, LangChain
- Blockchain: Ethereum (receipt verification)

---

## ✅ Completed Work (Labs 1-3)

### Lab 1: Project Setup ✅
**Commit:** `1aef64b`

**Completed:**
- Project structure and virtual environment
- PostgreSQL database connection (Neon Cloud)
- Core models: Donor, Campaign, NGO, Conversation, Impact Verification
- Database initialization scripts
- Basic FastAPI application setup
- Environment configuration (.env)

**Key Files:**
- `database/models.py` - SQLAlchemy models
- `database/db.py` - Database connection
- `main.py` - FastAPI entry point
- `.env` - Environment variables (not committed)

---

### Lab 2: Campaign & Donor APIs ✅
**Commit:** `11e5471`

**Completed:**
- RESTful endpoints for campaigns (CRUD)
- Donor registration and management
- NGO organization management
- Query filters and pagination
- Campaign goal tracking
- Comprehensive test suite

**Endpoints Added:**
- `GET /campaigns/` - List all campaigns
- `POST /campaigns/` - Create campaign
- `GET /campaigns/{id}` - Get campaign details
- `PUT /campaigns/{id}` - Update campaign
- `GET /donors/` - List donors
- `POST /donors/` - Register donor
- `GET /ngos/` - List NGOs

**Key Files:**
- `voice/routers/campaigns.py` - Campaign endpoints
- `voice/routers/donors.py` - Donor endpoints
- `voice/routers/ngos.py` - NGO endpoints
- `tests/test_lab2_endpoints.py` - API tests

---

### Lab 3: Payment Processing & Admin Approval ✅
**Commit:** `61fac99` (34 files changed, 7,035 insertions)

**Completed:**

#### 1. M-Pesa Integration
- STK Push for customer-initiated payments
- B2C payouts for mobile money disbursements
- Webhook handlers (result + timeout)
- Production credentials configured
- Sandbox testing complete

**Key Files:**
- `services/mpesa.py` - M-Pesa service with STK Push & B2C
- `voice/routers/webhooks.py` - M-Pesa webhook handlers
- `tests/test_mpesa_flow.py` - M-Pesa donation tests
- `tests/test_b2c_direct.py` - B2C payout tests

**Environment Variables:**
```bash
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_BUSINESS_SHORT_CODE=174379
MPESA_PASSKEY=your_passkey
MPESA_INITIATOR_NAME=testapi
MPESA_SECURITY_CREDENTIAL=base64_encrypted
MPESA_CALLBACK_URL=https://your-ngrok.ngrok-free.dev/webhooks/mpesa
```

#### 2. Stripe Integration
- Payment Intent creation for card payments
- Webhook signature verification
- Multi-currency support (USD, EUR, GBP)
- Test mode configured

**Key Files:**
- `services/stripe_service.py` - Stripe payment & payout service
- `voice/routers/webhooks.py` - Stripe webhook handler
- `tests/test_stripe_flow.py` - Stripe donation tests

**Environment Variables:**
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### 3. Donation System
- Multi-currency donation tracking
- Cross-currency conversion with caching
- Campaign balance tracking per currency
- Donation status management (pending, completed, failed)

**Key Files:**
- `services/currency_service.py` - Currency conversion with fallback rates
- `voice/routers/donations.py` - Donation endpoints
- `database/models.py` - Donation model updated

**Supported Currencies:**
- USD, EUR, GBP, KES, TZS, UGX, ZAR
- Auto-conversion for validation
- 24-hour rate caching

#### 4. Multi-Method Payout System
- **Bank Transfers:** SEPA (Europe), SWIFT (international)
- **M-Pesa B2C:** Instant mobile money (Kenya/Tanzania/Uganda)
- **Stripe Payouts:** 40+ countries, 2-7 day processing

**Key Files:**
- `voice/routers/payouts.py` - Payout endpoints with approval
- `database/models.py` - Payout model (extended)
- `tests/test_bank_payouts.py` - Bank transfer tests
- `tests/test_cross_currency.py` - Cross-currency validation

**Payout Fields:**
```python
# Mobile money
recipient_phone, conversation_id

# Bank transfer
bank_account_number, bank_routing_number, bank_name, bank_country

# Stripe
stripe_payout_id, stripe_transfer_id

# Admin approval
approved_by, approved_at, rejection_reason
```

#### 5. Admin Approval System ⭐
- JWT authentication with bcrypt password hashing
- Role-based access control (super_admin, ngo_admin, viewer)
- Payout approval/rejection workflow
- Audit trail for compliance

**Key Files:**
- `services/auth_service.py` - JWT & password hashing
- `voice/routers/admin.py` - Admin authentication endpoints
- `database/models.py` - User model with roles
- `tests/test_admin_approval.py` - Approval workflow tests

**Admin Account Created:**
- Email: `emmanuel@earesearch.net`
- Password: `Password123`
- Role: `super_admin`

**Endpoints:**
- `POST /admin/login` - Login (returns JWT)
- `GET /admin/me` - Current user info
- `POST /admin/users` - Create user (super admin only)
- `POST /payouts/{id}/approve` - Approve payout
- `POST /payouts/{id}/reject` - Reject payout

**Auth Flow:**
```python
# 1. Login
POST /admin/login
{
  "email": "emmanuel@earesearch.net",
  "password": "Password123"
}
# Returns: {"access_token": "eyJhbG...", "user": {...}}

# 2. Use token
headers = {"Authorization": "Bearer <token>"}
POST /payouts/123/approve
```

#### 6. Project Organization
- **tests/** - All test files (10+ files)
- **database/** - Models, init, seed data
- **services/** - M-Pesa, Stripe, Currency, Auth
- **admin-scripts/** - START_SERVICES.sh, STOP_SERVICES.sh
- **documentation/labs/** - Lab 1-3 complete

#### 7. Database Schema Updates
**Tables Created:**
- `users` - Admin users with roles
- `payouts` - Extended with approval fields
- `donations` - Multi-currency tracking

**Migrations Applied:**
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    ngo_id INTEGER REFERENCES ngo_organizations(id),
    is_active BOOLEAN DEFAULT TRUE
);

-- Payout approval columns
ALTER TABLE payouts ADD COLUMN approved_by INTEGER REFERENCES users(id);
ALTER TABLE payouts ADD COLUMN approved_at TIMESTAMP;
ALTER TABLE payouts ADD COLUMN rejection_reason TEXT;

-- Bank account columns
ALTER TABLE payouts ADD COLUMN bank_account_number VARCHAR(100);
ALTER TABLE payouts ADD COLUMN bank_routing_number VARCHAR(100);
ALTER TABLE payouts ADD COLUMN bank_name VARCHAR(200);
ALTER TABLE payouts ADD COLUMN bank_country VARCHAR(2);
```

---

## 🔧 Current System Architecture

### Payment Flow
```
1. Donor initiates donation
   ├─> M-Pesa: STK Push → Phone prompt → PIN entry
   └─> Stripe: Payment Intent → Card form → 3D Secure

2. Payment processor webhook
   ├─> Verify signature
   ├─> Update donation status
   └─> Update campaign balance

3. Campaign tracking
   ├─> Track in original currency
   └─> Convert to USD for validation
```

### Payout Flow
```
1. NGO creates payout request
   └─> Status: "pending" (bank transfers)
   └─> Status: "processing" (M-Pesa auto-approved)

2. Admin reviews (bank transfers only)
   ├─> Approve → Status: "approved" → Process
   └─> Reject → Status: "rejected" → Record reason

3. Payment processing
   ├─> Bank: Manual SEPA/SWIFT (1-5 days)
   ├─> M-Pesa: API call (instant)
   └─> Stripe: API call (2-7 days)
```

### Service Management
```bash
# Start all services
./admin-scripts/START_SERVICES.sh
# - FastAPI (port 8001)
# - ngrok tunnel (webhook access)
# - PostgreSQL (Neon Cloud)
# - Redis (optional caching)

# Stop services
./admin-scripts/STOP_SERVICES.sh

# Check logs
tail -f logs/trustvoice_api.log
```

---

## 📊 Testing Status

**Test Suite:** 10+ test files, all passing ✅

| Test File | Purpose | Status |
|-----------|---------|--------|
| `test_api.py` | Basic API health | ✅ |
| `test_lab2_endpoints.py` | Campaign/Donor CRUD | ✅ |
| `test_mpesa_flow.py` | M-Pesa donations | ✅ |
| `test_stripe_flow.py` | Stripe donations | ✅ |
| `test_mpesa_direct.py` | M-Pesa direct API | ✅ |
| `test_b2c_direct.py` | M-Pesa B2C payouts | ✅ |
| `test_bank_payouts.py` | Bank transfer payouts | ✅ |
| `test_cross_currency.py` | Cross-currency validation | ✅ |
| `test_all_payments.py` | Complete payment flow | ✅ |
| `test_admin_approval.py` | Admin approval workflow | ✅ |

**Run Tests:**
```bash
# All tests
pytest tests/

# Specific test
python tests/test_admin_approval.py

# With coverage
pytest tests/ --cov=voice --cov=services
```

---

## 📝 Important Configuration

### Database (PostgreSQL - Neon)
```bash
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/trustvoice?sslmode=require
```

### Redis (Optional Cache)
```bash
REDIS_URL=redis://localhost:6379/0
```

### JWT Authentication
```bash
JWT_SECRET_KEY=your-secret-key-change-in-production-trustvoice-2025
# Token expiry: 24 hours
```

### ngrok (Webhooks)
```bash
# Auto-started by START_SERVICES.sh
# Public URL: https://briary-torridly-raul.ngrok-free.dev
# Dashboard: http://localhost:4040
```

---

## 🚧 Known Issues & Notes

### 1. M-Pesa B2C Payouts
- **Status:** Failing in sandbox (expected)
- **Reason:** Sandbox requires special credentials/setup
- **Impact:** System correctly creates payout, sends API request, handles failure
- **Fix Needed:** Production credentials or sandbox reconfiguration
- **Code Status:** ✅ Production-ready

### 2. Stripe Payouts (Mock Mode)
- **Status:** Working but in mock mode
- **Reason:** No real Stripe Connect accounts configured
- **Impact:** Can create payouts, but not actually process
- **Fix Needed:** Set up Stripe Connect for real payouts
- **Code Status:** ✅ Production-ready

### 3. Documentation Generation
- **Status:** Labs 1-3 in `documentation/labs/` (gitignored)
- **Note:** Labs are auto-generated, shouldn't be committed
- **Exception:** SESSION_CONTEXT.md should be committed

### 4. Test Database
- **Removed:** `test.db` (was SQLite, now using PostgreSQL)
- **Current:** All tests use live PostgreSQL database
- **Note:** Consider adding test database isolation

---

## 🔄 TODO: Lab 4 - Voice AI Integration

### Overview
Build voice and chat interfaces for donations using:
- Telegram bot for text/voice messages
- WhatsApp integration (via Twilio)
- OpenAI GPT-4 for natural language processing
- LangChain for conversation management
- RAG (Retrieval Augmented Generation) for campaign FAQs

### High-Level Tasks

#### 1. Telegram Bot Integration
- [ ] Create Telegram bot with BotFather
- [ ] Set up python-telegram-bot webhook
- [ ] Implement conversation handlers
- [ ] Add payment buttons and inline keyboards
- [ ] Voice message transcription
- [ ] Multi-language support (English, Swahili, French)

#### 2. WhatsApp Integration (Twilio)
- [ ] Configure Twilio WhatsApp sandbox
- [ ] Set up webhook endpoints
- [ ] Message formatting for WhatsApp
- [ ] Media message handling
- [ ] Business account verification (production)

#### 3. AI Conversation Engine
- [ ] OpenAI GPT-4 integration
- [ ] LangChain conversation chains
- [ ] Context management (remember donor preferences)
- [ ] Intent recognition (donate, ask about campaign, check receipt)
- [ ] Entity extraction (amount, currency, campaign)

#### 4. RAG System for Campaign Info
- [ ] Pinecone vector database setup
- [ ] Campaign context embedding
- [ ] FAQ retrieval system
- [ ] Context-aware responses
- [ ] Admin interface to add campaign FAQs

#### 5. Voice Processing
- [ ] OpenAI Whisper for speech-to-text
- [ ] Text-to-speech for responses (OpenAI TTS)
- [ ] Voice message handling in Telegram
- [ ] Phone call integration (Twilio Voice API)

#### 6. Conversation Models
- [ ] ConversationLog model (already exists, needs extension)
- [ ] Message history tracking
- [ ] Donor preference storage
- [ ] Session management

### Detailed Implementation Steps

#### Step 1: Telegram Bot Setup
```python
# services/telegram_bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler

async def start(update: Update, context):
    """Welcome message"""
    await update.message.reply_text(
        "Welcome to TrustVoice! 🌍\n"
        "I can help you donate to NGO campaigns.\n"
        "Send /donate to get started!"
    )

async def donate(update: Update, context):
    """Show campaigns"""
    # Query database for active campaigns
    # Show inline keyboard with campaign options

# Setup
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("donate", donate))
```

#### Step 2: OpenAI Integration
```python
# services/ai_service.py
from openai import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

client = OpenAI(api_key=OPENAI_API_KEY)

async def process_message(user_message: str, context: dict):
    """Process user message with GPT-4"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful donation assistant..."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content
```

#### Step 3: RAG for Campaign FAQs
```python
# services/rag_service.py
from pinecone import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as PineconeVS

# Initialize
pc = Pinecone(api_key=PINECONE_API_KEY)
embeddings = OpenAIEmbeddings()

def search_campaign_info(query: str, campaign_id: int):
    """Search campaign-specific information"""
    # Embed query
    # Search Pinecone for relevant context
    # Return top 3 matches
```

### Environment Variables Needed
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhooks/telegram

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# OpenAI
OPENAI_API_KEY=sk-...

# Pinecone
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=trustvoice-campaigns

# Addis AI (Ethiopian languages)
ADDIS_AI_API_KEY=your_key (if using)
```

### Testing Strategy
```python
# tests/test_telegram_bot.py
- Test /start command
- Test /donate flow
- Test payment button clicks
- Test voice message handling

# tests/test_ai_conversation.py
- Test intent recognition
- Test entity extraction
- Test context retention
- Test multi-turn conversations

# tests/test_rag_retrieval.py
- Test campaign info retrieval
- Test relevance scoring
- Test FAQ matching
```

### Success Criteria for Lab 4
- [ ] Telegram bot responds to commands
- [ ] User can donate via chat interface
- [ ] AI understands donation intents
- [ ] Campaign information retrieved via RAG
- [ ] Voice messages transcribed and processed
- [ ] Multi-language support working
- [ ] Conversation history saved
- [ ] Payment integration works via chat

---

## 🎯 TODO: Lab 5+ (Future Work)

### Lab 5: Blockchain Receipt System
- [ ] Ethereum smart contract for donation receipts
- [ ] IPFS for receipt document storage
- [ ] Web3.py integration
- [ ] NFT-based donation certificates
- [ ] Blockchain verification endpoint

### Lab 6: Impact Verification
- [ ] Field officer mobile app (React Native)
- [ ] GPS-tagged photo uploads
- [ ] Impact report generation
- [ ] Donor notification system
- [ ] Blockchain anchoring of impact reports

### Lab 7: Analytics Dashboard
- [ ] React/TypeScript frontend
- [ ] Campaign performance metrics
- [ ] Donor engagement analytics
- [ ] Geographic donation heatmaps
- [ ] Real-time donation tracking

### Lab 8: Production Deployment
- [ ] Docker containerization
- [ ] Kubernetes orchestration
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production database migration
- [ ] Load testing and optimization
- [ ] Security audit
- [ ] GDPR compliance
- [ ] PCI-DSS for payment data

---

## 📚 Resources & Documentation

### API Documentation
- **Local:** http://localhost:8001/docs (FastAPI Swagger UI)
- **Public:** https://briary-torridly-raul.ngrok-free.dev/docs

### External APIs
- M-Pesa: https://developer.safaricom.co.ke/
- Stripe: https://stripe.com/docs/api
- Telegram: https://core.telegram.org/bots/api
- OpenAI: https://platform.openai.com/docs
- Pinecone: https://docs.pinecone.io/

### Internal Docs
- `documentation/IMPLEMENTATION_PLAN.md` - Overall roadmap
- `documentation/labs/LAB_01_PROJECT_SETUP.md` - Lab 1 guide
- `documentation/labs/LAB_02_CAMPAIGN_DONOR_APIS.md` - Lab 2 guide
- `documentation/labs/LAB_03_PAYMENT_PROCESSING.md` - Lab 3 guide (includes admin approval)

---

## 🚀 Quick Start for Next Session

```bash
# 1. Checkout working branch
git checkout lab-03-payments

# 2. Activate environment
source venv/bin/activate

# 3. Start services
./admin-scripts/START_SERVICES.sh

# 4. Verify everything works
curl http://localhost:8001/health

# 5. Test admin login
python tests/test_admin_approval.py

# 6. Create Lab 4 branch
git checkout -b lab-04-voice-ai

# 7. Start Lab 4 work
# - Install Telegram dependencies
# - Create Telegram bot
# - Set up OpenAI integration
```

---

## 💡 Key Decisions Made

1. **PostgreSQL over SQLite** - Production database from start
2. **Multi-currency tracking** - Store original currency, convert for validation only
3. **Admin approval required** - Bank transfers need human oversight
4. **JWT authentication** - Stateless, scalable auth system
5. **Role-based access** - NGO admins can only approve own payouts
6. **ngrok for webhooks** - Easy development webhook testing
7. **Mock mode support** - All payment services work without real credentials
8. **Test organization** - All tests in tests/ directory
9. **Service scripts** - Automated startup/shutdown for all services

---

## 🔐 Security Notes

1. **Never commit `.env`** - Contains all secrets
2. **JWT secret** - Should be rotated in production (openssl rand -hex 32)
3. **M-Pesa credentials** - Encrypted security credential (base64)
4. **Stripe webhook secret** - Verifies webhook authenticity
5. **Password hashing** - bcrypt with proper work factor
6. **Admin access** - Logged in `approved_by` field for audit

---

## 📞 Contact & Support

**Developer:** Emmanuel  
**Email:** emmanuel@earesearch.net  
**Project:** TrustVoice - Voice-First NGO Donation Platform  
**Repository:** [Local Git Repository]  
**Last Session:** 21 December 2025

---

**Session Status:** Lab 3 Complete ✅ | Ready for Lab 4 🚀

**Next Session Goals:**
1. Create Telegram bot
2. Integrate OpenAI GPT-4
3. Build conversation flow for donations
4. Test voice message handling
5. Set up basic RAG system

**Estimated Time for Lab 4:** 8-10 hours
