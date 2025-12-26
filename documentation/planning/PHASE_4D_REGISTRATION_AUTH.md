# Lab 4 Phase 4D: Registration & Cross-Interface Authentication

**Status:** 🚧 In Planning  
**Prerequisites:** Lab 4 Phases 4A-4C Complete  
**Estimated Effort:** 44 hours (4 weeks)  
**Reference:** `REGISTRATION_VERIFICATION_IDENTITY.md` (Voice-Ledger production system)

---

## Problem Statement

**Lab 4 Phases 4A-4C built:**
- ✅ Telegram bot with voice message processing
- ✅ ASR (Automatic Speech Recognition) - English + Amharic
- ✅ NLU (Natural Language Understanding) - Intent extraction
- ✅ Complete voice pipeline with Celery async processing

**Critical Missing Component:** Cross-interface authentication

**Users registered via Telegram CANNOT access:**
- **Web UI** - Campaign creation, admin dashboards, analytics
- **IVR** - Phone-based donations for feature phones (60% of Africa)
- **WhatsApp** - Alternative voice channel (future)

**Solution:** Implement Voice-Ledger's proven hybrid authentication pattern.

---

## Architecture Overview

### The Voice-Ledger Pattern

```
┌─────────────────────────────────────────────────┐
│         Telegram Bot (Primary Identity)          │
│  • /register → Language, role selection, PIN     │
│  • /set-pin → 4-digit PIN for web access        │
│  • Share Contact → Store phone for IVR           │
│  • Auto-approve: Donors (instant)                │
│  • Pending approval: Creators, Agents (admin)    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  PostgreSQL      │
         │  • users table   │
         │  • telegram_user_id (primary identity)   │
         │  • pin_hash (bcrypt, for web/IVR)       │
         │  • phone_number (for IVR lookup)        │
         │  • role (DONOR, CREATOR, AGENT, ADMIN)  │
         │  • is_approved (instant vs pending)     │
         └────┬────┬────┬───┘
              │    │    │
    ┌─────────┘    │    └─────────┐
    ▼              ▼              ▼
┌───────┐    ┌──────────┐    ┌──────┐
│Web UI │    │   IVR    │    │WhatsApp│
│       │    │ (Future) │    │(Future)│
│Login: │    │ Login:   │    │Login:  │
│@user  │    │ Phone#   │    │Phone#  │
│+PIN   │    │ +PIN(DTMF)    │+PIN    │
└───────┘    └──────────┘    └──────┘
```

**Key Principles:**
1. **Telegram is the source of truth** - All users register here first
2. **4-digit PIN** - Simple, memorable, works across all interfaces
3. **Role-based approval** - Donors instant, Creators/Agents need admin review
4. **Phone verification** - Optional, enables IVR access for feature phones
5. **Bcrypt hashing** - Industry-standard PIN security
6. **Account lockout** - 5 failed attempts = 30-minute lockout

---

## User Roles & Approval Flow

| Role | Default Approval | Features | PIN Required | Web Access | Registration Form |
|------|------------------|----------|--------------|------------|-------------------|
| **DONOR** | ✅ Instant | Voice donations, history, receipts | ❌ No | ❌ No | Language only |
| **CAMPAIGN_CREATOR** | ⏳ Admin approval | Create campaigns, view donations, request payouts | ✅ Yes | ✅ Yes | 7-question form |
| **FIELD_AGENT** | ⏳ Admin approval | GPS verification, impact reports | ✅ Yes | ✅ Yes | 7-question form |
| **SYSTEM_ADMIN** | Manual (database) | Approve registrations, system config | ✅ Yes | ✅ Yes | N/A |

**Rationale:**
- **Donors:** Low-friction onboarding, anyone can donate instantly
- **Campaign Creators:** Require vetting to prevent fraudulent campaigns
- **Field Agents:** Trusted role with verification authority
- **System Admin:** Platform operators only, created via database

---

## Database Schema Changes

### Migration: `lab_04_phase_4d_add_auth_fields.py`

```sql
-- Add authentication fields to users table
ALTER TABLE users ADD COLUMN telegram_user_id VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN telegram_username VARCHAR(100);
ALTER TABLE users ADD COLUMN telegram_first_name VARCHAR(100);
ALTER TABLE users ADD COLUMN telegram_last_name VARCHAR(100);
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'DONOR';
ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN approved_at TIMESTAMP;
ALTER TABLE users ADD COLUMN approved_by_admin_id INTEGER;

-- PIN authentication for web/IVR access
ALTER TABLE users ADD COLUMN pin_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN pin_set_at TIMESTAMP;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;

-- Phone verification for IVR access (optional)
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) UNIQUE;
ALTER TABLE users ADD COLUMN phone_verified_at TIMESTAMP;

-- Indexes for performance
CREATE INDEX idx_telegram_user_id ON users(telegram_user_id);
CREATE INDEX idx_role ON users(role);
CREATE INDEX idx_is_approved ON users(is_approved);
CREATE INDEX idx_phone_number ON users(phone_number);
```

