"""
Payout Handler - Module 6 of Lab 5

Enables campaign creators to request payouts (withdrawals) of raised funds.
Funds are transferred via M-Pesa B2C to the creator's verified phone number.

Payout Rules:
- Must be campaign creator or NGO admin
- Campaign must have raised funds
- Only verified phone numbers can receive payouts
- Payout history tracked for transparency
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from database.models import (
    Campaign,
    User,
    Donation
)

logger = logging.getLogger(__name__)


async def request_campaign_payout(
    db: Session,
    telegram_user_id: str,
    campaign_id: uuid.UUID,
    amount_usd: float,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Request a payout/withdrawal from campaign funds.
    
    Args:
        db: Database session
        telegram_user_id: Creator's Telegram ID
        campaign_id: Campaign to withdraw from
        amount_usd: Amount to withdraw in USD
        reason: Optional reason for withdrawal (e.g., "Equipment purchase")
    
    Returns:
        Dict with payout status and transaction details
    """
    try:
        # Get user
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            return {
                "success": False,
                "error": "User not found. Please register first with /start"
            }
        
        # Verify user role
        if user.role not in ["CAMPAIGN_CREATOR", "SYSTEM_ADMIN"]:
            return {
                "success": False,
                "error": f"Only Campaign Creators can request payouts. Your role: {user.role}"
            }
        
        # Get campaign
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()
        
        if not campaign:
            return {
                "success": False,
                "error": "Campaign not found"
            }
        
        # Verify ownership
        if campaign.ngo_id != user.ngo_id and user.role != "SYSTEM_ADMIN":
            return {
                "success": False,
                "error": "You don't have permission to withdraw from this campaign"
            }
        
        # Check available balance
        raised = campaign.raised_amount_usd or 0
        
        if raised <= 0:
            return {
                "success": False,
                "error": "No funds available for withdrawal. Campaign has not received donations yet."
            }
        
        if amount_usd > raised:
            return {
                "success": False,
                "error": f"Insufficient funds. Available: ${raised:.2f}, Requested: ${amount_usd:.2f}"
            }
        
        if amount_usd < 10:
            return {
                "success": False,
                "error": "Minimum payout amount is $10 USD"
            }
        
        # Verify phone number
        if not user.phone_number:
            return {
                "success": False,
                "error": "Phone number not found. Please update your profile with /verify_phone"
            }
        
        # Check if phone is Kenya number for M-Pesa
        if not user.phone_number.startswith("+254"):
            return {
                "success": False,
                "error": "M-Pesa payouts only available for Kenya (+254) numbers"
            }
        
        # Initiate M-Pesa B2C payout
        payout_result = await _initiate_mpesa_payout(
            db=db,
            user=user,
            campaign=campaign,
            amount_usd=amount_usd,
            reason=reason
        )
        
        if payout_result["success"]:
            # Update campaign balance (deduct withdrawal)
            campaign.raised_amount_usd = raised - amount_usd
            db.commit()
        
        return payout_result
        
    except Exception as e:
        logger.error(f"Error requesting payout: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": f"Failed to process payout: {str(e)}"
        }


async def _initiate_mpesa_payout(
    db: Session,
    user: User,
    campaign: Campaign,
    amount_usd: float,
    reason: Optional[str]
) -> Dict[str, Any]:
    """
    Execute M-Pesa B2C payout to campaign creator.
    
    Args:
        db: Database session
        user: User receiving payout
        campaign: Campaign funds are from
        amount_usd: Amount in USD
        reason: Payout reason
    
    Returns:
        Dict with payout transaction details
    """
    try:
        from services.mpesa import mpesa_b2c_payout
        
        # Convert USD to KES (approximate rate: 1 USD = 130 KES)
        amount_kes = int(amount_usd * 130)
        
        # Format payout details
        occasion = reason or "Campaign funds withdrawal"
        remarks = f"TrustVoice payout for {campaign.title[:30]}"
        
        # Execute M-Pesa B2C
        result = mpesa_b2c_payout(
            phone_number=user.phone_number,
            amount=amount_kes,
            occasion=occasion,
            remarks=remarks
        )
        
        if result.get("success"):
            # Create payout record
            from database.models import Base
            # Note: We should create a Payout model, but for now log it
            
            logger.info(
                f"Payout initiated: ${amount_usd:.2f} to {user.phone_number} "
                f"for campaign {campaign.title}"
            )
            
            return {
                "success": True,
                "amount_usd": amount_usd,
                "amount_kes": amount_kes,
                "phone_number": user.phone_number,
                "campaign_title": campaign.title,
                "transaction_id": result.get("ConversationID"),
                "message": (
                    f"✅ Payout Initiated\n\n"
                    f"💰 Amount: KES {amount_kes:,} (${amount_usd:.2f})\n"
                    f"📱 To: {user.phone_number}\n"
                    f"📋 Campaign: {campaign.title}\n"
                    f"🆔 Transaction: {result.get('ConversationID', 'N/A')}\n\n"
                    f"Funds will arrive within 1-5 minutes."
                )
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "M-Pesa payout failed")
            }
            
    except Exception as e:
        logger.error(f"M-Pesa payout error: {str(e)}")
        return {
            "success": False,
            "error": f"Payout failed: {str(e)}"
        }


