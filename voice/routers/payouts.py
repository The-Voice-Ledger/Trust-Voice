"""
Payout Router - Multi-Method Disbursements

Handles payouts FROM platform TO NGOs/beneficiaries via multiple methods:
- M-Pesa B2C: Mobile money (Kenya, Tanzania, Uganda)
- Bank Transfer: SEPA (Europe), SWIFT (international), local transfers
- Stripe Payout: Direct to bank accounts via Stripe

Endpoints:
- POST /payouts/ - Create new payout (disburse funds)
- GET /payouts/{id} - Get payout details
- GET /payouts/campaign/{campaign_id} - List campaign payouts
- GET /payouts/ - List all payouts with filters
- POST /payouts/{id}/approve - Approve pending payout (admin only)
- POST /payouts/{id}/reject - Reject pending payout (admin only)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from database.db import get_db
from database.models import Campaign, NGOOrganization, Payout, User
from services.mpesa import mpesa_service
from services.stripe_service import stripe_service
from services.currency_service import currency_service
from voice.routers.admin import get_current_user

router = APIRouter(prefix="/payouts", tags=["Payouts"])
logger = logging.getLogger(__name__)


class PayoutCreate(BaseModel):
    """Create new payout request."""
    campaign_id: Optional[int] = None
    ngo_id: Optional[int] = None
    recipient_name: str
    amount: float = Field(..., gt=0)
    currency: str = Field(default='USD', pattern=r'^[A-Z]{3}$')  # USD, EUR, GBP, KES, etc.
    payment_method: str = Field(..., pattern=r'^(mpesa_b2c|bank_transfer|stripe_payout)$')
    
    # Mobile money (required for mpesa_b2c)
    recipient_phone: Optional[str] = Field(None, pattern=r'^\+?254\d{9}$|^254\d{9}$|^0\d{9}$')
    
    # Bank account (required for bank_transfer, stripe_payout)
    bank_account_number: Optional[str] = None  # IBAN or account number
    bank_routing_number: Optional[str] = None  # SWIFT/BIC or routing number
    bank_name: Optional[str] = None
    bank_country: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$')  # ISO country code
    
    # Stripe Connect (for stripe_payout)
    stripe_account_id: Optional[str] = None  # Connected account ID
    
    purpose: Optional[str] = Field(default="Campaign disbursement")
    remarks: Optional[str] = Field(default="Payment from TrustVoice")


class PayoutResponse(BaseModel):
    """Payout response schema."""
    id: int
    campaign_id: Optional[int]
    ngo_id: Optional[int]
    recipient_phone: Optional[str]  # Optional - only for mpesa_b2c
    recipient_name: Optional[str]
    amount: float
    currency: str
    payment_method: str
    # Bank transfer fields
    bank_account_number: Optional[str]
    bank_routing_number: Optional[str]
    bank_name: Optional[str]
    bank_country: Optional[str]
    # Stripe fields
    stripe_payout_id: Optional[str]
    stripe_transfer_id: Optional[str]
    # M-Pesa fields
    conversation_id: Optional[str]
    originator_conversation_id: Optional[str]
    transaction_id: Optional[str]
    # Admin approval fields
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    # Common fields
    status: str
    status_message: Optional[str]
    purpose: Optional[str]
    remarks: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=PayoutResponse, status_code=201)
def create_payout(payout: PayoutCreate, db: Session = Depends(get_db)):
    """
    Initiate payout via M-Pesa, bank transfer, or Stripe.
    
    Supports multiple payment methods:
    - mpesa_b2c: Mobile money for Kenya (KES only)
    - bank_transfer: SEPA (EUR), SWIFT (USD, GBP), local transfers
    - stripe_payout: Direct to bank via Stripe (multiple currencies)
    
    Examples:
    
    **M-Pesa (Kenya mobile money):**
    ```json
    {
      "payment_method": "mpesa_b2c",
      "recipient_phone": "+254708374149",
      "recipient_name": "Water Warriors NGO",
      "amount": 50000,
      "currency": "KES"
    }
    ```
    
    **Bank Transfer (European NGO):**
    ```json
    {
      "payment_method": "bank_transfer",
      "recipient_name": "Deutsche Welthungerhilfe",
      "amount": 5000,
      "currency": "EUR",
      "bank_account_number": "DE89370400440532013000",
      "bank_routing_number": "COBADEFFXXX",
      "bank_name": "Commerzbank",
      "bank_country": "DE"
    }
    ```
    
    **Stripe Payout (to verified bank):**
    ```json
    {
      "payment_method": "stripe_payout",
      "recipient_name": "Water Warriors NGO",
      "amount": 1000,
      "currency": "USD",
      "stripe_account_id": "acct_1234567890"
    }
    ```
    """
    try:
        # Validate campaign exists
        if payout.campaign_id:
            campaign = db.query(Campaign).filter(Campaign.id == payout.campaign_id).first()
            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")
            
            # Check sufficient funds (convert payout currency to USD)
            payout_in_usd = currency_service.convert(
                amount=payout.amount,
                from_currency=payout.currency,
                to_currency="USD"
            )
            
            if campaign.raised_amount_usd < payout_in_usd:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient funds. Campaign raised ${campaign.raised_amount_usd:.2f} USD, "
                           f"but payout is {payout.amount} {payout.currency} (${payout_in_usd:.2f} USD)"
                )
        
        # Validate NGO exists
        if payout.ngo_id:
            ngo = db.query(NGOOrganization).filter(NGOOrganization.id == payout.ngo_id).first()
            if not ngo:
                raise HTTPException(status_code=404, detail="NGO not found")
        
        # Validate payment method specific requirements
        if payout.payment_method == 'mpesa_b2c':
            if not payout.recipient_phone:
                raise HTTPException(400, "recipient_phone required for M-Pesa payouts")
            if payout.currency != 'KES':
                raise HTTPException(400, "M-Pesa only supports KES currency")
        
        elif payout.payment_method in ['bank_transfer', 'stripe_payout']:
            if not payout.bank_account_number:
                raise HTTPException(400, f"bank_account_number required for {payout.payment_method}")
        
        # Create payout record (will be updated after payment processing)
        db_payout = Payout(
            campaign_id=payout.campaign_id,
            ngo_id=payout.ngo_id,
            recipient_name=payout.recipient_name,
            amount=payout.amount,
            currency=payout.currency,
            payment_method=payout.payment_method,
            recipient_phone=payout.recipient_phone,
            bank_account_number=payout.bank_account_number,
            bank_routing_number=payout.bank_routing_number,
            bank_name=payout.bank_name,
            bank_country=payout.bank_country,
            status='pending',
            purpose=payout.purpose,
            remarks=payout.remarks
        )
        
        db.add(db_payout)
        db.flush()  # Get ID without committing
        
        # Process payment based on method
        if payout.payment_method == 'mpesa_b2c':
            logger.info(f"Initiating M-Pesa B2C: {payout.amount} KES to {payout.recipient_phone}")
            
            mpesa_response = mpesa_service.b2c_payment(
                phone_number=payout.recipient_phone,
                amount=payout.amount,
                remarks=payout.remarks,
                occasion=payout.purpose or "Payout"
            )
            
            db_payout.conversation_id = mpesa_response.get('ConversationID')
            db_payout.originator_conversation_id = mpesa_response.get('OriginatorConversationID')
            db_payout.status = 'processing'
            db_payout.status_message = mpesa_response.get('ResponseDescription')
            
        elif payout.payment_method == 'stripe_payout':
            logger.info(f"Initiating Stripe payout: {payout.amount} {payout.currency} to {payout.recipient_name}")
            
            stripe_response = stripe_service.create_payout(
                amount=payout.amount,
                currency=payout.currency,
                destination=payout.stripe_account_id or 'default',
                description=f"{payout.purpose} - {payout.recipient_name}",
                metadata={
                    'payout_id': db_payout.id,
                    'campaign_id': payout.campaign_id,
                    'ngo_id': payout.ngo_id
                }
            )
            
            db_payout.stripe_payout_id = stripe_response.get('id')
            db_payout.status = 'processing'
            db_payout.status_message = f"Stripe payout created: {stripe_response.get('id')}"
            
        elif payout.payment_method == 'bank_transfer':
            # Manual bank transfer - mark as pending for admin processing
            logger.info(f"Bank transfer created: {payout.amount} {payout.currency} to {payout.bank_name}")
            db_payout.status = 'pending'
            db_payout.status_message = "Awaiting manual bank transfer processing"
        
        db.commit()
        db.refresh(db_payout)
        
        logger.info(f"Payout created: ID {db_payout.id}, Status: {db_payout.status}")
        
        return db_payout
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payout creation failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create payout: {str(e)}")


@router.get("/{payout_id}", response_model=PayoutResponse)
def get_payout(payout_id: int, db: Session = Depends(get_db)):
    """Get payout details by ID."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    return payout