### New Table: `pending_registrations`

```sql
CREATE TABLE pending_registrations (
    id SERIAL PRIMARY KEY,
    telegram_user_id VARCHAR(50) NOT NULL,
    telegram_username VARCHAR(100),
    telegram_first_name VARCHAR(100),
    telegram_last_name VARCHAR(100),
    
    -- Role request
    requested_role VARCHAR(50) NOT NULL,  -- 'CAMPAIGN_CREATOR' or 'FIELD_AGENT'
    
    -- Registration form data
    full_name VARCHAR(200),
    organization_name VARCHAR(200),  -- Campaign Creators
    location VARCHAR(200),
    phone_number VARCHAR(20),
    reason TEXT,
    
    -- Field Agent specific
    verification_experience TEXT,
    coverage_regions TEXT,
    has_gps_phone BOOLEAN,
    
    -- PIN (will be copied to users table on approval)
    pin_hash VARCHAR(255),
    
    -- Admin review
    status VARCHAR(20) DEFAULT 'PENDING',  -- 'PENDING', 'APPROVED', 'REJECTED'
    reviewed_by_admin_id INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pending_status ON pending_registrations(status);
CREATE INDEX idx_pending_telegram_user ON pending_registrations(telegram_user_id);
```

---

## Registration Flows

### 1. Donor Registration (Instant Approval)

**Command:** `/register` or `/start` (new users)

**Flow:**
```
1. User: /register
2. Bot: "Choose your language:
        🇬🇧 English
        🇪🇹 አማርኛ (Amharic)"
3. User: Selects language
4. Bot: "Select your role:
        🎁 Donor (instant access)
        📋 Campaign Creator (requires approval)
        🔍 Field Agent (requires approval)"
5. User: Taps "🎁 Donor"
6. Bot: ✅ "Registered! Send me a voice message:
        💬 'Show me education campaigns'
        💬 'Donate 50 dollars to Clean Water Kenya'"
```

**Database Action:**
```python
# Create user immediately (no pending approval)
user = User(
    telegram_user_id=str(user_id),
    telegram_username=username,
    telegram_first_name=first_name,
    telegram_last_name=last_name,
    preferred_language=language,  # 'en' or 'am'
    role='DONOR',
    is_approved=True,  # ✅ Instant approval
    approved_at=datetime.utcnow()
)
db.add(user)
db.commit()
```

**No PIN required** - Donors use Telegram only, no web access needed.

---

### 2. Campaign Creator Registration (Requires Admin Approval)

**Command:** `/register`

**Flow:**
```
1-3. Same as Donor (language selection)
4. User: Taps "📋 Campaign Creator"
5. Bot: "Let's set up your Campaign Creator account.
        
        📝 We'll ask you 7 quick questions.
        
        1️⃣ What's your full legal name?"
6. User: "John Doe"
7. Bot: "2️⃣ Organization name?"
8. User: "Hope Foundation Kenya"
9. Bot: "3️⃣ Location (city, country)?"
10. User: "Nairobi, Kenya"
11. Bot: "4️⃣ Phone number? (optional, for verification)"
12. User: "+254712345678" OR "Skip"
13. Bot: "5️⃣ Why do you want to create campaigns?"
14. User: "We run education programs for 500 children in Kibera."
15. Bot: "6️⃣ Set a 4-digit PIN for web access:
         
         ℹ️ This PIN lets you login to https://trustvoice.app
         
         Enter 4 digits:"
16. User: 1234
17. Bot: "7️⃣ Confirm your PIN:"
18. User: 1234
19. Bot: "✅ Registration submitted!
         
         ⏳ Admin will review within 24 hours.
         We'll notify you here when approved.
         
         Questions? Reply to this message."
```

**Redis Session Management:**
```python
# State machine for multi-step registration
session = {
    'state': 'awaiting_full_name',
    'role': 'CAMPAIGN_CREATOR',
    'language': 'en',
    'data': {}
}
redis_client.setex(f'reg:{user_id}', 3600, json.dumps(session))  # 1-hour TTL
```

**Database Action:**
```python
# Store in pending_registrations (NOT users table yet)
pending = PendingRegistration(
    telegram_user_id=str(user_id),
    telegram_username=username,
    telegram_first_name=first_name,
    telegram_last_name=last_name,
    requested_role='CAMPAIGN_CREATOR',
    full_name='John Doe',
    organization_name='Hope Foundation Kenya',
    location='Nairobi, Kenya',
    phone_number='+254712345678',
    reason='We run education programs for 500 children in Kibera.',
    pin_hash=bcrypt.hashpw('1234'.encode(), bcrypt.gensalt()).decode(),
    status='PENDING'
)
db.add(pending)
db.commit()

# Notify all admins
notify_admins(
    message=f"📋 New Campaign Creator registration:\n"
            f"Name: John Doe\n"
            f"Org: Hope Foundation Kenya\n"
            f"Location: Nairobi, Kenya\n\n"
            f"/admin-approve {pending.id}"
)
```

