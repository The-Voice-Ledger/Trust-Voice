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
from fastapi.responses import FileResponse, RedirectResponse
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

# Max durations per category (seconds)
MAX_DURATION_BY_CATEGORY = {
    "progress": 300,      # 5 minutes
    "verification": 300,  # 5 minutes
    "why": 600,           # 10 minutes
    "completion": 600,    # 10 minutes
}


# ── Helpers ─────────────────────────────────────────────────────

def _check_parent_exists(parent_type: str, parent_id: int, db: Session):
    """Validate parent entity exists. Returns (parent, campaign)."""
    if parent_type == "campaign":
        obj = db.query(Campaign).filter(Campaign.id == parent_id).first()
        if not obj:
            raise HTTPException(404, "Campaign not found")
        return obj, obj
    elif parent_type == "milestone":
        obj = db.query(ProjectMilestone).filter(ProjectMilestone.id == parent_id).first()
        if not obj:
            raise HTTPException(404, "Milestone not found")
        campaign = db.query(Campaign).filter(Campaign.id == obj.campaign_id).first()
        return obj, campaign
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
    duration_seconds: Optional[int] = Form(None),
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
    - **title**: Optional title (auto-generated from date + category if blank)
    - **description**: Optional description
    - **gps_latitude/gps_longitude**: Optional GPS coordinates
    - **duration_seconds**: Client-measured video duration
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

    # Server-side duration enforcement
    max_dur = MAX_DURATION_BY_CATEGORY.get(category)
    if max_dur and duration_seconds is not None and duration_seconds > max_dur:
        raise HTTPException(
            400,
            f"{category.title()} videos must be under {max_dur // 60} minutes "
            f"(yours is {duration_seconds // 60}:{duration_seconds % 60:02d})",
        )

    _validate_gps(gps_latitude, gps_longitude)

    # Validate parent exists and check permissions
    parent, campaign = _check_parent_exists(parent_type, parent_id, db)
    _check_upload_permission(parent_type, parent, current_user, category, db)

    # GPS proximity check against campaign location
    gps_proximity = None
    if gps_latitude is not None and gps_longitude is not None and campaign:
        project_gps = getattr(campaign, 'location_gps', None)
        gps_proximity = video_service.check_gps_proximity(
            gps_latitude, gps_longitude, project_gps,
        )
        if gps_proximity.get("within_range") is False:
            logger.warning(
                "GPS proximity warning: video at (%.4f,%.4f) is %.1f km from project — user %d",
                gps_latitude, gps_longitude,
                gps_proximity.get("distance_km", 0),
                current_user.id,
            )
            # Don't block, but attach warning to metadata

    # Auto-generate title if user left it blank
    if not title:
        parent_title = getattr(parent, 'title', None)
        title = video_service.auto_generate_title(category, parent_type, parent_title)

    # Store video file
    try:
        result = video_service.store_video(
            file=video.file,
            filename=video.filename or "video.mp4",
            category=category,
            parent_type=parent_type,
            parent_id=parent_id,
            pin_to_ipfs=pin_to_ipfs,
            duration_seconds=duration_seconds,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Build metadata JSON with GPS proximity result
    metadata = {}
    if gps_proximity:
        metadata["gps_proximity"] = gps_proximity

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
        duration_seconds=duration_seconds,
        metadata_json=metadata if metadata else None,
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    logger.info(
        "Video uploaded: id=%d, category=%s, parent=%s:%d, by user=%d, duration=%s",
        video_record.id, category, parent_type, parent_id, current_user.id,
        f"{duration_seconds}s" if duration_seconds else "unknown",
    )

    response = {
        "success": True,
        "video": video_record.to_dict(),
        "message": f"Video uploaded successfully ({result['file_size'] / 1024 / 1024:.1f} MB)",
    }
    # Include GPS proximity warning for the uploader
    if gps_proximity and gps_proximity.get("within_range") is False:
        response["gps_warning"] = (
            f"Video GPS is {gps_proximity['distance_km']} km from the project site "
            f"(threshold: {gps_proximity['threshold_km']} km)"
        )

    return response


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
    """Stream video file directly (local) or redirect to R2 URL."""
    video = db.query(TransparencyVideo).filter(
        TransparencyVideo.id == video_id
    ).first()
    if not video:
        raise HTTPException(404, "Video not found")

    # If storage_url is a full URL (R2), redirect to it
    if video.storage_url.startswith("http"):
        return RedirectResponse(url=video.storage_url)

    # Otherwise, serve from local disk
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