@router.get("/campaign/{campaign_id}", response_model=List[PayoutResponse])
def list_campaign_payouts(campaign_id: int, db: Session = Depends(get_db)):
    """List all payouts for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    payouts = db.query(Payout).filter(Payout.campaign_id == campaign_id).all()
    return payouts


@router.get("/", response_model=List[PayoutResponse])
def list_payouts(
    status: Optional[str] = None,
    campaign_id: Optional[int] = None,
    ngo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List payouts with optional filters.
    
    Query params:
    - status: Filter by status (pending, processing, completed, failed)
    - campaign_id: Filter by campaign
    - ngo_id: Filter by NGO
    - skip: Pagination offset
    - limit: Max records to return
    """
    query = db.query(Payout)
    
    if status:
        query = query.filter(Payout.status == status)
    if campaign_id:
        query = query.filter(Payout.campaign_id == campaign_id)
    if ngo_id:
        query = query.filter(Payout.ngo_id == ngo_id)
    
    payouts = query.offset(skip).limit(limit).all()
    return payouts


# ============================================
# ADMIN APPROVAL ENDPOINTS
# ============================================

class ApprovalRequest(BaseModel):
    """Request to approve a payout."""
    pass


class RejectionRequest(BaseModel):
    """Request to reject a payout."""
    rejection_reason: str = Field(..., description="Reason for rejection")


