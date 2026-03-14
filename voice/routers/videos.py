"""
Video Transparency REST Router

Endpoints for the three-act video transparency framework:
  Act 1 — "Why We Need This"  (campaign launch video)
  Act 2 — "What We Are Doing" (progress updates)
  Act 3 — "What We Did"       (milestone closeout evidence)
  Verification — field agent independent video evidence

Supports upload, retrieval, timeline view, integrity verification,
and content flagging.
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from database.db import get_db
from database.models import (
    TransparencyVideo, VideoCategory, VideoStatus,
    Campaign, ProjectMilestone, User,
)
from voice.routers.admin import get_current_user
from services.video_service import video_service, ALLOWED_MIME_TYPES, MAX_VIDEO_SIZE_BYTES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Video Transparency"])

VALID_CATEGORIES = {c.value for c in VideoCategory}
VALID_PARENT_TYPES = {"campaign", "milestone"}
ADMIN_ROLES = {"SYSTEM_ADMIN", "super_admin"}


# ── Helpers ─────────────────────────────────────────────────────

def _check_parent_exists(parent_type: str, parent_id: int, db: Session):
    """Validate parent entity exists."""
    if parent_type == "campaign":
        obj = db.query(Campaign).filter(Campaign.id == parent_id).first()
        if not obj:
            raise HTTPException(404, "Campaign not found")
        return obj
    elif parent_type == "milestone":
        obj = db.query(ProjectMilestone).filter(ProjectMilestone.id == parent_id).first()
        if not obj:
            raise HTTPException(404, "Milestone not found")
        return obj
    raise HTTPException(400, f"Invalid parent_type: {parent_type}")


def _check_upload_permission(
    parent_type: str, parent, user: User, category: str, db: Session,
):
    """
    Verify user is authorized to upload.

    - Campaign creator or NGO admin can upload why/progress/completion
    - Field agents can upload verification videos
    - Super admins can upload anything
    """
    if user.role in ADMIN_ROLES:
        return

    if category == VideoCategory.VERIFICATION.value:
        if user.role != "FIELD_AGENT":
            raise HTTPException(403, "Only field agents can upload verification videos")
        return

    # For non-verification videos, must be campaign owner or NGO admin
    campaign = parent if parent_type == "campaign" else None
    if parent_type == "milestone":
        campaign = db.query(Campaign).filter(
            Campaign.id == parent.campaign_id
        ).first()

    if not campaign:
        raise HTTPException(404, "Associated campaign not found")

    is_owner = campaign.creator_user_id == user.id
    is_ngo_admin = (campaign.ngo_id and user.ngo_id == campaign.ngo_id)

    if not is_owner and not is_ngo_admin:
        raise HTTPException(
            403,
            "Only the campaign creator or NGO admin can upload this video",
        )


def _validate_gps(lat: Optional[float], lng: Optional[float]):
    """Validate GPS coordinates if provided."""
    if lat is None and lng is None:
        return
    if lat is None or lng is None:
        raise HTTPException(400, "Both gps_latitude and gps_longitude must be provided together")
    if not (-90 <= lat <= 90):
        raise HTTPException(400, f"Invalid latitude: {lat}")
    if not (-180 <= lng <= 180):
        raise HTTPException(400, f"Invalid longitude: {lng}")
    if lat == 0.0 and lng == 0.0:
        raise HTTPException(400, "GPS coordinates cannot be (0, 0)")


# ── Upload ──────────────────────────────────────────────────────

@router.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    category: str = Form(...),
    parent_type: str = Form(...),
    parent_id: int = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    pin_to_ipfs: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a transparency video.

    Form fields:
    - **video**: Video file (mp4, webm, mov — max 100MB)
    - **category**: `why` | `progress` | `completion` | `verification`
    - **parent_type**: `campaign` | `milestone`
    - **parent_id**: ID of the campaign or milestone
    - **title**: Optional title
    - **description**: Optional description
    - **gps_latitude/gps_longitude**: Optional GPS coordinates
    - **pin_to_ipfs**: Pin to IPFS via Pinata (default: false)
    """
    # Validate category & parent_type
    if category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Invalid category. Must be one of: {VALID_CATEGORIES}")
    if parent_type not in VALID_PARENT_TYPES:
        raise HTTPException(400, f"Invalid parent_type. Must be: {VALID_PARENT_TYPES}")

    # Validate MIME type
    content_type = video.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            400,
            f"Invalid video format: {content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    _validate_gps(gps_latitude, gps_longitude)

    # Validate parent exists and check permissions
    parent = _check_parent_exists(parent_type, parent_id, db)
    _check_upload_permission(parent_type, parent, current_user, category, db)

    # Store video file
    try:
        result = video_service.store_video(
            file=video.file,
            filename=video.filename or "video.mp4",
            category=category,
            parent_type=parent_type,
            parent_id=parent_id,
            pin_to_ipfs=pin_to_ipfs,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Create database record
    video_record = TransparencyVideo(
        uuid=result["uuid"],
        category=category,
        parent_type=parent_type,
        parent_id=parent_id,
        title=title,
        description=description,
        uploaded_by=current_user.id,
        storage_url=result["storage_url"],
        content_hash_sha256=result["sha256"],
        ipfs_cid=result.get("ipfs_cid"),
        file_size_bytes=result["file_size"],
        mime_type=content_type,
        status=VideoStatus.READY.value,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    logger.info(
        "Video uploaded: id=%d, category=%s, parent=%s:%d, by user=%d",
        video_record.id, category, parent_type, parent_id, current_user.id,
    )

    return {
        "success": True,
        "video": video_record.to_dict(),
        "message": f"Video uploaded successfully ({result['file_size'] / 1024 / 1024:.1f} MB)",
    }


# ── Retrieval ───────────────────────────────────────────────────

@router.get("/parent/{parent_type}/{parent_id}")
async def get_videos_for_parent(
    parent_type: str,
    parent_id: int,
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get all videos for a campaign or milestone.

    Optional filter by category (why, progress, completion, verification).
    """
    if parent_type not in VALID_PARENT_TYPES:
        raise HTTPException(400, f"Invalid parent_type: {parent_type}")

    q = db.query(TransparencyVideo).filter(
        and_(
            TransparencyVideo.parent_type == parent_type,
            TransparencyVideo.parent_id == parent_id,
            TransparencyVideo.status != VideoStatus.REJECTED.value,
        )
    )
    if category:
        if category not in VALID_CATEGORIES:
            raise HTTPException(400, f"Invalid category: {category}")
        q = q.filter(TransparencyVideo.category == category)

    videos = q.order_by(TransparencyVideo.created_at.asc()).all()
    return {
        "parent_type": parent_type,
        "parent_id": parent_id,
        "count": len(videos),
        "videos": [v.to_dict() for v in videos],
    }


@router.get("/campaign/{campaign_id}/timeline")
async def get_campaign_timeline(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the full transparency timeline for a campaign.

    Returns all videos (campaign-level + milestone-level) organized by act:
      - act_1_why: Campaign pitch videos
      - act_2_progress: Progress updates (campaign + milestone level)
      - act_3_completion: Closeout evidence
      - verifications: Field agent video evidence
      - milestones: { milestone_id: { info, videos[] } }
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    # Fetch ALL videos for this campaign (direct + via milestones)
    campaign_videos = db.query(TransparencyVideo).filter(
        and_(
            TransparencyVideo.parent_type == "campaign",
            TransparencyVideo.parent_id == campaign_id,
            TransparencyVideo.status != VideoStatus.REJECTED.value,
        )
    ).order_by(TransparencyVideo.created_at.asc()).all()

    # Fetch milestones for this campaign
    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.campaign_id == campaign_id
    ).order_by(ProjectMilestone.sequence).all()

    milestone_ids = [m.id for m in milestones]

    milestone_videos = []
    if milestone_ids:
        milestone_videos = db.query(TransparencyVideo).filter(
            and_(
                TransparencyVideo.parent_type == "milestone",
                TransparencyVideo.parent_id.in_(milestone_ids),
                TransparencyVideo.status != VideoStatus.REJECTED.value,
            )
        ).order_by(TransparencyVideo.created_at.asc()).all()

    # Organize by act
    act_1 = [v.to_dict() for v in campaign_videos if v.category == "why"]
    act_2 = [v.to_dict() for v in campaign_videos if v.category == "progress"]
    act_3 = [v.to_dict() for v in campaign_videos if v.category == "completion"]
    verifications = [v.to_dict() for v in campaign_videos if v.category == "verification"]

    # Milestone-level videos grouped by milestone
    milestone_data = {}
    for m in milestones:
        m_videos = [v.to_dict() for v in milestone_videos if v.parent_id == m.id]
        milestone_data[m.id] = {
            "milestone_id": m.id,
            "title": m.title,
            "sequence": m.sequence,
            "status": m.status,
            "target_amount_usd": float(m.target_amount_usd) if m.target_amount_usd else 0,
            "videos": m_videos,
            "progress_videos": [v for v in m_videos if v["category"] == "progress"],
            "completion_videos": [v for v in m_videos if v["category"] == "completion"],
            "verification_videos": [v for v in m_videos if v["category"] == "verification"],
        }

    # Also add milestone progress/completion/verification to the top-level feeds
    for v in milestone_videos:
        d = v.to_dict()
        if v.category == "progress":
            act_2.append(d)
        elif v.category == "completion":
            act_3.append(d)
        elif v.category == "verification":
            verifications.append(d)

    # Sort combined feeds by date
    act_2.sort(key=lambda x: x["created_at"] or "")
    act_3.sort(key=lambda x: x["created_at"] or "")
    verifications.sort(key=lambda x: x["created_at"] or "")

    total_videos = len(campaign_videos) + len(milestone_videos)

    return {
        "campaign_id": campaign_id,
        "campaign_title": campaign.title,
        "total_videos": total_videos,
        "act_1_why": act_1,
        "act_2_progress": act_2,
        "act_3_completion": act_3,
        "verifications": verifications,
        "milestones": milestone_data,
    }


@router.get("/{video_id}")
async def get_video(
    video_id: int,
    db: Session = Depends(get_db),
):
    """Get a single video by ID, incrementing view count."""
    video = db.query(TransparencyVideo).filter(
        TransparencyVideo.id == video_id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")

    # Increment view count
    video.view_count = (video.view_count or 0) + 1
    db.commit()

    return video.to_dict()


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: Session = Depends(get_db),
):
    """Stream video file directly."""
    video = db.query(TransparencyVideo).filter(
        TransparencyVideo.id == video_id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")

    filepath = video_service.get_video_path(video.storage_url)
    if not filepath:
        raise HTTPException(404, "Video file not found on disk")

    return FileResponse(
        str(filepath),
        media_type=video.mime_type or "video/mp4",
        filename=f"{video.uuid}.mp4",
    )


# ── Integrity ───────────────────────────────────────────────────

@router.get("/{video_id}/verify")
async def verify_video_integrity(
    video_id: int,
    db: Session = Depends(get_db),
):
    """
    Verify video integrity using SHA-256 hash.

    Returns whether the stored file matches its recorded hash.
    Used by donors, auditors, and automated checks.
    """
    video = db.query(TransparencyVideo).filter(
        TransparencyVideo.id == video_id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")

    if not video.content_hash_sha256:
        return {
            "video_id": video_id,
            "verified": False,
            "reason": "No content hash recorded",
        }

    is_valid = video_service.verify_integrity(
        video.storage_url, video.content_hash_sha256
    )

    return {
        "video_id": video_id,
        "verified": is_valid,
        "content_hash_sha256": video.content_hash_sha256,
        "ipfs_cid": video.ipfs_cid,
    }


# ── Moderation ──────────────────────────────────────────────────

@router.post("/{video_id}/flag")
async def flag_video(
    video_id: int,
    reason: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Flag a video for review (any authenticated user can flag)."""
    video = db.query(TransparencyVideo).filter(
        TransparencyVideo.id == video_id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")

    video.status = VideoStatus.FLAGGED.value
    video.flag_reason = reason
    video.flagged_by = current_user.id
    video.updated_at = datetime.utcnow()
    db.commit()

    logger.warning(
        "Video %d flagged by user %d: %s", video_id, current_user.id, reason
    )
    return {"success": True, "message": "Video flagged for review"}


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a video. Only the uploader or an admin can delete.
    """
    video = db.query(TransparencyVideo).filter(
        TransparencyVideo.id == video_id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")

    is_uploader = video.uploaded_by == current_user.id
    is_admin = current_user.role in ADMIN_ROLES

    if not is_uploader and not is_admin:
        raise HTTPException(403, "Only the uploader or an admin can delete this video")

    # Delete file from disk
    video_service.delete_video(video.storage_url)

    # Remove DB record
    db.delete(video)
    db.commit()

    logger.info("Video %d deleted by user %d", video_id, current_user.id)
    return {"success": True, "message": "Video deleted"}
