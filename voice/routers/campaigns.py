"""
Campaign Management Endpoints
Handles CRUD operations for campaigns
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from io import BytesIO
import logging
import math

from database.db import get_db
from database.models import Campaign, NGOOrganization, User, ImpactVerification
from voice.routers.admin import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def enrich_campaign_response(campaign: Campaign, db: Session = None) -> dict:
    """
    Enrich campaign data with dynamic USD total calculation and NGO name.
    
    Args:
        campaign: Campaign model instance
        db: Database session (optional, for fetching NGO name)
        
    Returns:
        dict: Campaign data with current_usd_total and ngo_name added
    """
    campaign_dict = {
        "id": campaign.id,
        "ngo_id": campaign.ngo_id,
        "creator_user_id": campaign.creator_user_id,
        "title": campaign.title,
        "description": campaign.description,
        "goal_amount_usd": campaign.goal_amount_usd,
        "raised_amount_usd": campaign.raised_amount_usd,
        "raised_amounts": campaign.raised_amounts or {},
        "current_usd_total": campaign.get_current_usd_total(),
        "status": campaign.status,
        "category": campaign.category,
        "location_gps": campaign.location_gps,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }
    
    # Add NGO name and donation count if we have a database session
    if db:
        if campaign.ngo_id:
            ngo = db.query(NGOOrganization).filter(NGOOrganization.id == campaign.ngo_id).first()
            if ngo:
                campaign_dict["ngo_name"] = ngo.name
        
        # Add donation count
        campaign_dict["donation_count"] = len(campaign.donations) if campaign.donations else 0
    
    return campaign_dict


# Pydantic schemas for request/response
class CampaignCreate(BaseModel):
    # Ownership (exactly one must be provided)
    ngo_id: Optional[int] = None  # For NGO campaigns
    creator_user_id: Optional[int] = None  # For individual campaigns
    
    title: str = Field(..., min_length=3, max_length=200)
    description: str
    goal_amount_usd: float = Field(..., gt=0)
    status: Optional[str] = Field("active", pattern="^(active|paused|completed)$")
    location_gps: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "ngo_id": 1,
                "title": "Clean Water for Rural Kenya",
                "description": "Install 10 water wells in drought-affected villages",
                "goal_amount_usd": 50000.0,
                "status": "active",
                "location_gps": "-1.286389,36.817223"
            }
        }


class CampaignUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    goal_amount_usd: Optional[float] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(active|paused|completed)$")
    location_gps: Optional[str] = None


class CampaignResponse(BaseModel):
    id: int
    ngo_id: Optional[int] = None  # Set for NGO campaigns
    creator_user_id: Optional[int] = None  # Set for individual campaigns
    title: str
    description: str
    goal_amount_usd: float
    raised_amount_usd: float  # Cached USD total
    raised_amounts: Optional[dict] = {}  # Per-currency breakdown: {"USD": 1000, "EUR": 500}
    current_usd_total: Optional[float] = None  # Dynamic USD total with current rates
    status: str
    category: Optional[str] = None  # Campaign category (water, education, health, etc.)
    location_gps: Optional[str]
    created_at: datetime
    updated_at: datetime
    ngo_name: Optional[str] = None  # NGO organization name (fetched dynamically)
    donation_count: Optional[int] = 0  # Number of donations to this campaign
    
    class Config:
        from_attributes = True


@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """
    Create a new fundraising campaign (NGO or Individual).
    
    Must provide exactly one of: ngo_id (NGO campaign) or creator_user_id (individual campaign)
    """
    # Validate XOR: exactly one ownership field must be set
    if not ((campaign.ngo_id is not None) ^ (campaign.creator_user_id is not None)):
        raise HTTPException(
            status_code=400, 
            detail="Must provide exactly one of: ngo_id (NGO campaign) or creator_user_id (individual campaign)"
        )
    
    # Verify NGO exists (if NGO campaign)
    if campaign.ngo_id:
        ngo = db.query(NGOOrganization).filter(NGOOrganization.id == campaign.ngo_id).first()
        if not ngo:
            raise HTTPException(status_code=404, detail=f"NGO with id {campaign.ngo_id} not found")
    
    # Verify user exists (if individual campaign)
    if campaign.creator_user_id:
        from database.models import User
        user = db.query(User).filter(User.id == campaign.creator_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with id {campaign.creator_user_id} not found")
    
    # Create campaign
    db_campaign = Campaign(
        ngo_id=campaign.ngo_id,
        creator_user_id=campaign.creator_user_id,
        title=campaign.title,
        description=campaign.description,
        goal_amount_usd=campaign.goal_amount_usd,
        raised_amount_usd=0.0,
        status=campaign.status,
        location_gps=campaign.location_gps
    )
    
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    return enrich_campaign_response(db_campaign, db)


@router.get("/", response_model=List[CampaignResponse])
def list_campaigns(
    status: Optional[str] = None,
    ngo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all campaigns with optional filters
    """
    query = db.query(Campaign)
    
    if status:
        if status not in ["active", "paused", "completed"]:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: active, paused, or completed")
        query = query.filter(Campaign.status == status)
    
    if ngo_id:
        query = query.filter(Campaign.ngo_id == ngo_id)
    
    campaigns = query.offset(skip).limit(limit).all()
    return [enrich_campaign_response(c, db) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Get a specific campaign by ID
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign with id {campaign_id} not found")
    
    return enrich_campaign_response(campaign, db)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(campaign_id: int, updates: CampaignUpdate, db: Session = Depends(get_db)):
    """
    Update campaign details
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign with id {campaign_id} not found")
    
    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)
    
    return enrich_campaign_response(campaign, db)


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Delete a campaign (soft delete - set status to 'completed')
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign with id {campaign_id} not found")
    
    # Soft delete
    campaign.status = "completed"
    db.commit()
    
    return None


# ============================================
# TRANSPARENCY VIDEO ENDPOINTS
# ============================================

@router.post("/{campaign_id}/upload-video")
async def upload_campaign_video(
    campaign_id: int,
    video: UploadFile = File(...),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),    current_user: User = Depends(get_current_user),    db: Session = Depends(get_db)
):
    """
    Upload transparency video for a campaign.
    
    Campaign creators can upload a 2-5 minute video explaining:
    - Who they are
    - Why they need funding
    - How funds will be used
    - Expected impact
    
    Restrictions:
    - Max size: 50MB
    - Formats: mp4, mov, avi, webm
    - Only campaign creator/NGO can upload
    
    Optional GPS coordinates capture:
    - gps_latitude/gps_longitude: Location where video was filmed
    - Used to verify against field agent verification reports
    - Helps establish authenticity and on-site presence
    
    Video is pinned to IPFS via Pinata for permanent, censorship-resistant storage.
    """
    # Validate campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify user is authorized to upload video for this campaign
    is_authorized = False
    
    # Check if user is campaign creator
    if campaign.creator_user_id == current_user.id:
        is_authorized = True
    
    # Check if user is NGO admin for this campaign
    if campaign.ngo_id and current_user.ngo_id == campaign.ngo_id:
        is_authorized = True
    
    # Check if user is super admin
    if current_user.role in ["SYSTEM_ADMIN", "super_admin"]:
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to upload video for this campaign. Only campaign creator, NGO admin, or system admin can upload videos."
        )
    
    # Check if video already exists (prevent race conditions)
    if campaign.video_ipfs_hash:
        raise HTTPException(
            status_code=409,
            detail="Campaign already has a video. Delete the existing video first before uploading a new one."
        )
    
    # Validate GPS coordinates if provided
    if gps_latitude is not None or gps_longitude is not None:
        # Both must be provided together
        if gps_latitude is None or gps_longitude is None:
            raise HTTPException(
                status_code=400,
                detail="Both gps_latitude and gps_longitude must be provided together"
            )
        
        # Validate coordinate ranges
        if not (-90 <= gps_latitude <= 90):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid latitude: {gps_latitude}. Must be between -90 and 90"
            )
        
        if not (-180 <= gps_longitude <= 180):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid longitude: {gps_longitude}. Must be between -180 and 180"
            )
        
        # Reject null island (0,0) as it's unlikely to be a real location
        if gps_latitude == 0.0 and gps_longitude == 0.0:
            raise HTTPException(
                status_code=400,
                detail="GPS coordinates cannot be exactly (0, 0). Please provide accurate location."
            )
    
    # Validate file size (50MB = 52,428,800 bytes)
    content = await video.read()
    file_size = len(content)
    max_size = 50 * 1024 * 1024
    
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Video too large. Maximum size: 50MB, your file: {file_size / 1024 / 1024:.1f}MB"
        )
    
    # Validate file type
    allowed_types = [
        "video/mp4",
        "video/quicktime",  # .mov
        "video/x-msvideo",  # .avi
        "video/webm"
    ]
    
    if video.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video format. Allowed: mp4, mov, avi, webm. Got: {video.content_type}"
        )
    
    # Pin to IPFS
    try:
        from services.ipfs_service import ipfs_service
        
        result = ipfs_service.pin_file(
            file=BytesIO(content),
            filename=f"campaign_{campaign_id}_{video.filename}",
            metadata={
                "campaign_id": campaign_id,
                "campaign_title": campaign.title,
                "creator": campaign.get_owner_name(db),
                "upload_date": datetime.utcnow().isoformat(),
                "file_size": file_size,
                "content_type": video.content_type
            }
        )
        
        # Update campaign with video info
        campaign.video_ipfs_hash = result["IpfsHash"]
        campaign.video_ipfs_url = ipfs_service.get_gateway_url(result["IpfsHash"])
        campaign.video_uploaded_at = datetime.utcnow()
        campaign.video_file_size_bytes = file_size
        
        # Store GPS coordinates if provided (for verification against field agent reports)
        if gps_latitude is not None and gps_longitude is not None:
            campaign.location_gps = f"{gps_latitude},{gps_longitude}"
            logger.info(f"📍 GPS coordinates captured for campaign {campaign_id}: {campaign.location_gps}")
        
        db.commit()
        
        logger.info(f"✅ Video uploaded for campaign {campaign_id}: {result['IpfsHash']}")
        
        response_data = {
            "success": True,
            "message": "Video uploaded and pinned to IPFS successfully",
            "campaign_id": campaign_id,
            "ipfs_hash": result["IpfsHash"],
            "gateway_url": campaign.video_ipfs_url,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "uploaded_at": campaign.video_uploaded_at.isoformat()
        }
        
        # Add GPS info if provided
        if campaign.location_gps:
            response_data["gps_coordinates"] = campaign.location_gps
            response_data["verification_hint"] = "GPS coordinates will be verified against field agent reports"
        
        return response_data
        
    except Exception as e:
        db.rollback()  # Rollback any partial database changes
        logger.error(f"❌ Failed to upload video for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload video: {str(e)}"
        )


@router.get("/{campaign_id}/video")
async def get_campaign_video(campaign_id: int, db: Session = Depends(get_db)):
    """
    Get campaign video information.
    
    Returns IPFS URLs and metadata for the campaign's transparency video.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if not campaign.video_ipfs_hash:
        raise HTTPException(status_code=404, detail="No video uploaded for this campaign")
    
    from services.ipfs_service import ipfs_service
    
    video_data = {
        "campaign_id": campaign_id,
        "campaign_title": campaign.title,
        "video": {
            "ipfs_hash": campaign.video_ipfs_hash,
            "gateway_url": campaign.video_ipfs_url,
            "alternative_gateways": [
                ipfs_service.get_gateway_url(campaign.video_ipfs_hash, "https://ipfs.io/ipfs/"),
                ipfs_service.get_gateway_url(campaign.video_ipfs_hash, "https://cloudflare-ipfs.com/ipfs/")
            ],
            "uploaded_at": campaign.video_uploaded_at.isoformat() if campaign.video_uploaded_at else None,
            "file_size_mb": round(campaign.video_file_size_bytes / 1024 / 1024, 2) if campaign.video_file_size_bytes else None,
            "duration_seconds": campaign.video_duration_seconds
        }
    }
    
    # Add GPS if available
    if campaign.location_gps:
        try:
            lat, lon = map(float, campaign.location_gps.split(","))
            video_data["location"] = {
                "gps": campaign.location_gps,
                "latitude": lat,
                "longitude": lon,
                "verified": False  # Will check against field agent reports
            }
            
            # Check if location is verified by field agents
            verifications = db.query(ImpactVerification).filter(
                ImpactVerification.campaign_id == campaign_id,
                ImpactVerification.status == "approved",
                ImpactVerification.gps_latitude.isnot(None)
            ).all()
            
            for verification in verifications:
                distance = _calculate_gps_distance(
                    lat, lon,
                    verification.gps_latitude, verification.gps_longitude
                )
                if distance <= 500:  # Within 500m
                    video_data["location"]["verified"] = True
                    video_data["location"]["verified_by_field_agent"] = True
                    video_data["location"]["verification_distance_m"] = round(distance, 2)
                    break
        except (ValueError, AttributeError):
            pass  # Invalid GPS format, skip
    
    return video_data


@router.delete("/{campaign_id}/video")
async def delete_campaign_video(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete campaign video from IPFS.
    
    Unpins video from Pinata and removes database references.
    Video hash remains in IPFS distributed network but is no longer
    actively pinned by TrustVoice.
    
    Authorization: Campaign creator, NGO admin, or system admin only.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if not campaign.video_ipfs_hash:
        raise HTTPException(status_code=404, detail="No video to delete")
    
    # Verify user is authorized to delete video
    is_authorized = False
    
    if campaign.creator_user_id == current_user.id:
        is_authorized = True
    
    if campaign.ngo_id and current_user.ngo_id == campaign.ngo_id:
        is_authorized = True
    
    if current_user.role in ["SYSTEM_ADMIN", "super_admin"]:
        is_authorized = True
    
    if not is_authorized:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete video for this campaign"
        )
    
    try:
        from services.ipfs_service import ipfs_service
        
        # Unpin from Pinata (optional - frees up storage)
        ipfs_hash = campaign.video_ipfs_hash
        ipfs_service.unpin(ipfs_hash)
        
        # Clear video fields from campaign
        campaign.video_ipfs_hash = None
        campaign.video_ipfs_url = None
        campaign.video_uploaded_at = None
        campaign.video_duration_seconds = None
        campaign.video_thumbnail_url = None
        campaign.video_file_size_bytes = None
        
        db.commit()
        
        logger.info(f"✅ Video deleted for campaign {campaign_id}: {ipfs_hash}")
        
        return {
            "success": True,
            "message": "Video deleted successfully",
            "ipfs_hash": ipfs_hash
        }
        
    except Exception as e:
        db.rollback()  # Rollback any partial database changes
        logger.error(f"❌ Failed to delete video for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete video: {str(e)}"
        )


@router.get("/{campaign_id}/verify-location")
async def verify_campaign_location(campaign_id: int, db: Session = Depends(get_db)):
    """
    Verify campaign video location against field agent verification reports.
    
    Checks if:
    1. Campaign has GPS coordinates from video upload
    2. Field agents have verified the campaign with GPS
    3. GPS coordinates match within acceptable range (500m)
    
    Returns:
    - verification_status: verified, unverified, pending
    - distance_meters: Distance between video and verification GPS
    - verifications: List of matching field agent reports
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if campaign has GPS from video
    if not campaign.location_gps:
        return {
            "verification_status": "no_gps",
            "message": "Campaign video uploaded without GPS coordinates",
            "campaign_id": campaign_id
        }
    
    # Parse campaign GPS
    try:
        campaign_lat, campaign_lon = map(float, campaign.location_gps.split(","))
    except (ValueError, AttributeError):
        return {
            "verification_status": "invalid_gps",
            "message": "Campaign has invalid GPS format",
            "campaign_id": campaign_id
        }
    
    # Get all field agent verifications for this campaign
    try:
        verifications = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_id,
            ImpactVerification.status == "approved",
            ImpactVerification.gps_latitude.isnot(None),
            ImpactVerification.gps_longitude.isnot(None)
        ).all()
    except Exception as e:
        logger.error(f"❌ Database error fetching verifications for campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch verifications")
    
    if not verifications:
        return {
            "verification_status": "pending",
            "message": "No field agent verifications with GPS yet",
            "campaign_id": campaign_id,
            "campaign_gps": campaign.location_gps,
            "verification_count": 0
        }
    
    # Calculate distances and find matches
    matching_verifications = []
    max_distance_meters = 500  # 500m threshold for match
    
    for verification in verifications:
        distance = _calculate_gps_distance(
            campaign_lat, campaign_lon,
            verification.gps_latitude, verification.gps_longitude
        )
        
        verification_data = {
            "verification_id": verification.id,
            "agent_id": verification.field_agent_id,
            "verification_date": verification.verification_date.isoformat(),
            "trust_score": verification.trust_score,
            "distance_meters": round(distance, 2),
            "matches": distance <= max_distance_meters,
            "agent_gps": f"{verification.gps_latitude},{verification.gps_longitude}"
        }
        
        if distance <= max_distance_meters:
            matching_verifications.append(verification_data)
    
    # Determine overall status
    if matching_verifications:
        status = "verified"
        message = f"Location verified by {len(matching_verifications)} field agent(s)"
    else:
        status = "location_mismatch"
        message = f"Video GPS does not match field agent verification locations (>{max_distance_meters}m away)"
    
    return {
        "verification_status": status,
        "message": message,
        "campaign_id": campaign_id,
        "campaign_gps": campaign.location_gps,
        "matching_verifications": matching_verifications,
        "total_verifications": len(verifications),
        "threshold_meters": max_distance_meters
    }


def _calculate_gps_distance(
    lat1: float, lon1: float, 
    lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
    
    Returns:
        Distance in meters
        
    Raises:
        ValueError: If coordinates are invalid
    """
    # Validate inputs are not None
    if any(x is None for x in [lat1, lon1, lat2, lon2]):
        raise ValueError("GPS coordinates cannot be None")
    
    # Validate latitude ranges (-90 to 90)
    if not (-90 <= lat1 <= 90):
        raise ValueError(f"Invalid latitude lat1={lat1}. Must be between -90 and 90")
    if not (-90 <= lat2 <= 90):
        raise ValueError(f"Invalid latitude lat2={lat2}. Must be between -90 and 90")
    
    # Validate longitude ranges (-180 to 180)
    if not (-180 <= lon1 <= 180):
        raise ValueError(f"Invalid longitude lon1={lon1}. Must be between -180 and 180")
    if not (-180 <= lon2 <= 180):
        raise ValueError(f"Invalid longitude lon2={lon2}. Must be between -180 and 180")
    
    R = 6371000  # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2)**2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

