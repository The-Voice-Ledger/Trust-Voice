# Registration, Verification & Identity System

**Complete guide to user registration, verification, and identity management across all channels**

Last Updated: December 23, 2025  
Version: 1.8 (Production)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Identity Architecture](#identity-architecture)
3. [Registration Flow](#registration-flow)
4. [Multi-Channel Support](#multi-channel-support)
5. [Verification System](#verification-system)
6. [Authentication & Security](#authentication--security)
7. [Role-Based Access Control](#role-based-access-control)
8. [Admin Approval Workflow](#admin-approval-workflow)
9. [Adapting for Trust-Voice](#adapting-for-trust-voice)

---

## System Overview

Voice Ledger implements a comprehensive registration and verification system that:

- **Auto-generates DIDs** (Decentralized Identifiers) for all users
- **Zero-friction onboarding** - farmers don't manage private keys
- **Multi-channel support** - Telegram, IVR, Web UI
- **Role-based access** - Farmer, Cooperative, Exporter, Buyer, Admin
- **PIN authentication** - 4-digit PIN for web UI access
- **GPS photo verification** - EUDR compliance for farmers
- **Admin approval** - Non-farmer roles require approval
- **Session persistence** - Redis-backed, survives server restarts

**Key Principle:** Make blockchain-grade identity as easy as WhatsApp.

---

## Identity Architecture

### Decentralized Identifiers (DIDs)

Every user gets a **W3C-compliant DID** using the `did:key` method with Ed25519 cryptography:

```
did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK
```

**Components:**
- **DID**: Public identifier (shareable)
- **Public Key**: For signature verification
- **Private Key**: Encrypted, stored in database
- **Encryption**: Fernet symmetric encryption with app secret

### Database Schema

**`user_identities` Table:**

```sql
CREATE TABLE user_identities (
    id SERIAL PRIMARY KEY,
    telegram_user_id VARCHAR(50) UNIQUE NOT NULL,
    telegram_username VARCHAR(100),
    telegram_first_name VARCHAR(100),
    telegram_last_name VARCHAR(100),
    
    -- Auto-generated DID identity
    did VARCHAR(200) UNIQUE NOT NULL,
    encrypted_private_key TEXT NOT NULL,
    public_key VARCHAR(100) NOT NULL,
    
    -- Contact & location
    gln VARCHAR(13),  -- GS1 Global Location Number
    phone_number VARCHAR(20) UNIQUE,
    phone_verified_at TIMESTAMP,
    
    -- Role & organization
    role VARCHAR(50) DEFAULT 'FARMER',  -- FARMER, COOPERATIVE_MANAGER, EXPORTER, BUYER, SYSTEM_ADMIN
    organization_id INTEGER REFERENCES organizations(id),
    is_approved BOOLEAN DEFAULT TRUE,
    approved_at TIMESTAMP,
    approved_by_admin_id INTEGER,
    
    -- Language preference (conversational AI)
    preferred_language VARCHAR(2) DEFAULT 'en' NOT NULL,  -- 'en' or 'am'
    language_set_at TIMESTAMP,
    
    -- PIN authentication (web UI)
    pin_hash VARCHAR(255),  -- Bcrypt hash
    pin_set_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_telegram_user_id ON user_identities(telegram_user_id);
CREATE INDEX idx_did ON user_identities(did);
CREATE INDEX idx_role ON user_identities(role);
CREATE INDEX idx_is_approved ON user_identities(is_approved);
CREATE INDEX idx_phone_number ON user_identities(phone_number);
```

### Auto-Generation Flow

**File:** `ssi/user_identity.py`

```python
def get_or_create_user_identity(telegram_user_id, telegram_username, db_session):
    """
    Get existing user or create new one with auto-generated DID.
    
    Zero-friction onboarding: users don't manage keys.
    """
    # Check if user exists
    user = db_session.query(UserIdentity).filter_by(
        telegram_user_id=str(telegram_user_id)
    ).first()
    
    if user:
        # Update last active
        user.last_active_at = datetime.utcnow()
        db_session.commit()
        return {"did": user.did, "created": False}
    
    # Generate new DID
    identity = generate_did_key()  # Ed25519 key pair
    
    # Encrypt private key
    encryption_key = _get_encryption_key()  # From app secret
    fernet = Fernet(encryption_key)
    encrypted_private_key = fernet.encrypt(identity["private_key"].encode())
    
    # Create user record
    new_user = UserIdentity(
        telegram_user_id=str(telegram_user_id),
        telegram_username=telegram_username,
        did=identity["did"],
        encrypted_private_key=encrypted_private_key.decode(),
        public_key=identity["public_key"],
        role='FARMER',  # Default role
        is_approved=True  # Farmers auto-approved
    )
    
    db_session.add(new_user)
    db_session.commit()
    
    return {"did": new_user.did, "created": True}
```

**Key Features:**
- **First interaction**: DID generated automatically
- **Private key**: Never exposed to user
- **Encryption**: Fernet with app-level secret
- **Default role**: Farmer (auto-approved)

---

## Registration Flow

### 1. Farmer Registration (Instant, Auto-Approved)

**Command:** `/register`

**Flow:**
1. User sends `/register`
2. Select language (English/Amharic)
3. Upload farm photo with GPS (EUDR compliance)
4. Verify GPS coordinates (deforestation check)
5. **Instant approval** - DID generated, can use system immediately

**Telegram Handler:** `voice/telegram/register_handler.py`

```python
async def handle_register_command(user_id, username, first_name, last_name):
    """
    Start registration - language and role selection.
    Farmers get instant approval.
    """
    # Check if user exists
    existing_user = db.query(UserIdentity).filter_by(
        telegram_user_id=str(user_id)
    ).first()
    
    if existing_user:
        if existing_user.is_approved:
            return {"message": "✅ You're already registered!"}
        else:
            return {"message": "⏳ Your registration is pending approval."}
    
    # Start registration conversation
    conversation_states[user_id] = {
        'state': STATE_LANGUAGE,
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'started_at': datetime.utcnow().isoformat()
    }
    
    return {
        'message': (
            "🌍 Welcome to Voice Ledger!\n\n"
            "Choose your language:\n"
            "🇬🇧 English\n"
            "🇪🇹 Amharic (አማርኛ)"
        ),
        'inline_keyboard': [
            [
                {'text': '🇬🇧 English', 'callback_data': 'lang_en'},
                {'text': '🇪🇹 አማርኛ', 'callback_data': 'lang_am'}
            ]
        ]
    }
```

**States:**
1. **STATE_LANGUAGE**: Choose English/Amharic
2. **STATE_ROLE**: Select role (Farmer/Cooperative/Exporter/Buyer)
3. **STATE_UPLOAD_FARM_PHOTO**: Upload GPS photo (farmers only)
4. **STATE_VERIFY_GPS**: Deforestation check
5. **Complete**: DID generated, user active

### 2. Non-Farmer Registration (Requires Approval)

**Roles:** Cooperative Manager, Exporter, Buyer

**Flow:**
1. Select role: Cooperative/Exporter/Buyer
2. **7-question form** (varies by role):
   - Full name
   - Organization name
   - Location
   - Phone number
   - Registration/license number
   - Role-specific questions
   - Set 4-digit PIN
3. Submit to pending approvals
4. Admin reviews and approves/rejects
5. User notified, can access system

**Cooperative Manager Questions:**
```
1. Full Name: John Doe
2. Cooperative Name: Yirgacheffe Farmers Union
3. Location: Gedeo Zone, Ethiopia
4. Phone: +251912345678
5. Registration Number: COOP-2024-1234
6. Reason for joining: Traceability for 500 member farmers
7. Set PIN: ****
```

**Exporter Questions:**
```
1-6. (Same as above)
7. Export License: EXP-LIC-2024-5678
8. Port Access: Djibouti Port
9. Shipping Capacity: 1000 tons/year
10. Set PIN: ****
```

**Buyer Questions:**
```
1-6. (Same as above)
7. Business Type: Specialty Coffee Roaster
8. Country: United States
9. Target Volume: 50 tons/year
10. Quality Preferences: Organic, Fair Trade, SCA 84+
11. Set PIN: ****
```

**Pending Registrations Table:**

```sql
CREATE TABLE pending_registrations (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    telegram_username VARCHAR(100),
    requested_role VARCHAR(50) NOT NULL,
    
    -- Common fields
    full_name VARCHAR(200) NOT NULL,
    organization_name VARCHAR(200) NOT NULL,
    location VARCHAR(200) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    registration_number VARCHAR(100),
    reason TEXT,
    
    -- Exporter-specific
    export_license VARCHAR(100),
    port_access VARCHAR(100),
    shipping_capacity_tons FLOAT,
    
    -- Buyer-specific
    business_type VARCHAR(50),
    country VARCHAR(100),
    target_volume_tons_annual FLOAT,
    quality_preferences JSON,
    
    -- PIN (copied to user_identities on approval)
    pin_hash VARCHAR(255),
    
    -- Review
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED
    reviewed_by_admin_id INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Multi-Channel Support

### 1. Telegram Bot

**Primary interface** for farmers and organizations.

**Commands:**
- `/register` - Start registration
- `/myidentity` - View DID and credentials
- `/set-pin` - Set PIN for web UI
- `/change-pin` - Change existing PIN
- `/reset-pin` - Request PIN reset (admin approval)

**Session Management:**

Uses Redis for persistence across server restarts.

**File:** `voice/telegram/session_manager.py`

```python
import redis
import json
from typing import Optional, Dict, Any

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def get_session(user_id: int, prefix: str = "reg") -> Optional[Dict[str, Any]]:
    """Get session data from Redis"""
    key = f"{prefix}:{user_id}"
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_session(user_id: int, data: Dict[str, Any], prefix: str = "reg", ttl: int = 3600):
    """Set session data in Redis (1 hour TTL)"""
    key = f"{prefix}:{user_id}"
    redis_client.setex(key, ttl, json.dumps(data))

def delete_session(user_id: int, prefix: str = "reg"):
    """Delete session from Redis"""
    key = f"{prefix}:{user_id}"
    redis_client.delete(key)
```

**Benefits:**
- Survives server restarts
- Multi-instance support (horizontal scaling)
- 1-hour TTL (auto-cleanup)
- Separate prefixes for different flows (reg, pin, photo)

### 2. IVR (Interactive Voice Response)

**For feature phones** (70% of target users).

**Authentication:**
- Phone number lookup: `UserIdentity.phone_number`
- Must be verified via Telegram contact share first
- Voice PIN entry for transactions

**Flow:**
```
1. User calls toll-free number (e.g., 8000 1234)
2. System: "Press 1 for Amharic, 2 for English"
3. System: "Enter your PIN" (DTMF input)
4. Verify PIN against UserIdentity.pin_hash
5. Voice menu for batch recording, balance check, etc.
```

**File:** `voice/ivr/twilio_ivr.py` (planned)

### 3. Web UI

**For cooperatives, exporters, buyers** to manage batches and marketplace.

**Authentication:**
- Username: `telegram_username`
- Password: 4-digit PIN
- Session: JWT token (15-minute expiry)

**Login Flow:**
```python
@app.post("/api/auth/login")
async def login(username: str, pin: str):
    # Lookup user
    user = db.query(UserIdentity).filter_by(
        telegram_username=username
    ).first()
    
    if not user:
        return {"error": "User not found"}
    
    # Check if locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        return {"error": "Account locked. Try again later."}
    
    # Verify PIN
    if not bcrypt.checkpw(pin.encode(), user.pin_hash.encode()):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.commit()
        return {"error": "Invalid PIN"}
    
    # Success - reset attempts
    user.failed_login_attempts = 0
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Generate JWT
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }, SECRET_KEY)
    
    return {"token": token, "role": user.role}
```

---

## Verification System

### 1. GPS Photo Verification (EUDR Compliance)

**Required for farmers** to prove deforestation-free origin.

**Flow:**

1. **Upload Photo**: Farmer uploads farm photo via Telegram
2. **Extract GPS**: System reads EXIF metadata (latitude, longitude)
3. **Deforestation Check**: Query Global Forest Watch API
4. **Risk Assessment**:
   - **Gold**: <0.5ha forest loss (LOW risk)
   - **Silver**: 0.5-2ha forest loss (MEDIUM risk)
   - **Bronze**: >2ha forest loss (HIGH risk)
5. **Blockchain Anchor**: GPS + risk assessment anchored to blockchain
6. **5-Year Retention**: EUDR Article 33 compliance

**File:** `voice/verification/gps_photo_verifier.py`

```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def extract_gps_from_photo(photo_path: str) -> Dict[str, float]:
    """
    Extract GPS coordinates from photo EXIF metadata.
    
    Returns:
        {
            'latitude': 6.1234,
            'longitude': 38.5678,
            'altitude': 1850.0  # meters
        }
    """
    image = Image.open(photo_path)
    exif_data = image._getexif()
    
    if not exif_data:
        raise ValueError("No EXIF data found in photo")
    
    gps_info = {}
    for tag, value in exif_data.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == 'GPSInfo':
            for gps_tag in value:
                sub_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                gps_info[sub_tag_name] = value[gps_tag]
    
    if not gps_info:
        raise ValueError("No GPS data found in photo")
    
    # Convert GPS data to decimal degrees
    latitude = _convert_to_degrees(gps_info['GPSLatitude'])
    longitude = _convert_to_degrees(gps_info['GPSLongitude'])
    
    # Apply N/S and E/W direction
    if gps_info['GPSLatitudeRef'] == 'S':
        latitude = -latitude
    if gps_info['GPSLongitudeRef'] == 'W':
        longitude = -longitude
    
    return {
        'latitude': latitude,
        'longitude': longitude,
        'altitude': gps_info.get('GPSAltitude', 0)
    }
```

**File:** `voice/verification/deforestation_checker.py`

```python
import requests

def check_deforestation_risk(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Check deforestation risk using Global Forest Watch API.
    
    Returns:
        {
            'forest_loss_ha': 0.3,  # Hectares lost
            'risk_level': 'LOW',    # LOW, MEDIUM, HIGH
            'compliance_tier': 'GOLD'  # GOLD, SILVER, BRONZE
        }
    """
    # Query GFW API for 2km buffer around coordinates
    url = "https://data-api.globalforestwatch.org/dataset/umd_tree_cover_loss/latest/query"
    params = {
        'sql': f"""
            SELECT SUM(area__ha) as total_loss
            FROM data
            WHERE ST_Intersects(
                geom,
                ST_Buffer(ST_SetSRID(ST_Point({longitude}, {latitude}), 4326)::geography, 2000)::geometry
            )
            AND umd_tree_cover_loss__year >= 2020
        """
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    forest_loss_ha = data['data'][0]['total_loss'] or 0
    
    # Risk assessment
    if forest_loss_ha < 0.5:
        risk_level = 'LOW'
        compliance_tier = 'GOLD'
    elif forest_loss_ha < 2.0:
        risk_level = 'MEDIUM'
        compliance_tier = 'SILVER'
    else:
        risk_level = 'HIGH'
        compliance_tier = 'BRONZE'
    
    return {
        'forest_loss_ha': forest_loss_ha,
        'risk_level': risk_level,
        'compliance_tier': compliance_tier,
        'checked_at': datetime.utcnow().isoformat()
    }
```

### 2. Phone Verification

**Required for IVR access**.

**Method:** Telegram contact share (native, secure)

**Flow:**
1. User clicks "Share Contact" button in Telegram
2. Bot receives phone number (E.164 format: +251912345678)
3. Update `UserIdentity.phone_number`
4. Set `phone_verified_at = NOW()`
5. User can now call IVR system

**Benefits:**
- No SMS costs
- Instant verification
- Leverages Telegram's phone number validation

---

## Authentication & Security

### 1. PIN Authentication

**4-digit PIN** for web UI and IVR access.

**Security Features:**
- **Bcrypt hashing**: Industry-standard, slow by design
- **Salt**: Unique per user (included in bcrypt hash)
- **Lockout**: 5 failed attempts = 30-minute lock
- **Expiry**: Optional (future: 90-day PIN change requirement)

**PIN Hashing:**

```python
import bcrypt

def hash_pin(pin: str) -> str:
    """Hash PIN with bcrypt (slow, secure)"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pin.encode(), salt)
    return hashed.decode()

def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify PIN against hash"""
    return bcrypt.checkpw(pin.encode(), pin_hash.encode())
```

**PIN Commands:**

**File:** `voice/telegram/pin_commands.py`

- **`/set-pin`**: Set PIN for existing users without one
- **`/change-pin`**: Change PIN (requires old PIN verification)
- **`/reset-pin`**: Request PIN reset (admin approval required)

**PIN Flow (`/set-pin`):**

```
1. User: /set-pin
2. Bot: "Enter your new 4-digit PIN:"
3. User: 1234
4. Bot: "Confirm your PIN:"
5. User: 1234
6. Bot: "✅ PIN set successfully! You can now access the web UI."
```

**PIN Flow (`/change-pin`):**

```
1. User: /change-pin
2. Bot: "Enter your current PIN:"
3. User: 1234
4. Bot: "Enter your new PIN:"
5. User: 5678
6. Bot: "Confirm your new PIN:"
7. User: 5678
8. Bot: "✅ PIN changed successfully!"
```

**PIN Reset (`/reset-pin`):**

```
1. User: /reset-pin
2. Bot: "⚠️ PIN reset requires admin approval. Reason?"
3. User: "Forgot my PIN"
4. Bot: "Request submitted. Admin will review."
5. [Admin reviews via /admin-requests]
6. [Admin approves or denies]
7. Bot: "✅ PIN reset approved. Set new PIN: /set-pin"
```

### 2. Account Lockout

**Prevents brute-force attacks** on PIN authentication.

**Rules:**
- **5 consecutive failed attempts** = 30-minute lockout
- **Lock expires** automatically after 30 minutes
- **Reset on success**: Failed attempts counter resets to 0

**Implementation:**

```python
def check_login_attempts(user: UserIdentity) -> bool:
    """Check if user is locked out"""
    if user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = (user.locked_until - datetime.utcnow()).seconds // 60
        raise Exception(f"Account locked for {minutes_left} more minutes")
    
    # Clear expired lock
    if user.locked_until and user.locked_until <= datetime.utcnow():
        user.locked_until = None
        user.failed_login_attempts = 0
    
    return True
```

### 3. Session Management

**Redis-backed sessions** for multi-instance deployment.

**Session Types:**
- **Registration**: `reg:{user_id}` (1 hour TTL)
- **PIN setup**: `pin:{user_id}` (1 hour TTL)
- **Photo upload**: `photo:{user_id}` (1 hour TTL)

**Benefits:**
- **Persistence**: Survives server restarts
- **Scalability**: Shared across multiple bot instances
- **Auto-cleanup**: TTL expires inactive sessions

---

## Role-Based Access Control

### User Roles

| Role | Default Approval | Features | PIN Required |
|------|------------------|----------|--------------|
| **FARMER** | ✅ Instant | Voice recording, batch creation | ❌ No |
| **COOPERATIVE_MANAGER** | ⏳ Admin approval | Batch verification, farmer management | ✅ Yes |
| **EXPORTER** | ⏳ Admin approval | Shipment tracking, customs docs | ✅ Yes |
| **BUYER** | ⏳ Admin approval | RFQ creation, batch purchases | ✅ Yes |
| **SYSTEM_ADMIN** | Manual creation | Approve registrations, system config | ✅ Yes |

### Permission Matrix

| Action | Farmer | Cooperative | Exporter | Buyer | Admin |
|--------|--------|-------------|----------|-------|-------|
| Record batch | ✅ | ✅ | ✅ | ❌ | ✅ |
| Verify batch | ❌ | ✅ | ❌ | ❌ | ✅ |
| Create RFQ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Ship batch | ❌ | ✅ | ✅ | ❌ | ✅ |
| Approve user | ❌ | ❌ | ❌ | ❌ | ✅ |
| View marketplace | ✅ | ✅ | ✅ | ✅ | ✅ |

### Role Enforcement

```python
def require_role(*allowed_roles):
    """Decorator to enforce role-based access"""
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            
            with get_db() as db:
                user = db.query(UserIdentity).filter_by(
                    telegram_user_id=str(user_id)
                ).first()
                
                if not user:
                    await update.message.reply_text("❌ Not registered. Use /register")
                    return
                
                if user.role not in allowed_roles:
                    await update.message.reply_text(f"❌ Requires role: {', '.join(allowed_roles)}")
                    return
                
                return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_role('COOPERATIVE_MANAGER', 'SYSTEM_ADMIN')
async def verify_batch_command(update, context):
    """Only cooperative managers and admins can verify batches"""
    pass
```

---

## Admin Approval Workflow

### 1. View Pending Registrations

**Command:** `/admin-requests`

**Output:**
```
📋 Pending Registrations (3)

1️⃣ John Doe
   Role: Cooperative Manager
   Organization: Yirgacheffe Farmers Union
   Location: Gedeo Zone
   Phone: +251912345678
   [Approve] [Reject]

2️⃣ Jane Smith
   Role: Exporter
   Organization: Ethiopian Coffee Exports
   License: EXP-LIC-2024-5678
   [Approve] [Reject]

3️⃣ Bob Johnson
   Role: Buyer
   Organization: Blue Bottle Coffee
   Country: United States
   [Approve] [Reject]
```

### 2. Approve Registration

**File:** `voice/admin/registration_approval.py`

```python
async def approve_registration(pending_id: int, admin_user_id: int) -> Dict[str, Any]:
    """
    Approve pending registration.
    
    Steps:
    1. Create UserIdentity with auto-generated DID
    2. Copy PIN from pending registration
    3. Create Organization if needed
    4. Send notification to user
    5. Mark pending as approved
    """
    with get_db() as db:
        pending = db.query(PendingRegistration).get(pending_id)
        
        if not pending or pending.status != 'PENDING':
            return {"error": "Invalid or already processed"}
        
        # Generate DID for user
        identity = generate_did_key()
        
        # Encrypt private key
        encryption_key = _get_encryption_key()
        fernet = Fernet(encryption_key)
        encrypted_private_key = fernet.encrypt(identity["private_key"].encode())
        
        # Create UserIdentity
        new_user = UserIdentity(
            telegram_user_id=str(pending.telegram_user_id),
            telegram_username=pending.telegram_username,
            telegram_first_name=pending.telegram_first_name,
            telegram_last_name=pending.telegram_last_name,
            did=identity["did"],
            encrypted_private_key=encrypted_private_key.decode(),
            public_key=identity["public_key"],
            role=pending.requested_role,
            phone_number=pending.phone_number,
            pin_hash=pending.pin_hash,  # Copy PIN
            pin_set_at=datetime.utcnow(),
            is_approved=True,
            approved_at=datetime.utcnow(),
            approved_by_admin_id=admin_user_id
        )
        
        db.add(new_user)
        
        # Update pending status
        pending.status = 'APPROVED'
        pending.reviewed_at = datetime.utcnow()
        pending.reviewed_by_admin_id = admin_user_id
        
        db.commit()
        
        # Send notification
        await send_telegram_notification(
            pending.telegram_user_id,
            f"✅ Registration approved!\n\n"
            f"Your DID: {identity['did'][:30]}...\n"
            f"Role: {pending.requested_role}\n\n"
            f"You can now use all features."
        )
        
        return {
            "success": True,
            "user_id": new_user.id,
            "did": new_user.did
        }
```

### 3. Reject Registration

```python
async def reject_registration(pending_id: int, admin_user_id: int, reason: str):
    """Reject pending registration with reason"""
    with get_db() as db:
        pending = db.query(PendingRegistration).get(pending_id)
        
        pending.status = 'REJECTED'
        pending.reviewed_at = datetime.utcnow()
        pending.reviewed_by_admin_id = admin_user_id
        pending.rejection_reason = reason
        
        db.commit()
        
        # Notify user
        await send_telegram_notification(
            pending.telegram_user_id,
            f"❌ Registration rejected\n\n"
            f"Reason: {reason}\n\n"
            f"Please contact support if you have questions."
        )
```

---

## Adapting for Trust-Voice

### Key Differences

| Feature | Voice-Ledger | Trust-Voice |
|---------|--------------|-------------|
| **Primary users** | Farmers, cooperatives | Trust creators, beneficiaries |
| **Registration** | Role-based (4 roles) | Entity-based (Trust, Trustee, Beneficiary) |
| **Verification** | GPS photo, deforestation | Legal document verification |
| **Identity** | W3C DIDs (Ed25519) | W3C DIDs (Ed25519) ✅ Same |
| **Authentication** | PIN (4-digit) | PIN or passphrase |
| **Channels** | Telegram, IVR, Web | Web UI primary, SMS notifications |
| **Approval** | Admin approval for non-farmers | Legal verification required |

### Trust-Voice Registration Flow

**1. Trust Creator Registration**

```
Steps:
1. Create account (email + password)
2. Verify email
3. Upload trust document (PDF)
4. OCR + legal validation
5. Set beneficiaries (DIDs or emails)
6. Admin legal review
7. Approve + mint trust NFT
```

**2. Trustee Registration**

```
Steps:
1. Invited by trust creator (DID link)
2. Create account
3. Legal capacity verification
4. Set PIN/passphrase
5. Accept trusteeship
6. DID credential issued
```

**3. Beneficiary Registration**

```
Steps:
1. Invited by trust creator (DID link)
2. Create account (or claim via existing DID)
3. Identity verification (KYC if needed)
4. Accept beneficiary status
5. DID credential issued
```

### Reusable Components

**✅ Can Reuse Directly:**
- `ssi/did/did_key.py` - DID generation
- `ssi/user_identity.py` - Identity management (adapt table name)
- PIN hashing and verification logic
- Session management (Redis)
- Admin approval workflow structure

**🔧 Needs Adaptation:**
- Registration form (trust-specific questions)
- Verification system (legal docs instead of GPS photos)
- Role names (Trust Creator, Trustee, Beneficiary)
- Notification templates

### Trust-Voice Database Schema

```sql
CREATE TABLE trust_identities (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Auto-generated DID (same as Voice-Ledger)
    did VARCHAR(200) UNIQUE NOT NULL,
    encrypted_private_key TEXT NOT NULL,
    public_key VARCHAR(100) NOT NULL,
    
    -- Trust role
    role VARCHAR(50) NOT NULL,  -- TRUST_CREATOR, TRUSTEE, BENEFICIARY, SYSTEM_ADMIN
    
    -- Legal information
    full_legal_name VARCHAR(200) NOT NULL,
    date_of_birth DATE,
    national_id VARCHAR(100),
    verified_at TIMESTAMP,
    verified_by_admin_id INTEGER,
    
    -- PIN for transactions
    pin_hash VARCHAR(255),
    pin_set_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pending_trust_registrations (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    requested_role VARCHAR(50) NOT NULL,
    
    -- Trust document
    trust_document_path VARCHAR(500),
    trust_document_hash VARCHAR(64),  -- SHA-256
    
    -- Personal info
    full_legal_name VARCHAR(200) NOT NULL,
    date_of_birth DATE,
    national_id VARCHAR(100),
    address TEXT,
    phone_number VARCHAR(20),
    
    -- Legal verification
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, VERIFIED, REJECTED
    reviewed_by_admin_id INTEGER,
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Adaptation Checklist

**Identity System:**
- [x] DID generation (reuse as-is)
- [x] Key encryption (reuse as-is)
- [ ] Adapt table schema for trust roles
- [ ] Update registration form for legal info

**Authentication:**
- [x] PIN hashing (reuse as-is)
- [x] Lockout logic (reuse as-is)
- [ ] Add passphrase option (stronger than 4-digit PIN)
- [ ] Implement 2FA (optional, for high-value trusts)

**Verification:**
- [ ] Legal document OCR (new)
- [ ] Trust structure validation (new)
- [ ] Beneficiary identity verification (new)
- [ ] Legal capacity checks (new)

**Admin Workflow:**
- [x] Approval/rejection logic (reuse as-is)
- [ ] Legal review interface (new)
- [ ] Document annotation tools (new)
- [ ] Compliance reporting (new)

---

## Additional Resources

- **W3C DID Specification**: https://www.w3.org/TR/did-core/
- **W3C Verifiable Credentials**: https://www.w3.org/TR/vc-data-model/
- **Ed25519 Cryptography**: https://ed25519.cr.yp.to/
- **Bcrypt Best Practices**: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- **Redis Session Management**: https://redis.io/docs/manual/keyspace-notifications/

---

## Support

For questions about adapting this system to Trust-Voice:
- Review user flows in `voice/telegram/register_handler.py`
- Study DID generation in `ssi/user_identity.py`
- Check PIN management in `voice/telegram/pin_commands.py`
- Test admin approval in `voice/admin/registration_approval.py`

---

**Version:** 1.0  
**Author:** Voice Ledger Team  
**Last Updated:** December 23, 2025
