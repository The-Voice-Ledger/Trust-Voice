"""
Donation Management Router

Handles donation creation, payment processing, and tracking.
Integrates with M-Pesa (mobile money) and Stripe (cards).
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from database.db import get_db
from database.models import Donation, Campaign, Donor

router = APIRouter(prefix="/donations", tags=["Donations"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class DonationCreate(BaseModel):
    """Request schema for creating a donation."""
    donor_id: int
    campaign_id: int
    amount: float = Field(..., gt=0, description="Amount in the specified currency")
    currency: str = Field(..., min_length=3, max_length=3, pattern=r'^[A-Z]{3}$', description="ISO 4217 currency code (USD, EUR, KES, etc.)")
    payment_method: str = Field(..., pattern=r'^(mpesa|stripe|crypto)$')
    donor_message: Optional[str] = Field(None, max_length=500)
    is_anonymous: bool = False
    
    # M-Pesa specific fields
    phone_number: Optional[str] = Field(None, pattern=r'^\+[1-9]\d{1,14}$')
    
    # Stripe specific fields
    stripe_payment_method_id: Optional[str] = None
    
    # Crypto specific fields
    blockchain_wallet_address: Optional[str] = Field(
        None, 
        pattern=r'^0x[a-fA-F0-9]{40}$'
    )


class DonationResponse(BaseModel):
    """Response schema for donation."""
    id: int
    donor_id: int
    campaign_id: int
    amount: float
    currency: str
    payment_method: str
    status: str
    payment_intent_id: Optional[str]
    transaction_hash: Optional[str]
    donor_message: Optional[str]
    is_anonymous: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DonationStatusUpdate(BaseModel):
    """Schema for updating donation status (internal use)."""
    status: str = Field(..., pattern=r'^(pending|completed|failed|refunded)$')
    payment_intent_id: Optional[str] = None
    transaction_hash: Optional[str] = None


# ============================================================================
# Donation Endpoints
# ============================================================================

@router.post("/", response_model=DonationResponse, status_code=201)
async def create_donation(
    donation: DonationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new donation and initiate payment processing.
    
    Payment Methods:
    - mpesa: Kenya mobile money (requires phone_number)
    - stripe: International cards (requires stripe_payment_method_id)
    - crypto: Cryptocurrency (requires blockchain_wallet_address)
    
    Returns donation with status 'pending' or 'processing'.
    Actual payment processing happens asynchronously.
    """
    # Validate donor exists
    donor = db.query(Donor).filter(Donor.id == donation.donor_id).first()
    if not donor:
        raise HTTPException(
            status_code=404,
            detail=f"Donor with id {donation.donor_id} not found"
        )
    
    # Validate campaign exists and is active
    campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign with id {donation.campaign_id} not found"
        )
    
    if campaign.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Campaign is {campaign.status}, not accepting donations"
        )
    
    # Validate payment method requirements
    if donation.payment_method == "mpesa" and not donation.phone_number:
        raise HTTPException(
            status_code=400,
            detail="phone_number is required for M-Pesa payments"
        )
    
    if donation.payment_method == "stripe" and not donation.stripe_payment_method_id:
        raise HTTPException(
            status_code=400,
            detail="stripe_payment_method_id is required for Stripe payments"
        )
    
    if donation.payment_method == "crypto" and not donation.blockchain_wallet_address:
        raise HTTPException(
            status_code=400,
            detail="blockchain_wallet_address is required for crypto payments"
        )
    
    # Create donation record
    db_donation = Donation(
        donor_id=donation.donor_id,
        campaign_id=donation.campaign_id,
        amount=donation.amount,
        currency=donation.currency,
        payment_method=donation.payment_method,
        donor_message=donation.donor_message,
        is_anonymous=donation.is_anonymous,
        status="pending"
    )
    
    db.add(db_donation)
    db.flush()
    db.refresh(db_donation)
    
    # Process payment based on method
    # Note: In production, these would be actual API calls
    # For now, we'll use mock/stub implementations
    
    if donation.payment_method == "mpesa":
        # Initiate M-Pesa STK Push
        from services.mpesa import mpesa_service
        
        mpesa_response = mpesa_service.initiate_stk_push(
            phone_number=donation.phone_number,
            amount=donation.amount,
            account_reference=f"Campaign-{campaign.id}",
            transaction_desc=f"Donation to {campaign.title}"
        )
        
        db_donation.status = "processing"
        db_donation.payment_intent_id = mpesa_response.get('CheckoutRequestID')
        
    elif donation.payment_method == "stripe":
        # Create Stripe PaymentIntent
        from services.stripe_service import stripe_service
        
        payment_intent = stripe_service.create_payment_intent(
            amount=donation.amount,
            currency=donation.currency,
            customer_email=donor.preferred_name if donor else None,  # Use email if available
            metadata={
                'donation_id': db_donation.id,
                'campaign_id': campaign.id,
                'campaign_title': campaign.title,
                'donor_id': donor.id if donor else None
            }
        )
        
        db_donation.status = "pending"  # Waiting for client to confirm payment
        db_donation.payment_intent_id = payment_intent['id']
        # Store client_secret to return to frontend
        db_donation.status_message = payment_intent['client_secret']
        
    elif donation.payment_method == "crypto":
        # TODO: Implement blockchain transaction
        # For now, mark as processing
        db_donation.status = "processing"
        db_donation.transaction_hash = f"0x{db_donation.id:064x}"
    
    db.flush()
    db.refresh(db_donation)
    
    return db_donation


