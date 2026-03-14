"""
VBV LiveKit Voice Agent

Real-time conversational AI agent for VBV platform using LiveKit Cloud.
Uses Deepgram Nova-2 for streaming STT, OpenAI GPT-4o-mini for LLM,
OpenAI TTS for speech, and Silero for voice activity detection.

Architecture:
    AgentServer registers with LiveKit Cloud and waits for dispatch.
    When a user joins a room, @server.rtc_session fires a new job.
    AgentSession orchestrates the STT -> LLM -> TTS voice pipeline.
    VBVAssistant (Agent subclass) holds instructions, tools, and
    per-agent overrides.

Runs as a separate worker process (Python 3.11 venv-livekit)
alongside the FastAPI server.

Usage:
    source venv-livekit/bin/activate
    python -m voice.livekit_agent dev
"""


# Detect if running on Railway
IS_RAILWAY = os.environ.get("RAILWAY_ENVIRONMENT") == "production" or os.environ.get("RAILWAY_SERVICE_NAME") is not None

# Import noise_cancellation only if not on Railway
if not IS_RAILWAY:
    from livekit.plugins import noise_cancellation
else:
    noise_cancellation = None

import json
import logging
from typing import Annotated

from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    function_tool,
    room_io,
)
from livekit.plugins import deepgram, openai, silero

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("vbv-livekit-agent")
logger.setLevel(logging.INFO)


# ── Database helper ─────────────────────────────────────────────

def _get_db():
    """Get a fresh DB session."""
    from database.db import SessionLocal
    return SessionLocal()


# ── Tool implementations (standalone @function_tool) ────────────

@function_tool(description=(
    "Search for active fundraising campaigns. Use when the user "
    "wants to find, browse, list, or discover campaigns."
))
async def search_campaigns(
    category: Annotated[str | None, "Campaign category (education, health, water, environment, food, shelter, economic, community)"] = None,
    location: Annotated[str | None, "Location or region to filter by (e.g. Kenya, Nairobi)"] = None,
    keyword: Annotated[str | None, "Free-text keyword to search in titles and descriptions"] = None,
) -> str:
    """Search for active campaigns with optional filters."""
    from sqlalchemy import or_, func
    from database.models import Campaign

    db = _get_db()
    try:
        q = db.query(Campaign).filter(Campaign.status == "active")
        if category:
            q = q.filter(func.lower(Campaign.category) == category.lower())
        if location:
            q = q.filter(
                or_(
                    Campaign.location_country.ilike(f"%{location}%"),
                    Campaign.location_region.ilike(f"%{location}%"),
                )
            )
        if keyword:
            q = q.filter(
                or_(
                    Campaign.title.ilike(f"%{keyword}%"),
                    Campaign.description.ilike(f"%{keyword}%"),
                )
            )
        campaigns = q.order_by(Campaign.created_at.desc()).limit(5).all()
        if not campaigns:
            return json.dumps({"campaigns": [], "message": "No campaigns found matching your criteria."})

        results = []
        for c in campaigns:
            goal = float(c.goal_amount_usd or 0)
            raised = float(c.raised_amount_usd or 0)
            pct = round((raised / goal * 100) if goal > 0 else 0, 1)
            results.append({
                "id": c.id,
                "title": c.title,
                "category": c.category,
                "location": c.location_country or c.location_region or "N/A",
                "raised_usd": round(raised, 2),
                "goal_usd": round(goal, 2),
                "progress_pct": pct,
            })
        return json.dumps({"campaigns": results})
    finally:
        db.close()


@function_tool(description=(
    "Get full details of a specific campaign including goal, "
    "amount raised, description, and location."
))
async def get_campaign_details(
    campaign_id: Annotated[int, "The campaign ID number"],
) -> str:
    """Get detailed info about a specific campaign."""
    from database.models import Campaign, NGOOrganization

    db = _get_db()
    try:
        c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not c:
            return json.dumps({"error": f"Campaign #{campaign_id} not found."})

        ngo = None
        if c.ngo_id:
            ngo = db.query(NGOOrganization).filter(NGOOrganization.id == c.ngo_id).first()

        goal = float(c.goal_amount_usd or 0)
        raised = float(c.raised_amount_usd or 0)
        pct = round((raised / goal * 100) if goal > 0 else 0, 1)

        return json.dumps({
            "campaign": {
                "id": c.id,
                "title": c.title,
                "description": (c.description or "")[:300],
                "category": c.category,
                "location": c.location_country or c.location_region or "N/A",
                "ngo_name": ngo.name if ngo else "Individual",
                "raised_usd": round(raised, 2),
                "goal_usd": round(goal, 2),
                "progress_pct": pct,
                "status": c.status,
                "donor_count": getattr(c, "donor_count", 0) or 0,
            }
        })
    finally:
        db.close()


@function_tool(description=(
    "Get platform-wide statistics: active campaigns, total donated, "
    "number of donations, and number of donors."
))
async def get_platform_stats() -> str:
    """Get aggregate platform stats."""
    from sqlalchemy import func as sqlfunc
    from database.models import Campaign, Donation, Donor

    db = _get_db()
    try:
        active = db.query(Campaign).filter(Campaign.status == "active").count()
        total_donated = db.query(
            sqlfunc.coalesce(sqlfunc.sum(Donation.amount_usd), 0)
        ).filter(Donation.status == "completed").scalar()
        total_donations = db.query(Donation).filter(
            Donation.status == "completed"
        ).count()
        total_donors = db.query(Donor).count()

        return json.dumps({
            "stats": {
                "active_campaigns": active,
                "total_raised_usd": round(float(total_donated), 2),
                "total_donations": total_donations,
                "total_donors": total_donors,
            }
        })
    finally:
        db.close()


