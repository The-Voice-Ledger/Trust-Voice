# Trust-Voice Web Frontend & Agentic AI Assistant

> **Purpose:** Replication guide for The Voice Ledger sister project.
> Covers the full-stack architecture of the React SPA frontend and the GPT function-calling agent that powers the unified AI assistant.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Tech Stack](#2-tech-stack)
3. [Frontend Structure](#3-frontend-structure)
4. [The Agentic Assistant (Backend)](#4-the-agentic-assistant-backend)
5. [The Assistant Page (Frontend)](#5-the-assistant-page-frontend)
6. [Voice Pipeline](#6-voice-pipeline)
7. [API Contract](#7-api-contract)
8. [State Management](#8-state-management)
9. [Replication Checklist](#9-replication-checklist)

---

## 1. Architecture Overview

```
                        Browser (React SPA at /app)
                                  |
                     ┌────────────┴────────────┐
                     │      Assistant.jsx       │
                     │  useChat() local state   │
                     │  VoiceManager singleton  │
                     └────────┬───────┬─────────┘
                 voiceAgent() │       │ textAgent()
                  (FormData)  │       │ (JSON body)
                              ▼       ▼
                 POST /voice/agent   POST /voice/agent/text
                              │       │
                     ┌────────┴───────┴─────────┐
                     │     agent_router.py       │
                     │   (FastAPI, prefix=/voice)│
                     │                           │
                     │   Audio? ──► ASR (Whisper) │
                     │        ▼                  │
                     │ _run_agent_with_fallback() │
                     └────────────┬──────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼              ▼
              AgentExecutor   NLU fallback   Generic error
              (GPT + tools)   (legacy)       (tier 3)
                    │
          ┌─────────┴──────────┐
          │  OpenAI GPT-4o-mini │
          │  function calling   │
          │  loop (max 6 turns) │
          └─────────┬──────────┘
                    │ dispatches
          ┌─────────┼─────────────┐
          ▼         ▼             ▼
      READ tools  WRITE tools  Platform tools
     (direct DB)  (handlers)   (lang, help)
          │         │
          ▼         ▼
       PostgreSQL  Business logic
       (SQLAlchemy) (existing handlers)
```

**Key design decisions:**
- Two endpoints replace 7+ legacy voice endpoints: one for audio, one for text
- Three-tier fallback: agent -> NLU -> error (ensures the user always gets a response)
- READ tools query the DB directly for speed; WRITE tools delegate to existing business logic handlers so validation/side-effects are reused
- Conversation history stored in Redis with 30-message cap and 30-minute TTL
- Response includes both `response_text` (for display/TTS) and typed `data` + `response_type` (for rich card rendering)

---

## 2. Tech Stack

### Frontend

| Dependency | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| Vite | 7.x | Build tool, dev server, proxy |
| Tailwind CSS | 4.x | Utility-first styling (via `@tailwindcss/vite`) |
| React Router | 7.x | Client-side routing (`basename="/app"`) |
| Zustand | 5.x | Global state management (auth, voice) |
| i18next + react-i18next | 25.x / 16.x | Internationalization (English, Amharic) |
| react-icons | 5.x | Icon library (Heroicons 2 + Material Design) |
| Swiper | 12.x | Campaign carousel on Landing page |

No `tailwind.config.js` is needed. Tailwind 4.0 uses `@import "tailwindcss"` in `index.css` and the Vite plugin handles the rest.

### Backend (relevant to the assistant)

| Component | Technology |
|-----------|------------|
| Web framework | FastAPI |
| LLM | OpenAI GPT-4o-mini (function calling) |
| ASR | OpenAI Whisper (via `voice.asr.asr_infer`) |
| TTS | Custom provider (`voice.tts.tts_provider`) |
| Session store | Redis (conversation history) |
| Database | PostgreSQL via SQLAlchemy (async) |

### Environment Variables (Agent-specific)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `AGENT_MODEL` | `gpt-4o-mini` | Model for the agent loop |
| `AGENT_MAX_TURNS` | `6` | Max tool-call iterations per request |
| `AGENT_TEMPERATURE` | `0.2` | Sampling temperature |
| `AGENT_HISTORY_TTL` | `1800` | Redis key TTL in seconds (30 min) |

---

## 3. Frontend Structure

### Entry Point & Routing

```
web-frontend/
  vite.config.js        # base: '/app/', proxy /api -> :8001
  src/
    main.jsx            # <BrowserRouter basename="/app"> wrapping <App />
    App.jsx             # Route definitions + layout shell
    index.css           # @import "tailwindcss" + custom utilities
    i18n.js             # i18next setup (en.json, am.json)
```

**`vite.config.js`**
```js
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/app/',
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8001', changeOrigin: true },
      '/ws':  { target: 'ws://localhost:8001', ws: true },
    },
  },
});
```

**`App.jsx` Layout & Routes**
```jsx
<Navbar />
<main className="pb-20 sm:pb-0">
  <Routes>
    <Route path="/"                element={<Landing />} />
    <Route path="/campaigns"       element={<Home />} />
    <Route path="/campaign/:id"    element={<CampaignDetail />} />
    <Route path="/donate"          element={<DonateCheckout />} />
    <Route path="/donate/:campaignId" element={<DonateCheckout />} />
    <Route path="/analytics"       element={<Analytics />} />
    <Route path="/admin"           element={<AdminPanel />} />
    <Route path="/register-ngo"    element={<RegisterNgo />} />
    <Route path="/create-campaign" element={<CreateCampaign />} />
    <Route path="/field-agent"     element={<FieldAgent />} />
    <Route path="/assistant"       element={<Assistant />} />
    <Route path="/login"           element={<Login />} />
    <Route path="/dashboard"       element={<Dashboard />} />
  </Routes>
</main>
<Footer />
<MobileBottomNav />
```

### Page Inventory

| Page | File | Role |
|------|------|------|
| Landing | `pages/Landing.jsx` | Marketing page with hero, stats, Swiper carousel, feature cards, CTA |
| Campaigns | `pages/Home.jsx` | Campaign grid with search, category filters, sort, pagination |
| Campaign Detail | `pages/CampaignDetail.jsx` | Single campaign with progress bar, donate CTA |
| Donate | `pages/DonateCheckout.jsx` | Donation form with M-Pesa/Stripe |
| Analytics | `pages/Analytics.jsx` | Summary cards, funnel chart, event feed, daily table |
| **Assistant** | **`pages/Assistant.jsx`** | **Unified AI assistant (voice + text chat)** |
| Admin | `pages/AdminPanel.jsx` | Tabs: registrations, users, NGOs, campaigns |
| Register NGO | `pages/RegisterNgo.jsx` | Multi-step wizard with voice hints |
| Create Campaign | `pages/CreateCampaign.jsx` | Multi-step wizard with video upload |
| Field Agent | `pages/FieldAgent.jsx` | GPS-verified field report submission |
| Login | `pages/Login.jsx` | Username/phone + 4-digit PIN |
| Dashboard | `pages/Dashboard.jsx` | User's donations, receipts, active campaigns |

### Component Inventory

| Component | File | Purpose |
|-----------|------|---------|
| Navbar | `components/Navbar.jsx` | Sticky top nav, desktop primary + "More" dropdown, mobile hamburger |
| MobileBottomNav | `components/MobileBottomNav.jsx` | Fixed bottom bar (mobile only), 5 items with center Assistant button |
| Footer | `components/Footer.jsx` | 4-column footer links, trust badges, logo |
| CampaignCard | `components/CampaignCard.jsx` | Campaign grid card with category icon, progress bar |
| ProgressBar | `components/ProgressBar.jsx` | Animated gradient progress bar |
| DonationForm | `components/DonationForm.jsx` | Amount selection, payment method, donor info |
| LanguageToggle | `components/LanguageToggle.jsx` | EN/AM language switcher |
| VoiceButton | `components/VoiceButton.jsx` | Standalone mic button (used in some legacy pages) |
| SkeletonCard | `components/SkeletonCard.jsx` | Loading skeleton for campaign grid |

---

## 4. The Agentic Assistant (Backend)

### File Layout

```
voice/
  agent/
    __init__.py       # Package init, re-exports AgentExecutor
    tools.py          # 13 OpenAI function-calling tool schemas
    executor.py       # Agent loop, Redis history, tool dispatch
  routers/
    agent_router.py   # FastAPI endpoints, ASR/TTS integration, fallback
```

### 4.1 Tool Schemas (`voice/agent/tools.py`)

`AGENT_TOOLS` is a Python list of 13 dicts conforming to the OpenAI function-calling format. Each tool has `type: "function"` and a `function` object with `name`, `description`, and `parameters` (JSON Schema).

| # | Tool | Category | Required Params | Optional Params |
|---|------|----------|-----------------|-----------------|
| 1 | `search_campaigns` | Discovery | -- | `category` (enum: 8), `location`, `keyword` |
| 2 | `get_campaign_details` | Discovery | `campaign_id` (int) | -- |
| 3 | `make_donation` | Donation | `campaign_id`, `amount` | `currency` (7 options), `payment_method` |
| 4 | `check_donation_status` | Donation | -- | `donation_id` (UUID) |
| 5 | `view_donation_history` | Donation | -- | `limit` (int) |
| 6 | `create_campaign` | NGO | `title`, `description`, `goal_amount`, `category` | `location` |
| 7 | `register_ngo` | NGO | `name`, `description` | `website`, `country` |
| 8 | `view_my_campaigns` | NGO | -- | -- |
| 9 | `submit_field_report` | Field | `campaign_id`, `description` | `verification_status` |
| 10 | `withdraw_funds` | Field | `campaign_id` | `amount` |
| 11 | `get_platform_stats` | Platform | -- | -- |
| 12 | `change_language` | Platform | `language` (en/am) | -- |
| 13 | `get_help` | Platform | -- | -- |

**Tool description pattern:** Natural language instructions to the LLM that include usage constraints, e.g. `"ALWAYS confirm the amount and campaign with the user before calling this tool"`.

**Schema example:**
```python
{
    "type": "function",
    "function": {
        "name": "search_campaigns",
        "description": "Search for active donation campaigns. Use when the user wants to find, browse, or discover campaigns.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["water", "education", "health", "infrastructure", "food", "environment", "shelter", "children"],
                    "description": "Filter by category"
                },
                "location": { "type": "string", "description": "Filter by location/country/region" },
                "keyword":  { "type": "string", "description": "Search keyword for campaign title or description" }
            },
            "required": []
        }
    }
}
```

### 4.2 Agent Executor (`voice/agent/executor.py`)

#### Redis Conversation History

```python
AGENT_KEY_PREFIX = "agent_conv"
AGENT_MAX_HISTORY = 30              # messages retained
AGENT_HISTORY_TTL = int(os.getenv("AGENT_HISTORY_TTL", "1800"))  # 30 min

# Key format: agent_conv:{user_id}:{conversation_id}
# Value: JSON array of {role, content, tool_calls?, tool_call_id?}
```

Helper functions:
- `_redis()` -- lazy import of `redis_client`; returns `None` if unavailable (graceful degradation)
- `_get_history(user_id, conversation_id)` -- loads and parses JSON
- `_save_history(user_id, conversation_id, messages)` -- trims to last 30, saves with TTL

#### System Prompt Builder

`_build_system_prompt(user_id, db, language, context)` constructs a prompt that includes:

1. Platform identity and role description
2. User's name, role, and language
3. Amharic instruction (when `language == "am"`)
4. Page context (current page, selected campaign) from the frontend's `context` dict
5. Six behavioral rules:
   - Keep responses concise (2-3 sentences)
   - Use tools for real data; don't fabricate
   - Handle compound requests (e.g., "search AND donate")
   - Confirm before executing write operations
   - Always reference specific campaign IDs
   - Never guess -- ask the user if unclear

#### AgentExecutor Class

```python
class AgentExecutor:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("AGENT_MODEL", "gpt-4o-mini")
        self.max_turns = int(os.getenv("AGENT_MAX_TURNS", "6"))
        self.temperature = float(os.getenv("AGENT_TEMPERATURE", "0.2"))

    async def run(self, user_message, user_id, db, language="en",
                  conversation_id=None, context=None) -> dict:
        # Returns: {
        #   conversation_id, response_text, response_type,
        #   data, tools_used
        # }
```

**`run()` flow:**

1. Generate `conversation_id` if not provided (`uuid4`)
2. Load history from Redis
3. Build system prompt with user context
4. Construct messages: `[system] + history + [user_message]`
5. **Tool-calling loop** (up to `max_turns` iterations):
   - Call OpenAI `chat.completions.create(model, messages, tools=AGENT_TOOLS, tool_choice="auto")`
   - If `finish_reason != "tool_calls"` -- extract final text, break
   - For each tool call in response:
     - Parse `function.name` and `function.arguments` (JSON)
     - Dispatch via `_execute_tool(name, args, user_id, db)`
     - Append tool call message + tool result message to conversation
     - Track tool name in `tools_used` list
6. Post-loop: collect structured data from last tool result
7. Save history to Redis (excluding system prompt)
8. Derive `response_type` from data keys:
   - `campaigns` key -> `campaign_list`
   - `campaign` key -> `campaign_detail`
   - `donation` key with success markers -> `donation_confirmation`
   - `donations` key -> `donation_history`
   - `stats` key -> `analytics_summary`
   - Otherwise -> `text`

#### Tool Dispatch

`_execute_tool(name, args, user_id, db)` maps tool names to handler methods:

**READ tools** (direct SQLAlchemy queries for speed):
| Tool | Method | Query |
|------|--------|-------|
| `search_campaigns` | `_tool_search_campaigns` | Filter `Campaign` by category, location (ILIKE on region/country/description), keyword (ILIKE on title/description), limit 10 |
| `get_campaign_details` | `_tool_get_campaign_details` | Single `Campaign` lookup by ID |
| `view_donation_history` | `_tool_view_donation_history` | Resolve user -> `Donor` (via telegram_user_id) -> `Donation` join `Campaign`, limit 20 |
| `view_my_campaigns` | `_tool_view_my_campaigns` | Resolve user -> `NGOOrganization` (via admin_user_id) -> campaigns |
| `get_platform_stats` | `_tool_get_platform_stats` | Aggregate: count(active campaigns), count(donations), sum(completed amounts), count(donors) |
| `get_help` | `_tool_get_help` | Static role-aware capability list |

**WRITE tools** (delegate to existing handler modules):
| Tool | Delegates To |
|------|-------------|
| `make_donation` | `voice.handlers.donation_handler.initiate_voice_donation` |
| `check_donation_status` | `voice.handlers.donation_handler.get_donation_status` |
| `create_campaign` | `voice.handlers.ngo_handlers.handle_create_campaign` |
| `register_ngo` | `voice.handlers.ngo_handlers.handle_register_ngo` |
| `submit_field_report` | `voice.handlers.ngo_handlers.handle_field_report` |
| `withdraw_funds` | `voice.handlers.ngo_handlers.handle_withdraw_funds` |
| `change_language` | `voice.handlers.general_handlers.handle_change_language` |

### 4.3 Router Endpoints (`voice/routers/agent_router.py`)

**Router:** `APIRouter(prefix="/voice", tags=["agent"])`

**Singleton:** `_agent = AgentExecutor()` (one instance for the app lifetime)

#### `POST /voice/agent` (voice input)

| Param | Type | Default | Source |
|-------|------|---------|--------|
| `audio` | UploadFile | *(required)* | FormData |
| `user_id` | str | `"web_anonymous"` | FormData |
| `user_language` | str | `"en"` | FormData |
| `conversation_id` | str | None | FormData |
| `context` | str (JSON) | None | FormData |

**Flow:**
1. Parse `context` from JSON string
2. Save audio to temp file (extension from content-type mapping: webm/ogg/wav/mp3/mp4/flac)
3. `transcribe_audio(path, language)` via Whisper -- get transcript + detected language
4. If empty transcript -> return `{ success: false, error: "no_speech" }`
5. `_run_agent_with_fallback(transcript, ...)`
6. `_generate_tts(response_text, language)` -> audio URL
7. Return full response
8. Cleanup: close DB session, delete temp file

#### `POST /voice/agent/text` (text input)

**Pydantic body:**
```python
class TextAgentRequest(BaseModel):
    text: str
    user_id: str = "web_anonymous"
    user_language: str = "en"
    conversation_id: Optional[str] = None
    context: Optional[dict] = None
```

Same flow as voice, minus ASR. Still generates TTS for accessibility.

#### Three-Tier Fallback (`_run_agent_with_fallback`)

```python
async def _run_agent_with_fallback(text, user_id, db, language, conv_id, context):
    try:
        # Tier 1: Agent executor (GPT function calling)
        result = await _agent.run(text, user_id, db, language, conv_id, context)
        result["response_source"] = "agent"
    except Exception as agent_err:
        try:
            # Tier 2: Legacy NLU pipeline (intent classification + command router)
            intent_data = extract_intent_and_entities(text, language)
            response = await route_command(intent_data, user_id, db, language)
            result = { ..., "response_source": "fallback_nlu", "agent_error": str(agent_err) }
        except Exception as fallback_err:
            # Tier 3: Generic error
            result = { ..., "response_source": "fallback_failed",
                       "agent_error": str(agent_err), "fallback_error": str(fallback_err) }
    return result
```

#### TTS Helper

```python
async def _generate_tts(text, language):
    provider = TTSProvider()
    cleaned = clean_text_for_tts(text)
    filename = await provider.synthesize(cleaned, language)
    return f"/api/voice/audio/{filename}"  # or None on failure
```

---

## 5. The Assistant Page (Frontend)

### File: `web-frontend/src/pages/Assistant.jsx` (~620 lines)

This is the core chat interface -- a full-screen conversational UI with voice and text input, rich response rendering, and TTS auto-playback.

### 5.1 Local State: `useChat()` Hook

```jsx
function useChat() {
  const [messages, setMessages] = useState([]);      // chat history
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);

  const addMessage = useCallback((msg) => {
    setMessages(prev => [...prev, { ...msg, id: Date.now() + Math.random() }]);
  }, []);

  const clear = useCallback(() => { setMessages([]); setConversationId(null); }, []);

  return { messages, conversationId, setConversationId, loading, setLoading, addMessage, clear };
}
```

Messages are local/per-session. Backend handles persistence via Redis.

**Message shape:**
```js
{
  id: number,               // unique client ID
  role: 'user' | 'assistant',
  text: string,
  responseType?: string,    // campaign_list, campaign_detail, etc.
  data?: object,            // structured data for rich cards
  audioUrl?: string,        // TTS audio URL
  toolsUsed?: string[],     // which agent tools were called
  isVoice?: boolean,        // if user sent via voice
}
```

### 5.2 Main Component State & Refs

```jsx
const user = useAuthStore(s => s.user);
const language = useVoiceStore(s => s.language);
const userId = user?.id || user?.telegram_user_id || 'web_anonymous';

const [input, setInput] = useState('');
const [voiceStatus, setVoiceStatus] = useState('idle'); // idle | recording | processing
const [autoSpeak, setAutoSpeak] = useState(true);
const scrollRef = useRef(null);   // messages scroll container
const inputRef = useRef(null);    // textarea
const audioRef = useRef(null);    // current Audio object
```

### 5.3 Core Callbacks

**`sendText(text)`** -- text message flow:
```jsx
const sendText = useCallback(async (text) => {
  if (!text.trim() || loading) return;
  addMessage({ role: 'user', text: text.trim() });
  setInput('');
  setLoading(true);
  try {
    const res = await textAgent(text.trim(), userId, language, conversationId);
    if (res.conversation_id) setConversationId(res.conversation_id);
    addMessage({
      role: 'assistant',
      text: res.response_text,
      responseType: res.response_type || 'text',
      data: res.data || {},
      audioUrl: res.audio_url,
      toolsUsed: res.tools_used || [],
    });
    await playAudio(res.audio_url);
  } catch (err) {
    addMessage({ role: 'assistant', text: err.message, responseType: 'error' });
  } finally {
    setLoading(false);
  }
}, [loading, userId, language, conversationId, ...]);
```

**Voice recording flow:**
```jsx
startVoice()  -> stopAudio() + voiceManager.startRecording()
stopVoice()   -> voiceManager.stopRecording() -> hasSound() check
                 -> voiceAgent(blob, userId, language, conversationId)
                 -> add transcription message + assistant response + playAudio()
cancelVoice() -> voiceManager.stopRecording() + reset status
```

**Deep-link support:**
```jsx
// ?campaign=<id> auto-asks about a campaign
useEffect(() => {
  const campaignId = searchParams.get('campaign');
  if (campaignId && !deepLinkHandled.current) {
    deepLinkHandled.current = true;
    setSearchParams({}, { replace: true });
    setTimeout(() => sendText(`Tell me about campaign #${campaignId}`), 300);
  }
}, [searchParams, sendText]);
```

### 5.4 UI Structure

```
┌──────────────────────────────────────────┐
│  Header                                  │
│  [Icon] TrustVoice Assistant             │
│  [Auto-speak toggle] [Clear button]      │
├──────────────────────────────────────────┤
│  Messages area (scrollable)              │
│                                          │
│  (empty) -> WelcomeScreen with           │
│             4 suggestion buttons         │
│                                          │
│  User bubble (blue, right-aligned)       │
│  Assistant bubble (white, left-aligned)  │
│    + optional rich card below            │
│    + optional audio replay button        │
│                                          │
│  Loading indicator (3 bouncing dots)     │
├──────────────────────────────────────────┤
│  Input bar                               │
│  [Recording overlay if active]           │
│  [Mic btn] [Textarea] [Send btn]         │
│  Disclaimer text                         │
└──────────────────────────────────────────┘
```

### 5.5 Rich Response Cards

Each card is rendered conditionally based on `msg.responseType`:

**`CampaignListCard`** -- clickable list of up to 5 campaigns, each with:
- Campaign ID badge, title, progress bar, progress %, category, location, raised/goal amounts
- Links to `/campaign/:id`

**`CampaignDetailCard`** -- single campaign detail:
- Title, description, status badge, progress bar, raised/goal, category, location
- Link to `/campaign/:id`

**`DonationConfirmationCard`** -- green gradient card:
- Check badge + "Donation Initiated" label
- Donation ID, campaign title, amount, currency, payment method, instructions

**`DonationHistoryCard`** -- tabular history:
- Campaign title, date, amount, currency, status (color-coded)

**`AnalyticsSummaryCard`** -- 2x2 grid:
- Active campaigns, total donated, total donations, total donors

### 5.6 Welcome Screen

Shown when `messages.length === 0`:

```jsx
const suggestions = [
  { text: 'Find education campaigns in Kenya', Icon: HiOutlineMagnifyingGlass, color: 'blue' },
  { text: 'How much has been raised this month?', Icon: HiOutlineChartBarSquare, color: 'emerald' },
  { text: 'Show me water projects', Icon: HiOutlineGlobeAlt, color: 'sky' },
  { text: "What can you do?", Icon: HiOutlineQuestionMarkCircle, color: 'amber' },
];
```

Each suggestion is a styled button that calls `onSuggestion(text)` -> `sendText`.

---

## 6. Voice Pipeline

### 6.1 Browser: VoiceManager (`web-frontend/src/voice/VoiceManager.js`)

Singleton class that wraps the MediaRecorder API:

```js
class VoiceManager {
  // Properties: mediaRecorder, chunks, stream, currentAudio

  async init()              // requests getUserMedia({ audio: true })
  async startRecording()    // creates MediaRecorder (webm/opus preferred), 100ms chunks
  async stopRecording()     // returns Blob with .ext property for Whisper compatibility
  static extForMime(mime)   // maps MIME to extension: webm, ogg, wav, mp3, flac, mp4

  async play(url)           // plays Audio(url), returns Promise
  stopPlayback()            // pauses current audio
  async hasSound(blob)      // decodes via AudioContext, computes RMS, threshold 0.01
  destroy()                 // cleanup
}

export default new VoiceManager();  // singleton
```

**MIME preference order:** `audio/webm;codecs=opus` -> `audio/ogg;codecs=opus` -> browser default

**Silence detection:** `hasSound(blob)` uses `AudioContext.decodeAudioData` to compute RMS energy across all samples. Returns `false` if RMS < 0.01, preventing empty recordings from hitting the API.

### 6.2 Backend: ASR + TTS

**ASR:** `voice.asr.asr_infer.transcribe_audio(file_path, language)` -- calls OpenAI Whisper API. Returns `{ transcript, language }`.

**TTS:** `voice.tts.tts_provider.TTSProvider.synthesize(text, language)` -- generates audio file, returns filename. Audio served at `/api/voice/audio/{filename}`.

---

## 7. API Contract

### 7.1 Frontend API Client (`web-frontend/src/api/voice.js`)

```js
import { api } from './client';  // shared HTTP client with base URL + auth token

// Agent endpoints (the ones that matter)
export async function voiceAgent(audioBlob, userId, language, conversationId, context) {
  const fd = new FormData();
  fd.append('audio', new File([audioBlob], `recording.${audioBlob.ext || 'webm'}`));
  fd.append('user_id', userId);
  fd.append('user_language', language);
  if (conversationId) fd.append('conversation_id', conversationId);
  if (context) fd.append('context', JSON.stringify(context));
  return api.upload('/voice/agent', fd);
}

export async function textAgent(text, userId, language, conversationId, context) {
  return api.post('/voice/agent/text', {
    text, user_id: userId, user_language: language,
    conversation_id: conversationId,
    context: context ? JSON.stringify(context) : undefined,
  });
}
```

### 7.2 Response Shape (both endpoints)

```json
{
  "success": true,
  "conversation_id": "uuid-string",
  "transcription": "user's spoken text",
  "language": "en",
  "response_text": "Here are 3 education campaigns in Kenya...",
  "response_type": "campaign_list",
  "audio_url": "/api/voice/audio/abc123.mp3",
  "data": {
    "campaigns": [
      {
        "id": 1,
        "title": "Clean Water for Turkana",
        "category": "water",
        "goal_usd": 5000,
        "raised_usd": 3200,
        "progress_pct": 64,
        "location": "Kenya",
        "description_preview": "..."
      }
    ]
  },
  "tools_used": ["search_campaigns"],
  "response_source": "agent",
  "agent_error": null,
  "fallback_error": null
}
```

**`response_type` values:**

| Value | Trigger | Frontend Card |
|-------|---------|---------------|
| `campaign_list` | `data.campaigns` exists | `CampaignListCard` |
| `campaign_detail` | `data.campaign` exists | `CampaignDetailCard` |
| `donation_confirmation` | `data.donation` with success | `DonationConfirmationCard` |
| `donation_history` | `data.donations` exists | `DonationHistoryCard` |
| `analytics_summary` | `data.stats` exists | `AnalyticsSummaryCard` |
| `text` | default | Plain text bubble |

**`response_source` values** (observability):
- `agent` -- GPT function-calling succeeded
- `fallback_nlu` -- agent failed, legacy NLU pipeline handled it
- `fallback_failed` -- both failed, generic error message returned

---

## 8. State Management

### Zustand Stores

**`stores/authStore.js`** -- Authentication:
```js
{
  user: null,      // { id, telegram_user_id, full_name, role, ... }
  token: null,
  loading: false,
  error: null,

  login({ identifier, phoneNumber, pin }),  // -> apiLogin() + getMe()
  restore(token),                            // -> setToken() + getMe()
  logout(),                                  // -> apiLogout() + clearToken()
  isAuthenticated(),                          // -> !!token
}
```

**`stores/voiceStore.js`** -- Voice/Language:
```js
{
  status: 'idle',         // idle | recording | processing | playing
  language: 'en',         // persisted in localStorage key 'tv_lang'
  lastTranscription: '',
  error: null,

  setStatus(s), setLanguage(lang),  // setLanguage also saves to localStorage
  setTranscription(t), setError(e), reset(),
}
```

**How Assistant.jsx uses the stores:**
- Reads `authStore.user` to extract `userId` (passed to every agent API call)
- Reads `voiceStore.language` to pass `user_language` to agent calls
- Does NOT use `voiceStore.status` directly -- maintains its own `voiceStatus` local state for the recording UI

---

## 9. Replication Checklist

To replicate this system in The Voice Ledger:

### Backend

- [ ] Create `voice/agent/` package with `__init__.py`, `tools.py`, `executor.py`
- [ ] Define tool schemas in `tools.py` (adapt to Voice Ledger's domain entities)
- [ ] Implement `AgentExecutor` class with:
  - [ ] OpenAI function-calling loop (AsyncOpenAI, `tool_choice="auto"`)
  - [ ] Redis conversation history (load/save with TTL)
  - [ ] System prompt builder with user context injection
  - [ ] `_execute_tool` dispatch table
  - [ ] READ tools (direct DB queries) and WRITE tools (delegate to handlers)
- [ ] Create `voice/routers/agent_router.py` with:
  - [ ] `POST /voice/agent` (audio: FormData -> ASR -> agent -> TTS)
  - [ ] `POST /voice/agent/text` (text: JSON body -> agent -> TTS)
  - [ ] Three-tier fallback: agent -> NLU -> error
  - [ ] Response shape with `response_type`, `data`, `tools_used`, `response_source`
- [ ] Register router in FastAPI app
- [ ] Set environment variables: `OPENAI_API_KEY`, `AGENT_MODEL`, `AGENT_MAX_TURNS`, etc.

### Frontend

- [ ] Set up Vite + React + Tailwind 4.0 + React Router (basename="/app") + Zustand + i18next
- [ ] Create `api/voice.js` with `textAgent()` and `voiceAgent()` functions
- [ ] Create `voice/VoiceManager.js` singleton (MediaRecorder + silence detection)
- [ ] Create `stores/authStore.js` and `stores/voiceStore.js`
- [ ] Build `pages/Assistant.jsx`:
  - [ ] `useChat()` local state hook
  - [ ] Text input with Enter-to-send
  - [ ] Voice recording with press-and-hold mic (pointer events)
  - [ ] Auto-scroll on new messages
  - [ ] TTS auto-playback with toggle
  - [ ] `WelcomeScreen` with domain-relevant suggestion chips
  - [ ] `ChatMessage` renderer with user/assistant styling
  - [ ] Rich response cards matched to your `response_type` values
  - [ ] Deep-link support via URL search params
- [ ] Add `/assistant` route to `App.jsx`
- [ ] Add Assistant to `Navbar.jsx` primary nav items
- [ ] Add Assistant as center button in `MobileBottomNav.jsx`
- [ ] Configure Vite proxy: `/api` -> backend port

### Key Patterns to Preserve

1. **Unified endpoint** -- two routes (audio + text) replacing many single-purpose endpoints
2. **Function calling, not prompt engineering** -- tools define what the LLM can do; the LLM decides when to call them
3. **READ/WRITE separation** -- direct DB for reads, existing handlers for writes
4. **Typed responses** -- `response_type` + `data` enables rich UI without parsing text
5. **Three-tier fallback** -- never leave the user with a blank screen
6. **Silence detection** -- RMS energy check prevents empty recordings from consuming API calls
7. **Conversation continuity** -- Redis-backed history with UUID conversation IDs
8. **Page context injection** -- frontend can pass `context: { page, campaignId }` to help the agent give more relevant responses

---

*Document created: 4 March 2026*
*Source project: Trust-Voice (commit b88b4f1)*
