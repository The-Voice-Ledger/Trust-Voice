# LiveKit Voice UI — Design & Theme Guide

A practical reference for recreating the TrustVoice voice panel design — the full-screen overlay, animated orb, state-driven colors, floating trigger button, and action cards. Framework-agnostic concepts with React/Tailwind examples.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [The Trigger Button](#2-the-trigger-button)
3. [Full-Screen Voice Overlay](#3-full-screen-voice-overlay)
4. [Color System — State-Driven Palette](#4-color-system--state-driven-palette)
5. [The Central Orb](#5-the-central-orb)
6. [Audio Visualizer Bars](#6-audio-visualizer-bars)
7. [SVG Ambient Background](#7-svg-ambient-background)
8. [State Label & Status Dot](#8-state-label--status-dot)
9. [Session Controls](#9-session-controls)
10. [Transcript Panel — Data Flow & Implementation](#10-transcript-panel--data-flow--implementation)
11. [Action Cards (Data Channel UI)](#11-action-cards-data-channel-ui)
12. [Animation Inventory](#12-animation-inventory)
13. [Tailwind / CSS Notes](#13-tailwind--css-notes)
14. [Adapting the Theme](#14-adapting-the-theme)

---

## 1. Design Philosophy

The voice UI follows three principles:

- **Dark immersive overlay** — Voice interaction demands full attention. The panel takes over the entire screen with a near-black background (`gray-950/95`) and `backdrop-blur-xl`. This signals "you are now in a conversation" and eliminates distractions.

- **State communicates through color** — The user never needs to read text to know what's happening. Green = listening/ready. Purple = thinking. Cyan = speaking. Yellow = connecting. Red = error. Every visual element — the orb, the rings, the status dot, the glow — shifts color together.

- **Subtle constant motion** — Slow-rotating orbital rings, gently floating particles, and breathing animations create a sense of "alive" even when idle. Nothing is static. This builds trust that the system is active and listening.

---

## 2. The Trigger Button

The voice session is launched from a small button embedded in the chat input bar.

### Design

```
┌──────────────────────────────────────────┐
│  [🎤]  [ Type a message or tap the mic ] [→] │
└──────────────────────────────────────────┘
  ↑ trigger button
```

- **Shape**: `w-11 h-11 rounded-2xl` — a rounded square, not a circle. This distinguishes it from the send button.
- **Gradient**: `bg-gradient-to-br from-emerald-500 via-green-600 to-amber-600` — emerald-to-amber diagonal. Warm and inviting.
- **Shadow**: `shadow-md shadow-amber-200/40` — amber-tinted shadow for warmth.
- **Hover**: Scale up 5% (`hover:scale-105`), shadow intensifies (`hover:shadow-lg hover:shadow-amber-300/50`).
- **Active**: Scale down 5% (`active:scale-95`) — tactile "press" feel.
- **Icon**: `HiOutlineMicrophone` from Heroicons, `w-5 h-5`, white.

### Why This Works

The gradient makes it the most colorful element in the input bar, naturally drawing the eye. The amber warmth distinguishes it from the green-only send button. The scale animation gives physical feedback.

### Code Pattern

```jsx
<button
  onClick={openVoice}
  className="flex-shrink-0 w-11 h-11 rounded-2xl flex items-center justify-center
    bg-gradient-to-br from-emerald-500 via-green-600 to-amber-600
    text-white shadow-md shadow-amber-200/40
    hover:shadow-lg hover:shadow-amber-300/50
    hover:scale-105 active:scale-95 transition-all duration-200"
>
  <MicrophoneIcon className="w-5 h-5" />
</button>
```

---

## 3. Full-Screen Voice Overlay

When triggered, the voice panel takes over the entire viewport.

### Layout Structure

```
┌──────────────────────────────────────────┐
│ [Logo + "VBV Voice"]              [  ✕  ] │  ← Top bar
│          status label                     │
│                                           │
│              ┌─────────┐                  │
│              │  ◯ orb  │                  │  ← Central orb (idle)
│              │  / bars │                  │  ← or BarVisualizer (active)
│              └─────────┘                  │
│                                           │
│            ● Listening…                   │  ← State label + dot
│          username • live session          │
│                                           │
│         [Show/Hide transcript]            │  ← Collapsible
│         [Show/Hide actions]               │  ← Collapsible
│                                           │
│    [ 🎤 Mic Toggle ]  [ 📞 End Call ]    │  ← Controls (when active)
│    [ ▶ Start Voice Session ]              │  ← Or start button (when idle)
│                                           │
│    Powered by LiveKit • Deepgram • OpenAI │  ← Footer
└──────────────────────────────────────────┘
```

### Container CSS

```css
/* Full-screen dark overlay */
position: fixed;
inset: 0;
z-index: 50;
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
background: rgb(3 7 18 / 0.95);   /* gray-950 at 95% opacity */
backdrop-filter: blur(24px);       /* backdrop-blur-xl */
```

The 95% opacity lets a faint ghost of the app show through, maintaining spatial context.

---

## 4. Color System — State-Driven Palette

Every visual element reads from a single color map keyed by agent state. This is the core of the design — **one state change updates everything**.

### The Color Map

| State | Ring | Dot | Glow | Meaning |
|-------|------|-----|------|---------|
| `disconnected` | `#6B7280` (gray-500) | `#9CA3AF` (gray-400) | `rgba(107,114,128,0.15)` | Offline |
| `connecting` | `#F59E0B` (amber-500) | `#FBBF24` (amber-400) | `rgba(245,158,11,0.2)` | Connecting |
| `initializing` | `#F59E0B` | `#FBBF24` | `rgba(245,158,11,0.2)` | Starting up |
| `idle` | `#10B981` (emerald-500) | `#34D399` (emerald-400) | `rgba(16,185,129,0.2)` | Ready |
| `listening` | `#10B981` | `#34D399` | `rgba(16,185,129,0.35)` | Hearing you |
| `thinking` | `#8B5CF6` (violet-500) | `#A78BFA` (violet-400) | `rgba(139,92,246,0.25)` | LLM generating |
| `speaking` | `#06B6D4` (cyan-500) | `#22D3EE` (cyan-400) | `rgba(6,182,212,0.3)` | Agent talking |
| `failed` | `#EF4444` (red-500) | `#F87171` (red-400) | `rgba(239,68,68,0.2)` | Error |

### Three Color Roles

- **Ring** — Used for SVG stroke on orbital rings and the inner glow circle. The "structural" color.
- **Dot** — Used for the status indicator dot and the state label text. The "foreground" accent.
- **Glow** — Used for `box-shadow` on the outer orb and `radialGradient` fills. The "atmosphere" color.

### Usage Pattern

```js
const STATE_COLORS = {
  disconnected: { ring: '#6B7280', dot: '#9CA3AF', glow: 'rgba(107,114,128,0.15)' },
  listening:    { ring: '#10B981', dot: '#34D399', glow: 'rgba(16,185,129,0.35)' },
  thinking:     { ring: '#8B5CF6', dot: '#A78BFA', glow: 'rgba(139,92,246,0.25)' },
  speaking:     { ring: '#06B6D4', dot: '#22D3EE', glow: 'rgba(6,182,212,0.3)'  },
  // ...
};

const colors = STATE_COLORS[agentState] || STATE_COLORS.disconnected;
// Then use colors.ring, colors.dot, colors.glow everywhere
```

---

## 5. The Central Orb

The orb is a 256×256 SVG with layered rings, centered in a 16rem (256px) container.

### Layers (outside → inside)

1. **Box-shadow glow** — A CSS `box-shadow` on the container div. Two concentric shadows using `colors.glow`. Opacity increases when `speaking` or `listening`.

```css
box-shadow: 0 0 40px 8px ${colors.glow}, 0 0 80px 16px ${colors.glow};
opacity: speaking || listening ? 0.6 : 0.2;
transition: all 1s;
```

2. **Outer dashed ring** — SVG circle, r=124, `strokeDasharray="3 9"`, rotating clockwise in 20s.

3. **Middle ring** — SVG circle, r=108, solid stroke, rotating counter-clockwise in 15s.

4. **Inner breathing ring** — SVG circle, r=88. The radius pulses between 85–91 over 3s. Opacity varies by state (0.4 when speaking, 0.3 listening, 0.1 idle).

5. **Orbital dots** — Two tiny circles (r=2 and r=1.5) placed on the ring paths, rotating at different speeds (8s and 12s). Creates a "satellite" effect.

6. **Center content** — Either the idle microphone icon OR the BarVisualizer (when active).

### Idle State (Before Session Starts)

A soft green orb with a microphone icon drawn in SVG:

```svg
<circle cx="40" cy="40" r="30" fill="url(#orb-idle)" opacity="0.8" />
<!-- Microphone: rounded rect body + arc + stem -->
<rect x="36" y="28" width="8" height="14" rx="4" fill="none" stroke="#fff" strokeWidth="1.5" opacity="0.7" />
<path d="M32 40a8 8 0 0016 0" fill="none" stroke="#fff" strokeWidth="1.5" opacity="0.7" />
<path d="M40 48v5" stroke="#fff" strokeWidth="1.5" opacity="0.7" />
```

The `orb-idle` gradient is a radial: emerald-500 at 25% opacity in the center → emerald-950 at 10% at the edge.

---

## 6. Audio Visualizer Bars

When the session is active, the idle orb is replaced by LiveKit's `<BarVisualizer>`.

### Configuration

```jsx
<BarVisualizer
  state={agentState}    // drives animation intensity
  barCount={7}          // number of bars
  track={audioTrack}    // agent's audio track
  className="lk-voice-bars"
/>
```

### Custom Styling (Critical — Do Not Import Default Styles)

LiveKit's default `@livekit/components-styles` will reset your entire app's CSS. Instead, style the bars manually:

```css
.lk-voice-bars {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.lk-voice-bars .lk-audio-bar {
  width: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.12);     /* dim gray when quiet */
  transition: height 0.12s ease, background 0.3s ease;
  min-height: 8px;
}

.lk-voice-bars .lk-audio-bar.lk-highlighted {
  background: linear-gradient(to top, #10B981, #06B6D4);  /* emerald → cyan */
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);            /* green glow */
}
```

### Design Decisions

- **7 bars** — odd number so there's a center bar. Gives visual symmetry.
- **6px wide with 6px gap** — total width ~78px, fits comfortably inside the 160px visualizer container.
- **Emerald-to-cyan gradient when active** — matches the listening→speaking color transition.
- **0.12s height transition** — fast enough to feel responsive, slow enough to not flicker.
- **Min-height 8px** — bars never fully disappear, maintaining the visual structure.

---

## 7. SVG Ambient Background

A full-viewport SVG sits behind everything (`pointer-events-none`). It creates depth and atmosphere without any images.

### Elements

#### 7a. Grid Pattern

A subtle repeating 40×40 grid in emerald at 8% opacity:

```svg
<pattern id="vp-grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#10B981" strokeWidth="0.15" opacity="0.08" />
</pattern>
<rect width="800" height="800" fill="url(#vp-grid)" />
```

This gives a faint technical/digital feel to the background.

#### 7b. Radial Gradients (3 layers)

Three overlapping radial glows at different positions and sizes:

| Gradient | Position | Radius | Color | Purpose |
|----------|----------|--------|-------|---------|
| Primary | center (50%, 45%) | 35% | `colors.glow` (state-driven) | Reacts to agent state |
| Secondary | lower-left (25%, 70%) | 25% | emerald at 6% | Fixed warm area |
| Tertiary | upper-right (75%, 30%) | 20% | cyan at 4% | Fixed cool area |

The primary gradient changes color with agent state. The other two are fixed, creating a subtle warm/cool asymmetry.

#### 7c. Orbital Rings (3 rings)

Three concentric circles centered on the orb area, rotating at different speeds and directions:

| Ring | Radius | Speed | Direction | Dash Pattern |
|------|--------|-------|-----------|-------------|
| Inner | 180 | 60s | Clockwise | Solid |
| Middle | 220 | 45s | Counter-clockwise | `4 12` |
| Outer | 260 | 80s | Clockwise | `2 18` |

The different speeds and directions create a subtle parallax depth effect.

#### 7d. Corner Accents

Small triangles in each corner at ~3% opacity:

```svg
<path d="M0 0 L60 0 L0 60Z" fill="#10B981" opacity="0.03" />
```

These frame the viewport and prevent the background from feeling like an empty void.

#### 7e. Floating Particles

Four small circles (r=0.8–1.5) at different positions, gently bobbing up and down:

```svg
<circle cx="120" cy="200" r="1.5" fill="#10B981" opacity="0.15">
  <animate attributeName="cy" values="200;180;200" dur="4s" repeatCount="indefinite" />
  <animate attributeName="opacity" values="0.15;0.3;0.15" dur="4s" repeatCount="indefinite" />
</circle>
```

Each particle has a different duration (3.5s–6s) so they never sync up. The opacity also pulses, making them feel like distant stars.

#### 7f. Hexagonal Accent

A single hexagon near the orb center, slowly rotating in 30s:

```svg
<polygon points="400,310 432,328 432,364 400,382 368,364 368,328"
  fill="none" stroke="#10B981" strokeWidth="0.4" opacity="0.04" />
```

Very faint — you almost don't notice it, but it adds a subtle geometric texture.

---

## 8. State Label & Status Dot

Below the orb, a colored dot + text label shows the current state.

### Structure

```
  ● Listening…
  username • live session
```

### The Dot

- `w-2 h-2 rounded-full`
- `backgroundColor: colors.dot`
- `boxShadow: 0 0 8px ${colors.glow}`
- **Pulsing animation** on `listening`, `connecting`, and `thinking` states:

```css
@keyframes pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}
```

### The Label

- `text-sm font-medium tracking-wide`
- Color: `colors.dot` (matches the dot)
- Text from a label map: `listening → "Listening…"`, `thinking → "Thinking…"`, etc.

### The Subtitle

- Only shown when session is active
- `text-[11px] text-white/25 font-mono` — very faint, monospace
- Format: `"username • live session"`

---

## 9. Session Controls

### Start Button (Before Session)

A prominent CTA with gradient, glow, and micro-interactions:

```jsx
<button className="group relative px-8 py-4 rounded-2xl
  bg-gradient-to-br from-emerald-500 to-green-600
  text-white font-semibold text-sm
  shadow-lg shadow-emerald-500/20
  hover:shadow-emerald-500/40 hover:scale-105
  active:scale-95 transition-all">
  {/* Hover glow overlay */}
  <div className="absolute -inset-px rounded-2xl
    bg-gradient-to-br from-emerald-400/20 to-green-400/20
    opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
  <span className="relative flex items-center gap-2">
    <MicrophoneIcon />
    Start Voice Session
  </span>
</button>
```

Key details:
- **`group` + child hover** — the glow overlay appears on hover via `group-hover:opacity-100`
- **`relative` on span** — keeps text above the glow overlay
- **`-inset-px`** — glow overlay is 1px larger on each side, creating a border-like glow

### Active Controls (During Session)

Two circular buttons side by side:

| Button | Size | Background | Color | Purpose |
|--------|------|-----------|-------|---------|
| Mic Toggle | `w-14 h-14` | `bg-white/10` | `text-white/80` | Mute/unmute mic |
| End Call | `w-14 h-14` | `bg-red-500/15` | `text-red-400` | End session |

The mic toggle uses LiveKit's `<TrackToggle source={Track.Source.Microphone}>`.

The end call button has a phone-hangup SVG icon:

```svg
<path d="M2 8c0-1 2-4 8-4s8 3 8 4v1c0 1-1 2-2 2h-1l-1-3h-2v4h-4V8H6l-1 3H4c-1 0-2-1-2-2V8z" />
```

---

## 10. Transcript Panel — Data Flow & Implementation

A collapsible live transcript that shows the conversation as it happens, powered entirely by the LiveKit SDK's built-in transcription pipeline. No custom WebSocket messages, no polling — transcription segments arrive automatically for both the agent's speech and the user's speech.

### 10.1 How Transcription Data Flows

```
         Server (Python agent)                            Client (React)
  ┌─────────────────────────────┐            ┌───────────────────────────────┐
  │  Deepgram STT plugin        │            │                               │
  │  ↓ transcribes user audio   │            │  useVoiceAssistant()          │
  │  Agent sends response text  │     WS     │    → agentTranscriptions[]    │
  │  TTS plugin speaks it       │  ───────►  │                               │
  │  (segments published to     │            │  Each segment has:            │
  │   the LiveKit room via      │            │    .id  .text  .isAgent       │
  │   data channel)             │            │    .final  .language          │
  └─────────────────────────────┘            └───────────────────────────────┘
```

The LiveKit agent framework publishes transcription segments to the room automatically whenever:
1. **The agent speaks** — each TTS utterance creates agent segments.
2. **The user speaks** — the STT plugin (Deepgram) transcribes user audio and publishes user segments.

On the React side, `useVoiceAssistant()` collects both agent and user transcription segments into a single deduplicated, time-ordered array.

### 10.2 The Hook

```jsx
import { useVoiceAssistant } from '@livekit/components-react';

const { state: agentState, audioTrack, agentTranscriptions } = useVoiceAssistant();

// Guard against the array being undefined before the first segment arrives
const transcriptions = agentTranscriptions || [];
```

**What `useVoiceAssistant()` returns:**

| Property | Type | Description |
|----------|------|-------------|
| `state` | `AgentState` | `'disconnected' \| 'connecting' \| 'initializing' \| 'listening' \| 'thinking' \| 'speaking'` |
| `audioTrack` | `TrackReference \| undefined` | The agent's audio track (for the visualizer) |
| `agentTranscriptions` | `ReceivedTranscriptionSegment[]` | All segments — both agent AND user — in arrival order |
| `agentAttributes` | `RemoteParticipant['attributes']` | Custom key-value metadata on the agent participant |

### 10.3 The Segment Shape

Each entry in `agentTranscriptions` is a `ReceivedTranscriptionSegment`, which extends the base `TranscriptionSegment` from `livekit-client`:

```ts
// From livekit-client
interface TranscriptionSegment {
  id: string;               // Unique segment identifier
  text: string;             // The transcribed text content
  language: string;         // e.g. "en"
  startTime: number;        // Media timestamp start
  endTime: number;          // Media timestamp end
  final: boolean;           // true when segment is finalized (won't change)
  firstReceivedTime: number;
  lastReceivedTime: number;
}

// From @livekit/components-core — extends the above
type ReceivedTranscriptionSegment = TranscriptionSegment & {
  receivedAtMediaTimestamp: number;
  receivedAt: number;       // Wall-clock timestamp of receipt
};
```

The component-level `isAgent` boolean is inferred by the SDK internals — segments from the agent participant track are flagged so you can distinguish speakers.

### 10.4 Rendering the Transcript

```jsx
{transcriptions.map((seg, i) => (
  <p key={i} className={`text-xs leading-relaxed ${
    seg.isAgent ? 'text-emerald-300/70' : 'text-white/50'
  }`}>
    <span className="font-mono text-[9px] text-white/20 mr-1.5">
      {seg.isAgent ? 'AI' : 'You'}
    </span>
    {seg.text}
  </p>
))}
```

| Speaker | Label | Label Style | Text Color |
|---------|-------|-------------|------------|
| Agent | `AI` | `font-mono text-[9px] text-white/20` | `text-emerald-300/70` |
| User | `You` | `font-mono text-[9px] text-white/20` | `text-white/50` |

### 10.5 Auto-Scroll

A ref on the scroll container + a `useEffect` watching the transcription array keeps the view pinned to the latest entry:

```jsx
const transcriptRef = useRef(null);

useEffect(() => {
  if (transcriptRef.current) {
    transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
  }
}, [transcriptions]);
```

Every time a new segment arrives (or an existing segment updates its `text` as it becomes `final`), the `transcriptions` array reference changes, the effect fires, and the container scrolls to bottom.

### 10.6 Collapsible Toggle

The transcript is hidden by default and only appears once the user toggles it — this keeps the orb as the primary focal point.

```jsx
const [showTranscript, setShowTranscript] = useState(false);

// Only render when session is active AND at least one segment exists
{isStarted && transcriptions.length > 0 && (
  <div className="w-full">
    <button
      onClick={() => setShowTranscript(v => !v)}
      className="w-full flex items-center justify-center gap-1.5
                 text-[11px] text-white/30 hover:text-white/50 transition-colors mb-2"
    >
      {/* Mini doc icon — 3 lines of different widths */}
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
           stroke="currentColor" strokeWidth="1">
        <path d="M2 4h8M2 6h6M2 8h7" />
      </svg>
      {showTranscript ? 'Hide transcript' : 'Show transcript'}
    </button>

    {showTranscript && (
      <div ref={transcriptRef}
           className="max-h-32 overflow-y-auto rounded-xl bg-white/5
                      border border-white/5 px-4 py-3 space-y-1.5 scrollbar-thin">
        {/* ...map segments here... */}
      </div>
    )}
  </div>
)}
```

### 10.7 Transcript Container Styling

```css
max-height: 8rem;                          /* max-h-32 — compact, doesn't crowd the orb */
overflow-y: auto;
border-radius: 0.75rem;                    /* rounded-xl */
background: rgba(255,255,255, 0.05);       /* bg-white/5 — barely visible glass */
border: 1px solid rgba(255,255,255, 0.05); /* border-white/5 */
padding: 0.75rem 1rem;                     /* px-4 py-3 */
gap: 0.375rem;                             /* space-y-1.5 between entries */
```

### 10.8 Alternative Lower-Level Hook

If you need finer control (e.g. only agent transcriptions, or per-track), `@livekit/components-react` also exposes:

```jsx
import { useTrackTranscription } from '@livekit/components-react';

const { segments } = useTrackTranscription(trackRef);
// segments: ReceivedTranscriptionSegment[]
```

`useTrackTranscription` subscribes to a specific track's transcription events rather than aggregating. Useful if you want separate transcript panes for agent and user.

### 10.9 Design Rationale

- **Transcript is secondary** — The orb is the primary feedback mechanism. The transcript exists for accessibility and review, not as the main interface. That's why it starts collapsed and sits below the orb.
- **Compact height** — `max-h-32` (8rem) keeps it to ~4 lines visible. More content scrolls. This prevents the transcript from dominating the screen.
- **Muted colors** — Agent text uses `emerald-300` at 70% opacity, user text uses `white` at 50% opacity. Both are intentionally dim so they don't compete with the orb's glow.
- **Monospace labels** — The tiny `AI`/`You` labels use monospace at 9px. They're functional waypoints, not headlines.
- **No timestamps shown** — Despite having `startTime`/`endTime` in the segment data, we omit visible timestamps to keep the UI minimal. The data is available if you want to add them.

---

## 11. Action Cards (Data Channel UI) — How TrustVoice Sends Data to the Briefing Room

During a voice session the agent needs to push structured visual data — payment links, donation receipts, campaign progress cards, admin summaries — into the overlay alongside the conversation. LiveKit's **text stream** (reliable data channel) is the transport. In this project the pattern works end-to-end across three layers: a Python helper that serializes and sends, a React hook that subscribes, and a dispatcher component that routes each card to a typed renderer.

### 11.1 The Send Helper (Python Agent)

In `voice/livekit_agent.py` a single constant defines the topic and a single async helper wraps every send:

```python
ACTION_TOPIC = "vbv.action"

async def _send_action_card(ctx: RunContext, card: dict) -> None:
    """Push a visual action card to the frontend via LiveKit text stream."""
    try:
        room = ctx.session.room_io.room
        await room.local_participant.send_text(
            json.dumps(card),
            topic=ACTION_TOPIC,
        )
    except Exception as e:
        logger.warning(f"Failed to send action card: {e}")
```

**Key points:**
- `room.local_participant.send_text()` is the LiveKit Python SDK's reliable data-channel method. It guarantees ordered delivery over SCTP — no messages are dropped.
- The topic string `"vbv.action"` is an arbitrary namespace. The frontend subscribes to exactly this topic. You can define multiple topics if you need independent streams (e.g. `"myapp.charts"`, `"myapp.alerts"`).
- The payload is always a JSON dict with a `"type"` field that the frontend uses to dispatch to the correct renderer.
- `ctx` is a `RunContext` from `livekit-agents`, available inside every `@function_tool`. It carries the room handle, session metadata, and the `userdata` dict (user ID, role, name).

### 11.2 Every Card Payload Sent in This Project

Below are the exact `_send_action_card` calls from the TrustVoice agent, showing what triggers each card and the full payload shape.

#### Payment Link (Stripe checkout)

Sent when a donor initiates a card payment via voice:

```python
await _send_action_card(ctx, {
    "type": "payment_link",
    "url": checkout_url,               # Stripe Checkout Session URL
    "amount": amount,                   # e.g. 25.00
    "currency": currency.upper(),       # "USD", "KES"
    "campaign_title": campaign.title,
    "campaign_id": campaign.id,
    "donation_id": str(result.get("donation_id", "")),
})
```

#### Donation Receipt (M-Pesa pending)

Sent when a mobile-money donation is initiated — the user needs to complete on their phone:

```python
await _send_action_card(ctx, {
    "type": "donation_receipt",
    "amount": amount,
    "currency": currency.upper(),
    "campaign_title": campaign.title,
    "campaign_id": campaign.id,
    "payment_method": "mpesa",
    "status": "pending",
    "message": result.get("instructions", "Check your phone for the M-Pesa prompt."),
})
```

#### Donation History

Sent when a user asks "show me my past donations":

```python
await _send_action_card(ctx, {
    "type": "donation_history",
    "donations": results,               # list of dicts, each with:
    # { donation_id, campaign, amount_usd, currency, status, date, payment_method }
    "total_donated_usd": round(total, 2),
    "count": len(results),
})
```

#### Campaign Card (newly created)

Sent after the agent creates a campaign on behalf of an NGO admin:

```python
await _send_action_card(ctx, {
    "type": "campaign_card",
    "id": campaign.id,
    "title": campaign.title,
    "category": category.lower(),
    "goal_usd": float(campaign.goal_amount_usd),
    "raised_usd": 0,
    "progress_pct": 0,
    "location": location_country or location_region or "N/A",
    "status": "active",
    "just_created": True,
})
```

#### Payout Status (admin action)

Sent when an admin approves or rejects a payout via voice:

```python
await _send_action_card(ctx, {
    "type": "payout_status",
    "payout_id": payout.id,
    "amount": float(payout.amount),
    "currency": payout.currency,
    "status": "approved",               # or "rejected"
    "action": "approved",
})
```

#### Admin Summary (proactive push at session start)

For admin users, the agent proactively pushes a dashboard summary card when the session begins — before the user says anything. This is sent directly (not via the helper) during the `@server.rtc_session()` entrypoint:

```python
# Built in _load_ambient_context():
cards.append({
    "type": "admin_summary",
    "pending_payouts": pending_payouts,
    "pending_milestones": pending_milestones,
    "funded_milestones": funded_milestones,
})

# Pushed at session start:
for card in ambient.get("cards", []):
    await ctx.room.local_participant.send_text(
        json.dumps(card),
        topic=ACTION_TOPIC,
    )
```

### 11.3 Full Payload Reference

| `type` | Key Fields | Trigger |
|--------|-----------|---------|
| `payment_link` | `url`, `amount`, `currency`, `campaign_title`, `campaign_id`, `donation_id` | Stripe donation initiated |
| `donation_receipt` | `amount`, `currency`, `campaign_title`, `payment_method`, `status`, `message` | M-Pesa donation initiated |
| `donation_history` | `donations[]`, `total_donated_usd`, `count` | User asks for history |
| `campaign_card` | `id`, `title`, `category`, `goal_usd`, `raised_usd`, `progress_pct`, `location`, `status` | Campaign created via voice |
| `campaign_list` | `campaigns[]` (same shape as campaign_card) | Search results |
| `payout_status` | `payout_id`, `amount`, `currency`, `status`, `action` | Admin approves/rejects payout |
| `milestone_update` | `milestone_id`, `message`, `status` | Milestone status change |
| `admin_summary` | `pending_payouts`, `pending_milestones`, `funded_milestones` | Proactive push at session start |
| `error` | `message` | Any error the agent wants to surface visually |

> **Note:** `campaign_list`, `milestone_update`, and `error` have frontend renderers ready but no agent-side sends yet — they exist as extension points.

### 11.4 Receiving on the Frontend (React)

The frontend subscribes with a single hook call in `LiveVoicePanel.jsx`:

```jsx
import { useTextStream } from '@livekit/components-react';

const { textStreams: actionStreams } = useTextStream('vbv.action');
```

`useTextStream('vbv.action')` returns `{ textStreams }` — an array that grows as new messages arrive on the `"vbv.action"` topic. Each entry has a `.text` property containing the raw JSON string sent by the agent.

#### Auto-Show & Auto-Scroll

When new cards arrive, the panel automatically opens and scrolls to the latest:

```jsx
const [showActions, setShowActions] = useState(true);
const actionsRef = useRef(null);

useEffect(() => {
  if (actionsRef.current) {
    actionsRef.current.scrollTop = actionsRef.current.scrollHeight;
  }
  if (actionStreams.length > 0) {
    setShowActions(true);
  }
}, [actionStreams]);
```

#### Collapsible Section

```jsx
{isStarted && actionStreams.length > 0 && (
  <div className="w-full">
    <button onClick={() => setShowActions(v => !v)}
            className="w-full flex items-center justify-center gap-1.5
                       text-[11px] text-white/30 hover:text-white/50 transition-colors mb-2">
      {showActions ? 'Hide actions' : `Show actions (${actionStreams.length})`}
    </button>
    {showActions && (
      <div ref={actionsRef} className="max-h-56 overflow-y-auto scrollbar-thin">
        <ActionCards textStreams={actionStreams} />
      </div>
    )}
  </div>
)}
```

### 11.5 The ActionCards Dispatcher (JSON → Typed Component)

`ActionCards.jsx` parses the JSON from each stream entry, discards any malformed messages, and routes to the correct renderer via a `switch` on the `type` field:

```jsx
export default function ActionCards({ textStreams }) {
  if (!textStreams || textStreams.length === 0) return null;

  const cards = textStreams
    .map((stream) => {
      try { return JSON.parse(stream.text || stream); }
      catch { return null; }
    })
    .filter(Boolean);

  if (cards.length === 0) return null;

  return (
    <div className="w-full space-y-3">
      {cards.map((card, i) => <ActionCard key={i} data={card} />)}
    </div>
  );
}

function ActionCard({ data }) {
  switch (data?.type) {
    case 'payment_link':     return <PaymentLinkCard data={data} />;
    case 'donation_receipt': return <DonationReceiptCard data={data} />;
    case 'donation_history': return <DonationHistoryCard data={data} />;
    case 'campaign_card':    return <CampaignCard data={data} />;
    case 'campaign_list':    return <CampaignListCard data={data} />;
    case 'payout_status':    return <PayoutStatusCard data={data} />;
    case 'milestone_update': return <MilestoneUpdateCard data={data} />;
    case 'admin_summary':    return <AdminSummaryCard data={data} />;
    case 'error':            return <ErrorCard data={data} />;
    default:                 return null;   // unknown types silently ignored
  }
}
```

### 11.6 Common Card Styling

All cards share a glass-morphism base:

```css
border-radius: 0.75rem;                           /* rounded-xl */
background: rgba(255,255,255, 0.05);              /* bg-white/5 */
border: 1px solid rgba(255,255,255, 0.10);         /* border-white/10 */
padding: 1rem;                                     /* p-4 */
```

Accent cards (e.g. `payment_link`) use a gradient background to draw attention:

```css
background: linear-gradient(to bottom-right, rgba(16,185,129,0.15), rgba(22,163,74,0.10));
border-color: rgba(16,185,129,0.20);
```

### 11.7 The Full Pipeline at a Glance

```
  Python Agent (@function_tool)          LiveKit Room            React Frontend
  ─────────────────────────────          ──────────────          ───────────────
  1. Tool executes business logic
     (create donation, fetch history…)
                 │
  2. Build a dict with "type" key
                 │
  3. _send_action_card(ctx, card)
       └─► room.local_participant      ─► reliable data ─►   useTextStream('vbv.action')
             .send_text(                    channel              │
               json.dumps(card),            (SCTP)         4. textStreams grows
               topic="vbv.action"                              │
             )                                            5. ActionCards parses JSON
                                                              │
                                                          6. switch(card.type)
                                                              │
                                                          7. Render <PaymentLinkCard />
                                                             or <CampaignCard /> etc.
```

### 11.8 Adapting This Pattern for Your Project

To send your own data types (charts, tables, notifications):

1. **Define your topic** — pick a namespace string, e.g. `"myapp.cards"`.
2. **Create the send helper** — copy `_send_action_card`, changing only `ACTION_TOPIC`.
3. **Define payload shapes** — every dict must have a `"type"` field. Keep payloads flat when possible; deeply nested objects are harder to render.
4. **Call it from your tools** — after your `@function_tool` does its work, `await` the send before returning. The agent's spoken response and the visual card arrive nearly simultaneously.
5. **Subscribe on the frontend** — `useTextStream('myapp.cards')` gives you the array.
6. **Build a dispatcher** — a `switch` on `type` that routes to your components. Unknown types return `null`, making it safe to add new card types server-side without breaking old clients.
7. **Proactive pushes** — you can send cards outside of tool calls (like the `admin_summary` at session start) by accessing `ctx.room.local_participant` directly in the session entrypoint.

> **Gotcha**: `send_text` is fire-and-forget from the agent's perspective — there's no ACK callback. If you need confirmation that the frontend rendered a card, you'd need a reverse text stream from the frontend back to the agent (topic `"myapp.ack"`).

---

## 12. Animation Inventory

All animations used in the voice panel:

| Animation | Where | CSS/SVG | Duration | Easing |
|-----------|-------|---------|----------|--------|
| **Orbital rotation** | Background rings | `animateTransform type="rotate"` | 45s–80s | Linear (constant) |
| **Particle float** | Background dots | `animate attributeName="cy"` | 3.5s–6s | Linear (smooth) |
| **Hexagon rotation** | Background hex | `animateTransform type="rotate"` | 30s | Linear |
| **Ring breathing** | Inner orb ring | `animate attributeName="r"` values="85;91;85" | 3s | Linear |
| **Status dot pulse** | State indicator | `@keyframes pulse` scale(1)→scale(1.3) | 1.5s | ease-in-out |
| **Glow transition** | Orb outer shadow | CSS `transition: all 1s` | 1s | Default ease |
| **Bar height** | BarVisualizer bars | CSS `transition: height 0.12s ease` | 0.12s | Ease |
| **Button scale** | All buttons | CSS `hover:scale-105 active:scale-95` | 0.2s | Default |
| **Dot color** | Orb satellite dots | Driven by state color map | Instant | — |

### Performance Notes

- All background animations use SVG `<animate>` / `<animateTransform>` — these run on the compositor thread and don't trigger layout recalculations.
- The BarVisualizer transitions are CSS-only (`transition: height`), hardware-accelerated.
- The pulse keyframe uses `transform: scale()` — GPU-composited, no reflow.

---

## 13. Tailwind / CSS Notes

### Do NOT Import @livekit/components-styles Globally

This package includes aggressive CSS resets that will break Tailwind. Specifically, it resets `box-sizing`, font sizes, and margins globally. Instead, write custom styles for the BarVisualizer in a scoped `<style>` block or CSS module.

### Key Tailwind Utilities Used

| Pattern | Purpose |
|---------|---------|
| `bg-white/5`, `border-white/10` | Subtle glass-morphism on dark backgrounds |
| `text-white/30`, `text-white/50` | Hierarchical text opacity for information density |
| `backdrop-blur-xl` | Frosted glass effect on the overlay |
| `shadow-emerald-500/20` | Colored shadows that match the brand |
| `font-mono text-[9px]` | Technical-looking labels (speaker tags, footer) |
| `tracking-wide` | Slightly spaced-out text for labels |
| `transition-all duration-200` | Smooth micro-interactions on hover/active |

### Color Palette Summary

The design uses approximately 5 colors:

- **Emerald-500 (#10B981)** — Primary brand. Rings, dots, bars, buttons, grid.
- **Cyan-500 (#06B6D4)** — Secondary. Bar gradient tip, speaking state, background accent.
- **Violet-500 (#8B5CF6)** — Thinking state only. Creates contrast from the green family.
- **Amber-500 (#F59E0B)** — Connecting/loading states. Warmth and urgency.
- **Gray-950 (#030712)** — Background. Near-black with a blue undertone.

---

## 14. Adapting the Theme

### To Change the Brand Color

1. Replace all `#10B981` (emerald-500) references in:
   - `STATE_COLORS` map (idle, listening states)
   - SVG background elements (grid, rings, particles, corners, hexagon)
   - BarVisualizer gradient
   - Button gradients

2. Update the secondary color (`#06B6D4` cyan) to complement your new primary.

3. Keep violet for `thinking` and amber for `connecting` — these are functional, not brand colors.

### To Use on a Light Background

The design is built for dark mode. To adapt:

- Invert the overlay: `bg-white/95 backdrop-blur-xl` instead of `bg-gray-950/95`
- SVG strokes: reduce opacity further (0.02–0.04 instead of 0.04–0.08)
- Text: use `text-gray-900` / `text-gray-500` instead of `text-white/90` / `text-white/30`
- Glow shadows: increase opacity and use lighter ring colors
- Card backgrounds: `bg-gray-100` instead of `bg-white/5`

### To Remove the Orbital Rings / Particles

Delete the SVG background block entirely. The orb and controls work independently. The panel will look cleaner but less atmospheric.

### Minimum Viable Voice UI

If you want the simplest possible version, you need just:

1. A button that calls your token endpoint
2. `<SessionProvider>` + `<RoomAudioRenderer />`
3. The `useVoiceAssistant()` hook for `state`
4. A state label showing "Listening / Thinking / Speaking"
5. A disconnect button

Everything else — the orb, rings, particles, visualizer, transcript, action cards — is progressive enhancement.
