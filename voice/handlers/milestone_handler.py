"""
Milestone Handler — business logic for milestone-based crowdfunding.

Covers:
- Creating milestones on a campaign
- Submitting evidence for a milestone
- Verifying a milestone (field agent)
- Releasing funds after verification
- Querying milestone status / treasury overview
"""

import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from database.models import (
    Campaign, User, ProjectMilestone, MilestoneVerification,
    MilestoneStatus, PlatformFee, ProjectUpdate,
)

logger = logging.getLogger(__name__)

PLATFORM_DEFAULT_FEE = Decimal("0.0600")  # 6 %


# ── Helpers ─────────────────────────────────────────────────────

def _resolve_user(user_id: str, db: Session) -> Optional[User]:
    """Resolve a user from UUID string or telegram_user_id."""
    try:
        uid = uuid.UUID(user_id)
        return db.query(User).filter(User.id == uid).first()
    except (ValueError, AttributeError):
        return db.query(User).filter(
            User.telegram_user_id == str(user_id)
        ).first()


def _owns_campaign(user: User, campaign: Campaign, db: Session) -> bool:
    """Check if user is the campaign owner (direct or via NGO)."""
    if campaign.creator_user_id and campaign.creator_user_id == user.id:
        return True
    if campaign.ngo_id:
        from database.models import NGOOrganization
        ngo = db.query(NGOOrganization).filter(
            NGOOrganization.id == campaign.ngo_id,
            NGOOrganization.admin_user_id == user.id,
        ).first()
        return ngo is not None
    return False


# ── Create milestones ──────────────────────────────────────────

async def create_milestones(
    campaign_id: int,
    milestones_data: List[Dict[str, Any]],
    user_id: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Create milestones for a campaign.

    milestones_data: [
        {"title": "Land Preparation", "description": "...", "target_amount": 2000},
        {"title": "Seedling Purchase", "description": "...", "target_amount": 3500},
    ]
    """
    user = _resolve_user(user_id, db)
    if not user:
        return {"error": "User not found. Please register first."}

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found."}

    if not _owns_campaign(user, campaign, db) and user.role not in (
        "SYSTEM_ADMIN", "super_admin"
    ):
        return {"error": "Only the campaign owner can create milestones."}

    # Check no milestones already exist
    existing = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.campaign_id == campaign_id)
        .count()
    )
    if existing > 0:
        return {"error": "Milestones already exist for this campaign. Delete them first."}

    created: List[Dict] = []
    total_target = Decimal("0")
    for idx, m in enumerate(milestones_data, start=1):
        target = Decimal(str(m["target_amount"]))
        total_target += target
        ms = ProjectMilestone(
            campaign_id=campaign_id,
            title=m["title"],
            description=m.get("description", ""),
            sequence=idx,
            target_amount_usd=target,
            status=MilestoneStatus.PENDING.value,
            due_date=m.get("due_date"),
        )
        db.add(ms)
        db.flush()  # get ID
        created.append({
            "id": ms.id,
            "sequence": idx,
            "title": ms.title,
            "target_amount_usd": float(target),
        })

    # Mark campaign as milestone-gated
    campaign.use_milestones = True
    if campaign.platform_fee_rate is None:
        campaign.platform_fee_rate = PLATFORM_DEFAULT_FEE
    db.commit()

    logger.info(
        f"Created {len(created)} milestones for campaign {campaign_id}, "
        f"total target ${total_target}"
    )

    return {
        "success": True,
        "campaign_id": campaign_id,
        "milestones": created,
        "total_target_usd": float(total_target),
    }


# ── Get milestones ─────────────────────────────────────────────

async def get_milestones(
    campaign_id: int, db: Session
) -> Dict[str, Any]:
    """Return all milestones for a campaign with progress info."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found."}

    milestones = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.campaign_id == campaign_id)
        .order_by(ProjectMilestone.sequence)
        .all()
    )

    if not milestones:
        return {
            "campaign_id": campaign_id,
            "campaign_title": campaign.title,
            "use_milestones": bool(campaign.use_milestones),
            "milestones": [],
            "message": "This campaign does not have milestones yet.",
        }

    items = []
    total_target = Decimal("0")
    total_released = Decimal("0")
    for m in milestones:
        target = m.target_amount_usd or Decimal("0")
        released = m.released_amount_usd or Decimal("0")
        total_target += target
        total_released += released
        items.append({
            "id": m.id,
            "sequence": m.sequence,
            "title": m.title,
            "description": (m.description or "")[:200],
            "target_amount_usd": float(target),
            "released_amount_usd": float(released),
            "status": m.status,
            "due_date": str(m.due_date) if m.due_date else None,
        })

    return {
        "campaign_id": campaign_id,
        "campaign_title": campaign.title,
        "milestones": items,
        "total_target_usd": float(total_target),
        "total_released_usd": float(total_released),
        "progress_pct": int(
            (float(total_released) / max(float(total_target), 1)) * 100
        ),
    }


