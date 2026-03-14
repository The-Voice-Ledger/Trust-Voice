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

# Fix multiprocessing and threading issues on Railway
import os
os.environ["PYTHONMULTIPROCESSING"] = "0"
os.environ["LIVEKIT_WORKERS"] = "1"

# Disable OpenTelemetry to prevent thread creation issues
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
os.environ["LIVEKIT_OTEL_ENABLED"] = "false"

# Additional Railway-specific fixes
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["NO_PROXY"] = "*"
os.environ["PYTHONPATH"] = "/opt/venv/lib/python3.12/site-packages"

# Rust/Tokio thread limits for Railway
os.environ["TOKIO_WORKER_THREADS"] = "1"
os.environ["RAYON_NUM_THREADS"] = "1"
os.environ["NUMBA_NUM_THREADS"] = "1"

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


# ── Action-card helper (push visual cards to frontend) ──────────

ACTION_TOPIC = "vbv.action"

async def _send_action_card(ctx: RunContext, card: dict) -> None:
    """Push a visual action card to the frontend via LiveKit text stream.

    Card types: payment_link, campaign_card, campaign_list,
    donation_receipt, donation_history, milestone_update, error
    """
    try:
        room = ctx.session.room_io.room
        await room.local_participant.send_text(
            json.dumps(card),
            topic=ACTION_TOPIC,
        )
    except Exception as e:
        logger.warning(f"Failed to send action card: {e}")


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
            sqlfunc.coalesce(sqlfunc.sum(Donation.amount), 0)
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
            from database.models import ProjectMilestone
            milestones = db.query(ProjectMilestone).filter(
                ProjectMilestone.campaign_id == campaign_id
            ).order_by(ProjectMilestone.sequence).all()

            results = []
            for m in milestones:
                results.append({
                    "id": m.id,
                    "title": m.title,
                    "description": (m.description or "")[:150],
                    "status": m.status,
                    "target_amount_usd": float(m.target_amount_usd or 0),
                    "released_amount_usd": float(m.released_amount_usd or 0),
                    "sequence": m.sequence,
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
            "Donate to a campaign by voice",
            "Check your donation history",
            "Approve or reject milestones (admin/field agent)",
            "Submit milestone evidence (NGO)",
            "Approve or reject payouts (admin)",
            "Create a new campaign (NGO)",
            "Learn about how TrustVoice works",
        ],
        "message": (
            "I can help you donate, search for campaigns, manage milestones, "
            "check platform stats, and much more. Just ask me anything!"
        ),
    })


# ── TIER 1 — Write tools (voice-actionable) ────────────────────


