"""
Registration Approval API Endpoints
Provides web-based admin dashboard APIs for managing pending registrations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database.db import get_db
from database.models import User, PendingRegistration, UserRole
from services.auth_service import decode_access_token

router = APIRouter(prefix="/admin/registrations", tags=["Admin Registrations"])
security = HTTPBearer()


# ===========================
# Pydantic Schemas
# ===========================

class PendingRegistrationResponse(BaseModel):
    """Response schema for pending registration"""
    id: int
    telegram_user_id: int
    full_name: str
    phone_number: str
    role: str
    organization: Optional[str]
    reason: Optional[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    admin_id: Optional[int]
    admin_notes: Optional[str]
    
    class Config:
        from_attributes = True


class RegistrationApprovalRequest(BaseModel):
    """Request schema for approving registration"""
    admin_notes: Optional[str] = None


class RegistrationRejectionRequest(BaseModel):
    """Request schema for rejecting registration"""
    reason: str  # Required: admin must provide rejection reason


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_users: int
    pending_registrations: int
    approved_today: int
    rejected_today: int
    total_admins: int
    total_creators: int
    total_agents: int
    total_donors: int


# ===========================
# Helper Functions
# ===========================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verify user is admin."""
    if current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ===========================
# API Endpoints
# ===========================

@router.get("/", response_model=List[PendingRegistrationResponse])
async def list_pending_registrations(
    status_filter: Optional[str] = "pending",
    role_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    List pending registrations with filtering and pagination
    
    Query Parameters:
    - status_filter: Filter by status (pending, approved, rejected). Default: pending
    - role_filter: Filter by role (CAMPAIGN_CREATOR, FIELD_AGENT). Default: all
    - limit: Maximum number of results. Default: 50
    - offset: Number of results to skip for pagination. Default: 0
    """
    query = db.query(PendingRegistration)
    
    # Apply filters
    if status_filter:
        query = query.filter(PendingRegistration.status == status_filter)
    
    if role_filter:
        try:
            role = UserRole[role_filter.upper()]
            query = query.filter(PendingRegistration.role == role)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role_filter}"
            )
    
    # Sort by created_at descending (newest first)
    query = query.order_by(desc(PendingRegistration.created_at))
    
    # Apply pagination
    registrations = query.limit(limit).offset(offset).all()
    
    return registrations


@router.post("/{registration_id}/approve", response_model=dict)
async def approve_registration(
    registration_id: int,
    approval_data: RegistrationApprovalRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Approve a pending registration and create User account
    
    This endpoint:
    1. Fetches the pending registration
    2. Creates a new User record
    3. Updates the pending registration status to 'approved'
    4. Records the admin who approved and timestamp
    """
    # Fetch pending registration
    pending_reg = db.query(PendingRegistration).filter(
        PendingRegistration.id == registration_id
    ).first()
    
    if not pending_reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    # Check if already processed
    if pending_reg.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration already {pending_reg.status}"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.telegram_user_id == pending_reg.telegram_user_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists with this Telegram ID"
        )
    
    # Create new User
    new_user = User(
        telegram_user_id=pending_reg.telegram_user_id,
        full_name=pending_reg.full_name,
        phone_number=pending_reg.phone_number,
        role=pending_reg.role,
        organization=pending_reg.organization,
        is_approved=True,
        pin_hash=None,  # User will set PIN after approval
        failed_login_attempts=0,
        locked_until=None
    )
    
    db.add(new_user)
    
    # Update pending registration
    pending_reg.status = "approved"
    pending_reg.admin_id = current_admin.id
    pending_reg.admin_notes = approval_data.admin_notes
    pending_reg.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_user)
    
    return {
        "status": "success",
        "message": f"Registration approved for {pending_reg.full_name}",
        "user_id": new_user.id,
        "telegram_user_id": new_user.telegram_user_id,
        "role": new_user.role.value,
        "approved_by": current_admin.full_name,
        "approved_at": pending_reg.reviewed_at.isoformat()
    }


@router.post("/{registration_id}/reject", response_model=dict)
async def reject_registration(
    registration_id: int,
    rejection_data: RegistrationRejectionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Reject a pending registration
    
    This endpoint:
    1. Fetches the pending registration
    2. Updates status to 'rejected'
    3. Records rejection reason and admin details
    """
    # Fetch pending registration
    pending_reg = db.query(PendingRegistration).filter(
        PendingRegistration.id == registration_id
    ).first()
    
    if not pending_reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    # Check if already processed
    if pending_reg.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration already {pending_reg.status}"
        )
    
    # Update pending registration
    pending_reg.status = "rejected"
    pending_reg.admin_id = current_admin.id
    pending_reg.admin_notes = rejection_data.reason
    pending_reg.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Registration rejected for {pending_reg.full_name}",
        "registration_id": pending_reg.id,
        "telegram_user_id": pending_reg.telegram_user_id,
        "rejected_by": current_admin.full_name,
        "rejected_at": pending_reg.reviewed_at.isoformat(),
        "reason": rejection_data.reason
    }


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get dashboard statistics for admin overview
    
    Returns counts of:
    - Total users
    - Pending registrations
    - Approvals/rejections today
    - Users by role
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = DashboardStats(
        total_users=db.query(func.count(User.id)).scalar(),
        pending_registrations=db.query(func.count(PendingRegistration.id)).filter(
            PendingRegistration.status == "pending"
        ).scalar(),
        approved_today=db.query(func.count(PendingRegistration.id)).filter(
            PendingRegistration.status == "approved",
            PendingRegistration.reviewed_at >= today_start
        ).scalar(),
        rejected_today=db.query(func.count(PendingRegistration.id)).filter(
            PendingRegistration.status == "rejected",
            PendingRegistration.reviewed_at >= today_start
        ).scalar(),
        total_admins=db.query(func.count(User.id)).filter(
            User.role == UserRole.SYSTEM_ADMIN
        ).scalar(),
        total_creators=db.query(func.count(User.id)).filter(
            User.role == UserRole.CAMPAIGN_CREATOR
        ).scalar(),
        total_agents=db.query(func.count(User.id)).filter(
            User.role == UserRole.FIELD_AGENT
        ).scalar(),
        total_donors=db.query(func.count(User.id)).filter(
            User.role == UserRole.DONOR
        ).scalar(),
    )
    
    return stats


@router.get("/{registration_id}", response_model=PendingRegistrationResponse)
async def get_registration_details(
    registration_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get detailed information about a specific registration"""
    registration = db.query(PendingRegistration).filter(
        PendingRegistration.id == registration_id
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration {registration_id} not found"
        )
    
    return registration
