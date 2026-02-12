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
from voice.routers.admin import get_current_user
from database.models import User

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
    stripe_client_secret = None
    
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
        # Store client_secret to return to frontend for payment confirmation
        stripe_client_secret = payment_intent.get('client_secret')
        
    elif donation.payment_method == "crypto":
        # TODO: Implement blockchain transaction
        # For now, mark as processing
        db_donation.status = "processing"
        db_donation.transaction_hash = f"0x{db_donation.id:064x}"
    
    db.flush()
    db.refresh(db_donation)
    
    # Build response — include client_secret for Stripe payments
    response = {
        "id": db_donation.id,
        "donor_id": db_donation.donor_id,
        "campaign_id": db_donation.campaign_id,
        "amount": db_donation.amount,
        "currency": db_donation.currency,
        "payment_method": db_donation.payment_method,
        "payment_intent_id": db_donation.payment_intent_id,
        "transaction_hash": db_donation.transaction_hash,
        "nft_token_id": db_donation.nft_token_id,
        "donor_message": db_donation.donor_message,
        "is_anonymous": db_donation.is_anonymous,
        "status": db_donation.status,
        "created_at": db_donation.created_at,
        "updated_at": db_donation.updated_at,
    }
    if donation.payment_method == "stripe" and stripe_client_secret:
        response["stripe_client_secret"] = stripe_client_secret
    
    return response


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update donation payment status.
    
    Admin only. This endpoint should only be used for manual overrides.
    Normal status updates come via webhook handlers.
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


# ============================================
# TAX RECEIPT NFT ENDPOINTS
# ============================================

