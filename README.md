# TrustVoice

A Voice-first donation platform for African changemakers. Supports NGO donations and crowdfunding through voice interfaces (Telegram bot, phone calls) with multiple payment methods.

## What Is This?

TrustVoice lets people donate to campaigns and create fundraising projects using their voice. No typing, no forms - just speak naturally in English or Amharic. The system understands what you want and guides you through the process.

**Who Can Use It:**
- Donors: Anyone can donate via voice (no registration required for anonymous donations)
- NGOs: Register and create verified campaigns after admin approval
- Campaign Creators: Launch personal fundraising projects (requires approval)
- Field Agents: Verify project impact and submit reports (requires approval)

**How It Works:**
1. Speak naturally: "Show me education projects in Nairobi"
2. System finds matching campaigns and responds in voice
3. Donate by voice: "I want to donate 100 USD"
4. Choose payment: M-Pesa or card
5. Confirm and complete

## User Capabilities

### For Donors

**What You Can Do:**
- Search campaigns by voice (category, location, urgency)
- Browse active campaigns with voice navigation
- Make donations using natural language
- Track donation history
- Receive voice confirmations and receipts
- Switch between English and Amharic anytime

**How to Donate:**

Via Telegram Bot:
1. Start bot: `/start`
2. Send voice message: "Show campaigns about clean water"
3. Bot lists campaigns and reads them aloud
4. Say: "Donate 50 USD to the first one"
5. Choose M-Pesa or card payment
6. Complete payment and receive confirmation

Via Browser Miniapp:
1. Open campaigns.html or donate.html
2. Click microphone button
3. Speak your search or donation intent
4. System responds with voice + text
5. Follow voice prompts to complete donation

**Anonymous vs Registered:**
- Anonymous: Donate freely, preference saved locally
- Registered: Track donations, sync across devices, manage recurring gifts

### For NGOs

**What You Can Do:**
- Register your organization (requires admin approval)
- Create campaigns with goals and deadlines
- Accept donations via multiple payment methods
- Track campaign progress and donor analytics
- Update campaign status and milestones
- Withdraw funds when goals are met
- Submit impact reports with field verification

**How to Get Started:**

1. Register via Telegram:
```
/register
→ Select "Campaign Creator" or "NGO Admin"
→ Provide organization details via voice
→ Wait for admin approval (usually 24-48 hours)
```

2. Or via Browser:
```
Open ngo-register-wizard.html
→ Click mic, speak each field
→ System guides you through: name, location, mission, registration docs
→ Submit for review
```

3. After Approval:
```
/campaigns → View your campaigns
Create new campaign via voice or create-campaign-wizard.html
Set goal, deadline, description
Campaign goes live after review
```

**Managing Campaigns:**
- Update progress via voice commands
- Respond to donor questions
- Request fund withdrawals when milestones hit
- Submit impact verification reports

### For Campaign Creators

**What You Can Do:**
- Launch personal fundraising projects (medical, education, business)
- Tell your story via voice (no need to write)
- Set funding goals and timelines
- Share campaign links on social media
- Receive donations via M-Pesa or cards
- Update supporters with progress reports
- Withdraw funds when needed

**How to Launch a Campaign:**

1. Register:
```
/register
→ Select "Campaign Creator"
→ Provide personal details
→ Explain why you need to fundraise (voice recording)
→ Wait for approval
```

2. Create Campaign:
```
Open create-campaign-wizard.html
→ Click mic: "Medical treatment for my daughter"
→ System asks: "How much do you need?"
→ You say: "2000 USD for surgery"
→ System: "When do you need it by?"
→ You say: "End of March"
→ Continue answering voice prompts
→ Campaign created and goes live
```

3. Manage Campaign:
```
Check donations: /my_campaigns
Update supporters via voice
Share Telegram link or browser link
```

**Campaign Types:**
- Medical emergencies
- Education fees
- Business startup capital
- Community projects
- Emergency relief

### For Field Agents

**What You Can Do:**
- Verify project completion on the ground
- Submit GPS-tagged photo evidence
- Record voice impact reports
- Validate fund usage
- Approve or flag campaigns for review

**How to Verify Projects:**

