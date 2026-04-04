# AI for Good Impact Awards - Application Draft

Prepared answers for Sections 3 and 4 of the ITU AI for Good Impact Awards application form.

---

## Section 3: AI Solution Overview

### Name of the Project

TrustVoice

### Brief description of your AI solution

TrustVoice is a voice-first donation and crowdfunding platform for African changemakers. It allows users to discover, donate to, and manage fundraising campaigns entirely through natural voice conversation, in English or Amharic. The platform combines real-time conversational AI (LiveKit agents with GPT-4o-mini, Deepgram Nova-2 STT, OpenAI TTS), multi-channel delivery (web, Telegram, IVR), and a blockchain-backed transparency layer (ERC-721 NFT tax receipts, on-chain milestone audit trails) to remove barriers. Users who cannot read or type, or who lack access to credit cards, can still fund projects using their voice and mobile money (M-Pesa). Field agents verify project impact on the ground with GPS-tagged photo reports, and funds are released only after milestones are independently verified.

### AI technology used

- [x] Machine Learning (ML)
- [x] Deep Learning
- [x] Natural Language Processing (NLP)
- [x] Large Language Models
- [ ] Computer Vision
- [ ] Reinforcement Learning
- [x] Speech Recognition
- [ ] Anomaly Detection
- [x] Generative AI
- [ ] Other

### Problem addressed, target users, and approach

**Problem:**
Charitable giving and crowdfunding in Africa face three compounding barriers. First, low digital literacy means many potential donors and beneficiaries cannot navigate form-based web platforms. Second, credit card penetration sits at roughly 15% across the continent, locking out the vast majority from platforms like GoFundMe or Patreon. Third, donors worldwide distrust where their money goes. Opacity in fund usage, combined with limited verification infrastructure, suppresses giving.

**Target users:**

- Donors (including diaspora communities) who want to fund African projects with confidence that money reaches its destination
- NGOs and community organizations that need to raise funds and demonstrate impact to retain donor trust
- Campaign creators (individuals raising money for education, medical, or business needs)
- Field agents who verify project progress on the ground and earn income ($30 USD per approved verification)
- Platform administrators who approve registrations, manage payouts, and monitor the system

**Approach:**

The platform is built around three core principles:

1. Voice-first interaction: A real-time conversational AI agent (built on LiveKit agents v1.4.5 with Deepgram Nova-2 for streaming STT, GPT-4o-mini for intent understanding and response generation, and OpenAI TTS for speech output) handles the full user journey by voice. Users say "I want to donate to a clean water project" and the agent searches campaigns, confirms the choice, processes the payment, and delivers a receipt, all in a single conversation. For Amharic speakers, a dedicated pipeline uses AddisAI for STT and TTS, with a local HuggingFace Whisper model (b1n1yam/shook-medium-amharic-2k) as fallback. The voice agent has 13 function tools that cover searching campaigns, making donations, checking history, creating campaigns, submitting milestone evidence, verifying milestones, releasing funds, and approving payouts, meaning the entire platform can be operated without touching a screen.

2. Mobile money native payments: M-Pesa STK Push integration lets users pay directly from their phone's mobile wallet. No credit card, no bank account needed. Stripe handles card payments for international donors. Crypto/Web3 is available for blockchain-native users.

3. Transparent fund tracking with milestone-based releases: Donations flow into campaigns that define milestones. Funds are not released in a lump sum. Instead, field agents travel to project sites, upload GPS-tagged photos and observation reports, and receive a trust score (0-100). Scores of 80 or above trigger automatic milestone approval. Every milestone event is recorded on-chain via a MilestoneTreasury smart contract (Solidity/Foundry), and donors receive ERC-721 NFT tax receipts stored on IPFS, creating an immutable audit trail from donation to impact.

### Operational readiness

The platform is at the **MVP/Pilot** stage. The full stack is built and deployed on Railway as three services: a FastAPI web API, a Celery background worker, and a LiveKit voice agent. The frontend is a React SPA with full bilingual support (English and Amharic). An automated test suite covers voice pipeline, donation flows, payment integrations, field agent workflows, and authentication.

### Evidence of functionality

