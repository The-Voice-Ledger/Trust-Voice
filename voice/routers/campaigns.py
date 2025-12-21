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


# Pydantic schemas for request/response
class CampaignCreate(BaseModel):
    ngo_id: int
    title: str = Field(..., min_length=3, max_length=200)
    description: str
    goal_amount_usd: float = Field(..., gt=0)
    location_gps: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "ngo_id": 1,
                "title": "Clean Water for Rural Kenya",
                "description": "Install 10 water wells in drought-affected villages",
                "goal_amount_usd": 50000.0,
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
    ngo_id: int
    title: str
    description: str
    goal_amount_usd: float
    raised_amount_usd: float
    status: str
    location_gps: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """
    Create a new fundraising campaign
    """
    # Verify NGO exists
    ngo = db.query(NGOOrganization).filter(NGOOrganization.id == campaign.ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail=f"NGO with id {campaign.ngo_id} not found")
    
    # Create campaign
    db_campaign = Campaign(
        ngo_id=campaign.ngo_id,
        title=campaign.title,
        description=campaign.description,
        goal_amount_usd=campaign.goal_amount_usd,
        raised_amount_usd=0.0,
        status="active",
        location_gps=campaign.location_gps
    )
    
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    return db_campaign


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
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Get a specific campaign by ID
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign with id {campaign_id} not found")
    
    return campaign


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
    
    return campaign


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
