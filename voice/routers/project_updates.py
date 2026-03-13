"""
Project Updates Endpoints
Allows project owners to post narrative updates visible to funders.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from database.db import get_db
from database.models import ProjectUpdate, Campaign, User
from voice.routers.admin import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/project-updates", tags=["Project Updates"])


class ProjectUpdateCreate(BaseModel):
    campaign_id: int
    title: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=10)
    media_ipfs_hashes: Optional[list] = None

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": 28,
                "title": "Moringa seedlings planted!",
                "body": "We planted 2,000 moringa seedlings across 3 hectares this week.",
                "media_ipfs_hashes": []
            }
        }


class ProjectUpdateResponse(BaseModel):
    id: int
    campaign_id: int
    posted_by: Optional[int] = None
    title: str
    body: str
    media_ipfs_hashes: Optional[list] = None
    created_at: datetime
    author_name: Optional[str] = None

    class Config:
        from_attributes = True


def enrich_update(update: ProjectUpdate, db: Session) -> dict:
    """Enrich update with author name."""
    data = {
        "id": update.id,
        "campaign_id": update.campaign_id,
        "posted_by": update.posted_by,
        "title": update.title,
        "body": update.body,
        "media_ipfs_hashes": update.media_ipfs_hashes or [],
        "created_at": update.created_at,
        "author_name": None,
    }
    if update.posted_by:
        user = db.query(User).filter(User.id == update.posted_by).first()
        if user:
            data["author_name"] = user.full_name or user.telegram_username or f"User #{user.id}"
    return data


@router.post("/", status_code=201)
async def create_project_update(
    payload: ProjectUpdateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Post a project update. Only campaign creator, NGO admin, or platform admin."""
    campaign = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Authorization
    is_authorized = False
    if campaign.creator_user_id == current_user.id:
        is_authorized = True
    if campaign.ngo_id and current_user.ngo_id == campaign.ngo_id:
        is_authorized = True
    if current_user.role in ("SYSTEM_ADMIN", "SUPER_ADMIN", "super_admin"):
        is_authorized = True
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Not authorized to post updates for this campaign")

    update = ProjectUpdate(
        campaign_id=payload.campaign_id,
        posted_by=current_user.id,
        title=payload.title,
        body=payload.body,
        media_ipfs_hashes=payload.media_ipfs_hashes or [],
    )
    db.add(update)
    db.commit()
    db.refresh(update)
    return enrich_update(update, db)


@router.get("/campaign/{campaign_id}")
async def list_project_updates(
    campaign_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all updates for a campaign, newest first. Public endpoint."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    updates = (
        db.query(ProjectUpdate)
        .filter(ProjectUpdate.campaign_id == campaign_id)
        .order_by(ProjectUpdate.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [enrich_update(u, db) for u in updates]


@router.delete("/{update_id}", status_code=204)
async def delete_project_update(
    update_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project update. Author or platform admin only."""
    update = db.query(ProjectUpdate).filter(ProjectUpdate.id == update_id).first()
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")

    if update.posted_by != current_user.id and current_user.role not in ("SYSTEM_ADMIN", "SUPER_ADMIN", "super_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(update)
    db.commit()
    return None