- The voice agent is live and operational, handling real-time conversations via WebRTC (LiveKit Cloud). Users connect from the React frontend, speak naturally, and the agent executes actions through 13 function tools. Conversations are transcribed and displayed in real time with speaker labels.
- The agent pushes structured visual data (payment links, campaign cards, donation receipts, admin summaries) to the frontend during conversations via LiveKit's reliable data channel, so users see actionable UI alongside the spoken interaction.
- Stripe and M-Pesa payment flows are integrated with webhook confirmation, tested end-to-end with test keys.
- The NLU layer (GPT-4o-mini with structured JSON output) handles 14 distinct intents: donate, search_campaigns, campaign_details, register_ngo, create_campaign, check_donations, admin_approve, admin_reject, field_verify, update_milestone, analytics_query, set_preference, help, and general_question.
- The field agent pipeline supports photo upload, GPS capture, observation submission, trust scoring, and payout tracking.
- Two Solidity contracts (TaxReceiptNFT and MilestoneTreasury) are written and compiled with Foundry, targeting low-fee EVM chains (Polygon, Base, Arbitrum).
- The Telegram bot provides an alternate entry point for users without web access.
- 346 automated tests validate the system across voice, payments, auth, field verification, analytics, and language routing.

---

## Section 4: Solution Details

### Innovation

TrustVoice introduces several innovations to the charitable giving and crowdfunding space:

**Voice as the primary interface, not an add-on.** Most donation platforms bolt voice onto an existing form-based UI. TrustVoice was designed voice-first from the start. The LiveKit agent carries 13 function tools that cover the entire platform workflow. A user can register an NGO, create a campaign, donate, check their history, submit milestone evidence, verify milestones, release funds, and approve payouts, all through natural speech. The visual UI exists as a complement, not a prerequisite.

**Real-time structured data delivery during voice conversations.** While the agent speaks, it simultaneously pushes structured visual cards (payment links, campaign progress, donation receipts, admin dashboards) to the user's screen via LiveKit's reliable data channel. This dual-delivery approach (spoken audio + visual action cards) is not standard in voice AI applications. It allows financial transactions to happen within the voice session rather than requiring the user to leave the conversation and navigate a separate UI.

**Bilingual AI pipeline for underserved languages.** English voice AI is well-served by commercial APIs, but Amharic (spoken by 57M+ people) is not. TrustVoice integrates AddisAI, a native Ethiopian AI provider, for Amharic STT and TTS, with a local HuggingFace Whisper model (b1n1yam/shook-medium-amharic-2k, 1.5GB) as an offline fallback. This three-tier approach (commercial API, regional provider, local model) gives resilience for a language with limited cloud AI coverage.

**Field agent verification with on-chain audit trail.** The verification pipeline physically connects donated funds to outcomes. Field agents visit project sites, upload GPS-tagged photos, write observations, and count beneficiaries. Their reports receive automatic trust scores. This verification is then recorded on-chain via the MilestoneTreasury smart contract, creating an immutable record that donors, auditors, and regulators can inspect independently. The field agent role also creates income: $30 USD per approved verification, paid via M-Pesa.

**NFT tax receipts for charitable donations.** The TaxReceiptNFT contract mints an ERC-721 token per donation, with metadata stored on IPFS. Receipts are optionally soulbound (non-transferable) and can be verified by tax authorities. This replaces paper or PDF receipts with a cryptographically verifiable, permanent record.

### Impact and scalability

**Current reach and potential:**

The platform targets two populations: African communities seeking to fund local projects, and diaspora/global donors who want transparent giving channels. Sub-Saharan Africa has 500M+ mobile money accounts but roughly 15% credit card penetration, meaning conventional donation platforms cannot serve the majority. By integrating M-Pesa directly, TrustVoice reaches users that Stripe-only platforms cannot.

**Measurable indicators:**

- The system tracks donations per campaign, amount raised vs. goal, currency breakdown (USD, EUR, GBP, KES), donor count, field verification completion rates, trust scores, milestone completion rates, and payout turnaround times. All of these are stored in the database and surfaced through the analytics API.
- Conversation metrics (daily aggregated stats) track engagement: how many voice sessions, intents resolved, languages used.
- Field agent activity is tracked per verification: GPS coordinates, photo count, beneficiary count, trust score, and payout status.

**Scalability architecture:**

- The backend is a stateless FastAPI application deployed on Railway with horizontal scaling. Background tasks run on a Celery worker with Redis as the broker.
- The LiveKit agent runs as a separate containerized service (Python 3.12-slim Docker image) that can scale independently based on concurrent voice sessions.
- The database is PostgreSQL (Neon Cloud), which supports connection pooling and read replicas.
- Payment processing is delegated to Stripe and Safaricom (M-Pesa), both of which handle their own scaling.
- The blockchain layer records only audit events (milestone state changes, receipt minting), not fund custody, keeping gas costs minimal on Layer 2 chains.

**Growth path:**

Adding new languages requires integrating an additional STT/TTS provider and adding an i18n translation file. The Amharic pipeline demonstrates this pattern. Swahili (100M+ speakers across East Africa) and French (widespread in West Africa) are logical next additions using the same three-tier approach.

### Sustainability

**Revenue model:**

