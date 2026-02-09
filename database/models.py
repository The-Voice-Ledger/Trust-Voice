"""
TrustVoice Database Models

This module defines all SQLAlchemy models for the TrustVoice platform.

Architecture:
- Donors: Individual users who donate via voice/chat
- NGOs: Organizations running campaigns
- Campaigns: Fundraising projects (e.g., "Mwanza Water Project")
- Donations: Individual contributions linked to donors and campaigns
- Impact Verifications: Field officer reports proving project completion
- Conversation Logs: AI conversation history for debugging/improvement
- Campaign Context: FAQ/story content for RAG (vector search)
- Users: Admin users who can approve payouts
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date,
    Text, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class UserRole(enum.Enum):
    """User roles for access control and registration."""
    # Admin roles (password-based)
    SUPER_ADMIN = "super_admin"  # Platform admins (approve all)
    NGO_ADMIN = "ngo_admin"      # NGO admins (approve own payouts)
    VIEWER = "viewer"            # Read-only access
    
    # Telegram user roles (PIN-based)
    DONOR = "DONOR"                    # Instant approval
    CAMPAIGN_CREATOR = "CAMPAIGN_CREATOR"  # Requires admin approval
    FIELD_AGENT = "FIELD_AGENT"        # Requires admin approval
    SYSTEM_ADMIN = "SYSTEM_ADMIN"      # Manual creation


class User(Base):
    """
    User model supporting both admin users and Telegram users.
    
    Admin users (password-based):
    - super_admin: Can approve all payouts, manage all NGOs
    - ngo_admin: Can approve payouts for their assigned NGO
    - viewer: Read-only access
    
    Telegram users (PIN-based for cross-interface auth):
    - DONOR: Instant approval, voice donations
    - CAMPAIGN_CREATOR: Requires admin approval, can create campaigns
    - FIELD_AGENT: Requires admin approval, can verify campaigns
    - SYSTEM_ADMIN: Manual creation, platform operators
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    
    # Admin authentication (password-based)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    
    # Telegram identity (primary for Telegram users)
    telegram_user_id = Column(String(50), unique=True, nullable=True, index=True)
    telegram_username = Column(String(100), nullable=True)
    telegram_first_name = Column(String(100), nullable=True)
    telegram_last_name = Column(String(100), nullable=True)
    
    # Common fields
    full_name = Column(String(255))
    role = Column(String(50), default="VIEWER", nullable=False)  # Store enum value as string
    ngo_id = Column(Integer, ForeignKey('ngo_organizations.id'))  # For ngo_admin
    preferred_language = Column(String(2), default="en")  # Language preference ('en' or 'am')
    
    # Approval fields (for Telegram users)
    is_approved = Column(Boolean, default=True)  # Instant for DONOR, pending for others
    approved_at = Column(DateTime, nullable=True)
    approved_by_admin_id = Column(Integer, nullable=True)
    
    # PIN authentication (for cross-interface access: Web/IVR/WhatsApp)
    pin_hash = Column(String(255), nullable=True)  # Bcrypt hash of 4-digit PIN
    pin_set_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    
    # Phone verification (for IVR access)
    phone_number = Column(String(20), unique=True, nullable=True, index=True)
    phone_verified_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)  # Deprecated, use last_login_at
    
    # Relationships
    ngo = relationship("NGOOrganization", backref="admin_users")


class PendingRegistration(Base):
    """
    Pending user registrations awaiting admin approval.
    
    Used for CAMPAIGN_CREATOR and FIELD_AGENT roles.
    DONOR role gets instant approval (no pending record).
    
    Workflow:
    1. User completes registration form via Telegram
    2. Record created with status='PENDING'
    3. Admin reviews via /admin-requests
    4. On approval: Create User record, update status='APPROVED'
    5. On rejection: Update status='REJECTED', store reason
    """
    __tablename__ = "pending_registrations"
    
    id = Column(Integer, primary_key=True)
    
    # Telegram identity
    telegram_user_id = Column(String(50), nullable=False, index=True)
    telegram_username = Column(String(100))
    telegram_first_name = Column(String(100))
    telegram_last_name = Column(String(100))
    
    # Role request
    requested_role = Column(String(50), nullable=False)  # 'CAMPAIGN_CREATOR' or 'FIELD_AGENT'
    
    # Registration form data
    full_name = Column(String(200))
    organization_name = Column(String(200))  # Campaign Creators
    location = Column(String(200))
    phone_number = Column(String(20))
    reason = Column(Text)
    
    # Field Agent specific fields
    verification_experience = Column(Text)
    coverage_regions = Column(Text)
    has_gps_phone = Column(Boolean)
    
    # PIN (will be copied to users table on approval)
    pin_hash = Column(String(255))
    
    # Admin review
    status = Column(String(20), default='PENDING', nullable=False, index=True)  # PENDING, APPROVED, REJECTED
    reviewed_by_admin_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_admin_id])