# ── Submit evidence ────────────────────────────────────────────

async def submit_milestone_evidence(
    milestone_id: int,
    notes: str,
    ipfs_hashes: Optional[List[str]],
    user_id: str,
    db: Session,
) -> Dict[str, Any]:
    """Project owner submits evidence that a milestone is complete."""
    user = _resolve_user(user_id, db)
    if not user:
        return {"error": "User not found."}

    milestone = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.id == milestone_id)
        .first()
    )
    if not milestone:
        return {"error": f"Milestone {milestone_id} not found."}

    campaign = db.query(Campaign).filter(
        Campaign.id == milestone.campaign_id
    ).first()

    if not _owns_campaign(user, campaign, db) and user.role not in (
        "SYSTEM_ADMIN", "super_admin"
    ):
        return {"error": "Only the campaign owner can submit evidence."}

    if milestone.status not in (
        MilestoneStatus.PENDING.value,
        MilestoneStatus.ACTIVE.value,
        MilestoneStatus.FAILED.value,  # allow re-submission after failure
    ):
        return {
            "error": (
                f"Cannot submit evidence — milestone is '{milestone.status}'."
            )
        }

    milestone.evidence_notes = notes
    milestone.evidence_ipfs_hashes = ipfs_hashes or []
    milestone.evidence_submitted_at = datetime.utcnow()
    milestone.status = MilestoneStatus.EVIDENCE_SUBMITTED.value
    db.commit()

    logger.info(
        f"Evidence submitted for milestone {milestone_id} "
        f"(campaign {milestone.campaign_id})"
    )

    return {
        "success": True,
        "milestone_id": milestone_id,
        "status": milestone.status,
        "message": (
            f"Evidence submitted for milestone '{milestone.title}'. "
            "A field agent will be assigned to verify."
        ),
    }


# ── Verify milestone (field agent) ────────────────────────────

async def verify_milestone(
    milestone_id: int,
    trust_score: int,
    agent_notes: str,
    user_id: str,
    db: Session,
    photos: Optional[List[str]] = None,
    gps_lat: Optional[float] = None,
    gps_lng: Optional[float] = None,
) -> Dict[str, Any]:
    """Field agent verifies a milestone on the ground."""
    user = _resolve_user(user_id, db)
    if not user:
        return {"error": "User not found."}

    if user.role not in ("FIELD_AGENT", "SYSTEM_ADMIN", "super_admin"):
        return {"error": "Only field agents can verify milestones."}

    milestone = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.id == milestone_id)
        .first()
    )
    if not milestone:
        return {"error": f"Milestone {milestone_id} not found."}

    if milestone.status != MilestoneStatus.EVIDENCE_SUBMITTED.value:
        return {
            "error": (
                f"Cannot verify — milestone status is '{milestone.status}'. "
                "Evidence must be submitted first."
            )
        }

    trust_score = max(0, min(100, trust_score))

    # Create verification record
    verification = MilestoneVerification(
        milestone_id=milestone_id,
        field_agent_id=user.id,
        agent_notes=agent_notes,
        photos=photos or [],
        gps_latitude=gps_lat,
        gps_longitude=gps_lng,
        trust_score=trust_score,
        status="approved" if trust_score >= 80 else "pending",
        agent_payout_amount_usd=Decimal("30.00"),
        agent_payout_status="initiated" if trust_score >= 80 else None,
    )
    db.add(verification)

    # Auto-approve if trust score >= 80
    if trust_score >= 80:
        milestone.status = MilestoneStatus.VERIFIED.value
        message = (
            f"Milestone '{milestone.title}' verified with trust score "
            f"{trust_score}/100. Funds are ready for release."
        )
    else:
        milestone.status = MilestoneStatus.UNDER_REVIEW.value
        message = (
            f"Milestone '{milestone.title}' submitted for admin review "
            f"(trust score {trust_score}/100)."
        )

    db.commit()

    logger.info(
        f"Milestone {milestone_id} verified by agent {user.id}, "
        f"score={trust_score}, status={milestone.status}"
    )

    return {
        "success": True,
        "milestone_id": milestone_id,
        "trust_score": trust_score,
        "status": milestone.status,
        "auto_approved": trust_score >= 80,
        "message": message,
    }


