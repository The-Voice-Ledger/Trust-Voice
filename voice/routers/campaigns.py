"""
Campaign Management Endpoints
Handles CRUD operations for campaigns
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database.db import get_db
from database.models import Campaign, NGOOrganization

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