class PendingNGORegistration(Base):
    """
    Pending NGO organization registrations awaiting admin approval.
    
    Workflow:
    1. NGO submits registration via mini app or voice
    2. Record created with status='PENDING'
    3. Admin reviews via /admin panel
    4. On approval: Create NGOOrganization record, update status='APPROVED'
    5. On rejection: Update status='REJECTED', store reason
    """
    __tablename__ = "pending_ngo_registrations"
    
    id = Column(Integer, primary_key=True)
    
    # Submitter info (if via Telegram)
    submitted_by_telegram_id = Column(String(50), index=True)
    submitted_by_telegram_username = Column(String(100))
    submitted_by_name = Column(String(200))
    
    # NGO Organization Details
    organization_name = Column(String(200), nullable=False)
    registration_number = Column(String(100))  # Official registration/tax ID
    organization_type = Column(String(100))  # Charity, Foundation, Community Group, etc.
    
    # Contact Information
    email = Column(String(200))
    phone_number = Column(String(20))
    website = Column(String(500))
    
    # Location
    country = Column(String(100))
    region = Column(String(200))
    address = Column(Text)
    
    # Organization Details
    mission_statement = Column(Text)
    focus_areas = Column(Text)  # e.g., "Education, Healthcare, Water"
    year_established = Column(Integer)
    staff_size = Column(String(50))  # e.g., "1-10", "11-50", "50+"
    
    # Verification Documents (URLs or file paths)
    registration_document_url = Column(String(500))
    tax_certificate_url = Column(String(500))
    additional_documents = Column(Text)  # JSON array of document URLs
    
    # Banking Information (for payouts)
    bank_name = Column(String(200))
    account_number = Column(String(100))
    account_name = Column(String(200))
    swift_code = Column(String(50))
    
    # Admin Review
    status = Column(String(20), default='PENDING', nullable=False, index=True)  # PENDING, APPROVED, REJECTED, NEEDS_INFO
    reviewed_by_admin_id = Column(Integer, ForeignKey('users.id'))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    admin_notes = Column(Text)
    
    # Created NGO (if approved)
    ngo_id = Column(Integer, ForeignKey('ngo_organizations.id'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_admin_id])
    ngo = relationship("NGOOrganization", foreign_keys=[ngo_id])


class Donor(Base):
    """
    Individual donor who interacts via phone/Telegram/WhatsApp.
    
    Key Fields:
    - preferred_language: Set during registration (en/fr/de/it/am/sw)
      Used to route to correct AI (GPT-4 vs Addis AI)
    - phone_number: For IVR calls
    - telegram_user_id: For Telegram messages
    - whatsapp_number: For WhatsApp messages
    
    A donor may have multiple contact methods.
    """
    __tablename__ = "donors"
    
    id = Column(Integer, primary_key=True)
    
    # Contact Methods (at least one required)
    phone_number = Column(String(20), unique=True, index=True)
    telegram_user_id = Column(String(50), unique=True, index=True)
    whatsapp_number = Column(String(20), unique=True, index=True)
    
    # Profile
    preferred_name = Column(String(100))
    preferred_language = Column(String(10), default="en")  # CRITICAL: No auto-detection
    email = Column(String(255))
    country_code = Column(String(2))  # ISO 3166-1 alpha-2 (e.g., "DE", "US")
    
    # Payment Info
    blockchain_wallet_address = Column(String(66))  # Ethereum address (optional)
    stripe_customer_id = Column(String(100))  # Stripe Customer ID (auto-created)
    
    # Stats
    total_donated_usd = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)  # Email/phone verified
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime)
    
    # Relationships
    donations = relationship("Donation", back_populates="donor")


class NGOOrganization(Base):
    """
    NGO running fundraising campaigns.
    
    Examples:
    - WaterAid Tanzania
    - Ethiopian Education Foundation
    - Healthcare for All Kenya
    """
    __tablename__ = "ngo_organizations"
    
    id = Column(Integer, primary_key=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    description = Column(Text)  # What the NGO does
    website_url = Column(String(255))  # NGO website
    registration_number = Column(String(100))  # Government registration
    country = Column(String(100))
    contact_email = Column(String(255))
    admin_phone = Column(String(20))
    
    # Financial
    blockchain_wallet_address = Column(String(66))  # Where funds are sent
    stripe_account_id = Column(String(100))  # Stripe Connect account
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="ngo")


