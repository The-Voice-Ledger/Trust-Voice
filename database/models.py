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
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    """User roles for access control."""
    SUPER_ADMIN = "super_admin"  # Platform admins (approve all)
    NGO_ADMIN = "ngo_admin"      # NGO admins (approve own payouts)
    VIEWER = "viewer"            # Read-only access


class User(Base):
    """
    Admin users who can approve payouts and manage the platform.
    
    Roles:
    - super_admin: Can approve all payouts, manage all NGOs
    - ngo_admin: Can approve payouts for their assigned NGO
    - viewer: Read-only access
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    ngo_id = Column(Integer, ForeignKey('ngo_organizations.id'))  # For ngo_admin
    preferred_language = Column(String(2), default="en")  # Language preference ('en' or 'am')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    ngo = relationship("NGOOrganization", backref="admin_users")


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
    ngo_id = Column(Integer, ForeignKey("ngo_organizations.id"), nullable=False)
    
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
    
    # Dates
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ngo = relationship("NGOOrganization", back_populates="campaigns")
    donations = relationship("Donation", back_populates="campaign")
    verifications = relationship("ImpactVerification", back_populates="campaign")
    context_items = relationship("CampaignContext", back_populates="campaign")
    
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
    
    # Blockchain Receipt
    blockchain_receipt_url = Column(Text)  # IPFS URL with receipt NFT
    
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
    Field officer report proving project completion.
    
    Example:
    - Campaign: Mwanza Water Project
    - Verifier: Ibrahim (WaterAid field officer)
    - Type: milestone_completed
    - Description: "Well #3 completed, serving 450 families"
    - Audio: 30-second voice recording (IPFS URL)
    - Photos: [well_photo1.jpg, well_photo2.jpg] (IPFS URLs)
    - GPS: -2.5164, 32.9175
    - Blockchain: Anchored to Polygon with tx hash
    
    This verification is linked to all $100 donor receipts.
    """
    __tablename__ = "impact_verifications"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    
    # Field Officer Info
    verifier_phone = Column(String(20))
    verifier_name = Column(String(100))
    
    # Verification Details
    verification_type = Column(String(50))  # milestone, completion, beneficiary_count
    description = Column(Text)
    
    # Media
    audio_recording_url = Column(Text)  # IPFS URL
    photo_urls = Column(JSON)  # Array of IPFS URLs stored as JSON
    
    # Location & Impact
    gps_coordinates = Column(String(100))  # "latitude,longitude"
    beneficiary_count = Column(Integer)  # Number of people impacted
    
    # Blockchain Anchor
    blockchain_anchor_tx = Column(String(66))  # Polygon transaction hash
    
    # Timestamp
    verified_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="verifications")


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