---

### 3. Field Agent Registration (Requires Admin Approval)

**Command:** `/register`

**Similar Flow to Campaign Creator, with different questions:**

```
1-4. Same (language + role selection)
5. Bot: "1️⃣ What's your full legal name?"
6. User: "Jane Smith"
7. Bot: "2️⃣ Location (where can you verify campaigns)?"
8. User: "Mombasa and surrounding areas, Kenya"
9. Bot: "3️⃣ Phone number?"
10. User: "+254723456789"
11. Bot: "4️⃣ Do you have GPS-enabled smartphone?"
12. User: "Yes"
13. Bot: "5️⃣ Describe your verification experience:"
14. User: "5 years working with Red Cross, verified 50+ projects"
15. Bot: "6️⃣ Set a 4-digit PIN:"
16-18. PIN setup (same as Campaign Creator)
19. Bot: "✅ Registration submitted! Admin will review."
```

**Database Action:**
```python
pending = PendingRegistration(
    telegram_user_id=str(user_id),
    requested_role='FIELD_AGENT',
    full_name='Jane Smith',
    location='Mombasa and surrounding areas, Kenya',
    phone_number='+254723456789',
    has_gps_phone=True,
    verification_experience='5 years working with Red Cross...',
    pin_hash=bcrypt.hashpw('5678'.encode(), bcrypt.gensalt()).decode(),
    status='PENDING'
)
db.add(pending)
db.commit()
```

---

## Admin Approval System

### Telegram Admin Commands

**File:** `voice/telegram/admin_commands.py`

**Role Check Decorator:**
```python
def require_admin(func):
    """Decorator to enforce admin-only access"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        with get_db() as db:
            user = db.query(User).filter_by(
                telegram_user_id=str(user_id)
            ).first()
            
            if not user or user.role != 'SYSTEM_ADMIN':
                await update.message.reply_text(
                    "❌ Admin access required.\n"
                    "This command is restricted to system administrators."
                )
                return
            
            return await func(update, context)
    return wrapper
```

**1. View Pending Registrations:**
```python
@require_admin
async def admin_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin-requests - View all pending registrations.
    """
    with get_db() as db:
        pending_list = db.query(PendingRegistration).filter_by(
            status='PENDING'
        ).order_by(PendingRegistration.created_at.desc()).all()
        
        if not pending_list:
            await update.message.reply_text("✅ No pending registrations!")
            return
        
        message = f"📋 Pending Registrations ({len(pending_list)})\n\n"
        
        for idx, pending in enumerate(pending_list, 1):
            hours_ago = (datetime.utcnow() - pending.created_at).seconds // 3600
            
            message += f"{idx}️⃣ {pending.requested_role}\n"
            message += f"   Name: {pending.full_name}\n"
            
            if pending.organization_name:
                message += f"   Org: {pending.organization_name}\n"
            
            message += f"   Location: {pending.location}\n"
            message += f"   Reason: {pending.reason[:100]}...\n"
            message += f"   Submitted: {hours_ago}h ago\n"
            message += f"   \n"
            message += f"   ✅ /admin-approve {pending.id}\n"
            message += f"   ❌ /admin-reject {pending.id}\n\n"
        
        await update.message.reply_text(message)
```

**2. Approve Registration:**
```python
@require_admin
async def admin_approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin-approve <id> - Approve pending registration.
    
    Actions:
    1. Move from pending_registrations → users
    2. Copy all fields including PIN hash
    3. Set is_approved = True
    4. Send Telegram notification to user
    """
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /admin-approve <id>")
        return
    
    pending_id = int(context.args[0])
    admin_user_id = update.effective_user.id
    
    with get_db() as db:
        # Get admin user
        admin = db.query(User).filter_by(
            telegram_user_id=str(admin_user_id)
        ).first()
        
        # Get pending registration
        pending = db.query(PendingRegistration).filter_by(
            id=pending_id,
            status='PENDING'
        ).first()
        
        if not pending:
            await update.message.reply_text("❌ Registration not found or already processed")
            return
        
        # Create user from pending registration
        new_user = User(
            telegram_user_id=pending.telegram_user_id,
            telegram_username=pending.telegram_username,
            telegram_first_name=pending.telegram_first_name,
            telegram_last_name=pending.telegram_last_name,
            role=pending.requested_role,
            preferred_language='en',  # Default, user can change
            pin_hash=pending.pin_hash,  # Copy PIN hash
            pin_set_at=datetime.utcnow(),
            phone_number=pending.phone_number,
            is_approved=True,
            approved_at=datetime.utcnow(),
            approved_by_admin_id=admin.id
        )
        db.add(new_user)
        
        # Update pending status
        pending.status = 'APPROVED'
        pending.reviewed_by_admin_id = admin.id
        pending.reviewed_at = datetime.utcnow()
        
        db.commit()
        
        # Notify user
        bot = context.bot
        await bot.send_message(
            chat_id=int(pending.telegram_user_id),
            text=(
                f"🎉 Your registration is approved!\n\n"
                f"Role: {pending.requested_role}\n\n"
                f"You can now:\n"
                f"• Login to web UI: https://trustvoice.app/login\n"
                f"• Username: @{pending.telegram_username}\n"
                f"• PIN: (your 4-digit PIN)\n\n"
                f"Need help? Send /help"
            )
        )
        
        await update.message.reply_text(
            f"✅ Approved: {pending.full_name}\n"
            f"Role: {pending.requested_role}\n"
            f"User notified via Telegram"
        )
```