class Campaign(Base):
    """
    Individual fundraising project.
    
    Example:
    - Title: "Clean Water for Mwanza"
    - Goal: $50,000
    - Description: "Build 10 wells serving 3,000 families"
    - Location: Mwanza, Tanzania (-2.5164, 32.9175)
    """
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True)
    
    # Campaign Ownership (XOR: exactly one must be set)
    ngo_id = Column(Integer, ForeignKey("ngo_organizations.id"), nullable=True)  # NGO campaigns
    creator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Individual campaigns
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    goal_amount_usd = Column(Float, nullable=False)
    raised_amount_usd = Column(Float, default=0.0)  # Cached USD total (denormalized)
    raised_amounts = Column(JSON, default=dict)  # Per-currency totals: {"USD": 1000, "EUR": 500}
    
    # Classification
    category = Column(String(50))  # water, education, health, infrastructure
    
    # Location
    location_country = Column(String(100))
    location_region = Column(String(100))
    location_gps = Column(String(100))  # "latitude,longitude"
    
    # Status
    status = Column(String(20), default="active")  # active, paused, completed, cancelled
    
    # Verification Metrics (for impact reports)
    verification_count = Column(Integer, default=0)  # Number of field agent verifications
    total_trust_score = Column(Float, default=0.0)  # Sum of all trust scores
    avg_trust_score = Column(Float, default=0.0)  # Average trust score (calculated)
    
    # Transparency Video (IPFS)
    video_ipfs_hash = Column(String(100), nullable=True)  # QmXxxx... IPFS content hash
    video_ipfs_url = Column(String(500), nullable=True)   # https://gateway.pinata.cloud/ipfs/QmXxxx...
    video_uploaded_at = Column(DateTime, nullable=True)
    video_duration_seconds = Column(Integer, nullable=True)  # Video length
    video_thumbnail_url = Column(String(500), nullable=True)  # Optional thumbnail image
    video_file_size_bytes = Column(Integer, nullable=True)  # File size for bandwidth estimates
    
    # Dates
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ngo = relationship("NGOOrganization", back_populates="campaigns")
    creator_user = relationship("User", foreign_keys=[creator_user_id], backref="created_campaigns")
    donations = relationship("Donation", back_populates="campaign")
    verifications = relationship("ImpactVerification", back_populates="campaign")
    context_items = relationship("CampaignContext", back_populates="campaign")
    
    def validate_ownership(self) -> bool:
        """Ensure exactly one of ngo_id or creator_user_id is set (XOR)."""
        return (self.ngo_id is not None) != (self.creator_user_id is not None)
    
    def get_owner_name(self, db_session) -> str:
        """Get display name of campaign owner."""
        if self.ngo_id:
            ngo = db_session.query(NGOOrganization).filter(NGOOrganization.id == self.ngo_id).first()
            return f"{ngo.name} (NGO)" if ngo else "Unknown NGO"
        elif self.creator_user_id:
            from database.models import User
            user = db_session.query(User).filter(User.id == self.creator_user_id).first()
            return f"{user.full_name} (Individual)" if user else "Unknown Creator"
        return "Unknown Owner"
    
    def get_current_usd_total(self):
        """
        Calculate current USD total from all currency buckets using live rates.
        
        This provides dynamic conversion - the USD total updates with exchange rates.
        The cached raised_amount_usd field is for quick queries but may be stale.
        
        Returns:
            float: Current USD equivalent of all donations
        """
        if not self.raised_amounts:
            return 0.0
        
        from services.currency_service import currency_service
        total_usd = 0.0
        
        for currency, amount in self.raised_amounts.items():
            if currency == "USD":
                total_usd += amount
            else:
                try:
                    usd_amount = currency_service.convert_to_usd(amount, currency)
                    total_usd += usd_amount
                except Exception as e:
                    # Log error but don't fail - use cached rate
                    print(f"Warning: Could not convert {currency} to USD: {e}")
                    continue
        
        return total_usd


class CampaignContext(Base):
    """
    Content for RAG (Retrieval-Augmented Generation).
    
    When donor asks "How will the money be used?", we search
    campaign_context table for relevant content using vector similarity.
    
    Content Types:
    - faq: Frequently asked questions
    - story: Beneficiary stories
    - budget: Detailed budget breakdown
    - partner_info: About implementing partners
    """
    __tablename__ = "campaign_context"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    
    content_type = Column(String(50))  # faq, story, budget, partner_info
    content = Column(Text, nullable=False)
    language = Column(String(10))  # en, fr, de, it, am, sw
    
    # Note: embedding_vector stored separately in Pinecone
    # (PostgreSQL pgvector extension is optional - adds complexity)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="context_items")