1. Register as Field Agent:
```
/register
→ Select "Field Agent"
→ Provide credentials and regions covered
→ Share verification experience
→ Wait for admin approval
```

2. Conduct Verification:
```
Visit project site
Take photos with GPS location
Record voice report: "I visited Mwanza Water Project. 3 wells completed, serving 500 families. Photos attached."
Submit via /verify or miniapp
```

3. System Actions:
```
→ Photos stored with GPS coordinates
→ Voice report transcribed
→ NGO receives verification
→ Donors notified of impact
→ Blockchain receipt updated
```

### For Administrators

**What You Can Do:**
- Review and approve NGO registrations
- Approve campaign creator applications
- Verify field agent credentials
- Monitor platform activity and fraud
- Approve fund withdrawals
- Manage user roles and permissions

**How to Manage:**

1. Review Pending Requests:
```
/admin_requests
→ See all pending registrations
→ Review details, voice recordings, documentation
```

2. Approve or Reject:
```
/admin_approve <id>  → Grant access
/admin_reject <id>   → Deny with reason
```

3. Monitor Activity:
```
Access analytics.html
→ View donation trends
→ Track campaign success rates
→ Monitor voice command patterns
→ Identify fraud patterns
```

## Core Features

## Core Features

**Voice-First Interface:**
- Speak naturally, no keywords required
- Multi-turn conversations (ask follow-up questions)
- Context awareness (system remembers what you're talking about)
- Dual delivery (hear response + see text)

**Language Support:**
- English and Amharic
- Automatic language detection
- Toggle anytime mid-conversation
- Preference saved across sessions

**Payment Methods:**
- M-Pesa (Kenya, Tanzania mobile money)
- Stripe (international credit/debit cards)
- Multi-currency support (KES, USD, EUR, GBP)

**Security:**
- PIN protection for registered users
- Phone number verification
- Admin approval for NGOs and creators
- Blockchain receipts for transparency

**Accessibility:**
- No typing required (voice-only interface available)
- Works on basic smartphones
- Low bandwidth friendly (audio compression)
- Works via Telegram (no app install needed)

## Real-World Usage Examples

**Donor Searching for Campaigns:**
```
User (voice): "Show me urgent medical campaigns in Nairobi"
Bot (voice): "I found 3 urgent medical campaigns in Nairobi. 
              First one is 'Heart Surgery for Baby Amani', needs 150,000 USD, 
              85% funded with 5 days left. Would you like to hear more?"
User (voice): "Yes, tell me about it"
Bot (voice): "Baby Amani is 6 months old and needs urgent heart surgery..."
User (voice): "I want to donate 5000 USD"
Bot (voice): "Great! 5000 USD to Heart Surgery for Baby Amani. 
              How would you like to pay? M-Pesa or card?"
```

**NGO Creating Campaign:**
```
NGO (voice in wizard): "Clean water project in Kisumu"
System (voice): "Great title. How much do you need to raise?"
NGO (voice): "20 000 USD"
System (voice): "When do you need it by?"
NGO (voice): "End of June"
System (voice): "Perfect. Now tell me about the project..."
NGO (voice): "We will drill 5 boreholes in rural Kisumu serving 2000 families 
              who currently walk 3 kilometers for water..."
System (voice): "Excellent. I've drafted your campaign. Review and submit?"
```

**Field Agent Verification:**
```
Agent (voice): "I'm at the Mwanza school project"
System (voice): "Great. What's the status?"
Agent (voice): "Construction is complete. 6 classrooms built, 
                 300 students now attending. Photos uploaded with GPS."
System (voice): "Verified. Impact report saved. NGO and donors will be notified."
```

**Campaign Creator Update:**
```
Creator (voice): "/my_campaigns"
Bot (voice): "You have 1 active campaign: 'Sarah's College Fund'. 
              Currently at 65,000 out of 150,000 USD. 43% funded."
Creator (voice): "Can I withdraw some funds?"
Bot (voice): "You can withdraw up to 60,000 USD (leaving 10% buffer). 
              Would you like to proceed?"
Creator (voice): "Yes, withdraw 50,000 to my M-Pesa"
Bot (voice): "Withdrawal request submitted. Admin will approve within 24 hours."
```

## How Voice Commands Work

**Natural Language Understanding:**
The system doesn't need specific phrases. All these work:

Searching:
- "Show campaigns about education"
- "Find me water projects"
- "What campaigns are in Nairobi?"
- "I want to help kids go to school"

Donating:
- "I want to donate 1000 USD"
- "Give 50 dollars to this campaign"
- "Donate 5000"
- "I'd like to support this with 2000 bob"

Getting Info:
- "Tell me more about this"
- "What's the impact?"
- "How much has been raised?"
- "Who is running this campaign?"

**Multi-turn Conversations:**
```
You: "Show education campaigns"
Bot: [lists campaigns]
You: "Tell me about the second one"
Bot: [explains campaign]
You: "Donate 3000"
Bot: [processes donation]
You: "Actually, show me health campaigns instead"
Bot: [switches context, shows health campaigns]
```

## Platform Access Methods

**1. Telegram Bot (Primary Interface):**
- Add bot: @TrustVoiceBot (search in Telegram)
- Send voice messages or type commands
- Works on any phone with Telegram
- No additional app needed
- Best for: Regular users, quick donations

**2. Browser Miniapps (Secondary Interface):**
- Direct URL access: https://trustvoice.app
- Click-to-speak interface
- Works on phones and computers
- No Telegram required
- Best for: Campaign creation, browsing, admin tasks

**3. Phone Calls (Planned):**
- Dial platform number
- Voice IVR system
- No smartphone needed
- Works on feature phones
- Best for: Rural areas, elderly users

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

**Campaign Transparency:**
- Video uploads with GPS capture
- IPFS permanent storage via Pinata (50MB limit)
- GPS verification against field agent reports
- 500m verification threshold for location matching

**Blockchain Tax Receipts:**
- NFT tax receipts minted on Base/Polygon networks
- ERC-721 standard with metadata on IPFS
- Donor wallet addresses for blockchain verification
- Transaction tracking and explorer links
- ~$0.01 per NFT mint cost

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
- `POST /api/campaigns/{id}/video` - Upload campaign video (with GPS)
- `GET /api/campaigns/{id}/video` - Get video details + GPS verification
- `DELETE /api/campaigns/{id}/video` - Delete campaign video
- `GET /api/campaigns/{id}/verify-location` - Verify GPS match with field agent

**Donations:**
- `POST /api/donations/` - Record donation
- `GET /api/donations/` - List donations
- `GET /api/donations/{id}` - Get donation details
- `POST /api/donations/{id}/mint-nft-receipt` - Mint blockchain NFT receipt
- `GET /api/donations/{id}/nft-receipt` - Get NFT receipt details
- `GET /api/donations/{id}/verify-receipt` - Verify NFT on blockchain
- `GET /api/donations/user/{user_id}/tax-summary` - Annual tax summary

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
- Pinata API credentials (for IPFS video storage)
- Web3 provider RPC URL (Alchemy/Infura for blockchain)
- Foundry (for smart contract development)

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

# IPFS (Pinata)
PINATA_API_KEY=your-pinata-api-key
PINATA_API_SECRET=your-pinata-secret
PINATA_JWT=your-pinata-jwt

# Blockchain (Base/Polygon)
WEB3_PROVIDER_URL=https://base-mainnet.g.alchemy.com/v2/your-key
BASE_SEPOLIA_RPC_URL=https://base-sepolia.g.alchemy.com/v2/your-key
CONTRACT_ADDRESS=0x... (deployed NFT contract address)
PRIVATE_KEY_SEP=0x... (deployment wallet private key - NEVER commit)
ETHERSCAN_API_KEY=your-etherscan-api-key

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

### Smart Contract Deployment

1. Navigate to blockchain directory:
```bash
cd blockchain
```

2. Compile contracts:
```bash
forge build
```

3. Run tests:
```bash
forge test
```

4. Deploy to Base Sepolia testnet:
```bash
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $BASE_SEPOLIA_RPC_URL \
  --private-key $PRIVATE_KEY_SEP \
  --broadcast \
  --verify \
  --verifier-url "https://api.etherscan.io/v2/api?chainid=84532" \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --via-ir
```

5. Update .env with deployed contract address

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
- Send voice message: "Donate 100 USD to campaign X"
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

### M-Pesa 

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