@function_tool(description=(
    "Get milestones for a campaign showing project progress, "
    "status of each milestone, and amounts."
))
async def get_project_milestones(
    campaign_id: Annotated[int, "The campaign ID number"],
) -> str:
    """Get milestones for a campaign."""
    from database.models import Campaign

    db = _get_db()
    try:
        c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not c:
            return json.dumps({"error": f"Campaign #{campaign_id} not found."})

        try:
            from database.models import Milestone
            milestones = db.query(Milestone).filter(
                Milestone.campaign_id == campaign_id
            ).order_by(Milestone.sequence_number).all()

            results = []
            for m in milestones:
                results.append({
                    "id": m.id,
                    "title": m.title,
                    "description": (m.description or "")[:150],
                    "status": m.status,
                    "amount_usd": float(m.amount_usd or 0),
                    "sequence": m.sequence_number,
                })
            return json.dumps({
                "milestones": results,
                "campaign_title": c.title,
            })
        except Exception:
            return json.dumps({
                "milestones": [],
                "campaign_title": c.title,
                "message": "No milestones configured.",
            })
    finally:
        db.close()


@function_tool(description="Get help on what the assistant can do.")
async def get_help() -> str:
    """Return capabilities list."""
    return json.dumps({
        "capabilities": [
            "Search and browse active campaigns",
            "Get detailed information about a specific campaign",
            "View platform-wide statistics and analytics",
            "Check project milestones and progress",
            "Learn about how VBV works",
        ],
        "message": (
            "I can help you search for campaigns, get campaign details, "
            "check platform stats, and view project milestones. "
            "Just ask me anything!"
        ),
    })


# ── System prompt ───────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are VBV Assistant -- a helpful, concise AI for a voice-first "
    "crowdfunding platform connecting donors with verified projects "
    "across Africa.\n\n"
    "PLATFORM MODEL: Projects raise funds through milestone-based "
    "releases. Donors fund a campaign, and money is released only "
    "after each milestone is verified by an independent field agent "
    "on the ground. A small platform fee (typically 6%) is deducted "
    "on each milestone release. This ensures transparency and "
    "accountability.\n\n"
    "RULES:\n"
    "1. Be concise -- responses are spoken aloud. Aim for 1-3 short "
    "sentences. Longer only when listing campaigns.\n"
    "2. Use tools for ALL data and actions -- never fabricate numbers.\n"
    "3. When listing campaigns, always include the campaign ID.\n"
    "4. If information is missing, ask -- don't guess.\n"
    "5. Be warm, professional, and encouraging. This is a platform "
    "for social good.\n"
    "6. When reading campaign results, summarize naturally -- "
    "don't read JSON.\n"
    "7. Use plain language. Avoid jargon.\n"
    "8. Do not use em-dashes in your responses.\n"
)

ALL_TOOLS = [
    search_campaigns,
    get_campaign_details,
    get_platform_stats,
    get_project_milestones,
    get_help,
]


# ── VBV Agent class ────────────────────────────────────────────

class VBVAssistant(Agent):
    """Voice-first assistant for the VBV crowdfunding platform."""

    def __init__(self, user_name: str = "there", user_role: str = "DONOR"):
        personalized_prompt = (
            SYSTEM_PROMPT
            + f"\nUSER: {user_name}  |  ROLE: {user_role}\n"
            + "Respond in English.\n"
        )
        super().__init__(
            instructions=personalized_prompt,
            tools=ALL_TOOLS,
        )
        self._user_name = user_name


# ── Agent Server + Session (v1.4 API) ──────────────────────────

server = AgentServer()


@server.rtc_session()
async def vbv_voice_session(ctx: JobContext):
    """
    Fired when a participant joins a LiveKit room.
    Waits for the user, reads metadata, creates session with
    STT/LLM/TTS/VAD pipeline, and starts the assistant.
    """
    logger.info(f"Agent job started for room: {ctx.room.name}")

    await ctx.connect()

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Extract user metadata set in the JWT
    metadata = {}
    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
        except (json.JSONDecodeError, TypeError):
            pass

    user_name = metadata.get("name", "there")
    user_role = metadata.get("role", "DONOR")

    # Create the session with audio pipeline components
    session = AgentSession(
        stt=deepgram.STT(model="nova-2", language="en-US"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.2),
        tts=openai.TTS(model="tts-1", voice="nova"),
        vad=silero.VAD.load(),
    )

    # Start the session with our agent + noise cancellation
    await session.start(
        agent=VBVAssistant(user_name=user_name, user_role=user_role),
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC() if noise_cancellation else None,
        ),
    )

    # Generate an initial greeting
    await session.generate_reply(
        instructions=(
            f"Greet the user whose name is {user_name}. "
            "Tell them you are the VBV assistant and you can help them "
            "find campaigns, check platform stats, view project milestones, "
            "or learn how VBV works. Keep it warm and brief."
        )
    )


# ── Worker entry point ──────────────────────────────────────────

if __name__ == "__main__":
    cli.run_app(server)
