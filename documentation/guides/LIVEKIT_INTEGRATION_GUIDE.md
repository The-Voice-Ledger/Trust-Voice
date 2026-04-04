# LiveKit Voice Agent Integration Guide

A practical, opinionated guide for integrating LiveKit's real-time voice AI agent into a Python/FastAPI + React project deployed on Railway. Based on hard-won lessons from the TrustVoice production integration.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [LiveKit Cloud Setup](#2-livekit-cloud-setup)
3. [Backend: Python Agent Worker](#3-backend-python-agent-worker)
4. [Backend: Token Endpoint](#4-backend-token-endpoint)
5. [Frontend: React Voice Panel](#5-frontend-react-voice-panel)
6. [Railway Deployment](#6-railway-deployment)
7. [Package Management (Critical)](#7-package-management-critical)
8. [Environment Variables](#8-environment-variables)
9. [Pitfalls & Gotchas](#9-pitfalls--gotchas)
10. [Testing](#10-testing)
11. [Reference Links](#11-reference-links)

---

## 1. Architecture Overview

```
┌─────────────┐   WebSocket    ┌──────────────┐   gRPC   ┌──────────────────┐
│  React SPA  │ ◄────────────► │ LiveKit Cloud │ ◄──────► │ Agent Worker     │
│  (browser)  │                │  (SFU rooms)  │          │ (Python process) │
└──────┬──────┘                └──────────────┘          └──────────────────┘
       │ POST /livekit/token                                     │
       ▼                                                         │
┌──────────────┐                                                 │
│  FastAPI     │                                                 │
│  (main app)  │◄────────────── DB queries (SQLAlchemy) ────────┘
└──────────────┘
```

Three independent processes:

| Process | What it does | Runs where |
|---------|-------------|------------|
| **FastAPI** | REST API + token endpoint | Railway service (or local uvicorn) |
| **Agent Worker** | Registers with LiveKit Cloud, joins rooms, runs STT→LLM→TTS pipeline | Railway service (or local CLI) |
| **LiveKit Cloud** | SFU — routes audio/video between browser and agent | Managed service (livekit.io) |

The **browser never talks directly to the agent**. It connects to a LiveKit room. The agent connects to the same room. LiveKit Cloud brokers all media.

---

## 2. LiveKit Cloud Setup

1. Sign up at [https://cloud.livekit.io](https://cloud.livekit.io)
2. Create a project → you get three values:
   - `LIVEKIT_URL` — e.g. `wss://your-project-abc123.livekit.cloud`
   - `LIVEKIT_API_KEY` — e.g. `APIxxxxxxxxxxxx`
   - `LIVEKIT_API_SECRET` — long secret string
3. These same credentials are used by:
   - The **token endpoint** (to sign JWTs)
   - The **agent worker** (to register and join rooms)
   - The **frontend** (only the URL, never the secret)

---

## 3. Backend: Python Agent Worker

### Minimal Agent

```python
"""voice/livekit_agent.py"""
from __future__ import annotations  # Required if targeting Python < 3.10

import json, logging, os
from typing import Annotated

from livekit import agents
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, RunContext,
    cli, function_tool, room_io,
)
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("my-agent")

# ── Define tools the agent can call ──────────────────────────────

@function_tool(description="Look up a user's order by ID")
async def get_order(
    ctx: RunContext,
    order_id: Annotated[int, "The order ID to look up"],
) -> str:
    """Return order details as JSON string."""
    # Access user info via ctx.userdata (set at session start)
    user_id = ctx.userdata.get("user_id")
    # ... your DB query here ...
    return json.dumps({"order_id": order_id, "status": "shipped"})


# ── Agent class ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful assistant for Acme Corp..."""

class MyAssistant(Agent):
    def __init__(self, user_name="there"):
        super().__init__(
            instructions=SYSTEM_PROMPT + f"\nUser: {user_name}",
            tools=[get_order],   # List of @function_tool functions
        )


# ── Server + Session ────────────────────────────────────────────

server = AgentServer()

@server.rtc_session()
async def handle_session(ctx: JobContext):
    """Fired when a participant joins a LiveKit room."""
    await ctx.connect()
    participant = await ctx.wait_for_participant()

    # Read user metadata from JWT (set by your token endpoint)
    metadata = {}
    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
        except (json.JSONDecodeError, TypeError):
            pass

    user_name = metadata.get("name", "there")
    user_id = metadata.get("user_id", "anonymous")

    session = AgentSession(
        stt=deepgram.STT(model="nova-2", language="en-US"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.2),
        tts=openai.TTS(model="tts-1", voice="nova"),
        vad=silero.VAD.load(),
        userdata={"user_id": user_id, "name": user_name},
    )

    await session.start(
        agent=MyAssistant(user_name=user_name),
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(),
    )

    # Optional: generate an initial greeting
    await session.generate_reply(
        instructions=f"Greet {user_name} warmly. Keep it brief."
    )

if __name__ == "__main__":
    cli.run_app(server)
```

### Key Concepts

- **`@function_tool`**: Decorator that registers a Python function as an LLM tool. The function's type annotations (`Annotated[str | None, "description"]`) are introspected at runtime to build the tool schema.
- **`RunContext`**: Passed as first arg to every tool. Access `ctx.userdata` for session-level data (user ID, role, etc.) and `ctx.session` for the session itself.
- **`AgentSession`**: Orchestrates the STT→LLM→TTS pipeline. Created per-participant.
- **`AgentServer`**: Registers with LiveKit Cloud and dispatches incoming room connections.
- **`generate_reply(instructions=...)`**: Ask the LLM to generate a response with specific instructions (useful for greetings, proactive messages).

### Running Locally

```bash
# Dev mode (auto-reloads, prints logs to stdout)
python -m voice.livekit_agent dev

# Production mode
python -m voice.livekit_agent start
```

The `dev` subcommand is provided by `cli.run_app()` automatically.

---

## 4. Backend: Token Endpoint

Your FastAPI app needs a route that generates signed JWTs for the frontend to join a room. The agent worker auto-joins when it detects a participant.

```python
"""voice/routers/livekit_router.py"""
from __future__ import annotations

import os, time, json, logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants

router = APIRouter(prefix="/livekit", tags=["livekit"])

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")


class TokenRequest(BaseModel):
    user_id: Optional[str] = "anonymous"
    user_name: Optional[str] = "Guest"
    user_role: Optional[str] = "user"


class TokenResponse(BaseModel):
    token: str
    url: str
    room: str


@router.post("/token", response_model=TokenResponse)
async def create_token(req: TokenRequest):
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(503, "LiveKit not configured")

    # Unique room per user session
    room_name = f"voice-{req.user_id}-{int(time.time())}"

    # Metadata — agent reads this to know who it's talking to
    metadata = json.dumps({
        "name": req.user_name,
        "role": req.user_role,
        "user_id": req.user_id,
    })

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(str(req.user_id))
        .with_name(req.user_name or "Guest")
        .with_metadata(metadata)         # <-- agent reads this
        .with_grants(VideoGrants(room_join=True, room=room_name))
        .with_ttl(timedelta(hours=1))
    )

    return TokenResponse(
        token=token.to_jwt(),
        url=LIVEKIT_URL,
        room=room_name,
    )


@router.get("/health")
async def health():
    configured = bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET and LIVEKIT_URL)
    return {"configured": configured}
```

Register it in your main app:

```python
from voice.routers.livekit_router import router as livekit_router
app.include_router(livekit_router, prefix="/api")
```

---

## 5. Frontend: React Voice Panel

### Packages

```bash
npm install livekit-client @livekit/components-react @livekit/components-styles
```

| Package | Purpose |
|---------|---------|
| `livekit-client` | Core JS SDK — room connect, tracks, token |
| `@livekit/components-react` | React hooks: `useSession`, `useAgent`, `useVoiceAssistant`, `BarVisualizer` |
| `@livekit/components-styles` | Optional CSS. **Warning:** its resets can conflict with Tailwind — import selectively |

### Minimal Component

```jsx
import { useState, useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import {
  useSession,
  useAgent,
  useVoiceAssistant,
  SessionProvider,
  BarVisualizer,
  RoomAudioRenderer,
} from '@livekit/components-react';
import { Track } from 'livekit-client';

export default function VoicePanel({ userId, userName }) {
  const tokenSource = useMemo(
    () =>
      TokenSource.custom(async () => {
        const res = await fetch('/api/livekit/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, user_name: userName }),
        });
        const data = await res.json();
        return { participantToken: data.token, serverUrl: data.url };
      }),
    [userId, userName],
  );

  const session = useSession(tokenSource);

  return (
    <SessionProvider session={session}>
      <VoicePanelInner session={session} />
    </SessionProvider>
  );
}

function VoicePanelInner({ session }) {
  const agent = useAgent(session);
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant();

  return (
    <div>
      <p>Agent state: {state}</p>

      {/* Renders agent audio — required or you won't hear anything */}
      <RoomAudioRenderer />

      {/* Visual audio bars */}
      {audioTrack && (
        <BarVisualizer
          state={state}
          barCount={5}
          trackRef={audioTrack}
        />
      )}

      {/* Connect/disconnect */}
      <button onClick={() => session.isConnected ? session.disconnect() : session.connect()}>
        {session.isConnected ? 'Disconnect' : 'Start Voice'}
      </button>
    </div>
  );
}
```

### Key Frontend Patterns

- **`TokenSource.custom()`** — async function that fetches a token from your backend. Called on connect and on token refresh.
- **`useSession(tokenSource)`** — manages the room lifecycle. Returns a session object.
- **`<SessionProvider>`** — React context that makes the session available to child hooks.
- **`useVoiceAssistant()`** — returns `state` (listening/thinking/speaking/idle), `audioTrack`, `agentTranscriptions`.
- **`<RoomAudioRenderer />`** — **CRITICAL**: renders a hidden `<audio>` element. Without it, you won't hear the agent.
- **`useTextStream('topic')`** — receive text data from the agent (e.g., action cards, structured data).

### Agent States

```
disconnected → connecting → initializing → idle → listening → thinking → speaking → idle → ...
```

The agent goes idle between turns. `listening` means STT is active. `thinking` means the LLM is generating. `speaking` means TTS audio is playing.

---

## 6. Railway Deployment

### Service Architecture

You need **two Railway services** sharing the same codebase:

| Service Name | Start Command | Purpose |
|---|---|---|
| `web` (or default) | `uvicorn main:app --host 0.0.0.0 --port $PORT` | FastAPI + token endpoint |
| `LiveKit Voice Agent` | `python -m voice.livekit_agent start` | Agent worker |

### railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "if [ \"$RAILWAY_SERVICE_NAME\" = \"LiveKit Voice Agent\" ]; then python -m voice.livekit_agent start; else uvicorn main:app --host 0.0.0.0 --port $PORT; fi",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Use `$RAILWAY_SERVICE_NAME` to branch the start command.

### Railway-Specific Environment Fixes

The agent worker **will crash on Railway** without these environment overrides. Set them at the top of your agent module, before any LiveKit imports:

```python
import os

# Single-worker mode — Railway containers have limited PIDs/threads
os.environ["LIVEKIT_WORKERS"] = "1"

# Disable OpenTelemetry — it spawns background threads that crash on Railway
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
os.environ["LIVEKIT_OTEL_ENABLED"] = "false"

# Unbuffered output for Railway logs
os.environ["PYTHONUNBUFFERED"] = "1"

# Rust/Tokio thread limits (livekit-agents uses Rust under the hood)
os.environ["TOKIO_WORKER_THREADS"] = "1"
os.environ["RAYON_NUM_THREADS"] = "1"
os.environ["NUMBA_NUM_THREADS"] = "1"
```

**Why?** Railway runs containers with limited PID/thread resources. LiveKit's agent SDK defaults to multi-worker mode and enables OpenTelemetry — both spawn threads that hit Railway's limits and cause `OSError: [Errno 1] Operation not permitted` or silent crashes.

### Detecting Railway at Runtime

```python
IS_RAILWAY = (
    os.environ.get("RAILWAY_ENVIRONMENT") == "production"
    or os.environ.get("RAILWAY_SERVICE_NAME") is not None
)
```

Useful for conditional logic (e.g., different logging levels, disabling certain features).

---

## 7. Package Management (Critical)

This is the **single biggest pain point**. Read carefully.

### The Two-Venv Problem

The LiveKit Agents SDK (`livekit-agents`) requires **Python 3.10+** (it uses `TypeAlias`, `str | None` syntax, etc.). If your main application runs on Python 3.9 (common on macOS), you cannot install the agent SDK in the same virtualenv.

**Solution: Use two virtual environments locally.**

```bash
# Main app venv (Python 3.9+ for FastAPI, can be any version)
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# LiveKit agent venv (Python 3.11+)
python3.11 -m venv venv-livekit
source venv-livekit/bin/activate
pip install -r requirements.txt   # same requirements.txt works
```

On **Railway**, this isn't an issue — Nixpacks auto-detects Python 3.11+ from `requirements.txt`. Both services share the same build.

### The Token Endpoint Package

Your **FastAPI** server needs `livekit-api` (lightweight, for signing tokens). It does NOT need `livekit-agents` or the plugins. However, if they're all in the same `requirements.txt`, they'll all be installed.

Minimum for the token endpoint only:

```
livekit-api>=1.1.0
```

Full set for the agent worker:

```
livekit>=1.1.0
livekit-agents>=1.4.0
livekit-api>=1.1.0
livekit-plugins-deepgram>=1.4.0
livekit-plugins-openai>=1.4.0
livekit-plugins-silero>=1.4.0
```

Optional:
```
livekit-plugins-noise-cancellation>=0.2.0  # Krisp-based, adds ~50MB
```

### Version Pinning

**Keep `livekit-agents` and all `livekit-plugins-*` on the same minor version.** They are released in lockstep. Mixing versions (e.g., agents 1.4.5 with plugins 1.3.x) will cause subtle runtime errors.

### `from __future__ import annotations`

If your codebase may run on Python < 3.10 (even just for tests), add this to any file that uses `str | None` union syntax:

```python
from __future__ import annotations
```

This makes all annotations strings (PEP 563), deferring evaluation. It's safe for LiveKit — the `@function_tool` decorator uses `typing.get_type_hints()` which correctly resolves string annotations on Python 3.10+.

---

## 8. Environment Variables

| Variable | Required By | Example |
|----------|------------|---------|
| `LIVEKIT_URL` | Token endpoint + Frontend | `wss://your-project.livekit.cloud` |
| `LIVEKIT_API_KEY` | Token endpoint + Agent worker | `APIxxxxxxxxxxxx` |
| `LIVEKIT_API_SECRET` | Token endpoint + Agent worker | `secret...` |
| `DEEPGRAM_API_KEY` | Agent worker (STT) | `dg_...` |
| `OPENAI_API_KEY` | Agent worker (LLM + TTS) | `sk-...` |

Set all of these in Railway's service variables. The agent worker reads `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` automatically (convention from the SDK).

---

## 9. Pitfalls & Gotchas

### 1. Lazy Imports for Cross-Service Code

If your agent tools import modules that depend on packages only in your main venv (e.g., `stripe`, `redis`), those imports will fail in the agent worker's venv.

**Fix: Use lazy imports inside function bodies.**

```python
# BAD — fails at module load if stripe isn't installed
from services.stripe_service import create_payment_intent

async def donate(ctx: RunContext, amount: float) -> str:
    result = create_payment_intent(amount)  # crashes before we get here


# GOOD — only imported when the tool is actually called
async def donate(ctx: RunContext, amount: float) -> str:
    from services.stripe_service import create_payment_intent
    result = create_payment_intent(amount)
```

Also watch out for `__init__.py` files that eagerly import submodules — a single eager import in an `__init__.py` can cascade into a `ModuleNotFoundError` for an unrelated package.

### 2. `__init__.py` Import Chains

Python evaluates `__init__.py` when you import *any* submodule from a package. If your `voice/handlers/__init__.py` does:

```python
from voice.handlers import donor_handlers  # This triggers...
# donor_handlers.py imports donation_handler.py
# donation_handler.py imports stripe at module level → CRASH
```

The entire import chain executes. Move heavy imports to function bodies or guard them with try/except.

### 3. CSS Conflicts with `@livekit/components-styles`

The LiveKit components styles package includes CSS resets that will **break your existing styles** if you use Tailwind CSS or any other framework. Either:

- Don't import it globally — cherry-pick only what you need
- Import it in an isolated scope
- Write your own styles for LiveKit components

### 4. `<RoomAudioRenderer />` is Mandatory

If you don't render `<RoomAudioRenderer />` somewhere in the component tree inside `<SessionProvider>`, **you will not hear the agent**. There will be no error — just silence. This is the #1 "it's not working" issue.

### 5. Agent Worker Must Use `start`, Not `dev` in Production

```bash
# Local development (auto-reload, verbose logs)
python -m voice.livekit_agent dev

# Production (Railway)
python -m voice.livekit_agent start
```

The `dev` command enables features that are inappropriate for production (e.g., reload watchers that spawn extra threads).

### 6. Metadata is the Bridge Between Token and Agent

The user's identity, role, name, etc. must be embedded in the JWT **metadata** at the token endpoint. The agent reads it from `participant.metadata` when the user joins. There is no other way for the agent to know who it's talking to.

### 7. Action Cards via Text Streams

To send structured data from the agent to the frontend (e.g., payment links, UI cards), use LiveKit's text stream:

**Agent side:**
```python
await ctx.session.room_io.room.local_participant.send_text(
    json.dumps({"type": "payment_link", "url": "https://..."}),
    topic="my-app.actions",
)
```

**Frontend side:**
```jsx
const { textStreams } = useTextStream('my-app.actions');
// textStreams is a Map of stream entries — parse JSON from each
```

### 8. `userdata` vs `metadata`

- **`metadata`** — string attached to the JWT/participant. Set at the token endpoint. Read-only from the agent's perspective.
- **`userdata`** — Python dict passed to `AgentSession()`. Available in every `@function_tool` via `ctx.userdata`. Mutable. Use this for per-session state.

---

## 10. Testing

### Test Strategy

The agent worker runs in Python 3.11 with a specific set of heavy dependencies (livekit, deepgram, etc.). **Run your voice tests in the same environment the code runs in.**

Don't try to make voice agent tests work in a different Python version by stubbing the entire LiveKit SDK — it's fragile and defeats the purpose.

```bash
# Run voice tests in the livekit venv
venv-livekit/bin/python -m pytest tests/test_voice_tools.py -v
```

### Stubbing Pattern for Tools

Tools interact with the database and external services. Stub the DB and external calls, not LiveKit itself:

```python
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# In-memory SQLite for tests
engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)

@pytest.fixture
def db_session():
    from database.models import Base
    Base.metadata.create_all(engine)
    session = Session()
    # IMPORTANT: Neuter session.close() — tool code often calls
    # db.close() in a finally block, which would destroy our test session
    session.close = lambda: None
    yield session
    session.rollback()
    Base.metadata.drop_all(engine)

# Mock RunContext
def make_ctx(user_id="1", role="DONOR"):
    ctx = MagicMock()
    ctx.userdata = {"user_id": user_id, "role": role, "name": "Test"}
    ctx.session = MagicMock()
    return ctx

# Patch _get_db to return our test session
@patch("voice.livekit_agent._get_db")
async def test_my_tool(mock_db, db_session):
    mock_db.return_value = db_session
    # ... seed data, call tool, assert results ...
```

### Testing with Lazy Imports

If you moved imports to be lazy (inside function bodies), remember to patch at the **source module**, not the importing module:

```python
# If donation_handler does: from services.stripe_service import create_payment_intent
# inside the function body, patch the source:
with patch("services.stripe_service.create_payment_intent", return_value={"id": "pi_123"}):
    result = await initiate_donation(...)
```

---

## 11. Reference Links

### Official Documentation

- **LiveKit Agents (Python) — Quickstart**
  https://docs.livekit.io/agents/quickstart/

- **LiveKit Agents — Overview & Concepts**
  https://docs.livekit.io/agents/overview/

- **LiveKit Agents — Function Tools**
  https://docs.livekit.io/agents/build/tools/function-tools/

- **LiveKit Agents — Python API Reference**
  https://docs.livekit.io/agents/reference/python/

- **LiveKit Components React — Getting Started**
  https://docs.livekit.io/reference/components/react/

- **LiveKit Server SDK (Token Generation)**
  https://docs.livekit.io/home/get-started/authentication/

- **LiveKit Cloud Dashboard**
  https://cloud.livekit.io

### Plugin Docs

- **Deepgram STT Plugin**: https://docs.livekit.io/agents/plugins/stt/deepgram/
- **OpenAI LLM/TTS Plugin**: https://docs.livekit.io/agents/plugins/llm/openai/
- **Silero VAD Plugin**: https://docs.livekit.io/agents/plugins/utilities/silero/

### GitHub Repos

- `livekit/agents` (Python SDK): https://github.com/livekit/agents
- `livekit/components-js` (React components): https://github.com/livekit/components-js
- `livekit/python-sdks` (livekit-api for token gen): https://github.com/livekit/python-sdks

### Railway

- **Railway Nixpacks Python**: https://nixpacks.com/docs/providers/python
- **Railway Multi-Service Setup**: https://docs.railway.app/guides/services

---

## Quick Checklist

- [ ] LiveKit Cloud project created, 3 env vars noted
- [ ] `livekit-api` in requirements for token endpoint
- [ ] `livekit-agents` + plugins in requirements for agent worker
- [ ] All plugin versions match the agents version
- [ ] Token endpoint returns `{token, url, room}` with user metadata in JWT
- [ ] Agent worker reads metadata from `participant.metadata`
- [ ] `<RoomAudioRenderer />` rendered in frontend
- [ ] `from __future__ import annotations` in files using `str | None`
- [ ] Railway env vars set: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `DEEPGRAM_API_KEY`, `OPENAI_API_KEY`
- [ ] Railway agent service start command: `python -m <module> start`
- [ ] Railway thread/worker limits set at top of agent module
- [ ] Lazy imports for any cross-service dependencies (stripe, redis, etc.)
- [ ] Tests run in the same Python version as production