**3. Reject Registration:**
```python
@require_admin
async def admin_reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin-reject <id> <reason> - Reject pending registration.
    """
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /admin-reject <id> <reason>\n"
            "Example: /admin-reject 5 Insufficient verification experience"
        )
        return
    
    pending_id = int(context.args[0])
    reason = ' '.join(context.args[1:])
    admin_user_id = update.effective_user.id
    
    with get_db() as db:
        admin = db.query(User).filter_by(
            telegram_user_id=str(admin_user_id)
        ).first()
        
        pending = db.query(PendingRegistration).filter_by(
            id=pending_id,
            status='PENDING'
        ).first()
        
        if not pending:
            await update.message.reply_text("❌ Registration not found")
            return
        
        # Update status
        pending.status = 'REJECTED'
        pending.rejection_reason = reason
        pending.reviewed_by_admin_id = admin.id
        pending.reviewed_at = datetime.utcnow()
        db.commit()
        
        # Notify user
        bot = context.bot
        await bot.send_message(
            chat_id=int(pending.telegram_user_id),
            text=(
                f"❌ Your registration was not approved.\n\n"
                f"Reason: {reason}\n\n"
                f"You can apply again with improved information:\n"
                f"/register\n\n"
                f"Questions? Reply to this message."
            )
        )
        
        await update.message.reply_text(
            f"✅ Rejected: {pending.full_name}\n"
            f"Reason: {reason}\n"
            f"User notified"
        )
```

---

## PIN Authentication

### File: `services/auth_service.py`

**1. PIN Hashing (Bcrypt):**
```python
import bcrypt

def hash_pin(pin: str) -> str:
    """
    Hash PIN with bcrypt.
    
    Why bcrypt:
    - Slow by design (prevents brute force)
    - Auto-salting (unique hash even for same PIN)
    - Industry standard (OWASP recommended)
    
    Args:
        pin: 4-digit PIN string
    
    Returns:
        Bcrypt hash (60 characters)
    """
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = ~250ms
    hashed = bcrypt.hashpw(pin.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_pin(pin: str, pin_hash: str) -> bool:
    """
    Verify PIN against stored hash.
    
    Args:
        pin: Plain 4-digit PIN
        pin_hash: Bcrypt hash from database
    
    Returns:
        True if PIN matches, False otherwise
    """
    try:
        return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"PIN verification error: {e}")
        return False
```

**2. Account Lockout:**
```python
def check_login_attempts(user: User) -> tuple[bool, Optional[str]]:
    """
    Check if user account is locked due to failed login attempts.
    
    Rules:
    - 5 consecutive failures = 30-minute lockout
    - Lock expires automatically
    - Reset counter on successful login
    
    Args:
        user: User model instance
    
    Returns:
        (allowed, error_message)
    """
    # Check if currently locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = (user.locked_until - datetime.utcnow()).seconds // 60
        return False, f"Account locked. Try again in {minutes_left} minutes."
    
    # Clear expired lock
    if user.locked_until and user.locked_until <= datetime.utcnow():
        user.locked_until = None
        user.failed_login_attempts = 0
    
    return True, None


def record_failed_login(user: User, db: Session):
    """Record failed login and lock if threshold reached."""
    user.failed_login_attempts += 1
    
    if user.failed_login_attempts >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        logger.warning(
            f"Account locked: {user.telegram_username} "
            f"(5 failed attempts)"
        )
    
    db.commit()


def reset_login_attempts(user: User, db: Session):
    """Reset failed attempts on successful login."""
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.commit()
```

**3. JWT Token Generation:**
```python
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Generate with: openssl rand -hex 32
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 15

def generate_jwt_token(user: User) -> str:
    """
    Generate JWT token for web UI session.
    
    Payload:
    - user_id: Database primary key
    - role: User role (for authorization)
    - telegram_username: Display name
    - exp: Expiry timestamp (15 minutes)
    
    Args:
        user: User model instance
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user.id,
        'role': user.role,
        'telegram_username': user.telegram_username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict
    
    Raises:
        jwt.ExpiredSignatureError: Token expired
        jwt.InvalidTokenError: Invalid token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired. Please login again.")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token.")
```

---

## Web UI Login Endpoint

