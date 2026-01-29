"""
User Authentication Router

Endpoints for PIN-based authentication (Telegram users accessing web UI).
Separate from admin authentication which uses email/password.

POST /auth/login - Login with username + PIN
GET /auth/me - Get current user info from JWT token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from database.db import get_db
from database.models import User, UserRole
from services.auth_service import (
    verify_pin,
    create_access_token,
    decode_access_token,
    check_login_attempts,
    record_failed_login,
    reset_login_attempts
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request with username/phone and PIN"""
    username: Optional[str] = None  # telegram_username or email
    phone: Optional[str] = None     # phone_number
    pin: str                        # 4-digit PIN
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+254712345678",
                "pin": "1234"
            }
        }


class LoginResponse(BaseModel):
    """Login response with JWT token and user info"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
    user: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": 1,
                    "telegram_user_id": "123456789",
                    "telegram_username": "john_doe",
                    "role": "CAMPAIGN_CREATOR",
                    "email": "john@example.com",
                    "is_approved": True
                }
            }
        }


class UserInfoResponse(BaseModel):
    """Current user information"""
    id: int
    telegram_user_id: Optional[str]
    telegram_username: Optional[str]
    email: Optional[str]
    role: str
    is_approved: bool
    phone_verified: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "telegram_user_id": "123456789",
                "telegram_username": "john_doe",
                "email": "john@example.com",
                "role": "CAMPAIGN_CREATOR",
                "is_approved": True,
                "phone_verified": False
            }
        }


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user from JWT token.
    
    Usage:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
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


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with phone number and 4-digit PIN.
    
    Returns JWT token valid for 15 minutes.
    
    **Security Features:**
    - Account lockout after 5 failed attempts (30 minutes)
    - Bcrypt PIN verification (constant-time)
    - Failed login attempt tracking
    
    **Error Cases:**
    - 401: User not found
    - 401: PIN not set (user needs to set PIN via Telegram)
    - 403: Account not approved
    - 423: Account locked (too many failed attempts)
    - 401: Invalid PIN
    """
    # Find user by phone number (primary) or fallback to username/email
    user = None
    if request.phone:
        user = db.query(User).filter(User.phone_number == request.phone).first()
    elif request.username:
        user = db.query(User).filter(
            (User.telegram_username == request.username) |
            (User.email == request.username)
        ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or PIN"
        )
    
    # Check if user has PIN set
    if not user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN not set. Please set your PIN via Telegram using /set_pin"
        )
    
    # Check if user is approved
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending admin approval. You'll be notified via Telegram when approved."
        )
    
    # Check login attempts (account lockout)
    allowed, error_message = check_login_attempts(user)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=error_message
        )
    
    # Verify PIN
    if not verify_pin(request.pin, user.pin_hash):
        # Record failed attempt
        record_failed_login(user, db)
        
        # Check if account is now locked
        if user.failed_login_attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed attempts. Try again in 30 minutes."
            )
        
        remaining_attempts = 5 - user.failed_login_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid PIN. {remaining_attempts} attempts remaining before lockout."
        )
    
    # PIN correct - reset failed attempts
    reset_login_attempts(user, db)
    
    # Generate JWT token (15 minutes expiry)
    token_data = {
        "user_id": user.id,
        "telegram_user_id": user.telegram_user_id,
        "telegram_username": user.telegram_username,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=15)
    )
    
    # Return token and user info
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=900,  # 15 minutes
        user={
            "id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "telegram_username": user.telegram_username,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_approved": user.is_approved,
            "phone_verified": user.phone_verified_at is not None
        }
    )


@router.get("/me", response_model=UserInfoResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information from JWT token.
    
    Requires Authorization header with Bearer token.
    
    **Example:**
    ```
    GET /auth/me
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
    
    **Error Cases:**
    - 401: Invalid or expired token
    - 401: User not found
    """
    return UserInfoResponse(
        id=current_user.id,
        telegram_user_id=current_user.telegram_user_id,
        telegram_username=current_user.telegram_username,
        email=current_user.email,
        role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        is_approved=current_user.is_approved,
        phone_verified=current_user.phone_verified_at is not None
    )


@router.post("/logout")
def logout():
    """
    Logout endpoint (client should discard token).
    
    Since we use stateless JWT tokens, logout is handled client-side
    by discarding the token. This endpoint exists for API consistency.
    
    For true server-side logout, implement token blacklisting with Redis.
    """
    return {
        "message": "Logged out successfully. Please discard your token.",
        "action": "client_side_logout"
    }


@router.get("/language/{telegram_user_id}")
def get_user_language(telegram_user_id: str, db: Session = Depends(get_db)):
    """
    Get user's preferred language by Telegram user ID.
    
    Used by miniapps to initialize language preference from database.
    Falls back to 'en' if user not found or preference not set.
    
    Args:
        telegram_user_id: Telegram user ID from initDataUnsafe
        
    Returns:
        {"language": "en" | "am"}
    """
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    
    if not user or not user.preferred_language:
        return {"language": "en"}
    
    return {"language": user.preferred_language}