# ── Release funds ──────────────────────────────────────────────

async def release_milestone_funds(
    milestone_id: int,
    user_id: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Release funds for a verified milestone.

    Deducts platform fee, records PlatformFee ledger entry, and marks
    milestone as released.  Actual money movement (Stripe/M-Pesa/bank)
    is handled by the existing payout system.
    """
    user = _resolve_user(user_id, db)
    if not user:
        return {"error": "User not found."}

    # Only admins and campaign owners can trigger release
    milestone = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.id == milestone_id)
        .first()
    )
    if not milestone:
        return {"error": f"Milestone {milestone_id} not found."}

    if milestone.status != MilestoneStatus.VERIFIED.value:
        return {
            "error": (
                f"Cannot release — milestone status is '{milestone.status}'. "
                "Must be verified first."
            )
        }

    campaign = db.query(Campaign).filter(
        Campaign.id == milestone.campaign_id
    ).first()

    is_owner = _owns_campaign(user, campaign, db)
    is_admin = user.role in ("SYSTEM_ADMIN", "super_admin")
    if not (is_owner or is_admin):
        return {"error": "Only the campaign owner or admin can release funds."}

    # Calculate fee
    fee_rate = campaign.platform_fee_rate or PLATFORM_DEFAULT_FEE
    gross = milestone.target_amount_usd
    fee = (gross * fee_rate).quantize(Decimal("0.01"))
    net = gross - fee

    # Record fee
    fee_record = PlatformFee(
        milestone_id=milestone.id,
        campaign_id=campaign.id,
        gross_amount_usd=gross,
        fee_rate=fee_rate,
        fee_amount_usd=fee,
        net_to_project_usd=net,
    )
    db.add(fee_record)

    # Update milestone
    milestone.released_amount_usd = net
    milestone.platform_fee_usd = fee
    milestone.status = MilestoneStatus.RELEASED.value
    milestone.released_at = datetime.utcnow()
    db.commit()

    logger.info(
        f"Milestone {milestone_id} released: gross=${gross}, "
        f"fee=${fee} ({float(fee_rate)*100:.1f}%), net=${net}"
    )

    return {
        "success": True,
        "milestone_id": milestone_id,
        "milestone_title": milestone.title,
        "gross_amount_usd": float(gross),
        "fee_rate_pct": float(fee_rate) * 100,
        "fee_amount_usd": float(fee),
        "net_to_project_usd": float(net),
        "status": "released",
        "message": (
            f"${net:.2f} released to project (${fee:.2f} platform fee at "
            f"{float(fee_rate)*100:.1f}%)."
        ),
    }


# ── Treasury overview ──────────────────────────────────────────

async def get_project_treasury(
    campaign_id: int, db: Session
) -> Dict[str, Any]:
    """
    Aggregated treasury view for a campaign: raised, allocated,
    released, held, fees collected.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return {"error": f"Campaign {campaign_id} not found."}

    milestones = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.campaign_id == campaign_id)
        .order_by(ProjectMilestone.sequence)
        .all()
    )

    total_raised = float(campaign.raised_amount_usd or 0)
    total_target = sum(float(m.target_amount_usd or 0) for m in milestones)
    total_released = sum(float(m.released_amount_usd or 0) for m in milestones)
    total_fees = sum(float(m.platform_fee_usd or 0) for m in milestones)
    held = total_raised - total_released - total_fees

    milestones_summary = []
    for m in milestones:
        milestones_summary.append({
            "sequence": m.sequence,
            "title": m.title,
            "target_usd": float(m.target_amount_usd or 0),
            "released_usd": float(m.released_amount_usd or 0),
            "status": m.status,
        })

    return {
        "campaign_id": campaign_id,
        "campaign_title": campaign.title,
        "total_raised_usd": total_raised,
        "total_milestone_target_usd": total_target,
        "total_released_usd": total_released,
        "total_fees_collected_usd": total_fees,
        "funds_held_usd": max(held, 0),
        "milestones": milestones_summary,
    }
