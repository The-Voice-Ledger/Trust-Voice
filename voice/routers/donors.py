"""
Donor Management Endpoints
Handles donor registration and profile management
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database.db import get_db
from database.models import Donor

router = APIRouter(prefix="/donors", tags=["Donors"])


# Pydantic schemas
class DonorCreate(BaseModel):
    phone_number: Optional[str] = Field(None, pattern=r"^\+[1-9]\d{1,14}$")
    telegram_user_id: Optional[str] = None
    whatsapp_number: Optional[str] = Field(None, pattern=r"^\+[1-9]\d{1,14}$")
    preferred_language: str = Field("en", pattern="^(en|am|sw|fr|de|es)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+254712345678",
                "telegram_user_id": "123456789",
                "whatsapp_number": "+254712345678",
                "preferred_language": "en"
            }
        }


class DonorUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, pattern=r"^\+[1-9]\d{1,14}$")
    telegram_user_id: Optional[str] = None
    whatsapp_number: Optional[str] = Field(None, pattern=r"^\+[1-9]\d{1,14}$")
    preferred_language: Optional[str] = Field(None, pattern="^(en|am|sw|fr|de|es)$")


class DonorResponse(BaseModel):
    id: int
    phone_number: Optional[str]
    telegram_user_id: Optional[str]
    whatsapp_number: Optional[str]
    preferred_language: str
    total_donated_usd: float
    stripe_customer_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=DonorResponse, status_code=201)
def register_donor(donor: DonorCreate, db: Session = Depends(get_db)):
    """
    Register a new donor
    At least one contact method (phone, telegram, whatsapp) must be provided
    """
    # Validation: at least one contact method
    if not donor.phone_number and not donor.telegram_user_id and not donor.whatsapp_number:
        raise HTTPException(
            status_code=400, 
            detail="At least one contact method (phone_number, telegram_user_id, or whatsapp_number) must be provided"
        )
    
    # Check for existing donor
    if donor.phone_number:
        existing = db.query(Donor).filter(Donor.phone_number == donor.phone_number).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Donor with phone {donor.phone_number} already exists")
    
    if donor.telegram_user_id:
        existing = db.query(Donor).filter(Donor.telegram_user_id == donor.telegram_user_id).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Donor with Telegram ID {donor.telegram_user_id} already exists")
    
    # Create donor
    db_donor = Donor(
        phone_number=donor.phone_number,
        telegram_user_id=donor.telegram_user_id,
        whatsapp_number=donor.whatsapp_number,
        preferred_language=donor.preferred_language,
        total_donated_usd=0.0
    )
    
    db.add(db_donor)
    db.commit()
    db.refresh(db_donor)
    
    return db_donor


@router.get("/{donor_id}", response_model=DonorResponse)
def get_donor(donor_id: int, db: Session = Depends(get_db)):
    """
    Get donor profile by ID
    """
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail=f"Donor with id {donor_id} not found")
    
    return donor


@router.get("/phone/{phone_number}", response_model=DonorResponse)
def get_donor_by_phone(phone_number: str, db: Session = Depends(get_db)):
    """
    Get donor by phone number
    """
    donor = db.query(Donor).filter(Donor.phone_number == phone_number).first()
    if not donor:
        raise HTTPException(status_code=404, detail=f"Donor with phone {phone_number} not found")
    
    return donor


@router.get("/telegram/{telegram_user_id}", response_model=DonorResponse)
def get_donor_by_telegram(telegram_user_id: str, db: Session = Depends(get_db)):
    """
    Get donor by Telegram user ID
    """
    donor = db.query(Donor).filter(Donor.telegram_user_id == telegram_user_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail=f"Donor with Telegram ID {telegram_user_id} not found")
    
    return donor


@router.patch("/{donor_id}", response_model=DonorResponse)
def update_donor(donor_id: int, updates: DonorUpdate, db: Session = Depends(get_db)):
    """
    Update donor profile
    """
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail=f"Donor with id {donor_id} not found")
    
    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(donor, field, value)
    
    db.commit()
    db.refresh(donor)
    
    return donor
