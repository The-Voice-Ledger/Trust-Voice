"""
Milestones REST Router

CRUD endpoints for milestone-based crowdfunding.
These are used by the web frontend and admin dashboard.
The AI agent accesses the same business logic through its tool handlers.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db
from voice.handlers.milestone_handler import (
    create_milestones,
    get_milestones,
    submit_milestone_evidence,
    verify_milestone,
    release_milestone_funds,
    get_project_treasury,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/milestones", tags=["Milestones"])


# ── Request / Response schemas ─────────────────────────────────

class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    target_amount_usd: float = Field(..., gt=0)
    due_date: Optional[str] = None


class MilestonesCreateRequest(BaseModel):
    campaign_id: int
    milestones: List[MilestoneCreate] = Field(..., min_length=1)


class EvidenceSubmitRequest(BaseModel):
    milestone_id: int
    notes: str = Field(..., min_length=1)
    ipfs_hashes: Optional[List[str]] = None


class VerifyRequest(BaseModel):
    milestone_id: int
    trust_score: int = Field(..., ge=0, le=100)
    agent_notes: str = ""
    photos: Optional[List[str]] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None


class ReleaseRequest(BaseModel):
    milestone_id: int


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/create")
async def api_create_milestones(
    req: MilestonesCreateRequest,
    db: Session = Depends(get_db),
    # TODO: wire up real auth — for now pass user_id as header
):
    """Create milestones for a campaign."""
    # Placeholder user_id — in production, extract from JWT/session
    user_id = "system"
    result = await create_milestones(
        campaign_id=req.campaign_id,
        milestones_data=[m.model_dump() for m in req.milestones],
        user_id=user_id,
        db=db,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/campaign/{campaign_id}")
async def api_get_milestones(campaign_id: int, db: Session = Depends(get_db)):
    """Get all milestones for a campaign."""
    result = await get_milestones(campaign_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/evidence")
async def api_submit_evidence(
    req: EvidenceSubmitRequest,
    db: Session = Depends(get_db),
):
    """Submit evidence for a milestone."""
    user_id = "system"
    result = await submit_milestone_evidence(
        milestone_id=req.milestone_id,
        notes=req.notes,
        ipfs_hashes=req.ipfs_hashes,
        user_id=user_id,
        db=db,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/verify")
async def api_verify_milestone(
    req: VerifyRequest,
    db: Session = Depends(get_db),
):
    """Field agent verifies a milestone."""
    user_id = "system"
    result = await verify_milestone(
        milestone_id=req.milestone_id,
        trust_score=req.trust_score,
        agent_notes=req.agent_notes,
        user_id=user_id,
        db=db,
        photos=req.photos,
        gps_lat=req.gps_lat,
        gps_lng=req.gps_lng,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/release")
async def api_release_funds(
    req: ReleaseRequest,
    db: Session = Depends(get_db),
):
    """Release funds for a verified milestone."""
    user_id = "system"
    result = await release_milestone_funds(
        milestone_id=req.milestone_id,
        user_id=user_id,
        db=db,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/treasury/{campaign_id}")
async def api_get_treasury(campaign_id: int, db: Session = Depends(get_db)):
    """Get treasury overview for a campaign."""
    result = await get_project_treasury(campaign_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
