"""
Database Models for Payouts

Tracks disbursements from campaigns to NGOs/beneficiaries.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models import Base


class Payout(Base):
    """
    Tracks payments FROM platform TO NGOs/beneficiaries.
    
    Use cases:
    - Transfer raised funds to NGO after campaign completion
    - Refund donor if campaign fails
    - Bulk disbursements to beneficiaries
    
    Status flow:
    - pending: Payout initiated, waiting for M-Pesa/bank processing
    - processing: M-Pesa accepted request, in queue
    - completed: Money successfully sent
    - failed: Payout failed (insufficient balance, invalid number, etc.)
    """
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True)
    
    # Recipient
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    ngo_id = Column(Integer, ForeignKey('ngos.id'), nullable=True)
    recipient_phone = Column(String(20), nullable=False)  # M-Pesa recipient
    recipient_name = Column(String(200))
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='KES')  # M-Pesa is KES only
    payment_method = Column(String(20), default='mpesa_b2c')
    
    # M-Pesa specific
    conversation_id = Column(String(100))  # M-Pesa ConversationID
    originator_conversation_id = Column(String(100))  # M-Pesa OriginatorConversationID
    transaction_id = Column(String(100))  # M-Pesa TransactionID (receipt)
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    status_message = Column(Text)
    
    # Metadata
    purpose = Column(String(200))  # "Campaign disbursement", "Refund", etc.
    remarks = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    campaign = relationship("Campaign", backref="payouts", foreign_keys=[campaign_id])
    ngo = relationship("NGO", backref="payouts", foreign_keys=[ngo_id])
    
    def __repr__(self):
        return f"<Payout(id={self.id}, amount={self.amount} {self.currency}, status={self.status})>"
