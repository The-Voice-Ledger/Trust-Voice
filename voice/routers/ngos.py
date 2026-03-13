"""
NGO Management Endpoints
Handles NGO organization registration and management
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

from database.db import get_db
from database.models import NGOOrganization, Campaign

router = APIRouter(prefix="/ngos", tags=["NGOs"])


# Pydantic schemas
class NGOCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    blockchain_wallet_address: Optional[str] = Field(None, pattern=r"^0x[a-fA-F0-9]{40}$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Water For All Kenya",
                "description": "Providing clean water to rural communities",
                "website_url": "https://waterforallkenya.org",
                "contact_email": "contact@waterforallkenya.org",
                "blockchain_wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            }
        }


class NGOUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = Field(None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    blockchain_wallet_address: Optional[str] = Field(None, pattern=r"^0x[a-fA-F0-9]{40}$")
    stripe_account_id: Optional[str] = None


class NGOResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    mission_statement: Optional[str] = None
    focus_areas: Optional[str] = None
    website_url: Optional[str]
    registration_number: Optional[str] = None
    organization_type: Optional[str] = None
    year_established: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    contact_email: Optional[str]
    admin_phone: Optional[str] = None
    logo_url: Optional[str] = None
    intro_video_url: Optional[str] = None
    intro_video_ipfs_hash: Optional[str] = None
    blockchain_wallet_address: Optional[str]
    stripe_account_id: Optional[str]
    verification_status: Optional[str] = None
    verified_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=NGOResponse, status_code=201)
def create_ngo(ngo: NGOCreate, db: Session = Depends(get_db)):
    """
    Register a new NGO organization
    """
    # Check for duplicate name
    existing = db.query(NGOOrganization).filter(NGOOrganization.name == ngo.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"NGO with name '{ngo.name}' already exists")
    
    # Create NGO
    db_ngo = NGOOrganization(
        name=ngo.name,
        description=ngo.description,
        website_url=ngo.website_url,
        contact_email=ngo.contact_email,
        blockchain_wallet_address=ngo.blockchain_wallet_address
    )
    
    db.add(db_ngo)
    db.commit()
    db.refresh(db_ngo)
    
    return db_ngo


@router.get("/", response_model=List[NGOResponse])
def list_ngos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all registered NGOs
    """
    ngos = db.query(NGOOrganization).offset(skip).limit(limit).all()
    return ngos


@router.get("/{ngo_id}", response_model=NGOResponse)
def get_ngo(ngo_id: int, db: Session = Depends(get_db)):
    """
    Get a specific NGO by ID
    """
    ngo = db.query(NGOOrganization).filter(NGOOrganization.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail=f"NGO with id {ngo_id} not found")
    
    return ngo


@router.patch("/{ngo_id}", response_model=NGOResponse)
def update_ngo(ngo_id: int, updates: NGOUpdate, db: Session = Depends(get_db)):
    """
    Update NGO details
    """
    ngo = db.query(NGOOrganization).filter(NGOOrganization.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail=f"NGO with id {ngo_id} not found")
    
    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    
    # Check for name uniqueness if updating name
    if "name" in update_data:
        existing = db.query(NGOOrganization).filter(
            NGOOrganization.name == update_data["name"],
            NGOOrganization.id != ngo_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"NGO with name '{update_data['name']}' already exists")
    
    for field, value in update_data.items():
        setattr(ngo, field, value)
    
    db.commit()
    db.refresh(ngo)
    
    return ngo


@router.delete("/{ngo_id}", status_code=204)
def delete_ngo(ngo_id: int, db: Session = Depends(get_db)):
    """
    Delete an NGO (hard delete - be careful!)
    """
    ngo = db.query(NGOOrganization).filter(NGOOrganization.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail=f"NGO with id {ngo_id} not found")
    
    db.delete(ngo)
    db.commit()
    
    return None


@router.get("/{ngo_id}/campaigns")
def get_ngo_campaigns(ngo_id: int, db: Session = Depends(get_db)):
    """
    List all campaigns belonging to an NGO.
    Returns basic campaign info for the NGO profile page.
    """
    ngo = db.query(NGOOrganization).filter(NGOOrganization.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail=f"NGO with id {ngo_id} not found")
    
    campaigns = db.query(Campaign).filter(
        Campaign.ngo_id == ngo_id,
        Campaign.status.in_(['active', 'completed'])
    ).order_by(Campaign.created_at.desc()).all()
    
    result = []
    for c in campaigns:
        result.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "goal_amount_usd": float(c.goal_amount_usd) if c.goal_amount_usd else 0,
            "raised_amount_usd": float(c.raised_amount_usd) if c.raised_amount_usd else 0,
            "current_usd_total": c.get_current_usd_total() if hasattr(c, 'get_current_usd_total') else float(c.raised_amount_usd or 0),
            "status": c.status,
            "category": c.category,
            "donation_count": len(c.donations) if c.donations else 0,
            "created_at": c.created_at,
        })
    
    return result
