"""
Field Agent API Router

Provides REST API endpoints for field agents to:
- Upload verification photos
- Submit impact reports with GPS/photos
- View pending campaigns
- Track verification history and earnings

Supports three frontend interfaces:
- Telegram bot (photo message handlers)
- Telegram mini app (camera integration)
- Web UI (desktop interface)
"""

import os
import logging
import uuid
import tempfile
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.db import get_db
from database.models import User, Campaign, ImpactVerification
from voice.handlers.impact_handler import process_impact_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-agent", tags=["field-agent"])


# ============================================
# Pydantic Models
# ============================================

class PhotoUploadResponse(BaseModel):
    """Response after uploading a photo"""
    success: bool
    photo_id: str
    file_size: int
    message: Optional[str] = None


class VerificationSessionData(BaseModel):
    """Current verification session state"""
    campaign_id: Optional[str] = None
    photo_ids: List[str] = []
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    description: Optional[str] = None
    beneficiary_count: Optional[int] = None


class VerificationSubmitRequest(BaseModel):
    """Request to submit a complete verification"""
    telegram_user_id: str
    campaign_id: str
    description: str
    photo_ids: List[str] = []
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    beneficiary_count: Optional[int] = None
    testimonials: Optional[str] = None


class VerificationSubmitResponse(BaseModel):
    """Response after verification submission"""
    success: bool
    verification_id: Optional[str] = None
    trust_score: Optional[int] = None
    status: Optional[str] = None
    auto_approved: Optional[bool] = None
    payout: Optional[dict] = None
    error: Optional[str] = None


class PendingCampaign(BaseModel):
    """Campaign pending field verification"""
    id: str
    title: str
    description: str
    ngo_name: str
    target_amount_usd: float
    current_amount_usd: float
    gps_latitude: Optional[float]
    gps_longitude: Optional[float]
    status: str
    created_at: str


class VerificationHistory(BaseModel):
    """Field agent verification history item"""
    id: str
    campaign_id: str
    campaign_title: str
    verification_date: str
    trust_score: int
    status: str
    agent_payout_amount_usd: Optional[float]
    agent_payout_status: Optional[str]
    photos_count: int


# ============================================
# Session Management
# ============================================

from redis import Redis
import json

# Redis connection (reuse from voice pipeline)
try:
    from voice.pipeline import redis_client
except ImportError:
    redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)