@function_tool(description=(
    "Donate to a campaign. Use when the user wants to donate, fund, "
    "contribute, or give money to a campaign. ALWAYS confirm the "
    "campaign name, amount, and currency with the user BEFORE calling "
    "this tool. For Stripe/card payments, a secure checkout link will "
    "be displayed in the chat panel. For M-Pesa, a payment prompt "
    "will be sent to the user's phone."
))
async def donate_to_campaign(
    ctx: RunContext,
    campaign_id: Annotated[int, "The campaign ID to donate to"],
    amount: Annotated[float, "The donation amount (e.g. 50.0)"],
    currency: Annotated[str, "Currency code: USD, EUR, GBP, KES, etc."] = "USD",
    payment_method: Annotated[str | None, "Payment method: 'stripe' for card, 'mpesa' for M-Pesa. If not specified, auto-detected from user profile."] = None,
) -> str:
    """Initiate a donation to a campaign."""
    from database.models import Campaign, User, Donor
    from voice.handlers.donation_handler import initiate_voice_donation

    userdata = ctx.userdata
    user_id = userdata.get("user_id")

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to donate. Please log in first."})

    db = _get_db()
    try:
        # Validate campaign exists and is active
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return json.dumps({"error": f"Campaign #{campaign_id} not found."})
        if campaign.status != "active":
            return json.dumps({"error": f"Campaign is not active (status: {campaign.status})."})

        # Find user — try integer ID first, then telegram_user_id
        user = None
        try:
            uid = int(user_id)
            user = db.query(User).filter(User.id == uid).first()
        except (ValueError, TypeError):
            user = db.query(User).filter(User.telegram_user_id == str(user_id)).first()

        if not user:
            return json.dumps({"error": "User account not found. Please register first."})

        # Find or create donor record — link to user by telegram_user_id or phone
        donor = None
        if user.telegram_user_id:
            donor = db.query(Donor).filter(Donor.telegram_user_id == user.telegram_user_id).first()
        if not donor and user.phone_number:
            donor = db.query(Donor).filter(Donor.phone_number == user.phone_number).first()
        if not donor and user.email:
            donor = db.query(Donor).filter(Donor.email == user.email).first()

        # Create donor record if none exists
        if not donor:
            from datetime import datetime as dt
            donor = Donor(
                phone_number=user.phone_number,
                telegram_user_id=user.telegram_user_id,
                preferred_name=user.full_name,
                email=user.email if hasattr(user, 'email') else None,
                created_at=dt.utcnow(),
            )
            db.add(donor)
            db.flush()
            logger.info(f"Created donor record for user {user_id}")

        # Auto-detect payment method
        if not payment_method:
            if donor.phone_number and donor.phone_number.startswith("+254"):
                payment_method = "mpesa"
            elif currency.upper() == "KES":
                payment_method = "mpesa"
            else:
                payment_method = "stripe"

        # Use the lookup key for donation handler (telegram_user_id or str(id))
        lookup_id = user.telegram_user_id or str(user.id)

        result = await initiate_voice_donation(
            db=db,
            telegram_user_id=lookup_id,
            campaign_id=campaign.id,
            amount=float(amount),
            currency=currency.upper(),
            payment_method=payment_method,
        )

        if result.get("success"):
            response = {
                "success": True,
                "donation_id": str(result.get("donation_id", "")),
                "payment_method": result.get("payment_method"),
                "amount": amount,
                "currency": currency.upper(),
                "campaign_title": campaign.title,
            }
            if result.get("payment_method") == "stripe":
                checkout_url = result.get("checkout_url", "")
                response["checkout_url"] = checkout_url
                response["instructions"] = (
                    f"A secure payment link for ${amount:.2f} {currency.upper()} "
                    f"has been created for {campaign.title}. "
                    "Check the chat panel on your screen for the payment link. "
                    "Click it to complete your donation with a card."
                )
                # Push visual payment card to frontend
                await _send_action_card(ctx, {
                    "type": "payment_link",
                    "url": checkout_url,
                    "amount": amount,
                    "currency": currency.upper(),
                    "campaign_title": campaign.title,
                    "campaign_id": campaign.id,
                    "donation_id": str(result.get("donation_id", "")),
                })
            else:
                response["instructions"] = result.get("instructions", "")
                # Push M-Pesa confirmation card
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
            return json.dumps(response)

        return json.dumps({"error": result.get("error", "Donation failed. Please try again.")})
    except Exception as e:
        logger.error(f"donate_to_campaign error: {e}", exc_info=True)
        return json.dumps({"error": f"Something went wrong: {str(e)}"})
    finally:
        db.close()