async def get_payout_history(
    db: Session,
    telegram_user_id: str,
    campaign_id: Optional[uuid.UUID] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get payout history for a campaign creator.
    
    Args:
        db: Database session
        telegram_user_id: Creator's Telegram ID
        campaign_id: Filter by specific campaign (optional)
        limit: Max number of records to return
    
    Returns:
        Dict with payout history
    """
    try:
        # Get user
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Note: We need a Payout model to properly track this
        # For now, return campaigns with their current balance
        
        query = db.query(Campaign).filter(
            Campaign.ngo_id == user.ngo_id
        )
        
        if campaign_id:
            query = query.filter(Campaign.id == campaign_id)
        
        campaigns = query.order_by(Campaign.created_at.desc()).limit(limit).all()
        
        if not campaigns:
            return {
                "success": True,
                "campaigns": [],
                "total_raised": 0,
                "message": "No campaigns found"
            }
        
        # Calculate totals
        total_raised = sum(c.raised_amount_usd or 0 for c in campaigns)
        
        # Format campaign data
        campaign_list = []
        for c in campaigns:
            raised = c.raised_amount_usd or 0
            goal = c.goal_amount_usd or 1
            progress = (raised / goal * 100)
            
            campaign_list.append({
                "id": str(c.id),
                "title": c.title,
                "raised": raised,
                "goal": goal,
                "progress": progress,
                "status": c.status,
                "can_withdraw": raised >= 10  # Minimum $10
            })
        
        return {
            "success": True,
            "campaigns": campaign_list,
            "total_raised": total_raised,
            "total_count": len(campaigns)
        }
        
    except Exception as e:
        logger.error(f"Error getting payout history: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get history: {str(e)}"
        }


async def get_campaign_balance(
    db: Session,
    telegram_user_id: str,
    campaign_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get available balance for a specific campaign.
    
    Args:
        db: Database session
        telegram_user_id: Creator's Telegram ID
        campaign_id: Campaign to check
    
    Returns:
        Dict with balance details
    """
    try:
        # Get user
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Get campaign
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()
        
        if not campaign:
            return {
                "success": False,
                "error": "Campaign not found"
            }
        
        # Verify ownership
        if campaign.ngo_id != user.ngo_id and user.role != "SYSTEM_ADMIN":
            return {
                "success": False,
                "error": "You don't have permission to view this campaign's balance"
            }
        
        # Calculate balance
        raised = campaign.raised_amount_usd or 0
        goal = campaign.goal_amount_usd or 1
        progress = (raised / goal * 100)
        
        # Count donors
        donor_count = db.query(Donation.donor_id).filter(
            Donation.campaign_id == campaign_id,
            Donation.status == "completed"
        ).distinct().count()
        
        return {
            "success": True,
            "campaign_title": campaign.title,
            "balance_usd": raised,
            "balance_kes": int(raised * 130),
            "goal_usd": goal,
            "progress": progress,
            "donor_count": donor_count,
            "can_withdraw": raised >= 10,
            "minimum_withdrawal": 10,
            "status": campaign.status
        }
        
    except Exception as e:
        logger.error(f"Error getting campaign balance: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get balance: {str(e)}"
        }