class Donation(Base):
    """
    Individual donation transaction.
    
    Lifecycle:
    1. pending: Payment intent created
    2. completed: Payment confirmed by Stripe/PayPal
    3. failed: Payment declined
    4. refunded: Donor requested refund
    """
    __tablename__ = "donations"
    
    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    
    # Amount in donor's chosen currency
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")  # ISO 4217: USD, EUR, KES, GBP, etc.
    
    # Payment Method
    payment_method = Column(String(20))  # mpesa, stripe, crypto
    payment_intent_id = Column(String(255))  # Stripe Payment Intent ID or M-Pesa transaction ID
    transaction_hash = Column(String(66))  # If crypto, blockchain tx hash
    
    # Blockchain Receipt (Legacy field, kept for compatibility)
    blockchain_receipt_url = Column(Text)  # IPFS URL with receipt NFT
    
    # NFT Tax Receipt (Blockchain-based, verifiable by tax authorities)
    receipt_nft_token_id = Column(Integer, nullable=True)  # NFT token ID on blockchain
    receipt_nft_contract = Column(String(42), nullable=True)  # Contract address (0x...)
    receipt_nft_network = Column(String(20), nullable=True)  # polygon, ethereum, base, arbitrum
    receipt_nft_tx_hash = Column(String(66), nullable=True)  # Minting transaction hash
    receipt_metadata_ipfs = Column(String(100), nullable=True)  # QmXxxx... metadata hash
    receipt_minted_at = Column(DateTime, nullable=True)
    
    # Donor Tax Information (optional, for receipt generation)
    donor_tax_id = Column(String(50), nullable=True)  # SSN, EIN, Tax ID (encrypted)
    donor_full_legal_name = Column(String(200), nullable=True)  # Legal name for tax docs
    donor_wallet_address = Column(String(42), nullable=True)  # 0x... for NFT minting
    
    # Status
    status = Column(String(20), default="pending")
    
    # Optional Fields
    donor_message = Column(Text)  # "In memory of..."
    is_anonymous = Column(Boolean, default=False)
    tax_receipt_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    donor = relationship("Donor", back_populates="donations")
    campaign = relationship("Campaign", back_populates="donations")


class ImpactVerification(Base):
    """
    Field agent report proving project completion/progress.
    
    Example:
    - Campaign: Mwanza Water Project
    - Field Agent: Ibrahim (TrustVoice verified agent)
    - Description: "Well #3 completed, serving 450 families"
    - Photos: [photo1_file_id, photo2_file_id] (Telegram file IDs)
    - GPS: -2.5164, 32.9175
    - Trust Score: 85/100 (auto-approved)
    - Agent Payout: $30 USD via M-Pesa
    
    Field agents earn $30 per approved verification.
    Reports with trust score >= 80 are auto-approved.
    """
    __tablename__ = "impact_verifications"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    
    # Field Agent Info
    field_agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Verification Details
    verification_date = Column(DateTime, default=datetime.utcnow)
    agent_notes = Column(Text)  # Field agent's observations
    testimonials = Column(Text)  # Beneficiary quotes
    
    # Media (Telegram file IDs or URLs)
    photos = Column(JSON)  # Array of photo file IDs
    
    # Location & Impact
    gps_latitude = Column(Float)
    gps_longitude = Column(Float)
    beneficiary_count = Column(Integer, default=0)
    
    # Trust Scoring
    trust_score = Column(Integer, default=0)  # 0-100
    status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Agent Payout
    agent_payout_amount_usd = Column(Float)  # Typically $30
    agent_payout_status = Column(String(20))  # initiated, completed, failed
    agent_payout_transaction_id = Column(String(100))  # M-Pesa ConversationID
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="verifications")
    field_agent = relationship("User", foreign_keys=[field_agent_id])