@function_tool(description=(
    "Check the user's donation history. Use when the user asks about "
    "their past donations, contribution history, or wants a summary "
    "of what they have donated."
))
async def check_my_donations(
    ctx: RunContext,
    limit: Annotated[int, "Maximum number of recent donations to return"] = 5,
) -> str:
    """Get the current user's donation history."""
    from database.models import User, Donor, Donation, Campaign

    userdata = ctx.userdata
    user_id = userdata.get("user_id")

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to view your donations."})

    db = _get_db()
    try:
        # Find user
        user = None
        try:
            uid = int(user_id)
            user = db.query(User).filter(User.id == uid).first()
        except (ValueError, TypeError):
            user = db.query(User).filter(User.telegram_user_id == str(user_id)).first()

        if not user:
            return json.dumps({"error": "User account not found."})

        # Find donor record
        donor = None
        if user.telegram_user_id:
            donor = db.query(Donor).filter(Donor.telegram_user_id == user.telegram_user_id).first()
        if not donor and user.phone_number:
            donor = db.query(Donor).filter(Donor.phone_number == user.phone_number).first()
        if not donor and user.email:
            donor = db.query(Donor).filter(Donor.email == user.email).first()

        if not donor:
            return json.dumps({"donations": [], "message": "No donation history found. You haven't made any donations yet."})

        donations = (
            db.query(Donation)
            .filter(Donation.donor_id == donor.id)
            .order_by(Donation.created_at.desc())
            .limit(limit)
            .all()
        )

        if not donations:
            return json.dumps({"donations": [], "message": "No donations found."})

        results = []
        total = 0.0
        for d in donations:
            campaign = db.query(Campaign).filter(Campaign.id == d.campaign_id).first()
            amt = float(d.amount or 0)
            total += amt
            results.append({
                "donation_id": d.id,
                "campaign": campaign.title if campaign else "Unknown",
                "amount_usd": round(amt, 2),
                "currency": d.currency or "USD",
                "status": d.status,
                "date": d.created_at.strftime("%Y-%m-%d") if d.created_at else "N/A",
                "payment_method": d.payment_method or "N/A",
            })

        return_data = {
            "donations": results,
            "total_donated_usd": round(total, 2),
            "count": len(results),
        }

        # Push donation history card to frontend
        await _send_action_card(ctx, {
            "type": "donation_history",
            "donations": results,
            "total_donated_usd": round(total, 2),
            "count": len(results),
        })

        return json.dumps(return_data)
    finally:
        db.close()


@function_tool(description=(
    "Submit milestone evidence for a campaign. Use when an NGO user "
    "or campaign owner reports that a milestone is completed and wants "
    "to submit evidence. Requires the milestone ID and description of "
    "completed work."
))
async def submit_milestone_evidence(
    ctx: RunContext,
    milestone_id: Annotated[int, "The milestone ID"],
    notes: Annotated[str, "Description of the completed work or evidence"],
) -> str:
    """Submit evidence that a milestone has been completed."""
    from voice.handlers.milestone_handler import submit_milestone_evidence as _submit

    userdata = ctx.userdata
    user_id = userdata.get("user_id")
    user_role = (userdata.get("role") or "").upper()

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to submit evidence."})

    if user_role not in ("SYSTEM_ADMIN", "SUPER_ADMIN", "NGO_ADMIN", "CAMPAIGN_CREATOR"):
        return json.dumps({"error": "Only NGO admins and campaign owners can submit milestone evidence."})

    db = _get_db()
    try:
        result = await _submit(
            milestone_id=milestone_id,
            notes=notes,
            ipfs_hashes=None,
            user_id=str(user_id),
            db=db,
        )
        return json.dumps(result)
    finally:
        db.close()


@function_tool(description=(
    "Verify a milestone as a field agent or admin. Use when a field "
    "agent or admin wants to confirm that a milestone has been "
    "completed after reviewing evidence. Requires milestone ID and "
    "a trust score from 0 to 100."
))
async def verify_milestone(
    ctx: RunContext,
    milestone_id: Annotated[int, "The milestone ID to verify"],
    trust_score: Annotated[int, "Verification trust score from 0 (failed) to 100 (fully verified)"],
    agent_notes: Annotated[str, "Notes about the verification"] = "",
) -> str:
    """Verify a milestone after reviewing evidence."""
    from voice.handlers.milestone_handler import verify_milestone as _verify

    userdata = ctx.userdata
    user_id = userdata.get("user_id")
    user_role = (userdata.get("role") or "").upper()

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to verify milestones."})

    if user_role not in ("SYSTEM_ADMIN", "SUPER_ADMIN", "FIELD_AGENT"):
        return json.dumps({"error": "Only field agents and admins can verify milestones."})

    db = _get_db()
    try:
        result = await _verify(
            milestone_id=milestone_id,
            trust_score=trust_score,
            agent_notes=agent_notes,
            user_id=str(user_id),
            db=db,
        )
        return json.dumps(result)
    finally:
        db.close()


