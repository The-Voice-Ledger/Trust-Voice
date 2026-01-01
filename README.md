# TrustVoice

Voice-first donation platform for African changemakers. Supports NGO donations and crowdfunding through voice interfaces (Telegram bot, phone calls) with multiple payment methods.

## Overview

TrustVoice enables donations via voice commands in English and Amharic. Users can search campaigns, make donations, and track impact through conversational AI powered by OpenAI GPT-4 and AddisAI.

**Core Features:**
- Voice message processing (primary interface)
- Multi-language support (English, Amharic)
- Campaign search and discovery
- Voice-driven donation flows
- Payment processing (M-Pesa, Stripe)
- Admin approval workflows for NGOs and field agents
- Impact verification tracking

## Architecture

**Backend:**
- FastAPI (Python 3.9+)
- PostgreSQL database (Neon Cloud)
- Redis for caching and task queues
- Celery for background tasks
- SQLAlchemy ORM

**Voice Processing:**
- OpenAI Whisper (English ASR)
- AddisAI (Amharic ASR)
- OpenAI TTS (English)
- AddisAI TTS (Amharic)
- Dual delivery: text + audio responses

**Payment Integration:**
- M-Pesa (Kenya mobile money)
- Stripe (international cards)

**Deployment:**
- Railway (production)
- Telegram webhooks
- Static file serving for miniapps

## Project Structure

```
Trust-Voice/
├── main.py                 # FastAPI application entry point
├── database/
│   ├── models.py          # SQLAlchemy models
│   ├── db.py              # Database connections
│   └── migrations/        # SQL migration scripts
├── voice/
│   ├── routers/           # API endpoints
│   │   ├── miniapp_voice.py  # Voice processing endpoints
│   │   ├── campaigns.py      # Campaign CRUD
│   │   ├── donations.py      # Donation management
│   │   └── webhooks.py       # Payment webhooks
│   ├── telegram/          # Telegram bot
│   │   ├── bot.py         # Main bot logic
│   │   └── webhook.py     # Production webhook handler
│   ├── handlers/          # Command handlers
│   ├── conversation/      # Conversation management
│   └── workflows/         # Multi-step flows
├── services/
│   ├── mpesa.py          # M-Pesa integration
│   ├── stripe_service.py # Stripe integration
│   └── tts_provider.py   # TTS routing
├── frontend-miniapps/     # HTML/JS miniapps
│   ├── campaigns.html    # Browse campaigns
│   ├── donate.html       # Voice donation
│   ├── create-campaign-wizard.html
│   └── ngo-register-wizard.html
└── scripts/              # Deployment scripts

```

## Database Models

**Users:**
- Admins (password-based)
- Telegram users (PIN-based)
- Roles: donor, campaign_creator, field_agent, ngo_admin

**Campaigns:**
- Title, description, goal, deadline
- Multi-currency support
- Status tracking (draft, active, completed)

**Donations:**
- Linked to donor, campaign, payment method
- Multi-currency tracking
- Status management (pending, completed, failed)

**NGOs:**
- Organization profiles
- Admin approval required
- Campaign management

**Conversations:**
- Chat history for debugging
- User preferences
- Session management

## API Endpoints

**Voice Processing:**
- `POST /api/voice/search-campaigns` - Voice search
- `POST /api/voice/donate-by-voice` - Voice donation
- `POST /api/voice/wizard-step` - Multi-step form guidance
- `POST /api/voice/tts` - Text-to-speech
- `POST /api/voice/set-language` - Language preference

**Campaigns:**
- `GET /api/campaigns/` - List campaigns
- `POST /api/campaigns/` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign details
- `PUT /api/campaigns/{id}` - Update campaign

**Donations:**
- `POST /api/donations/` - Record donation
- `GET /api/donations/` - List donations
- `GET /api/donations/{id}` - Get donation details

**Webhooks:**
- `POST /webhooks/mpesa` - M-Pesa callback
- `POST /webhooks/stripe` - Stripe callback
- `POST /webhooks/telegram` - Telegram webhook (production)

**Admin:**
- `GET /api/registrations/` - Pending registrations
- `POST /api/registrations/{id}/approve` - Approve user
- `POST /api/registrations/{id}/reject` - Reject user

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Redis (optional, for Celery)
- Telegram bot token
- OpenAI API key
- AddisAI API key (for Amharic)

### Local Development

1. Clone repository:
```bash
git clone <repository-url>
cd Trust-Voice
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Run database migrations:
```bash
python database/migrations/run_migrations.py
```

6. Start services:
```bash
# Start FastAPI server
uvicorn main:app --reload --port 8001

# Start Telegram bot (separate terminal)
python voice/telegram/bot.py

# Start Celery worker (optional, separate terminal)
celery -A voice.tasks.celery_app worker --loglevel=info
```

7. Access miniapps:
```
http://localhost:8001/campaigns.html
http://localhost:8001/donate.html
http://localhost:8001/create-campaign-wizard.html
```

## Configuration

### Environment Variables

Core variables (see `.env.example` for full list):

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/database

# AI Services
OPENAI_API_KEY=sk-proj-your-key
ADDIS_AI_API_KEY=sk_your-key
ADDIS_AI_URL=https://api.addisassistant.com/api/v1/chat_generate

# Payments
STRIPE_SECRET_KEY=sk_test_your-key
MPESA_CONSUMER_KEY=your-key
MPESA_CONSUMER_SECRET=your-secret

# Communication
TELEGRAM_BOT_TOKEN=1234567890:ABC...

# Application
APP_ENV=development
ALLOWED_ORIGINS=http://localhost:8001
```