class VerificationSession:
    """Manages multi-step verification session state in Redis"""
    
    def __init__(self, telegram_user_id: str):
        self.telegram_user_id = telegram_user_id
        self.key = f"verification:{telegram_user_id}"
    
    def set(self, data: dict):
        """Store session data (expires in 1 hour)"""
        try:
            redis_client.setex(self.key, 3600, json.dumps(data))
            logger.info(f"Verification session saved for user {self.telegram_user_id}")
        except Exception as e:
            logger.error(f"Failed to save verification session: {e}")
    
    def get(self) -> Optional[dict]:
        """Retrieve session data"""
        try:
            data = redis_client.get(self.key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get verification session: {e}")
            return None
    
    def update(self, updates: dict):
        """Update specific fields in session"""
        data = self.get() or {}
        data.update(updates)
        self.set(data)
    
    def delete(self):
        """Delete session after submission"""
        try:
            redis_client.delete(self.key)
            logger.info(f"Verification session deleted for user {self.telegram_user_id}")
        except Exception as e:
            logger.error(f"Failed to delete verification session: {e}")
    
    def exists(self) -> bool:
        """Check if session exists"""
        try:
            return redis_client.exists(self.key) > 0
        except Exception as e:
            logger.error(f"Failed to check verification session: {e}")
            return False


# ============================================
# Photo Storage (Telegram file_id based)
# ============================================

class PhotoStorage:
    """Manages photo storage using Telegram file_ids"""
    
    @staticmethod
    def save_photo_metadata(telegram_user_id: str, file_id: str, file_size: int) -> str:
        """
        Store photo metadata in Redis with unique ID.
        Returns photo_id for later retrieval.
        """
        photo_id = str(uuid.uuid4())
        key = f"photo:{photo_id}"
        
        metadata = {
            "telegram_user_id": telegram_user_id,
            "file_id": file_id,
            "file_size": file_size,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Store for 24 hours (enough for verification submission)
            redis_client.setex(key, 86400, json.dumps(metadata))
            logger.info(f"Photo metadata saved: {photo_id}")
            return photo_id
        except Exception as e:
            logger.error(f"Failed to save photo metadata: {e}")
            raise
    
    @staticmethod
    def get_photo_file_id(photo_id: str) -> Optional[str]:
        """Retrieve Telegram file_id from photo_id"""
        key = f"photo:{photo_id}"
        try:
            data = redis_client.get(key)
            if data:
                metadata = json.loads(data)
                return metadata.get("file_id")
            return None
        except Exception as e:
            logger.error(f"Failed to get photo file_id: {e}")
            return None
    
    @staticmethod
    def get_photo_file_ids(photo_ids: List[str]) -> List[str]:
        """Convert list of photo_ids to Telegram file_ids"""
        file_ids = []
        for photo_id in photo_ids:
            file_id = PhotoStorage.get_photo_file_id(photo_id)
            if file_id:
                file_ids.append(file_id)
        return file_ids


# ============================================
# API Endpoints
# ============================================

@router.post("/photos/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    telegram_user_id: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a verification photo.
    
    For Telegram bot: Send file_id directly (no actual upload needed)
    For mini app/web: Upload actual image file
    
    Returns photo_id for later use in verification submission.
    """
    try:
        # Verify user exists and is a field agent
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.role != "FIELD_AGENT":
            raise HTTPException(
                status_code=403,
                detail=f"Only field agents can upload photos. Your role: {user.role}"
            )
        
        # Read file content
        content = await photo.read()
        file_size = len(content)
        
        # For now, store as Telegram file_id pattern (will be replaced with actual file_id from bot)
        # For mini app/web uploads, we'll generate a temporary file_id
        file_id = f"web_upload_{uuid.uuid4()}"
        
        # TODO: If this is from mini app/web, upload to Telegram or S3/R2 storage
        # For MVP, we'll just use a placeholder file_id
        
        # Save metadata and get photo_id
        photo_id = PhotoStorage.save_photo_metadata(
            telegram_user_id=telegram_user_id,
            file_id=file_id,
            file_size=file_size
        )
        
        # Update verification session
        session = VerificationSession(telegram_user_id)
        session_data = session.get() or {}
        photo_ids = session_data.get("photo_ids", [])
        photo_ids.append(photo_id)
        session.update({"photo_ids": photo_ids})
        
        logger.info(f"Photo uploaded: {photo_id} ({file_size} bytes) for user {telegram_user_id}")
        
        return PhotoUploadResponse(
            success=True,
            photo_id=photo_id,
            file_size=file_size,
            message=f"Photo {len(photo_ids)} uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


@router.post("/photos/telegram", response_model=PhotoUploadResponse)
async def upload_telegram_photo(
    telegram_user_id: str = Form(...),
    file_id: str = Form(...),
    file_size: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Register a Telegram photo for verification.
    
    This endpoint is used by the Telegram bot to register photos
    without actually uploading the file (Telegram stores the file).
    """
    try:
        # Verify user exists and is a field agent
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.role != "FIELD_AGENT":
            raise HTTPException(
                status_code=403,
                detail=f"Only field agents can upload photos. Your role: {user.role}"
            )
        
        # Save metadata using Telegram file_id
        photo_id = PhotoStorage.save_photo_metadata(
            telegram_user_id=telegram_user_id,
            file_id=file_id,
            file_size=file_size
        )
        
        # Update verification session
        session = VerificationSession(telegram_user_id)
        session_data = session.get() or {}
        photo_ids = session_data.get("photo_ids", [])
        photo_ids.append(photo_id)
        session.update({"photo_ids": photo_ids})
        
        logger.info(f"Telegram photo registered: {photo_id} (file_id: {file_id}) for user {telegram_user_id}")
        
        return PhotoUploadResponse(
            success=True,
            photo_id=photo_id,
            file_size=file_size,
            message=f"Photo {len(photo_ids)} registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering Telegram photo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register photo: {str(e)}")


@router.post("/verifications/submit", response_model=VerificationSubmitResponse)
async def submit_verification(
    request: VerificationSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a complete impact verification report.
    
    Converts photo_ids to Telegram file_ids and calls impact_handler.
    """
    try:
        # Verify user exists
        user = db.query(User).filter(
            User.telegram_user_id == request.telegram_user_id
        ).first()
        
        if not user:
            return VerificationSubmitResponse(
                success=False,
                error="User not found. Please register first with /start"
            )
        
        # Convert photo_ids to Telegram file_ids
        photo_urls = PhotoStorage.get_photo_file_ids(request.photo_ids)
        
        # Parse campaign_id
        try:
            campaign_uuid = uuid.UUID(request.campaign_id)
        except ValueError:
            return VerificationSubmitResponse(
                success=False,
                error=f"Invalid campaign ID format: {request.campaign_id}"
            )
        
        # Process verification through existing handler
        result = await process_impact_report(
            db=db,
            telegram_user_id=request.telegram_user_id,
            campaign_id=campaign_uuid,
            description=request.description,
            photo_urls=photo_urls,
            gps_latitude=request.gps_latitude,
            gps_longitude=request.gps_longitude,
            beneficiary_count=request.beneficiary_count,
            testimonials=request.testimonials
        )
        
        # Clear verification session on success
        if result.get("success"):
            session = VerificationSession(request.telegram_user_id)
            session.delete()
        
        return VerificationSubmitResponse(
            success=result.get("success", False),
            verification_id=result.get("verification_id"),
            trust_score=result.get("trust_score"),
            status=result.get("status"),
            auto_approved=result.get("auto_approved"),
            payout=result.get("payout"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error submitting verification: {str(e)}")
        return VerificationSubmitResponse(
            success=False,
            error=f"Failed to submit verification: {str(e)}"
        )


@router.get("/campaigns/pending")
async def get_pending_campaigns(
    telegram_user_id: str,
    db: Session = Depends(get_db)
) -> List[PendingCampaign]:
    """
    Get list of campaigns that need field verification.
    
    Returns active campaigns that the agent hasn't verified yet.
    """
    try:
        # Verify user is field agent
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.role != "FIELD_AGENT":
            raise HTTPException(
                status_code=403,
                detail=f"Only field agents can view pending campaigns. Your role: {user.role}"
            )
        
        # Get campaigns that are active and agent hasn't verified
        campaigns = db.query(Campaign).filter(
            Campaign.status.in_(["active", "completed"])
        ).all()
        
        # Filter out campaigns already verified by this agent
        verified_campaign_ids = [
            v.campaign_id for v in db.query(ImpactVerification).filter(
                ImpactVerification.field_agent_id == user.id
            ).all()
        ]
        
        pending = []
        for campaign in campaigns:
            if campaign.id not in verified_campaign_ids:
                # Get NGO name
                ngo_name = campaign.ngo.organization_name if campaign.ngo else "Unknown NGO"
                
                pending.append(PendingCampaign(
                    id=str(campaign.id),
                    title=campaign.title,
                    description=campaign.description or "",
                    ngo_name=ngo_name,
                    target_amount_usd=float(campaign.target_amount_usd),
                    current_amount_usd=float(campaign.current_amount_usd),
                    gps_latitude=campaign.gps_latitude,
                    gps_longitude=campaign.gps_longitude,
                    status=campaign.status,
                    created_at=campaign.created_at.isoformat()
                ))
        
        logger.info(f"Retrieved {len(pending)} pending campaigns for agent {telegram_user_id}")
        return pending
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pending campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve campaigns: {str(e)}")


@router.get("/verifications/history")
async def get_verification_history(
    telegram_user_id: str,
    db: Session = Depends(get_db)
) -> List[VerificationHistory]:
    """
    Get field agent's verification history and earnings.
    
    Returns all verifications submitted by this agent with payout status.
    """
    try:
        # Verify user is field agent
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.role != "FIELD_AGENT":
            raise HTTPException(
                status_code=403,
                detail=f"Only field agents can view verification history. Your role: {user.role}"
            )
        
        # Get all verifications by this agent
        verifications = db.query(ImpactVerification).filter(
            ImpactVerification.field_agent_id == user.id
        ).order_by(ImpactVerification.created_at.desc()).all()
        
        history = []
        for v in verifications:
            campaign = db.query(Campaign).filter(Campaign.id == v.campaign_id).first()
            campaign_title = campaign.title if campaign else "Unknown Campaign"
            
            history.append(VerificationHistory(
                id=str(v.id),
                campaign_id=str(v.campaign_id),
                campaign_title=campaign_title,
                verification_date=v.verification_date.isoformat(),
                trust_score=v.trust_score,
                status=v.status,
                agent_payout_amount_usd=v.agent_payout_amount_usd,
                agent_payout_status=v.agent_payout_status,
                photos_count=len(v.photos) if v.photos else 0
            ))
        
        logger.info(f"Retrieved {len(history)} verifications for agent {telegram_user_id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving verification history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.get("/session")
async def get_verification_session(
    telegram_user_id: str
) -> VerificationSessionData:
    """
    Get current verification session state.
    
    Used by frontends to resume in-progress verifications.
    """
    try:
        session = VerificationSession(telegram_user_id)
        data = session.get() or {}
        
        return VerificationSessionData(
            campaign_id=data.get("campaign_id"),
            photo_ids=data.get("photo_ids", []),
            gps_latitude=data.get("gps_latitude"),
            gps_longitude=data.get("gps_longitude"),
            description=data.get("description"),
            beneficiary_count=data.get("beneficiary_count")
        )
        
    except Exception as e:
        logger.error(f"Error retrieving verification session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")


@router.post("/session/update")
async def update_verification_session(
    telegram_user_id: str = Form(...),
    campaign_id: Optional[str] = Form(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    beneficiary_count: Optional[int] = Form(None)
):
    """
    Update verification session with partial data.
    
    Allows frontends to save progress as user fills in verification details.
    """
    try:
        session = VerificationSession(telegram_user_id)
        
        updates = {}
        if campaign_id:
            updates["campaign_id"] = campaign_id
        if gps_latitude is not None:
            updates["gps_latitude"] = gps_latitude
        if gps_longitude is not None:
            updates["gps_longitude"] = gps_longitude
        if description:
            updates["description"] = description
        if beneficiary_count is not None:
            updates["beneficiary_count"] = beneficiary_count
        
        session.update(updates)
        
        return JSONResponse(content={"success": True, "message": "Session updated"})
        
    except Exception as e:
        logger.error(f"Error updating verification session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.delete("/session")
async def clear_verification_session(telegram_user_id: str):
    """
    Clear verification session (cancel in-progress verification).
    """
    try:
        session = VerificationSession(telegram_user_id)
        session.delete()
        
        return JSONResponse(content={"success": True, "message": "Session cleared"})
        
    except Exception as e:
        logger.error(f"Error clearing verification session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")