The platform charges a small platform fee on milestone fund releases, tracked in the `PlatformFee` ledger table. NGOs themselves pay zero platform fees for receiving donations. The fee is applied at the point of fund release, not at donation time, aligning the platform's revenue with verified project outcomes rather than transaction volume.

**Operational costs:**

- Voice AI costs scale per-session: Deepgram Nova-2 for STT, GPT-4o-mini for LLM (chosen specifically for cost-efficiency over GPT-4o), and OpenAI TTS. For Amharic, AddisAI provides a regional pricing tier, and the local HuggingFace model provides a zero-marginal-cost fallback.
- Infrastructure runs on Railway with auto-scaling. The three-service architecture (web, worker, agent) means each component scales independently based on its own load profile.
- Blockchain costs are kept minimal by recording only audit trail events on Layer 2 EVM chains (Polygon, Base, Arbitrum) where gas fees are fractions of a cent.
- M-Pesa transaction fees are borne by the standard Safaricom fee schedule, which is already understood and accepted by the user base.

**Long-term viability:**

The platform is built on open protocols (WebRTC via LiveKit, EVM-compatible blockchains, standard REST APIs) rather than proprietary lock-in. The voice agent framework (livekit-agents) is open source. The smart contracts use OpenZeppelin standards. This reduces vendor dependency and allows the platform to migrate providers as costs and capabilities evolve.

### Contribution to global challenges

TrustVoice directly addresses several challenges outlined in the UN Sustainable Development Goals:

**Reducing inequality (SDG 10):** The platform removes three gatekeepers that exclude the majority of Africans from digital financial participation: literacy requirements (voice-first interface), credit card requirements (M-Pesa native), and English-only interfaces (Amharic support, with architecture ready for additional languages). A person who cannot read, has no bank account, and speaks only Amharic can still discover and fund a community project.

**Decent work and economic growth (SDG 8):** Field agents earn $30 USD per approved verification, creating a new income stream for people in project communities. This incentivized verification model turns transparency from a cost center into a job creation mechanism.

**Clean water, health, education (SDGs 3, 4, 6):** The platform's campaign categories include health, education, water, agriculture, and emergency relief. The NLU layer recognizes these categories and routes voice queries accordingly. Example campaigns in the seed data include "Clean Water for Mwanza" and education-focused fundraisers.

**Peace, justice, and strong institutions (SDG 16):** The blockchain audit trail (MilestoneTreasury contract) and NFT tax receipts (TaxReceiptNFT contract) create verifiable, tamper-proof records of fund flows. Field agent GPS-tagged verification reports provide physical evidence that funds reached their stated purpose. This infrastructure supports institutional accountability without requiring the institutions themselves to build the technology.

**Partnerships for the goals (SDG 17):** The platform connects global diaspora donors to local African communities through a single voice conversation. It integrates international payment rails (Stripe) with local payment rails (M-Pesa), bridging financial ecosystems that typically operate in isolation.

### Ethical Considerations

**Data privacy and consent:**

- User authentication uses bcrypt-hashed passwords and PINs with account lockout after 5 failed attempts. JWT tokens expire after 30 minutes.
- Voice conversations are processed in real time and not stored as raw audio. Transcription segments exist during the session for display purposes. Conversation logs store text summaries for debugging, not audio recordings.
- The Telegram bot integration respects the user's existing Telegram privacy settings and does not request additional permissions beyond message handling.

**Bias and language equity:**

- The Amharic pipeline uses a regional AI provider (AddisAI) that is trained on Ethiopian speech patterns, rather than relying on global models that underperform on African languages. The local HuggingFace model fallback ensures service continues even if the API is unavailable.
- The NLU layer uses structured JSON output from GPT-4o-mini with explicitly defined intents and entity schemas, reducing the risk of open-ended hallucination in financial contexts.

**Financial safeguards:**

- All financial voice actions (donations, payout approvals, fund releases) require explicit verbal confirmation before execution. The agent does not process payments on ambiguous intent.
- Role-based access control gates every function tool. A donor cannot approve payouts. A field agent cannot release milestone funds. An NGO admin cannot access other organizations' data.
- Milestone-based fund releases prevent lump-sum misuse. Funds are held until an independent field agent verifies the milestone on-site.

**Transparency of AI involvement:**

- The voice panel clearly identifies the AI agent ("AI" speaker label in transcripts, "VBV Voice" branding). Users know they are speaking with an AI system.
- Action cards pushed during conversations show the source data (campaign details, amounts, payment methods) so users can verify what the AI is acting on.

**Blockchain and environmental impact:**

- Smart contracts target Layer 2 EVM chains (Polygon, Base, Arbitrum) which use proof-of-stake consensus, minimizing energy consumption compared to proof-of-work chains.
- The MilestoneTreasury contract records events only (it does not custody funds on-chain), keeping transaction volume and associated energy use minimal.
