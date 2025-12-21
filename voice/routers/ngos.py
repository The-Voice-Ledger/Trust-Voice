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
from database.models import NGOOrganization

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
    website_url: Optional[str]
    contact_email: Optional[str]
    blockchain_wallet_address: Optional[str]
    stripe_account_id: Optional[str]
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
