"""
Multi-turn donation conversation flow

LAB 9 Enhancement: Clarification, context switching, user preferences, and analytics
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from voice.session_manager import (
    SessionManager,
    ConversationState,
    DonationStep
)
from database.models import Campaign, Donation, User
from voice.conversation.clarification import (
    ClarificationHandler,
    ConversationRepair
)
from voice.conversation.context_switcher import (
    ConversationContext,
    InterruptDetector,
    generate_resume_prompt
)
from voice.conversation.preferences import (
    PreferenceManager,
    PreferenceLearner
)
from voice.conversation.analytics import ConversationAnalytics
import re
import uuid
import logging

logger = logging.getLogger(__name__)


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
        # Generate session_id for analytics
        session_id = str(uuid.uuid4())
        
        # Create session
        SessionManager.create_session(user_id, ConversationState.DONATING)
        SessionManager.update_session(
            user_id,
            current_step=DonationStep.SELECT_CAMPAIGN.value,
            message="Started donation flow",
            data_update={"session_id": session_id}
        )
        
        # LAB 9 Part 4: Track conversation start
        user = db.query(User).filter(User.telegram_user_id == user_id).first()
        if user:
            ConversationAnalytics.track_event(
                db=db,
                user_id=user.id,
                session_id=session_id,
                event_type="conversation_started",
                conversation_state="donating",
                current_step="select_campaign"
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
        Process campaign selection with fuzzy matching
        
        LAB 9: Uses ClarificationHandler for typo tolerance and disambiguation
        
        Args:
            user_message: e.g., "Education", "educashun", "campaign 2", "#42"
        """
        # Try to extract campaign ID or name
        campaign = None
        
        # Check for ID pattern (#42, "campaign 2", "2")
        id_match = re.search(r'#?(\d+)', user_message)
        if id_match:
            campaign_id = int(id_match.group(1))
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        # LAB 9: Use fuzzy matching for campaign name
        if not campaign:
            result = await ClarificationHandler.handle_ambiguous_campaign(
                user_id, user_message, db
            )
            
            if result["type"] == "exact_match":
                # High confidence match found
                campaign_data = result["campaign"]
                campaign = db.query(Campaign).filter(
                    Campaign.id == campaign_data["id"]
                ).first()
            elif result["type"] == "clarification_needed":
                # Multiple matches - need user to clarify
                return {
                    "message": result["message"],
                    "step": "clarification",
                    "options": result["options"]
                }
            else:
                # No matches found
                return {
                    "message": result["message"],
                    "step": DonationStep.SELECT_CAMPAIGN.value
                }
        
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
        
        # LAB 9 Part 4: Track campaign selection
        session_data = SessionManager.get_session(user_id)
        session_id = session_data.get("data", {}).get("session_id")
        if user and session_id:
            ConversationAnalytics.track_event(
                db=db,
                user_id=user.id,
                session_id=session_id,
                event_type="step_completed",
                conversation_state="donating",
                current_step="campaign_selected",
                metadata={"campaign_id": campaign.id, "campaign_title": campaign.title}
            )
        
        # LAB 9 Part 3: Suggest amount based on user history
        amount_suggestion = ""
        user = db.query(User).filter(User.telegram_user_id == user_id).first()
        if user:
            suggested_amount = PreferenceManager.get_preference(
                user.id, "donation_amount", db
            )
            if suggested_amount:
                amount_suggestion = f"\n\n💡 Your usual amount is {suggested_amount} birr. Use this? (say 'yes' or enter different amount)"
        
        return {
            "message": f"Excellent choice! How much would you like to donate to {campaign.title}? 💰{amount_suggestion}",
            "step": DonationStep.ENTER_AMOUNT.value,
            "campaign": {"id": campaign.id, "title": campaign.title}
        }
    
    @staticmethod
    async def handle_amount(
        user_id: str,
        user_message: str,
        db: Session
    ) -> Dict[str, str]:
        """
        Process amount entry with word number parsing and preferences
        
        LAB 9 Part 1: ClarificationHandler.parse_number_with_units
        LAB 9 Part 3: Suggests default amount from preferences
        
        Args:
            user_message: e.g., "100", "500 birr", "fifty dollars", "five hundred", "yes" (for default)
        """
        session = SessionManager.get_session(user_id)
        campaign_title = session["data"]["campaign_title"]
        
        # Get user from session (telegram_user_id → user_id)
        user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        # LAB 9 Part 3: Check if user wants to use suggested default
        if user and user_message.lower() in ["yes", "y", "use default", "default"]:
            suggested_amount = PreferenceManager.get_preference(
                user.id, "donation_amount", db
            )
            if suggested_amount:
                amount = int(suggested_amount)
                # Save amount
                SessionManager.update_session(
                    user_id,
                    current_step=DonationStep.SELECT_PAYMENT.value,
                    data_update={"amount": amount},
                    message=f"Using default amount: {amount}"
                )
                
                return {
                    "message": f"Perfect! {amount} birr to {campaign_title}.\n\n"
                              f"How would you like to pay? 💳\n"
                              f"• Chapa\n"
                              f"• Telebirr\n"
                              f"• M-Pesa",
                    "step": DonationStep.SELECT_PAYMENT.value
                }
        
        # LAB 9 Part 1: Use enhanced number parser (handles word numbers)
        amount = ClarificationHandler.parse_number_with_units(user_message)
        
        if not amount or amount < 10:
            return {
                "message": "Please enter a valid amount (minimum 10). "
                          "You can say '50', 'fifty', or '500 birr'.",
                "step": DonationStep.ENTER_AMOUNT.value
            }
        
        # Save amount
        SessionManager.update_session(
            user_id,
            current_step=DonationStep.SELECT_PAYMENT.value,
            data_update={"amount": amount},
            message=f"Entered amount: {amount}"
        )
        
        # LAB 9 Part 4: Track amount entry
        session_data = SessionManager.get_session(user_id)
        session_id = session_data.get("data", {}).get("session_id")
        if user and session_id:
            ConversationAnalytics.track_event(
                db=db,
                user_id=user.id,
                session_id=session_id,
                event_type="step_completed",
                conversation_state="donating",
                current_step="amount_entered",
                metadata={"amount": amount}
            )
        
        # LAB 9 Part 3: Suggest payment method preference
        payment_suggestion = ""
        if user:
            suggested_provider = PreferenceManager.get_preference(
                user.id, "payment_provider", db
            )
            if suggested_provider:
                payment_suggestion = f"\n\n💡 Use your usual {suggested_provider.title()}? (say 'yes' or choose another)"
        
        return {
            "message": f"Perfect! {amount} birr to {campaign_title}.\n\n"
                      f"How would you like to pay? 💳\n"
                      f"• Chapa\n"
                      f"• Telebirr\n"
                      f"• M-Pesa{payment_suggestion}",
            "step": DonationStep.SELECT_PAYMENT.value
        }
    
    @staticmethod
    async def handle_payment_method(
        user_id: str,
        user_message: str,
        db: Session
    ) -> Dict[str, str]:
        """
        Process payment method selection with preferences
        
        LAB 9 Part 3: Supports "yes" for default payment method
        """
        session = SessionManager.get_session(user_id)
        
        # Get user from session
        user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        # LAB 9 Part 3: Check if user wants to use suggested default
        if user and user_message.lower() in ["yes", "y", "use default", "default"]:
            suggested_provider = PreferenceManager.get_preference(
                user.id, "payment_provider", db
            )
            if suggested_provider:
                provider = suggested_provider
            else:
                return {
                    "message": "Please choose Chapa, Telebirr, or M-Pesa.",
                    "step": DonationStep.SELECT_PAYMENT.value
                }
        else:
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
        
        # LAB 9 Part 4: Track payment method selection
        session_data = SessionManager.get_session(user_id)
        session_id = session_data.get("data", {}).get("session_id")
        user = db.query(User).filter(User.telegram_user_id == user_id).first()
        if user and session_id:
            ConversationAnalytics.track_event(
                db=db,
                user_id=user.id,
                session_id=session_id,
                event_type="step_completed",
                conversation_state="donating",
                current_step="payment_selected",
                metadata={"payment_provider": provider}
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
            # LAB 9 Part 4: Track abandonment
            session_data = SessionManager.get_session(user_id)
            session_id = session_data.get("data", {}).get("session_id")
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
            if user and session_id:
                ConversationAnalytics.track_event(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    event_type="conversation_abandoned",
                    conversation_state="donating",
                    current_step="cancelled",
                    metadata={"reason": "user_cancelled"}
                )
            
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
            
            # Payment will be confirmed via webhook callback (M-Pesa/Stripe)
            # Donation stays in 'pending' status until payment processor confirms
            logger.info(f"Donation {donation.id} created as pending, awaiting payment confirmation")
            
            # LAB 9 Part 3: Learn from completed donation
            PreferenceManager.learn_from_donation(
                user.id,
                {
                    "payment_provider": data["payment_provider"],
                    "amount": data["amount"]
                },
                db
            )
            
            # LAB 9 Part 4: Track successful completion
            session_id = session["data"].get("session_id")
            if session_id:
                ConversationAnalytics.track_event(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    event_type="conversation_completed",
                    conversation_state="donating",
                    current_step="completed",
                    metadata={
                        "donation_id": donation.id,
                        "amount": data["amount"],
                        "campaign_id": data["campaign_id"]
                    }
                )
            
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
    
    LAB 9 Part 1-2: Handles clarifications, corrections, and context switching
    
    Args:
        user_id: Telegram user ID
        message: User's message text
        db: Database session
        
    Returns:
        Bot response with next step
    """
    session = SessionManager.get_session(user_id)
    current_state = ConversationState(session["state"]) if session else ConversationState.IDLE
    
    # LAB 9 Part 2: Check for resume request
    if InterruptDetector.is_resume_request(message):
        if ConversationContext.has_paused_conversation(user_id):
            restored = ConversationContext.resume_conversation(user_id)
            if restored:
                prompt = generate_resume_prompt(restored)
                return {
                    "message": prompt,
                    "step": restored.get("step", "resumed"),
                    "resumed": True
                }
        return {
            "message": "No paused conversation to resume. Would you like to start a donation?",
            "step": "idle"
        }
    
    # LAB 9 Part 2: Check for interrupts (questions, navigation)
    if InterruptDetector.is_interrupt(message, current_state):
        interrupt_type = InterruptDetector.classify_interrupt(message)
        
        if interrupt_type == "navigation":
            # Handle cancel/stop
            if any(word in message.lower() for word in ["cancel", "stop", "quit", "exit"]):
                cleared = ConversationContext.clear_all_contexts(user_id)
                SessionManager.end_session(user_id)
                return {
                    "message": "Cancelled. Let me know if you'd like to start again!",
                    "step": "cancelled"
                }
            
            # Handle "go back" - resume previous context
            elif "go back" in message.lower():
                if ConversationContext.has_paused_conversation(user_id):
                    restored = ConversationContext.resume_conversation(user_id)
                    if restored:
                        prompt = generate_resume_prompt(restored)
                        return {
                            "message": prompt,
                            "step": restored.get("step", "resumed")
                        }
                return {
                    "message": "Nothing to go back to. Let's start fresh!",
                    "step": "idle"
                }
        
        elif interrupt_type == "question":
            # Pause current conversation to handle question
            if session and current_state != ConversationState.IDLE:
                paused = ConversationContext.pause_current_conversation(
                    user_id,
                    "user_asked_question"
                )
                
                # For now, return a simple acknowledgment
                # In production, this would call handle_general_query()
                return {
                    "message": f"Let me answer that: [Question handler would process: '{message}']\n\n"
                              f"💬 Type 'continue' to resume your donation.",
                    "step": "question_answered",
                    "paused": True
                }
    
    if not session:
        return await DonationConversation.start(user_id, db)
    
    # LAB 9 Part 1: Check for pending clarification
    if session and session["data"].get("pending_clarification"):
        campaign = await ClarificationHandler.resolve_clarification(
            user_id, message, db
        )
        if campaign:
            # Clarification resolved - proceed to amount
            SessionManager.update_session(
                user_id,
                current_step=DonationStep.ENTER_AMOUNT.value,
                data_update={
                    "campaign_id": campaign.id,
                    "campaign_title": campaign.title,
                    "pending_clarification": None,
                    "clarification_options": None
                }
            )
            return {
                "message": f"Perfect! {campaign.title}. How much would you like to donate? 💰",
                "step": DonationStep.ENTER_AMOUNT.value
            }
        else:
            # Still unclear - ask again
            return {
                "message": "Please select a number from the list or type the full campaign name.",
                "step": "clarification"
            }
    
    # LAB 9 Part 1: Check for corrections ("actually...", "I meant...", etc.)
    if ConversationRepair.is_correction(message):
        result = await ConversationRepair.handle_correction(user_id, message, db)
        return result
    
    current_step = session.get("current_step")
    
    if current_step == DonationStep.SELECT_CAMPAIGN.value:
        return await DonationConversation.handle_campaign_selection(user_id, message, db)
    
    elif current_step == DonationStep.ENTER_AMOUNT.value:
        return await DonationConversation.handle_amount(user_id, message, db)
    
    elif current_step == DonationStep.SELECT_PAYMENT.value:
        return await DonationConversation.handle_payment_method(user_id, message, db)
    
    elif current_step == DonationStep.CONFIRM.value:
        return await DonationConversation.handle_confirmation(user_id, message, db)
    
    else:
        return {"message": "Something went wrong. Let's start over.", "step": "error"}