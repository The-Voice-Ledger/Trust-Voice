"""
Authentication Service

Handles user authentication, password hashing, PIN authentication, and JWT tokens.

Supports two authentication methods:
1. Password-based (for admin users)
2. PIN-based (for Telegram users accessing web/IVR)
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.critical("❌ JWT_SECRET_KEY (or SECRET_KEY) environment variable is required!")
    raise RuntimeError("JWT_SECRET_KEY environment variable is required. Set JWT_SECRET_KEY or SECRET_KEY.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes default

# PIN Authentication settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dict containing user info (user_id, email, role)
        expires_delta: Optional custom expiration time
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ============================================================================
# PIN Authentication Functions (for Telegram users)
# ============================================================================

def hash_pin(pin: str) -> str:
    """
    Hash PIN with bcrypt (same as password, for consistency).
    
    Args:
        pin: 4-digit PIN string
    
    Returns:
        Bcrypt hash string
    """
    if not pin or not pin.isdigit() or len(pin) != 4:
        raise ValueError("PIN must be exactly 4 digits")
    
    return pwd_context.hash(pin)


def verify_pin(pin: str, pin_hash: str) -> bool:
    """
    Verify PIN against stored hash.
    
    Args:
        pin: Plain 4-digit PIN
        pin_hash: Bcrypt hash from database
    
    Returns:
        True if PIN matches
    """
    try:
        return pwd_context.verify(pin, pin_hash)
    except Exception as e:
        logger.error(f"PIN verification error: {e}")
        return False


def check_login_attempts(user) -> Tuple[bool, Optional[str]]:
    """
    Check if user account is locked.
    
    Returns:
        (allowed, error_message)
    """
    if user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = (user.locked_until - datetime.utcnow()).seconds // 60
        return False, f"Account locked. Try again in {minutes_left} minutes."
    
    # Clear expired lock
    if user.locked_until and user.locked_until <= datetime.utcnow():
        user.locked_until = None
        user.failed_login_attempts = 0
    
    return True, None


def record_failed_login(user, db: Session) -> None:
    """Record failed login and lock if threshold reached."""
    user.failed_login_attempts += 1
    
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        logger.warning(f"Account locked: {user.telegram_username} ({MAX_FAILED_ATTEMPTS} attempts)")
    
    db.commit()


def reset_login_attempts(user, db: Session) -> None:
    """Reset failed attempts on successful login."""
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.commit()


def is_weak_pin(pin: str) -> Tuple[bool, Optional[str]]:
    """
    Check if PIN is weak.
    
    Returns:
        (is_weak, reason)
    """
    # Repeated digits
    if pin in ['0000', '1111', '2222', '3333', '4444', 
               '5555', '6666', '7777', '8888', '9999']:
        return True, "Repeated digits"
    
    # Sequential digits
    if pin in ['0123', '1234', '2345', '3456', '4567', '5678', '6789',
               '3210', '4321', '5432', '6543', '7654', '8765', '9876']:
        return True, "Sequential digits"
    
    return False, None