### Language Support

The platform supports English and Amharic:

**English (en):**
- ASR: OpenAI Whisper
- TTS: OpenAI TTS (tts-1, nova voice)

**Amharic (am):**
- ASR: AddisAI
- TTS: AddisAI (amharic_female voice)

Language detection uses Unicode range analysis (U+1200-U+137F for Amharic). Users can toggle language preference in miniapps, saved to database for registered users or localStorage for anonymous users.

## Deployment

### Railway Deployment

1. Commit code:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. Create Railway project:
- Go to railway.app
- Deploy from GitHub repo
- Connect Trust-Voice repository

3. Set environment variables:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link
railway login
railway link

# Run automated setup
python scripts/setup-railway-env.py
```

4. Configure webhooks after deployment:
- Telegram: automatically configured
- M-Pesa: update in Safaricom portal
- Stripe: update in Stripe dashboard

See `DEPLOYMENT_CHECKLIST.md` for detailed steps.

## Testing

Run test suite:
```bash
pytest tests/
```

Specific test categories:
```bash
pytest tests/test_miniapp_integration.py  # Miniapp voice features
pytest tests/test_donation_flow.py        # End-to-end donation
pytest tests/test_lab9_preferences.py     # User preferences
```

Smoke test deployed instance:
```bash
python tests/smoke_test.py https://your-app.railway.app
```

## Telegram Bot Usage

Start conversation:
```
/start
```

Register as user:
```
/register
```

Available roles:
- Donor (instant approval)
- Campaign Creator (admin approval required)
- Field Agent (admin approval required)

Voice commands:
- Send voice message: "Show me education campaigns"
- Send voice message: "Donate 1000 shillings to campaign X"
- Send voice message: "What impact has this campaign achieved?"

Text fallback:
- Type: "search education"
- Type: "donate"
- Type: "/campaigns"

## Miniapps

Browser-based voice interfaces:

**campaigns.html:**
- Browse active campaigns
- Voice search: click mic, speak query
- Language toggle (English/Amharic)

**donate.html:**
- Voice-driven donation flow
- Amount extraction from speech
- Payment method selection

**create-campaign-wizard.html:**
- Multi-step campaign creation
- Voice input for each field
- AI suggestions for descriptions

**ngo-register-wizard.html:**
- NGO registration workflow
- Voice input supported
- Admin approval required

## Payment Flows

### M-Pesa (Kenya)

1. User initiates donation via voice
2. System sends STK push to phone
3. User enters M-Pesa PIN
4. Webhook confirms payment
5. Donation recorded

### Stripe (International)

1. User selects Stripe payment
2. Redirected to Stripe checkout
3. Completes card payment
4. Webhook confirms payment
5. Donation recorded

## Admin Workflows

**Approve NGO Registration:**
1. NGO submits registration via bot
2. Admin receives notification
3. Admin reviews: `/admin_requests`
4. Approve: `/admin_approve <id>`
5. NGO can create campaigns

**Approve Campaign Creator:**
1. User registers as campaign creator
2. Admin reviews pending requests
3. Approve or reject via commands
4. Approved users can launch campaigns

## Conversation Analytics

Track user interactions:
```bash
GET /api/analytics/conversation-metrics
GET /api/analytics/events
GET /api/analytics/funnel
```

Metrics include:
- Command success rates
- Language distribution
- Response times
- User preferences

## Voice Features

**Dual Delivery:**
All voice responses include both text and audio. Frontend plays TTS audio while displaying transcription.

**Language Persistence:**
- Registered users: preference saved to database
- Anonymous users: preference saved to localStorage
- Cross-device sync for registered users

**Voice Processing Pipeline:**
1. Receive audio file
2. Detect language (Unicode analysis)
3. Route to appropriate ASR (Whisper or AddisAI)
4. Process command via NLU
5. Generate response
6. Route to appropriate TTS
7. Return text + audio URL

## Troubleshooting

**Bot not responding:**
```bash
# Check webhook status
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Reset webhook
curl -X POST https://your-app.railway.app/webhooks/telegram/set
```

**Database connection issues:**
Check DATABASE_URL format and network access.

**Voice processing failures:**
Verify API keys for OpenAI and AddisAI are valid.

**Payment webhooks not working:**
Ensure callback URLs are publicly accessible and properly configured in payment provider dashboards.

## Development Notes

**Telegram Bot Modes:**
- Development: polling mode (bot.py pulls updates)
- Production: webhook mode (Telegram pushes updates)

**TTS Audio Caching:**
Generated audio files cached in `/tts_cache` to reduce API costs.

**Conversation Context:**
User sessions maintained in memory with periodic database sync.

**Multi-turn Conversations:**
Context switching supported - users can switch between search, donate, and info requests mid-conversation.

## Contributing

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation if needed
4. Submit pull request

## License

Proprietary - All rights reserved.