@function_tool(description=(
    "Release funds for a verified milestone. Use when an admin wants "
    "to release the funds for a milestone that has been verified by "
    "a field agent. This transfers money to the NGO."
))
async def release_milestone_funds(
    ctx: RunContext,
    milestone_id: Annotated[int, "The milestone ID to release funds for"],
) -> str:
    """Release funds for a verified milestone."""
    from voice.handlers.milestone_handler import release_milestone_funds as _release

    userdata = ctx.userdata
    user_id = userdata.get("user_id")
    user_role = (userdata.get("role") or "").upper()

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to release funds."})

    if user_role not in ("SYSTEM_ADMIN", "SUPER_ADMIN"):
        return json.dumps({"error": "Only platform admins can release milestone funds."})

    db = _get_db()
    try:
        result = await _release(
            milestone_id=milestone_id,
            user_id=str(user_id),
            db=db,
        )
        return json.dumps(result)
    finally:
        db.close()


@function_tool(description=(
    "Approve a pending payout. Use when an admin wants to approve "
    "a payout that has been requested. Requires the payout ID."
))
async def approve_payout(
    ctx: RunContext,
    payout_id: Annotated[int, "The payout ID to approve"],
) -> str:
    """Approve a pending payout."""
    from database.models import User, Payout
    from datetime import datetime as dt

    userdata = ctx.userdata
    user_id = userdata.get("user_id")
    user_role = (userdata.get("role") or "").upper()

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to approve payouts."})

    if user_role not in ("SYSTEM_ADMIN", "SUPER_ADMIN", "NGO_ADMIN"):
        return json.dumps({"error": "Only admins can approve payouts."})

    db = _get_db()
    try:
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            return json.dumps({"error": f"Payout #{payout_id} not found."})
        if payout.status != "pending":
            return json.dumps({"error": f"Payout is already {payout.status}, cannot approve."})

        # NGO_ADMIN can only approve their own NGO's payouts
        if user_role == "NGO_ADMIN":
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user and payout.ngo_id != user.ngo_id:
                return json.dumps({"error": "You can only approve payouts for your own NGO."})

        payout.status = "approved"
        payout.approved_by = int(user_id)
        payout.approved_at = dt.utcnow()
        payout.status_message = f"Approved via voice by user {user_id}"
        db.commit()

        # Push payout status card
        await _send_action_card(ctx, {
            "type": "payout_status",
            "payout_id": payout.id,
            "amount": float(payout.amount),
            "currency": payout.currency,
            "status": "approved",
            "action": "approved",
        })

        return json.dumps({
            "success": True,
            "payout_id": payout.id,
            "amount": float(payout.amount),
            "currency": payout.currency,
            "status": "approved",
            "message": f"Payout #{payout.id} for {float(payout.amount)} {payout.currency} has been approved.",
        })
    except Exception as e:
        db.rollback()
        logger.error(f"approve_payout error: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@function_tool(description=(
    "Reject a pending payout. Use when an admin wants to reject "
    "a payout request. Requires the payout ID and a reason."
))
async def reject_payout(
    ctx: RunContext,
    payout_id: Annotated[int, "The payout ID to reject"],
    reason: Annotated[str, "Reason for rejecting the payout"],
) -> str:
    """Reject a pending payout."""
    from database.models import User, Payout
    from datetime import datetime as dt

    userdata = ctx.userdata
    user_id = userdata.get("user_id")
    user_role = (userdata.get("role") or "").upper()

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to reject payouts."})

    if user_role not in ("SYSTEM_ADMIN", "SUPER_ADMIN", "NGO_ADMIN"):
        return json.dumps({"error": "Only admins can reject payouts."})

    db = _get_db()
    try:
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            return json.dumps({"error": f"Payout #{payout_id} not found."})
        if payout.status != "pending":
            return json.dumps({"error": f"Payout is already {payout.status}, cannot reject."})

        payout.status = "rejected"
        payout.approved_by = int(user_id)
        payout.approved_at = dt.utcnow()
        payout.rejection_reason = reason
        payout.status_message = f"Rejected via voice: {reason}"
        db.commit()

        return json.dumps({
            "success": True,
            "payout_id": payout.id,
            "status": "rejected",
            "message": f"Payout #{payout.id} has been rejected. Reason: {reason}",
        })
    except Exception as e:
        db.rollback()
        logger.error(f"reject_payout error: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@function_tool(description=(
    "Create a new campaign. Use when an NGO user or admin wants to "
    "create a new fundraising campaign. Collect the title, description, "
    "category, goal amount, and optionally location from the user "
    "through conversation BEFORE calling this tool."
))
async def create_campaign(
    ctx: RunContext,
    title: Annotated[str, "Campaign title (3+ characters)"],
    description: Annotated[str, "Campaign description (10+ characters)"],
    category: Annotated[str, "Category: water, education, health, infrastructure, food, environment, shelter, children"],
    goal_amount_usd: Annotated[float, "Fundraising goal in USD"],
    location_country: Annotated[str | None, "Country name (e.g. 'Kenya', 'Tanzania')"] = None,
    location_region: Annotated[str | None, "Region or city (e.g. 'Kisumu', 'Mwanza')"] = None,
) -> str:
    """Create a new fundraising campaign."""
    from database.models import Campaign, User

    userdata = ctx.userdata
    user_id = userdata.get("user_id")
    user_role = (userdata.get("role") or "").upper()

    if not user_id or user_id == "web_anonymous":
        return json.dumps({"error": "You need to be signed in to create a campaign."})

    if user_role not in ("SYSTEM_ADMIN", "SUPER_ADMIN", "NGO_ADMIN", "CAMPAIGN_CREATOR"):
        return json.dumps({"error": "Only NGO admins and campaign creators can create campaigns."})

    db = _get_db()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return json.dumps({"error": "User not found."})

        ngo_id = user.ngo_id
        if not ngo_id and user_role in ("NGO_ADMIN", "CAMPAIGN_CREATOR"):
            return json.dumps({"error": "Your account is not linked to an NGO. Please complete NGO registration first."})

        from datetime import datetime as dt
        campaign = Campaign(
            title=title,
            description=description,
            category=category.lower(),
            goal_amount_usd=goal_amount_usd,
            location_country=location_country,
            location_region=location_region,
            ngo_id=ngo_id,
            creator_user_id=user.id if not ngo_id else None,
            status="active",
            created_at=dt.utcnow(),
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        # Push campaign created card to frontend
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

        return json.dumps({
            "success": True,
            "campaign_id": campaign.id,
            "title": campaign.title,
            "goal_usd": float(campaign.goal_amount_usd),
            "message": f"Campaign '{campaign.title}' created successfully with a goal of ${goal_amount_usd:,.0f}.",
        })
    except Exception as e:
        db.rollback()
        logger.error(f"create_campaign error: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
    finally:
        db.close()


# ── System prompt ───────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are the TrustVoice Assistant, a voice-first AI for a "
    "crowdfunding platform connecting donors with verified projects "
    "across Africa.\n\n"

    "PLATFORM MODEL: Projects raise funds through milestone-based "
    "releases. Donors fund a campaign, and money is released only "
    "after each milestone is verified by an independent field agent "
    "on the ground. A small platform fee (typically 6%) is deducted "
    "on each milestone release. This ensures transparency and "
    "accountability.\n\n"

    "YOUR CAPABILITIES:\n"
    "- READ: Search campaigns, get details, view milestones, check "
    "platform stats\n"
    "- DONATE: Initiate donations by voice (Stripe card or M-Pesa)\n"
    "- MANAGE: Submit milestone evidence, verify milestones, release "
    "funds, approve/reject payouts, create campaigns\n"
    "- HISTORY: Check user's donation history\n\n"

    "RULES:\n"
    "1. Be concise. Responses are spoken aloud. 1-3 short sentences "
    "unless listing items.\n"
    "2. Use tools for ALL data and actions. Never fabricate numbers.\n"
    "3. When listing campaigns, always include the campaign ID.\n"
    "4. If information is missing to complete an action, ASK the user. "
    "Do not guess amounts, campaigns, or payment methods.\n"
    "5. Be warm, professional, and encouraging.\n"
    "6. Summarize tool results naturally. Never read JSON aloud.\n"
    "7. Use plain language. Avoid jargon.\n"
    "8. Do not use em-dashes in your responses.\n\n"

    "CONFIRMATION PROTOCOL (critical for financial actions):\n"
    "- Before calling donate_to_campaign, ALWAYS read back the "
    "campaign name, amount, and currency. Ask 'Shall I proceed?' "
    "and wait for explicit confirmation (yes, confirm, go ahead).\n"
    "- Before calling approve_payout or reject_payout, read back "
    "the payout details and ask for confirmation.\n"
    "- Before calling release_milestone_funds, confirm which "
    "milestone and the amount to be released.\n"
    "- If the user says 'cancel', 'stop', 'no', or 'wait', do NOT "
    "proceed with the action.\n\n"

    "PAYMENT GUIDANCE:\n"
    "- For Stripe/card payments: tell the user a secure payment link "
    "will appear on their screen.\n"
    "- For M-Pesa: tell the user to check their phone for the "
    "payment prompt and enter their PIN.\n"
    "- If the user doesn't specify a payment method, the system "
    "auto-detects based on their profile.\n\n"

    "ROLE-BASED BEHAVIOR:\n"
    "- DONOR: Can search, view, donate, check donation history\n"
    "- NGO_ADMIN / CAMPAIGN_CREATOR: Above + create campaigns, "
    "submit milestone evidence\n"
    "- FIELD_AGENT: Can verify milestones\n"
    "- SYSTEM_ADMIN / SUPER_ADMIN: Full access to all actions "
    "including payout approvals and fund releases\n"
)

# ── Tool lists — read tools are available to all, write tools
#    are role-gated inside each function ─────────────────────────

READ_TOOLS = [
    search_campaigns,
    get_campaign_details,
    get_platform_stats,
    get_project_milestones,
    get_help,
]

WRITE_TOOLS = [
    donate_to_campaign,
    check_my_donations,
    submit_milestone_evidence,
    verify_milestone,
    release_milestone_funds,
    approve_payout,
    reject_payout,
    create_campaign,
]

ALL_TOOLS = READ_TOOLS + WRITE_TOOLS


# ── VBV Agent class ────────────────────────────────────────────

class VBVAssistant(Agent):
    """Voice-first assistant for the TrustVoice crowdfunding platform."""

    def __init__(self, user_name: str = "there", user_role: str = "DONOR"):
        role_upper = (user_role or "DONOR").upper()
        personalized_prompt = (
            SYSTEM_PROMPT
            + f"\nCURRENT USER: {user_name}  |  ROLE: {role_upper}\n"
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

    User metadata (set in JWT by livekit_router.py) is stored as
    session userdata so that tools can access user_id, role, etc.
    via RunContext.userdata.
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
    user_id = metadata.get("user_id", "web_anonymous")

    # Build userdata dict — passed to all tools via RunContext
    userdata = {
        "user_id": user_id,
        "name": user_name,
        "role": user_role,
    }

    # Create the session with audio pipeline components and userdata
    session = AgentSession(
        stt=deepgram.STT(model="nova-2", language="en-US"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.2),
        tts=openai.TTS(model="tts-1", voice="nova"),
        vad=silero.VAD.load(),
        userdata=userdata,
    )

    # Start the session with our agent + noise cancellation
    await session.start(
        agent=VBVAssistant(user_name=user_name, user_role=user_role),
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC() if noise_cancellation else None,
        ),
    )

    # Build role-aware greeting
    role_upper = (user_role or "").upper()
    if role_upper in ("SYSTEM_ADMIN", "SUPER_ADMIN"):
        capabilities = (
            "find campaigns, manage milestones, approve payouts, "
            "release funds, or check platform stats"
        )
    elif role_upper in ("NGO_ADMIN", "CAMPAIGN_CREATOR"):
        capabilities = (
            "manage your campaigns, submit milestone evidence, "
            "create new campaigns, or check platform stats"
        )
    elif role_upper == "FIELD_AGENT":
        capabilities = (
            "verify milestones, view campaign details, "
            "or check platform stats"
        )
    else:
        capabilities = (
            "find and donate to campaigns, check your donation history, "
            "view project milestones, or learn how TrustVoice works"
        )

    # Generate an initial greeting
    await session.generate_reply(
        instructions=(
            f"Greet the user whose name is {user_name}. "
            f"Tell them you are the TrustVoice assistant and you can help them "
            f"{capabilities}. Keep it warm and brief, 1-2 sentences."
        )
    )


# ── Worker entry point ──────────────────────────────────────────

if __name__ == "__main__":
    cli.run_app(server)