### File: `voice/routers/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User
from services.auth_service import (
    verify_pin,
    check_login_attempts,
    record_failed_login,
    reset_login_attempts,
    generate_jwt_token
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str  # Telegram username (without @)
    pin: str       # 4-digit PIN


class LoginResponse(BaseModel):
    """Login response schema"""
    token: str
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login for Campaign Creators and Field Agents.
    
    Returns JWT token for web UI access.
    
    Security:
    - Bcrypt PIN verification
    - Account lockout (5 attempts = 30 min)
    - JWT token (15-minute expiry)
    
    Example:
        POST /auth/login
        {
            "username": "johndoe",
            "pin": "1234"
        }
    """
    # Lookup user by Telegram username
    user = db.query(User).filter_by(
        telegram_username=request.username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Register on Telegram: /register"
        )
    
    # Check if approved
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration pending approval. Admin will review within 24 hours."
        )
    
    # Check if PIN is set
    if not user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN not set. Use /set-pin on Telegram."
        )
    
    # Check account lockout
    allowed, error = check_login_attempts(user)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error
        )
    
    # Verify PIN
    if not verify_pin(request.pin, user.pin_hash):
        record_failed_login(user, db)
        
        # Custom message after 3 failures
        if user.failed_login_attempts >= 3:
            detail = (
                f"Invalid PIN. "
                f"{5 - user.failed_login_attempts} attempts remaining "
                f"before 30-minute lockout."
            )
        else:
            detail = "Invalid PIN"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
    
    # Success!
    reset_login_attempts(user, db)
    
    # Generate JWT token
    token = generate_jwt_token(user)
    
    return LoginResponse(
        token=token,
        user={
            "id": user.id,
            "telegram_username": user.telegram_username,
            "telegram_first_name": user.telegram_first_name,
            "role": user.role,
            "preferred_language": user.preferred_language
        }
    )


@router.get("/me")
async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get current user info from JWT token.
    
    Headers:
        Authorization: Bearer <token>
    """
    from services.auth_service import verify_jwt_token
    
    try:
        payload = verify_jwt_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    user = db.query(User).filter_by(id=payload['user_id']).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "telegram_username": user.telegram_username,
        "role": user.role,
        "preferred_language": user.preferred_language,
        "phone_verified": bool(user.phone_verified_at)
    }
```

---

## Telegram PIN Commands

### File: `voice/telegram/pin_commands.py`

**State Constants:**
```python
# PIN setup states
STATE_ENTER_NEW_PIN = "enter_new_pin"
STATE_CONFIRM_PIN = "confirm_pin"

# Change PIN states
STATE_ENTER_OLD_PIN = "enter_old_pin"
STATE_ENTER_NEW_PIN_CHANGE = "enter_new_pin_change"
STATE_CONFIRM_NEW_PIN_CHANGE = "confirm_new_pin_change"
```

**1. Set PIN (First Time):**
```python
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from voice.telegram.session_manager import get_session, set_session, delete_session
from services.auth_service import hash_pin

async def set_pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /set-pin - Set PIN for web UI access.
    
    Only for Campaign Creators and Field Agents.
    Donors don't need PIN (Telegram-only access).
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_user_id=str(user_id)
        ).first()
        
        if not user:
            await update.message.reply_text(
                "❌ Not registered. Use /register first."
            )
            return ConversationHandler.END
        
        if user.role == 'DONOR':
            await update.message.reply_text(
                "ℹ️ Donors don't need a PIN.\n\n"
                "PIN is only for Campaign Creators and Field Agents "
                "who need web access.\n\n"
                "You can donate via voice commands here on Telegram! 🎤"
            )
            return ConversationHandler.END
        
        if user.pin_hash:
            await update.message.reply_text(
                "⚠️ You already have a PIN set.\n\n"
                "Use /change-pin to change it."
            )
            return ConversationHandler.END
    
    # Start PIN setup flow
    set_session(user_id, {'state': STATE_ENTER_NEW_PIN}, prefix='pin')
    
    await update.message.reply_text(
        "🔐 Let's set up your PIN for web access.\n\n"
        "Your PIN must be:\n"
        "• Exactly 4 digits\n"
        "• Easy to remember\n"
        "• Not sequential (e.g., 1234)\n"
        "• Not repeated (e.g., 1111)\n\n"
        "Enter your new PIN:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return STATE_ENTER_NEW_PIN


async def handle_enter_new_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new PIN entry"""
    pin = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Delete message immediately (security)
    await update.message.delete()
    
    # Validate PIN format
    if not pin.isdigit() or len(pin) != 4:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Invalid PIN. Must be exactly 4 digits.\n\nTry again:"
        )
        return STATE_ENTER_NEW_PIN
    
    # Check weak PINs
    if pin in ['0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999']:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Weak PIN (repeated digits).\n\nChoose a different PIN:"
        )
        return STATE_ENTER_NEW_PIN
    
    if pin in ['1234', '4321', '0123', '5678', '8765']:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Weak PIN (sequential digits).\n\nChoose a different PIN:"
        )
        return STATE_ENTER_NEW_PIN
    
    # Store PIN temporarily
    session = get_session(user_id, prefix='pin')
    session['pin'] = pin
    session['state'] = STATE_CONFIRM_PIN
    set_session(user_id, session, prefix='pin')
    
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Good PIN!\n\nConfirm your PIN:"
    )
    
    return STATE_CONFIRM_PIN


async def handle_confirm_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PIN confirmation"""
    pin_confirm = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Delete message immediately (security)
    await update.message.delete()
    
    session = get_session(user_id, prefix='pin')
    original_pin = session.get('pin')
    
    if pin_confirm != original_pin:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ PINs don't match.\n\n"
                "Let's start over. /set-pin"
            )
        )
        delete_session(user_id, prefix='pin')
        return ConversationHandler.END
    
    # Hash and save PIN
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_user_id=str(user_id)
        ).first()
        
        user.pin_hash = hash_pin(original_pin)
        user.pin_set_at = datetime.utcnow()
        db.commit()
    
    delete_session(user_id, prefix='pin')
    
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "✅ PIN set successfully!\n\n"
            "🌐 You can now login to the web UI:\n"
            "https://trustvoice.app/login\n\n"
            "Username: @" + update.effective_user.username + "\n"
            "PIN: (your 4-digit PIN)\n\n"
            "⚠️ Keep your PIN secret!\n"
            "📝 Use /change-pin if you need to change it."
        )
    )
    
    return ConversationHandler.END


