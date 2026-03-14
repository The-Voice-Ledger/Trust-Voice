"""
LiveKit Router -- Token generation for real-time voice sessions.

Provides a token endpoint that the frontend calls to join a
LiveKit room for real-time voice interaction with the AI agent.
"""

import os
import logging
import time
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from livekit.api import AccessToken, VideoGrants

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/livekit", tags=["livekit"])

# ── Config ──────────────────────────────────────────────────────
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")


class TokenRequest(BaseModel):
    """Request body for generating a LiveKit room token."""
    user_id: Optional[str | int] = "web_anonymous"  # Accept both string and int
    user_name: Optional[str] = "Guest"
    user_role: Optional[str] = "DONOR"


class TokenResponse(BaseModel):
    """Response with token and connection details."""
    token: str
    url: str
    room: str


@router.post("/token", response_model=TokenResponse)
async def create_livekit_token(req: TokenRequest):
    """
    Generate a LiveKit access token for a user to join a voice room.

    Each user gets their own room (1:1 with the AI agent).
    The LiveKit agent worker auto-joins when a participant connects.
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET.",
        )

    # Each user gets a unique room for their voice session
    # Convert user_id to string for LiveKit compatibility
    user_id_str = str(req.user_id) if req.user_id is not None else "web_anonymous"
    room_name = f"vbv-voice-{user_id_str}-{int(time.time())}"
    participant_identity = user_id_str

    # Metadata passed to the agent so it knows who it's talking to
    import json
    metadata = json.dumps({
        "name": req.user_name,
        "role": req.user_role,
        "user_id": user_id_str,
    })

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_identity)
        .with_name(req.user_name or "Guest")
        .with_metadata(metadata)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
            )
        )
        .with_ttl(timedelta(hours=1))
    )

    jwt_token = token.to_jwt()

    logger.info(
        f"LiveKit token generated: room={room_name}, "
        f"user={participant_identity}"
    )

    return TokenResponse(
        token=jwt_token,
        url=LIVEKIT_URL,
        room=room_name,
    )


@router.get("/health")
async def livekit_health():
    """Check if LiveKit integration is configured."""
    configured = bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET and LIVEKIT_URL)
    return {
        "configured": configured,
        "url": LIVEKIT_URL if configured else None,
    }