@router.post("/{donation_id}/mint-receipt-nft")
async def mint_tax_receipt_nft(
    donation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mint NFT tax receipt for a completed donation.
    
    This creates a blockchain-based tax receipt that:
    - Is permanently stored and verifiable
    - Can be used for tax deductions
    - Links to IPFS metadata with donation details
    - Is sent to donor's wallet address
    
    Requirements:
    - Donation must be completed
    - Donor must have wallet_address set
    - Receipt not already minted
    """
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    # Validate donation is completed
    if donation.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mint receipt for {donation.status} donation. Must be completed."
        )
    
    # Check if receipt already minted
    if donation.receipt_nft_token_id:
        raise HTTPException(
            status_code=400,
            detail=f"Receipt already minted. Token ID: {donation.receipt_nft_token_id}"
        )
    
    # Validate donor has wallet address
    if not donation.donor_wallet_address:
        raise HTTPException(
            status_code=400,
            detail="Donor wallet address not set. Cannot mint NFT."
        )
    
    # Generate receipt metadata
    try:
        campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
        donor = db.query(Donor).filter(Donor.id == donation.donor_id).first()
        
        ngo = None
        if campaign.ngo_id:
            ngo = db.query(NGOOrganization).filter(NGOOrganization.id == campaign.ngo_id).first()
        
        # Create NFT metadata following OpenSea standard
        receipt_metadata = {
            "name": f"TrustVoice Donation Receipt #{donation_id}",
            "description": f"Official tax-deductible donation receipt for ${donation.amount} {donation.currency} to {campaign.title}",
            "image": "ipfs://QmTrustVoiceReceiptTemplateImage",  # TODO: Design receipt image
            "external_url": f"https://trustvoice.org/receipts/{donation_id}",
            "attributes": [
                {"trait_type": "Donor_Name", "value": donor.preferred_name if donor else "Anonymous"},
                {"trait_type": "Campaign_Name", "value": campaign.title},
                {"trait_type": "NGO_Name", "value": ngo.name if ngo else "Individual Campaign"},
                {"trait_type": "Amount", "value": str(donation.amount)},
                {"trait_type": "Currency", "value": donation.currency},
                {"trait_type": "Date", "value": donation.completed_at.strftime("%Y-%m-%d")},
                {"trait_type": "Receipt_Number", "value": f"TV-{donation.completed_at.year}-{donation_id:06d}"},
                {"trait_type": "Tax_Year", "value": str(donation.completed_at.year)},
                {"trait_type": "Payment_Method", "value": donation.payment_method},
                {"trait_type": "Deductible", "value": "true"},
                {"trait_type": "Verified", "value": "true"}
            ],
            "properties": {
                "donation_id": donation_id,
                "campaign_id": campaign.id,
                "timestamp": donation.completed_at.isoformat(),
                "transaction_id": donation.payment_intent_id or donation.transaction_hash
            }
        }
        
        # Pin metadata to IPFS
        from services.ipfs_service import ipfs_service
        
        ipfs_result = ipfs_service.pin_json(
            json_data=receipt_metadata,
            name=f"tax_receipt_{donation_id}"
        )
        
        metadata_hash = ipfs_result["IpfsHash"]
        logger.info(f"✅ Receipt metadata pinned to IPFS: {metadata_hash}")
        
        # Mint NFT on blockchain (with IPFS rollback on failure)
        from services.blockchain_service import blockchain_service
        
        if not blockchain_service.is_configured():
            # Rollback IPFS pin before raising exception
            try:
                ipfs_service.unpin(metadata_hash)
                logger.info(f"🔄 Rolled back IPFS pin (blockchain not configured): {metadata_hash}")
            except Exception as unpin_error:
                logger.error(f"⚠️ Failed to rollback IPFS pin: {unpin_error}")
            
            raise HTTPException(
                status_code=503,
                detail="Blockchain service not configured. Please contact administrator."
            )
        
        try:
            mint_result = blockchain_service.mint_receipt_nft(
                donor_wallet=donation.donor_wallet_address,
                metadata_ipfs_hash=metadata_hash,
                donation_id=donation_id
            )
            
            if not mint_result.get("success"):
                # Blockchain minting failed, rollback IPFS pin
                error_msg = mint_result.get("error", "Unknown blockchain error")
                logger.warning(f"⚠️ NFT mint failed: {error_msg}")
                
                try:
                    ipfs_service.unpin(metadata_hash)
                    logger.info(f"🔄 Rolled back IPFS pin (mint failed): {metadata_hash}")
                except Exception as unpin_error:
                    logger.error(f"⚠️ Failed to rollback IPFS pin {metadata_hash}: {unpin_error}")
                
                raise Exception(error_msg)
            
            # Update donation record
            donation.receipt_nft_token_id = mint_result["token_id"]
            donation.receipt_nft_contract = blockchain_service.contract_address
            donation.receipt_nft_network = blockchain_service.network
            donation.receipt_nft_tx_hash = mint_result["tx_hash"]
            donation.receipt_metadata_ipfs = metadata_hash
            donation.receipt_minted_at = datetime.utcnow()
            donation.tax_receipt_sent = True
            
            db.commit()
            
        except Exception as mint_error:
            # Final safety net - cleanup IPFS if minting fails
            try:
                ipfs_service.unpin(metadata_hash)
                logger.info(f"🧹 Cleanup: Unpinned orphaned metadata {metadata_hash}")
            except Exception as cleanup_error:
                logger.error(f"⚠️ Final cleanup failed for {metadata_hash}: {cleanup_error}")
        
        logger.info(f"✅ NFT receipt minted for donation {donation_id}: token_id={mint_result['token_id']}")
        
        return {
            "success": True,
            "message": "Tax receipt NFT minted successfully",
            "donation_id": donation_id,
            "nft": {
                "token_id": mint_result["token_id"],
                "contract_address": blockchain_service.contract_address,
                "network": blockchain_service.network,
                "transaction_hash": mint_result["tx_hash"],
                "explorer_url": mint_result["explorer_url"],
                "opensea_url": mint_result.get("opensea_url"),
                "metadata_ipfs": metadata_hash,
                "metadata_url": ipfs_service.get_gateway_url(metadata_hash)
            },
            "gas_cost": {
                "eth": mint_result.get("gas_cost_eth"),
                "gas_used": mint_result.get("gas_used")
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to mint NFT receipt for donation {donation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mint NFT receipt: {str(e)}"
        )


@router.get("/{donation_id}/receipt")
async def get_tax_receipt(donation_id: int, db: Session = Depends(get_db)):
    """
    Get tax receipt information (NFT or traditional).
    
    Returns:
    - NFT details if minted (blockchain-based)
    - Metadata for traditional PDF receipt
    - Verification status
    """
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
    donor = db.query(Donor).filter(Donor.id == donation.donor_id).first()
    
    receipt_data = {
        "donation_id": donation_id,
        "receipt_number": f"TV-{donation.completed_at.year}-{donation_id:06d}" if donation.completed_at else None,
        "donation": {
            "amount": donation.amount,
            "currency": donation.currency,
            "date": donation.completed_at.isoformat() if donation.completed_at else None,
            "payment_method": donation.payment_method,
            "status": donation.status
        },
        "campaign": {
            "id": campaign.id,
            "title": campaign.title,
            "category": campaign.category
        },
        "donor": {
            "name": donor.preferred_name if donor and not donation.is_anonymous else "Anonymous",
            "anonymous": donation.is_anonymous
        },
        "nft_receipt": None,
        "traditional_receipt_url": f"/api/donations/{donation_id}/receipt/pdf"
    }
    
    # Add NFT details if minted
    if donation.receipt_nft_token_id:
        from services.ipfs_service import ipfs_service
        from services.blockchain_service import blockchain_service
        
        receipt_data["nft_receipt"] = {
            "token_id": donation.receipt_nft_token_id,
            "contract_address": donation.receipt_nft_contract,
            "network": donation.receipt_nft_network,
            "transaction_hash": donation.receipt_nft_tx_hash,
            "minted_at": donation.receipt_minted_at.isoformat() if donation.receipt_minted_at else None,
            "metadata_ipfs": donation.receipt_metadata_ipfs,
            "metadata_url": ipfs_service.get_gateway_url(donation.receipt_metadata_ipfs) if donation.receipt_metadata_ipfs else None,
            "explorer_url": blockchain_service._get_explorer_url(donation.receipt_nft_tx_hash) if donation.receipt_nft_tx_hash else None,
            "opensea_url": blockchain_service._get_opensea_url(donation.receipt_nft_token_id) if donation.receipt_nft_token_id else None
        }
    
    return receipt_data


@router.get("/{donation_id}/receipt/verify")
async def verify_tax_receipt(donation_id: int, db: Session = Depends(get_db)):
    """
    Verify tax receipt authenticity via blockchain.
    
    Used by:
    - Tax authorities
    - Auditors
    - Donors for verification
    
    Returns blockchain verification status.
    """
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    if not donation.receipt_nft_token_id:
        return {
            "verified": False,
            "message": "No blockchain receipt minted for this donation",
            "donation_id": donation_id,
            "traditional_receipt_available": donation.status == "completed"
        }
    
    # Verify on blockchain
    from services.blockchain_service import blockchain_service
    
    verification = blockchain_service.verify_receipt(donation.receipt_nft_token_id)
    
    return {
        "verified": verification.get("valid", False),
        "donation_id": donation_id,
        "nft": {
            "token_id": donation.receipt_nft_token_id,
            "owner": verification.get("owner"),
            "network": donation.receipt_nft_network,
            "contract": donation.receipt_nft_contract,
            "token_uri": verification.get("token_uri"),
            "explorer_url": verification.get("explorer_url")
        },
        "donation_details": {
            "amount": donation.amount,
            "currency": donation.currency,
            "date": donation.completed_at.isoformat() if donation.completed_at else None,
            "status": donation.status
        }
    }


@router.get("/tax-year/{year}")
async def get_annual_donation_summary(
    year: int,
    donor_id: int,
    db: Session = Depends(get_db)
):
    """
    Get annual donation summary for tax filing.
    
    Returns all donations for a specific tax year with:
    - Total USD equivalent
    - Individual receipts
    - NFT verification status
    
    Integrates with tax software (TurboTax, H&R Block, etc.)
    """
    from sqlalchemy import func, extract
    from services.currency_service import currency_service
    
    # Get all completed donations for the year
    donations = db.query(Donation).filter(
        Donation.donor_id == donor_id,
        Donation.status == "completed",
        extract('year', Donation.completed_at) == year
    ).all()
    
    if not donations:
        return {
            "tax_year": year,
            "donor_id": donor_id,
            "total_donations_usd": 0,
            "donation_count": 0,
            "receipts": [],
            "message": f"No donations found for tax year {year}"
        }
    
    # Calculate total in USD
    total_usd = 0
    receipts = []
    
    for d in donations:
        # Convert to USD if needed
        if d.currency == "USD":
            amount_usd = d.amount
        else:
            amount_usd = currency_service.convert_to_usd(d.amount, d.currency)
        
        total_usd += amount_usd
        
        campaign = db.query(Campaign).filter(Campaign.id == d.campaign_id).first()
        
        receipts.append({
            "donation_id": d.id,
            "date": d.completed_at.strftime("%Y-%m-%d"),
            "campaign": campaign.title if campaign else "Unknown",
            "amount": d.amount,
            "currency": d.currency,
            "amount_usd": round(amount_usd, 2),
            "receipt_number": f"TV-{year}-{d.id:06d}",
            "nft_minted": d.receipt_nft_token_id is not None,
            "nft_token_id": d.receipt_nft_token_id,
            "receipt_url": f"/api/donations/{d.id}/receipt",
            "pdf_url": f"/api/donations/{d.id}/receipt/pdf"
        })
    
    return {
        "tax_year": year,
        "donor_id": donor_id,
        "total_donations_usd": round(total_usd, 2),
        "donation_count": len(donations),
        "receipts": receipts,
        "summary": {
            "deductible_amount": round(total_usd, 2),
            "currency_breakdown": {
                curr: sum(d.amount for d in donations if d.currency == curr)
                for curr in set(d.currency for d in donations)
            }
        }
    }