# ConversationHandler setup
set_pin_handler = ConversationHandler(
    entry_points=[CommandHandler('set-pin', set_pin_command)],
    states={
        STATE_ENTER_NEW_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_enter_new_pin)],
        STATE_CONFIRM_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm_pin)]
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)
```

**2. Change PIN:**
```python
async def change_pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /change-pin - Change existing PIN.
    
    Requires old PIN verification for security.
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_user_id=str(user_id)
        ).first()
        
        if not user or not user.pin_hash:
            await update.message.reply_text(
                "❌ No PIN set. Use /set-pin first."
            )
            return ConversationHandler.END
    
    set_session(user_id, {'state': STATE_ENTER_OLD_PIN}, prefix='pin')
    
    await update.message.reply_text(
        "🔐 Change PIN\n\n"
        "First, verify your current PIN:"
    )
    
    return STATE_ENTER_OLD_PIN


async def handle_enter_old_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify old PIN before allowing change"""
    old_pin = update.message.text.strip()
    user_id = update.effective_user.id
    
    await update.message.delete()
    
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_user_id=str(user_id)
        ).first()
        
        if not verify_pin(old_pin, user.pin_hash):
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Incorrect PIN. Try again or /cancel"
            )
            return STATE_ENTER_OLD_PIN
    
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ Verified!\n\nEnter your new PIN (4 digits):"
    )
    
    return STATE_ENTER_NEW_PIN_CHANGE


# Continue with similar flow as set-pin...
```

---

## Phone Verification (IVR Access)

### File: `voice/telegram/phone_verification.py`

```python
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

async def verify_phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /verify-phone - Verify phone number for IVR access.
    
    Uses Telegram's native contact sharing (secure, no SMS costs).
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_user_id=str(user_id)
        ).first()
        
        if not user:
            await update.message.reply_text("❌ Not registered. Use /register")
            return
        
        if user.phone_verified_at:
            await update.message.reply_text(
                f"✅ Phone already verified: {user.phone_number}\n\n"
                f"You can call TrustVoice IVR (future feature)."
            )
            return
    
    # Native Telegram contact sharing
    keyboard = [
        [KeyboardButton("📞 Share Phone Number", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "📞 Verify your phone number for IVR access.\n\n"
        "Why verify?\n"
        "• Call TrustVoice toll-free number\n"
        "• Donate via USSD for feature phones\n"
        "• No smartphone required\n\n"
        "Click the button below:",
        reply_markup=reply_markup
    )


async def handle_contact_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle contact sharing.
    
    Telegram provides verified phone number (E.164 format).
    """
    contact = update.message.contact
    user_id = update.effective_user.id
    phone_number = contact.phone_number
    
    # Validate: Contact must be from user themselves
    if contact.user_id != user_id:
        await update.message.reply_text(
            "⚠️ Please share YOUR OWN contact, not someone else's."
        )
        return
    
    with get_db() as db:
        user = db.query(User).filter_by(
            telegram_user_id=str(user_id)
        ).first()
        
        # Check if phone already used by another user
        existing = db.query(User).filter_by(
            phone_number=phone_number
        ).first()
        
        if existing and existing.id != user.id:
            await update.message.reply_text(
                "❌ This phone number is already registered to another account."
            )
            return
        
        # Store phone number
        user.phone_number = phone_number
        user.phone_verified_at = datetime.utcnow()
        db.commit()
    
    await update.message.reply_text(
        f"✅ Phone verified: {phone_number}\n\n"
        f"🎉 You can now access TrustVoice via:\n"
        f"• Telegram (voice & text) ✅\n"
        f"• Web UI (if Campaign Creator) ✅\n"
        f"• IVR phone system (coming soon) 🔜\n\n"
        f"Questions? Send /help"
    )