@router.post("/{payout_id}/approve", response_model=PayoutResponse)
def approve_payout(
    payout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a pending payout (admin only).
    
    Bank transfers require admin approval before processing.
    M-Pesa and Stripe payouts are auto-processed.
    """
    # Get payout
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    # Check if already approved/rejected
    if payout.status not in ['pending']:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot approve payout with status: {payout.status}"
        )
    
    # Permission check
    from database.models import UserRole
    if current_user.role == UserRole.NGO_ADMIN:
        # NGO admins can only approve their own payouts
        if payout.ngo_id != current_user.ngo_id:
            raise HTTPException(
                status_code=403,
                detail="You can only approve payouts for your NGO"
            )
    elif current_user.role not in [UserRole.SUPER_ADMIN, UserRole.NGO_ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required to approve payouts"
        )
    
    # Approve payout
    payout.status = 'approved'
    payout.approved_by = current_user.id
    payout.approved_at = datetime.utcnow()
    payout.status_message = f"Approved by {current_user.email}"
    
    db.commit()
    db.refresh(payout)
    
    logger.info(f"Payout {payout_id} approved by user {current_user.id}")
    
    return payout


@router.post("/{payout_id}/reject", response_model=PayoutResponse)
def reject_payout(
    payout_id: int,
    request: RejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a pending payout (admin only).
    """
    # Get payout
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    # Check if already approved/rejected
    if payout.status not in ['pending']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject payout with status: {payout.status}"
        )
    
    # Permission check
    from database.models import UserRole
    if current_user.role == UserRole.NGO_ADMIN:
        # NGO admins can only reject their own payouts
        if payout.ngo_id != current_user.ngo_id:
            raise HTTPException(
                status_code=403,
                detail="You can only reject payouts for your NGO"
            )
    elif current_user.role not in [UserRole.SUPER_ADMIN, UserRole.NGO_ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required to reject payouts"
        )
    
    # Reject payout
    payout.status = 'rejected'
    payout.approved_by = current_user.id
    payout.approved_at = datetime.utcnow()
    payout.rejection_reason = request.rejection_reason
    payout.status_message = f"Rejected by {current_user.email}: {request.rejection_reason}"
    
    db.commit()
    db.refresh(payout)
    
    logger.info(f"Payout {payout_id} rejected by user {current_user.id}")
    
    return payout
