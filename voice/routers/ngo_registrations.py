"""
NGO Registration API Router

Endpoints:
- POST /ngo-registrations/ - Submit NGO registration
- GET /ngo-registrations/ - List pending registrations (admin)
- GET /ngo-registrations/{id} - Get specific registration
- POST /ngo-registrations/{id}/approve - Approve registration (admin)
- POST /ngo-registrations/{id}/reject - Reject registration (admin)
- GET /ngo-registrations/my-application - Get user's pending application
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from database.db import get_db
from database.models import PendingNGORegistration, NGOOrganization, User

router = APIRouter(prefix="/ngo-registrations", tags=["ngo-registrations"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class NGORegistrationCreate(BaseModel):
    """NGO registration submission"""
    # Submitter info
    submitted_by_telegram_id: Optional[str] = None
    submitted_by_telegram_username: Optional[str] = None
    submitted_by_name: Optional[str] = None
    
    # Organization details
    organization_name: str = Field(..., min_length=2, max_length=200)
    registration_number: Optional[str] = Field(None, max_length=100)
    organization_type: Optional[str] = Field(None, max_length=100)
    
    # Contact
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    
    # Location
    country: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    
    # Details
    mission_statement: Optional[str] = None
    focus_areas: Optional[str] = None  # Comma-separated
    year_established: Optional[int] = None
    staff_size: Optional[str] = None
    
    # Documents
    registration_document_url: Optional[str] = None
    tax_certificate_url: Optional[str] = None
    additional_documents: Optional[str] = None  # JSON string
    
    # Banking
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    swift_code: Optional[str] = None


class NGORegistrationResponse(BaseModel):
    """NGO registration response"""
    id: int
    status: str
    organization_name: str
    registration_number: Optional[str]
    organization_type: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    country: Optional[str]
    region: Optional[str]
    mission_statement: Optional[str]
    focus_areas: Optional[str]
    year_established: Optional[int]
    submitted_by_name: Optional[str]
    reviewed_by_admin_id: Optional[int]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    admin_notes: Optional[str]
    ngo_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    """Admin approval request"""
    admin_id: int
    admin_notes: Optional[str] = None


class RejectionRequest(BaseModel):
    """Admin rejection request"""
    admin_id: int
    rejection_reason: str = Field(..., min_length=10)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/", response_model=NGORegistrationResponse, status_code=status.HTTP_201_CREATED)
def submit_ngo_registration(
    registration: NGORegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    Submit NGO registration application.
    
    Can be called from:
    - Telegram mini app
    - Voice command
    - Web form
    """
    # Check if organization name already exists (pending or approved)
    existing_pending = db.query(PendingNGORegistration).filter(
        PendingNGORegistration.organization_name == registration.organization_name,
        PendingNGORegistration.status == 'PENDING'
    ).first()
    
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An application for '{registration.organization_name}' is already pending review"
        )
    
    existing_ngo = db.query(NGOOrganization).filter(
        NGOOrganization.name == registration.organization_name
    ).first()
    
    if existing_ngo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NGO '{registration.organization_name}' is already registered"
        )
    
    # Create pending registration
    pending_ngo = PendingNGORegistration(
        **registration.model_dump()
    )
    
    db.add(pending_ngo)
    db.commit()
    db.refresh(pending_ngo)
    
    return pending_ngo


@router.get("/", response_model=List[NGORegistrationResponse])
def list_ngo_registrations(
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List NGO registration applications.
    
    Query params:
    - status: Filter by status (PENDING, APPROVED, REJECTED, NEEDS_INFO)
    - limit: Max results (default 100)
    """
    query = db.query(PendingNGORegistration)
    
    if status_filter:
        query = query.filter(PendingNGORegistration.status == status_filter.upper())
    
    registrations = query.order_by(PendingNGORegistration.created_at.desc()).limit(limit).all()
    
    return registrations


@router.get("/my-application", response_model=Optional[NGORegistrationResponse])
def get_my_application(
    telegram_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user's pending NGO application by Telegram ID.
    """
    application = db.query(PendingNGORegistration).filter(
        PendingNGORegistration.submitted_by_telegram_id == telegram_id,
        PendingNGORegistration.status.in_(['PENDING', 'NEEDS_INFO'])
    ).order_by(PendingNGORegistration.created_at.desc()).first()
    
    return application


@router.get("/{registration_id}", response_model=NGORegistrationResponse)
def get_ngo_registration(
    registration_id: int,
    db: Session = Depends(get_db)
):
    """Get specific NGO registration by ID"""
    registration = db.query(PendingNGORegistration).filter(
        PendingNGORegistration.id == registration_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    return registration


@router.post("/{registration_id}/approve", response_model=NGORegistrationResponse)
def approve_ngo_registration(
    registration_id: int,
    approval: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve NGO registration and create NGOOrganization record.
    
    Admin only.
    """
    # Get pending registration
    pending = db.query(PendingNGORegistration).filter(
        PendingNGORegistration.id == registration_id
    ).first()
    
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    if pending.status != 'PENDING':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is already {pending.status}"
        )
    
    # Verify admin exists
    admin = db.query(User).filter(User.id == approval.admin_id).first()
    if not admin or admin.role != 'SYSTEM_ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve registrations"
        )
    
    # Create NGO organization
    ngo = NGOOrganization(
        name=pending.organization_name,
        registration_number=pending.registration_number,
        description=pending.mission_statement,
        website=pending.website,
        email=pending.email,
        phone_number=pending.phone_number,
        country=pending.country,
        region=pending.region,
        verification_status='VERIFIED',
        verified_at=datetime.utcnow()
    )
    
    db.add(ngo)
    db.flush()  # Get ngo.id
    
    # Update pending registration
    pending.status = 'APPROVED'
    pending.reviewed_by_admin_id = approval.admin_id
    pending.reviewed_at = datetime.utcnow()
    pending.admin_notes = approval.admin_notes
    pending.ngo_id = ngo.id
    pending.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(pending)
    
    return pending


@router.post("/{registration_id}/reject", response_model=NGORegistrationResponse)
def reject_ngo_registration(
    registration_id: int,
    rejection: RejectionRequest,
    db: Session = Depends(get_db)
):
    """
    Reject NGO registration.
    
    Admin only.
    """
    # Get pending registration
    pending = db.query(PendingNGORegistration).filter(
        PendingNGORegistration.id == registration_id
    ).first()
    
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    if pending.status != 'PENDING':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is already {pending.status}"
        )
    
    # Verify admin exists
    admin = db.query(User).filter(User.id == rejection.admin_id).first()
    if not admin or admin.role != 'SYSTEM_ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject registrations"
        )
    
    # Update pending registration
    pending.status = 'REJECTED'
    pending.reviewed_by_admin_id = rejection.admin_id
    pending.reviewed_at = datetime.utcnow()
    pending.rejection_reason = rejection.rejection_reason
    pending.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(pending)
    
    return pending


@router.post("/{registration_id}/request-info", response_model=NGORegistrationResponse)
def request_more_info(
    registration_id: int,
    admin_id: int,
    notes: str,
    db: Session = Depends(get_db)
):
    """
    Request more information from NGO applicant.
    
    Admin only.
    """
    pending = db.query(PendingNGORegistration).filter(
        PendingNGORegistration.id == registration_id
    ).first()
    
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    # Verify admin
    admin = db.query(User).filter(User.id == admin_id).first()
    if not admin or admin.role != 'SYSTEM_ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can request info"
        )
    
    pending.status = 'NEEDS_INFO'
    pending.admin_notes = notes
    pending.reviewed_by_admin_id = admin_id
    pending.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(pending)
    
    return pending