```

---

## Implementation Checklist

### Week 1: Core Registration (16 hours)
- [ ] **Database Migration** (2 hours)
  - [ ] Create migration: `lab_04_phase_4d_add_auth_fields.py`
  - [ ] Add auth fields to users table
  - [ ] Create pending_registrations table
  - [ ] Run migration: `alembic upgrade head`
  - [ ] Verify schema changes

- [ ] **Update Models** (2 hours)
  - [ ] Update `database/models.py`:
    - [ ] Add telegram fields to User model
    - [ ] Add role, approval fields
    - [ ] Add PIN authentication fields
    - [ ] Add phone verification fields
  - [ ] Create PendingRegistration model
  - [ ] Add relationships and indexes

- [ ] **Auth Service** (3 hours)
  - [ ] Create `services/auth_service.py`
  - [ ] Implement `hash_pin()` - bcrypt with 12 rounds
  - [ ] Implement `verify_pin()` - constant-time comparison
  - [ ] Implement `check_login_attempts()` - lockout logic
  - [ ] Implement `record_failed_login()` - increment attempts
  - [ ] Implement `reset_login_attempts()` - on success
  - [ ] Implement `generate_jwt_token()` - 15-min expiry
  - [ ] Implement `verify_jwt_token()` - decode + validate
  - [ ] Unit tests for all functions

- [ ] **Registration Flow** (9 hours)
  - [ ] Update `/start` command:
    - [ ] Check if user exists in database
    - [ ] Show main menu for existing users
    - [ ] Redirect to `/register` for new users
  - [ ] Create `/register` command:
    - [ ] Language selection (reuse existing)
    - [ ] Role selection buttons (Donor/Creator/Agent)
    - [ ] Implement Donor instant registration
    - [ ] Implement Creator multi-step form (7 questions)
    - [ ] Implement Agent multi-step form (7 questions)
    - [ ] Redis session management (1-hour TTL)
    - [ ] PIN setup flow (only for Creator/Agent)
    - [ ] Store in pending_registrations (Creator/Agent)
    - [ ] Create user record (Donor only)
  - [ ] Test: Donor instant registration
  - [ ] Test: Creator pending registration
  - [ ] Test: Session persistence across messages

### Week 2: PIN & Web Login (12 hours)
- [ ] **Web Auth Endpoint** (5 hours)
  - [ ] Create `voice/routers/auth.py`
  - [ ] Implement `POST /auth/login`:
    - [ ] Lookup user by telegram_username
    - [ ] Check is_approved status
    - [ ] Check PIN hash exists
    - [ ] Verify account not locked
    - [ ] Verify PIN with bcrypt
    - [ ] Record failed attempts
    - [ ] Lock account after 5 failures
    - [ ] Generate JWT token on success
    - [ ] Reset attempts on success
    - [ ] Return token + user info
  - [ ] Implement `GET /auth/me`:
    - [ ] Extract token from Authorization header
    - [ ] Verify and decode JWT
    - [ ] Return current user info
  - [ ] Pydantic schemas (LoginRequest, LoginResponse)
  - [ ] Test: Successful login
  - [ ] Test: Invalid PIN
  - [ ] Test: Account lockout

- [ ] **Telegram PIN Commands** (7 hours)
  - [ ] Create `voice/telegram/pin_commands.py`
  - [ ] Implement `/set-pin` command:
    - [ ] Check user exists and role
    - [ ] Check PIN not already set
    - [ ] Conversation state: enter PIN
    - [ ] Validate PIN format (4 digits)
    - [ ] Check weak PINs (1234, 1111, etc.)
    - [ ] Delete PIN message immediately (security)
    - [ ] Conversation state: confirm PIN
    - [ ] Check PINs match
    - [ ] Hash and store PIN
    - [ ] Send web login instructions
  - [ ] Implement `/change-pin` command:
    - [ ] Verify old PIN first
    - [ ] Follow same flow as set-pin
  - [ ] Create ConversationHandler
  - [ ] Test: Set PIN flow
  - [ ] Test: Change PIN flow
  - [ ] Test: Weak PIN rejection

### Week 3: Admin Approval (10 hours)
- [ ] **Admin Commands** (8 hours)
  - [ ] Create `voice/telegram/admin_commands.py`
  - [ ] Create `@require_admin` decorator:
    - [ ] Check user exists
    - [ ] Check role is SYSTEM_ADMIN
    - [ ] Return error if unauthorized
  - [ ] Implement `/admin-requests` command:
    - [ ] Query pending_registrations (status=PENDING)
    - [ ] Format list with numbered items
    - [ ] Show key info (name, org, reason, time)
    - [ ] Show approve/reject commands
    - [ ] Pagination if >10 requests
  - [ ] Implement `/admin-approve <id>` command:
    - [ ] Validate pending request exists
    - [ ] Create user from pending data
    - [ ] Copy all fields including PIN hash
    - [ ] Set is_approved=True, approved_at, approved_by
    - [ ] Update pending status=APPROVED
    - [ ] Send Telegram notification to user
    - [ ] Send confirmation to admin
  - [ ] Implement `/admin-reject <id> <reason>` command:
    - [ ] Validate pending request exists
    - [ ] Update pending status=REJECTED
    - [ ] Store rejection_reason
    - [ ] Send Telegram notification to user
    - [ ] Send confirmation to admin
  - [ ] Test: View pending requests
  - [ ] Test: Approve registration
  - [ ] Test: Reject registration
  - [ ] Test: User notification on approval
  - [ ] Test: User notification on rejection

- [ ] **Admin Notifications** (2 hours)
  - [ ] Send notification when new registration submitted
  - [ ] Broadcast to all SYSTEM_ADMIN users
  - [ ] Include quick approve/reject buttons
  - [ ] Test notification delivery

### Week 4: Phone Verification (6 hours)
- [ ] **Phone Verification** (5 hours)
  - [ ] Create `voice/telegram/phone_verification.py`
  - [ ] Implement `/verify-phone` command:
    - [ ] Check user exists
    - [ ] Check not already verified
    - [ ] Show "Share Contact" button
    - [ ] Explain IVR benefits
  - [ ] Implement contact share handler:
    - [ ] Validate contact is from user (not someone else)
    - [ ] Check phone not already used
    - [ ] Store phone_number (E.164 format)
    - [ ] Set phone_verified_at timestamp
    - [ ] Send confirmation message
  - [ ] Test: Share contact flow
  - [ ] Test: Duplicate phone rejection

- [ ] **Integration Testing** (1 hour)
  - [ ] End-to-end: Register → Approve → Set PIN → Login
  - [ ] Test all user roles
  - [ ] Test error cases

### Week 5: Testing & Documentation (6 hours)
- [ ] **Test Suite** (4 hours)
  - [ ] Create `tests/test_registration_flow.py`:
    - [ ] Test donor instant registration
    - [ ] Test creator pending registration
    - [ ] Test agent pending registration
    - [ ] Test role validation
  - [ ] Create `tests/test_pin_authentication.py`:
    - [ ] Test PIN hashing
    - [ ] Test PIN verification
    - [ ] Test weak PIN rejection
    - [ ] Test account lockout
  - [ ] Create `tests/test_admin_approval.py`:
    - [ ] Test approve workflow
    - [ ] Test reject workflow
    - [ ] Test notifications
  - [ ] Create `tests/test_web_login.py`:
    - [ ] Test successful login
    - [ ] Test invalid credentials
    - [ ] Test account lockout
    - [ ] Test JWT token generation

- [ ] **Documentation** (2 hours)
  - [ ] Update [LAB_04_VOICE_AI_INTEGRATION.md](LAB_04_VOICE_AI_INTEGRATION.md)
  - [ ] Add Phase 4D section
  - [ ] API documentation for auth endpoints
  - [ ] User guide: "How to register as Campaign Creator"
  - [ ] Admin guide: "How to approve registrations"

---

## Success Criteria

**Phase 4D Complete When:**
- [x] All database migrations applied successfully
- [x] Donor registration works (instant approval)
- [x] Campaign Creator registration works (pending approval)
- [x] Field Agent registration works (pending approval)
- [x] Admin can view pending registrations
- [x] Admin can approve/reject registrations
- [x] Users receive Telegram notifications
- [x] PIN setup works via `/set-pin`
- [x] Web login endpoint works with username + PIN
- [x] Account lockout works (5 attempts = 30 min)
- [x] JWT token generation and validation works
- [x] Phone verification works via contact sharing
- [x] All tests passing (50+ tests)
- [x] Documentation complete

---

## Next: Phase 4E - Voice Campaign Creation

**After Phase 4D:**
- Multi-turn conversational interview
- AI content generation (GPT-4)
- Campaign page HTML generation
- GPS photo upload (EUDR compliance)
- Budget breakdown voice input
- Admin campaign approval

**Reference:** `documentation/VoiceFirst_Interface_Design.md`

---

## Next: Phase 4F - KYC & Identity Verification

**After Phase 4E:**
- KYC tier system (Tier 1/2/3 based on amount)
- Field Agent verification tools
- GPS photo verification with deforestation check
- Document OCR for legal docs
- Admin review interface

**Reference:** `documentation/REGISTRATION_VERIFICATION_IDENTITY.md`

---

**Phase 4D Status:** 🚧 In Planning  
**Total Estimated Time:** 44 hours (4 weeks)  
**Dependencies:** Lab 4 Phases 4A-4C Complete ✅