@router.get("/{donation_id}", response_model=DonationResponse)
def get_donation(donation_id: int, db: Session = Depends(get_db)):
    """
    Get donation details by ID.
    
    Use this to check payment status after initiating donation.
    """
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    return donation


@router.get("/donor/{donor_id}", response_model=List[DonationResponse])
def get_donor_donations(
    donor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all donations by a specific donor.
    
    Useful for showing donation history.
    """
    # Verify donor exists
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    if limit > 100:
        limit = 100
    
    donations = db.query(Donation).filter(
        Donation.donor_id == donor_id
    ).offset(skip).limit(limit).all()
    
    return donations


@router.get("/campaign/{campaign_id}", response_model=List[DonationResponse])
def get_campaign_donations(
    campaign_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all donations for a specific campaign.
    
    Useful for campaign analytics and donor recognition.
    """
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if limit > 100:
        limit = 100
    
    donations = db.query(Donation).filter(
        Donation.campaign_id == campaign_id
    ).offset(skip).limit(limit).all()
    
    return donations


@router.patch("/{donation_id}/status", response_model=DonationResponse)
def update_donation_status(
    donation_id: int,
    status_update: DonationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update donation payment status.
    
    This endpoint is typically called by webhook handlers
    when payment processors send status updates.
    
    In production, this should be protected and only accessible
    to internal services or verified webhook sources.
    """
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    # Store old status before updating
    old_status = donation.status
    
    # Update status
    donation.status = status_update.status
    
    if status_update.payment_intent_id:
        donation.payment_intent_id = status_update.payment_intent_id
    
    if status_update.transaction_hash:
        donation.transaction_hash = status_update.transaction_hash
    
    # If payment completed, update campaign raised_amount_usd
    if status_update.status == "completed" and old_status != "completed":
        campaign = db.query(Campaign).filter(
            Campaign.id == donation.campaign_id
        ).first()
        
        if campaign:
            # Add to currency-specific bucket
            if not campaign.raised_amounts:
                campaign.raised_amounts = {}
            
            currency = donation.currency
            current_amount = campaign.raised_amounts.get(currency, 0.0)
            campaign.raised_amounts[currency] = current_amount + float(donation.amount)
            
            # Also update cached USD total
            from services.currency_service import currency_service
            amount_usd = currency_service.convert_to_usd(
                float(donation.amount),
                donation.currency
            )
            campaign.raised_amount_usd += amount_usd
            
            # Mark raised_amounts as modified so SQLAlchemy detects the change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(campaign, "raised_amounts")
    
    db.commit()
    db.refresh(donation)
    
    return donation


@router.get("/", response_model=List[DonationResponse])
def list_donations(
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all donations with optional filtering.
    
    Query Parameters:
    - status: Filter by status (pending/completed/failed/refunded)
    - payment_method: Filter by method (mpesa/stripe/crypto)
    - skip: Pagination offset
    - limit: Max results (capped at 100)
    """
    query = db.query(Donation)
    
    if status:
        query = query.filter(Donation.status == status)
    
    if payment_method:
        query = query.filter(Donation.payment_method == payment_method)
    
    if limit > 100:
        limit = 100
    
    donations = query.offset(skip).limit(limit).all()
    return donations