class ConversationLog(Base):
    """
    Logs all AI conversations for debugging and improvement.
    
    Use Cases:
    - Debug why AI misunderstood donor intent
    - Calculate LLM token usage (costs)
    - Improve conversation flows
    - Compliance (GDPR: user can request conversation history)
    """
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey("donors.id"))
    
    # Channel Info
    channel = Column(String(20))  # ivr, telegram, whatsapp
    session_id = Column(String(100))  # Groups messages in same conversation
    
    # Message Content
    message_type = Column(String(20))  # user, assistant, system
    message_text = Column(Text)
    
    # AI Metadata
    intent_detected = Column(String(50))  # ask_campaign_info, initiate_donation, etc.
    entities_extracted = Column(Text)  # JSON: {"campaign_id": 5, "amount": 100}
    llm_model = Column(String(50))  # gpt-4-turbo, addis-ai-am
    llm_tokens_used = Column(Integer)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class Payout(Base):
    """
    Tracks payments FROM platform TO NGOs/beneficiaries.
    
    Supported payment methods:
    - mpesa_b2c: M-Pesa Business to Customer (Kenya mobile money)
    - bank_transfer: Direct bank transfer (SEPA, SWIFT, local)
    - stripe_payout: Stripe Payouts (to bank account or debit card)
    
    Use cases:
    - Transfer raised funds to NGO after campaign completion
    - Refund donor if campaign fails
    - Bulk disbursements to beneficiaries
    - Cross-border payments (EUR to European NGO, KES to Kenyan NGO)
    
    Status flow:
    - pending: Payout initiated, waiting for processing
    - processing: Payment processor accepted request, in queue
    - completed: Money successfully sent
    - failed: Payout failed (insufficient balance, invalid account, etc.)
    """
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True)
    
    # Recipient
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    ngo_id = Column(Integer, ForeignKey('ngo_organizations.id'), nullable=True)
    recipient_name = Column(String(200))
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')  # USD, EUR, GBP, KES, etc.
    payment_method = Column(String(20), default='bank_transfer')  # mpesa_b2c, bank_transfer, stripe_payout
    
    # Mobile money (M-Pesa, etc.)
    recipient_phone = Column(String(20))  # For M-Pesa B2C
    conversation_id = Column(String(100))  # M-Pesa ConversationID
    originator_conversation_id = Column(String(100))  # M-Pesa OriginatorConversationID
    
    # Bank account details
    bank_account_number = Column(String(100))  # Account number or IBAN
    bank_routing_number = Column(String(100))  # Routing/Sort code/SWIFT
    bank_name = Column(String(200))
    bank_country = Column(String(2))  # ISO country code (DE, KE, US)
    
    # Stripe Payouts
    stripe_payout_id = Column(String(100))  # Stripe Payout ID
    stripe_transfer_id = Column(String(100))  # Stripe Transfer ID
    
    # Transaction receipt (universal)
    transaction_id = Column(String(100))  # M-Pesa TransactionID or bank reference
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, approved, processing, completed, failed, rejected
    status_message = Column(Text)
    
    # Admin approval (for bank transfers)
    approved_by = Column(Integer, ForeignKey('users.id'))  # Admin who approved
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Metadata
    purpose = Column(String(200))  # "Campaign disbursement", "Refund", etc.
    remarks = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    campaign = relationship("Campaign", backref="payouts", foreign_keys=[campaign_id])
    ngo = relationship("NGOOrganization", backref="payouts", foreign_keys=[ngo_id])
    approver = relationship("User", backref="approved_payouts", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<Payout(id={self.id}, amount={self.amount} {self.currency}, status={self.status})>"


class UserPreference(Base):
    """
    User preferences for personalized conversations
    
    LAB 9 Part 3: Stores user preferences across sessions for faster interactions
    
    Supported preference types:
    - payment_provider: Default payment method (chapa, telebirr, mpesa)
    - donation_amount: Default donation amount
    - language: Preferred language (en, am)
    - notification_preference: Notification settings (all, major, none)
    - favorite_category: Preferred campaign category
    """
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="preferences")
    
    __table_args__ = (
        # Ensure one preference per key per user
        # UniqueConstraint('user_id', 'preference_key', name='uq_user_preference'),
    )
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, key={self.preference_key}, value={self.preference_value})>"


class ConversationEvent(Base):
    """Track conversation events for analytics"""
    __tablename__ = "conversation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    conversation_state = Column(String(50), nullable=True)
    current_step = Column(String(50), nullable=True)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", backref="conversation_events")
    
    def __repr__(self):
        return f"<ConversationEvent(id={self.id}, type={self.event_type}, session={self.session_id})>"


class ConversationMetrics(Base):
    """Daily conversation metrics for analytics"""
    __tablename__ = "conversation_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    conversation_type = Column(String(50), nullable=False)
    started_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    abandoned_count = Column(Integer, default=0)
    avg_duration_seconds = Column(Integer, nullable=True)
    avg_messages = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('date', 'conversation_type', name='uq_date_conversation_type'),
    )
    
    def __repr__(self):
        return f"<ConversationMetrics(date={self.date}, type={self.conversation_type}, started={self.started_count})>"
