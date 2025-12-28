"""
Multi-turn donation conversation flow
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from voice.session_manager import (
    SessionManager,
    ConversationState,
    DonationStep
)
from database.models import Campaign, Donation, User
import re


class DonationConversation:
    """Handle multi-turn donation conversation"""
    
    @staticmethod
    async def start(user_id: str, db: Session) -> Dict[str, str]:
        """
        Start donation conversation
        
        Returns:
            message: Bot response
            campaigns: List of active campaigns
        """
        # Create session
        SessionManager.create_session(user_id, ConversationState.DONATING)
        SessionManager.update_session(
            user_id,
            current_step=DonationStep.SELECT_CAMPAIGN.value,
            message="Started donation flow"
        )
        
        # Get active campaigns
        campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).limit(5).all()
        
        # Format response
        message = "Great! Which campaign would you like to support? 🎯\n\n"
        for camp in campaigns:
            message += f"• {camp.title} (#{camp.id})\n"
        message += "\nOr say the campaign name."
        
        return {
            "message": message,
            "campaigns": [{"id": c.id, "title": c.title} for c in campaigns],
            "step": DonationStep.SELECT_CAMPAIGN.value
        }
    
    @staticmethod
    async def handle_campaign_selection(
        user_id: str,
        user_message: str,
        db: Session
    ) -> Dict[str, str]:
        """
        Process campaign selection
        
        Args:
            user_message: e.g., "Education", "campaign 2", "#42"
        """
        # Try to extract campaign ID or name
        campaign = None
        
        # Check for ID pattern (#42, "campaign 2", "2")
        id_match = re.search(r'#?(\d+)', user_message)
        if id_match:
            campaign_id = int(id_match.group(1))
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        # Fallback: Search by title
        if not campaign:
            campaign = db.query(Campaign).filter(
                Campaign.title.ilike(f"%{user_message}%")
            ).first()
        
        if not campaign:
            return {
                "message": "I couldn't find that campaign. Please try again or use the campaign number.",
                "step": DonationStep.SELECT_CAMPAIGN.value
            }
        
        # Save to session
        SessionManager.update_session(
            user_id,
            current_step=DonationStep.ENTER_AMOUNT.value,
            data_update={
                "campaign_id": campaign.id,
                "campaign_title": campaign.title
            },
            message=f"Selected campaign: {campaign.title}"
        )
        
        return {
            "message": f"Excellent choice! How much would you like to donate to {campaign.title}? 💰",
            "step": DonationStep.ENTER_AMOUNT.value,
            "campaign": {"id": campaign.id, "title": campaign.title}
        }
    
    @staticmethod
    async def handle_amount(
        user_id: str,
        user_message: str
    ) -> Dict[str, str]:
        """
        Process amount entry
        
        Args:
            user_message: e.g., "100", "500 birr", "fifty dollars"
        """
        session = SessionManager.get_session(user_id)
        campaign_title = session["data"]["campaign_title"]
        
        # Extract number from message
        amount = DonationConversation._extract_amount(user_message)
        
        if not amount or amount < 10:
            return {
                "message": "Please enter a valid amount (minimum 10).",
                "step": DonationStep.ENTER_AMOUNT.value
            }
        
        # Save amount
        SessionManager.update_session(
            user_id,
            current_step=DonationStep.SELECT_PAYMENT.value,
            data_update={"amount": amount},
            message=f"Entered amount: {amount}"
        )
        
        return {
            "message": f"Perfect! {amount} to {campaign_title}.\n\n"
                      f"How would you like to pay? 💳\n"
                      f"• Chapa\n"
                      f"• Telebirr\n"
                      f"• M-Pesa",
            "step": DonationStep.SELECT_PAYMENT.value
        }
    
    @staticmethod
    async def handle_payment_method(
        user_id: str,
        user_message: str
    ) -> Dict[str, str]:
        """Process payment method selection"""
        session = SessionManager.get_session(user_id)
        
        # Map to payment provider
        message_lower = user_message.lower()
        if "chapa" in message_lower:
            provider = "chapa"
        elif "telebirr" in message_lower or "tele" in message_lower:
            provider = "telebirr"
        elif "mpesa" in message_lower or "m-pesa" in message_lower:
            provider = "mpesa"
        else:
            return {
                "message": "Please choose Chapa, Telebirr, or M-Pesa.",
                "step": DonationStep.SELECT_PAYMENT.value
            }
        
        # Save payment method
        SessionManager.update_session(
            user_id,
            current_step=DonationStep.CONFIRM.value,
            data_update={"payment_provider": provider},
            message=f"Selected payment: {provider}"
        )
        
        # Show summary
        data = session["data"]
        message = (
            f"📋 Summary:\n"
            f"• Amount: {data['amount']}\n"
            f"• Campaign: {data['campaign_title']}\n"
            f"• Payment: {provider.title()}\n\n"
            f"Type 'confirm' to proceed or 'cancel' to stop."
        )
        
        return {
            "message": message,
            "step": DonationStep.CONFIRM.value,
            "summary": data
        }
    
    @staticmethod
    async def handle_confirmation(
        user_id: str,
        user_message: str,
        db: Session
    ) -> Dict[str, str]:
        """Process final confirmation"""
        session = SessionManager.get_session(user_id)
        
        message_lower = user_message.lower()
        
        if "cancel" in message_lower or "no" in message_lower:
            SessionManager.end_session(user_id)
            return {
                "message": "Donation cancelled. Let me know if you'd like to try again!",
                "step": "cancelled"
            }
        
        if "confirm" in message_lower or "yes" in message_lower:
            # Process donation
            data = session["data"]
            
            # Get or create user for donation
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
            
            # For testing: create temp user if not exists
            if not user:
                from datetime import datetime
                user = User(
                    telegram_user_id=user_id,
                    full_name="Test User",
                    role="DONOR",
                    preferred_language="en",
                    is_approved=True,
                    created_at=datetime.utcnow()
                )
                db.add(user)
                db.flush()
            
            donation = Donation(
                campaign_id=data["campaign_id"],
                donor_id=user.id,
                amount=data["amount"],
                currency="USD",
                payment_method=data["payment_provider"],
                status="pending"
            )
            db.add(donation)
            db.commit()
            
            # TODO: Initiate payment with Chapa/Telebirr/M-Pesa
            # For now, mark as complete
            donation.status = "completed"
            db.commit()
            
            # End session
            SessionManager.end_session(user_id)
            
            return {
                "message": f"✅ Donation successful! Thank you for supporting {data['campaign_title']}!",
                "step": "completed",
                "donation_id": donation.id
            }
        
        return {
            "message": "Please type 'confirm' to proceed or 'cancel' to stop.",
            "step": DonationStep.CONFIRM.value
        }
    
    @staticmethod
    def _extract_amount(text: str) -> Optional[int]:
        """Extract numeric amount from text"""
        # Remove currency words
        text = re.sub(r'\b(birr|dollar|usd|etb|kes)\b', '', text, flags=re.IGNORECASE)
        
        # Find number
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))
        
        # TODO: Handle word numbers ("fifty" -> 50)
        return None


# Main conversation router

async def route_donation_message(
    user_id: str,
    message: str,
    db: Session
) -> Dict[str, str]:
    """
    Route message to appropriate donation flow handler
    
    Args:
        user_id: Telegram user ID
        message: User's message text
        db: Database session
        
    Returns:
        Bot response with next step
    """
    session = SessionManager.get_session(user_id)
    
    if not session:
        return await DonationConversation.start(user_id, db)
    
    current_step = session.get("current_step")
    
    if current_step == DonationStep.SELECT_CAMPAIGN.value:
        return await DonationConversation.handle_campaign_selection(user_id, message, db)
    
    elif current_step == DonationStep.ENTER_AMOUNT.value:
        return await DonationConversation.handle_amount(user_id, message)
    
    elif current_step == DonationStep.SELECT_PAYMENT.value:
        return await DonationConversation.handle_payment_method(user_id, message)
    
    elif current_step == DonationStep.CONFIRM.value:
        return await DonationConversation.handle_confirmation(user_id, message, db)
    
    else:
        return {"message": "Something went wrong. Let's start over.", "step": "error"}
