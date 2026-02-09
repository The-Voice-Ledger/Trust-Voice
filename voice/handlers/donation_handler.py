"""
Voice Donation Handler
Processes donation requests initiated via voice commands
"""

import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Campaign, Donor, Donation, User
from services.mpesa import mpesa_stk_push
from services.stripe_service import create_payment_intent
from voice.session_manager import SessionManager, ConversationState, DonationStep

logger = logging.getLogger(__name__)


async def initiate_voice_donation(
    db: Session,
    telegram_user_id: str,
    campaign_id: uuid.UUID,
    amount: float,
    currency: str = "USD",
    payment_method: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initiate donation via voice command
    
    Args:
        db: Database session
        telegram_user_id: User's Telegram ID
        campaign_id: Campaign to donate to
        amount: Donation amount
        currency: Currency code (USD, KES, etc.)
        payment_method: Optional preferred method ("mpesa", "stripe")
        
    Returns:
        {
            "success": True/False,
            "donation_id": uuid,
            "payment_method": "mpesa"|"stripe",
            "instructions": "Payment instructions text",
            "checkout_url": "https://..." (for Stripe),
            "error": "Error message" (if failed)
        }
    """
    try:
        # Get or create donor
        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
        if not user:
            return {
                "success": False,
                "error": "User not registered. Please register first."
            }
        
        # Get or create donor record
        donor = db.query(Donor).filter(
            Donor.telegram_user_id == telegram_user_id
        ).first()
        
        if not donor:
            # Create donor from user
            donor = Donor(
                id=uuid.uuid4(),
                telegram_user_id=telegram_user_id,
                phone_number=user.phone_number,
                full_name=user.full_name,
                email=None,  # Optional
                created_at=datetime.utcnow()
            )
            db.add(donor)
            db.flush()  # Get donor ID but don't commit yet
            logger.info(f"Created donor record for user {telegram_user_id}")
        
        # Validate campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {
                "success": False,
                "error": "Campaign not found"
            }
        
        if campaign.status != "active":
            return {
                "success": False,
                "error": f"Campaign is not active (status: {campaign.status})"
            }
        
        # Determine payment method and validate requirements
        if not payment_method:
            if donor.phone_number and donor.phone_number.startswith("+254"):
                payment_method = "mpesa"
            elif currency == "KES":
                payment_method = "mpesa"
            else:
                payment_method = "stripe"
        
        # Validate phone number for M-Pesa
        if payment_method == "mpesa" and not donor.phone_number:
            return {
                "success": False,
                "error": "Phone number required for M-Pesa payments. Please update your profile with /settings"
            }
        
        # Convert amount to USD using currency service
        amount_usd = amount
        if currency != "USD":
            try:
                from services.currency_service import currency_service
                amount_usd = currency_service.convert_to_usd(amount, currency)
            except Exception as e:
                logger.error(f"Currency conversion failed: {e}")
                return {
                    "success": False,
                    "error": f"Unable to convert {currency} to USD. Please try USD directly."
                }
        
        # Create donation record (pending) - DON'T COMMIT YET
        donation = Donation(
            id=uuid.uuid4(),
            donor_id=donor.id,
            campaign_id=campaign_id,
            amount_usd=amount_usd,
            currency=currency,
            status="pending",
            payment_method=payment_method,
            created_at=datetime.utcnow()
        )
        db.add(donation)
        db.flush()  # Get donation ID but don't commit transaction yet
        
        logger.info(f"Created donation {donation.id}: ${amount_usd} USD to campaign {campaign_id}")
        
        # Initiate payment - only commit if successful
        try:
            if payment_method == "mpesa":
                result = await _initiate_mpesa_payment(db, donation, donor, campaign, amount, currency)
            else:
                result = await _initiate_stripe_payment(db, donation, donor, campaign, amount_usd)
            
            # Payment initiated successfully - commit the transaction
            if result.get("success"):
                db.commit()
                logger.info(f"✅ Payment initiated and donation committed: {donation.id}")
            else:
                # Payment initiation failed - rollback
                db.rollback()
                logger.warning(f"⚠️ Payment initiation failed, donation rolled back: {result.get('error')}")
            
            return result
        except Exception as e:
            # Any error - rollback the transaction
            db.rollback()
            logger.error(f"❌ Payment initiation error, rolled back: {e}")
            raise
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initiating donation: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to initiate donation: {str(e)}"
        }


async def _initiate_mpesa_payment(
    db: Session,
    donation: Donation,
    donor: Donor,
    campaign: Campaign,
    amount: float,
    currency: str
) -> Dict[str, Any]:
    """Initiate M-Pesa STK Push payment"""
    try:
        # Validate phone number
        phone = donor.phone_number
        if not phone:
            return {
                "success": False,
                "donation_id": donation.id,
                "error": "Phone number required for M-Pesa. Please update your profile."
            }
        
        # M-Pesa expects KES amount
        if currency != "KES":
            # Convert to KES using currency service
            try:
                from services.currency_service import currency_service
                amount_kes = currency_service.convert(amount, currency, "KES")
            except Exception:
                # Fallback to approximate rate
                amount_kes = amount * 130  # 1 USD ≈ 130 KES
        else:
            amount_kes = amount
        
        # Floor to nearest whole number (favor donor, M-Pesa doesn't accept decimals)
        import math
        amount_kes = int(math.floor(amount_kes))
        
        logger.info(f"Initiating M-Pesa STK Push: {phone}, {amount_kes} KES for donation {donation.id}")
        
        # Call M-Pesa service
        result = mpesa_stk_push(
            phone_number=phone,
            amount=amount_kes,
            account_reference=f"DONATION-{str(donation.id)[:8]}",
            transaction_desc=f"Donation to {campaign.title[:20]}"
        )
        
        if result.get("success"):
            # Update donation with transaction info
            donation.payment_transaction_id = result.get("CheckoutRequestID")
            db.commit()
            
            instructions = (
                f"📱 M-Pesa Payment Initiated\n\n"
                f"Amount: KES {amount_kes:,}\n"
                f"Phone: {phone}\n\n"
                f"✅ Check your phone for M-Pesa prompt\n"
                f"📲 Enter your M-Pesa PIN to complete\n\n"
                f"💡 You'll receive confirmation once payment is processed."
            )
            
            return {
                "success": True,
                "donation_id": donation.id,
                "payment_method": "mpesa",
                "instructions": instructions,
                "checkout_request_id": result.get("CheckoutRequestID")
            }
        else:
            donation.status = "failed"
            donation.payment_error = result.get("error", "M-Pesa payment failed")
            db.commit()
            
            return {
                "success": False,
                "donation_id": donation.id,
                "error": f"M-Pesa error: {result.get('error', 'Unknown error')}"
            }
        
    except Exception as e:
        logger.error(f"M-Pesa payment error: {str(e)}")
        donation.status = "failed"
        donation.payment_error = str(e)
        db.commit()
        
        return {
            "success": False,
            "donation_id": donation.id,
            "error": f"M-Pesa payment failed: {str(e)}"
        }


async def _initiate_stripe_payment(
    db: Session,
    donation: Donation,
    donor: Donor,
    campaign: Campaign,
    amount_usd: float
) -> Dict[str, Any]:
    """Initiate Stripe card payment"""
    try:
        # Convert amount to cents (Stripe expects smallest currency unit)
        amount_cents = int(amount_usd * 100)
        
        logger.info(f"Creating Stripe payment intent: ${amount_usd} for donation {donation.id}")
        
        # Create Stripe payment intent
        result = create_payment_intent(
            amount=amount_cents,
            currency="usd",
            description=f"Donation to {campaign.title}",
            metadata={
                "donation_id": str(donation.id),
                "campaign_id": str(campaign.id),
                "donor_id": str(donor.id),
                "campaign_title": campaign.title
            }
        )
        
        if result.get("success"):
            payment_intent = result["payment_intent"]
            
            # Update donation with Stripe info
            donation.payment_transaction_id = payment_intent["id"]
            donation.stripe_payment_intent_id = payment_intent["id"]
            db.commit()
            
            # Generate checkout URL (this would be your hosted checkout page)
            # For now, return the client secret for frontend integration
            checkout_url = f"https://trustvoice.com/donate/checkout?payment_intent={payment_intent['client_secret']}"
            
            instructions = (
                f"💳 Card Payment Ready\n\n"
                f"Amount: ${amount_usd:.2f} USD\n"
                f"Campaign: {campaign.title}\n\n"
                f"Click the link below to complete your donation securely:\n"
                f"{checkout_url}\n\n"
                f"💡 You can pay with any credit/debit card."
            )
            
            return {
                "success": True,
                "donation_id": donation.id,
                "payment_method": "stripe",
                "instructions": instructions,
                "checkout_url": checkout_url,
                "client_secret": payment_intent["client_secret"]
            }
        else:
            donation.status = "failed"
            donation.payment_error = result.get("error", "Stripe payment failed")
            db.commit()
            
            return {
                "success": False,
                "donation_id": donation.id,
                "error": f"Payment setup failed: {result.get('error', 'Unknown error')}"
            }
        
    except Exception as e:
        logger.error(f"Stripe payment error: {str(e)}")
        donation.status = "failed"
        donation.payment_error = str(e)
        db.commit()
        
        return {
            "success": False,
            "donation_id": donation.id,
            "error": f"Payment setup failed: {str(e)}"
        }


async def get_donation_status(
    db: Session,
    telegram_user_id: str,
    donation_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Get status of donation(s) for a user
    
    Args:
        db: Database session
        telegram_user_id: User's Telegram ID
        donation_id: Optional specific donation ID (gets most recent if None)
        
    Returns:
        Donation status information
    """
    try:
        # Get donor
        donor = db.query(Donor).filter(
            Donor.telegram_user_id == telegram_user_id
        ).first()
        
        if not donor:
            return {
                "success": False,
                "error": "No donations found. Please make a donation first."
            }
        
        # Get donation
        if donation_id:
            donation = db.query(Donation).filter(
                Donation.id == donation_id,
                Donation.donor_id == donor.id
            ).first()
        else:
            # Get most recent donation
            donation = db.query(Donation).filter(
                Donation.donor_id == donor.id
            ).order_by(Donation.created_at.desc()).first()
        
        if not donation:
            return {
                "success": False,
                "error": "Donation not found"
            }
        
        # Get campaign details
        campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
        
        # Format status
        status_emojis = {
            "pending": "⏳",
            "completed": "✅",
            "failed": "❌",
            "refunded": "↩️"
        }
        
        status_text = {
            "pending": "Payment in progress",
            "completed": "Payment successful",
            "failed": "Payment failed",
            "refunded": "Payment refunded"
        }
        
        return {
            "success": True,
            "donation": {
                "id": str(donation.id),
                "amount": donation.amount_usd,
                "currency": donation.currency,
                "status": donation.status,
                "status_emoji": status_emojis.get(donation.status, "❓"),
                "status_text": status_text.get(donation.status, "Unknown"),
                "campaign_title": campaign.title if campaign else "Unknown",
                "created_at": donation.created_at.isoformat(),
                "transaction_id": donation.payment_transaction_id,
                "payment_method": donation.payment_method,
                "error": donation.payment_error if donation.status == "failed" else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting donation status: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get donation status: {str(e)}"
        }


# ============================================================================
# LAB 8: Multi-turn Conversational Donations
# ============================================================================

async def start_conversational_donation(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Start conversational donation flow (Lab 8)
    
    Handler for "make_donation" intent when user doesn't have all details.
    Starts a multi-step conversation to collect campaign, amount, and payment info.
    
    Args:
        entities: Extracted entities (may be empty or partial)
        user_id: User's telegram_user_id
        db: Database session
        context: Conversation context with transcript
        
    Returns:
        Success response with first question
    """
    from voice.workflows.donation_flow import DonationConversation
    from voice.workflows.search_flow import SearchConversation
    
    try:
        # Check if user mentioned a campaign reference in the transcript
        transcript = context.get("transcript", "") if context else ""
        campaign_id = None
        
        if transcript:
            # Try to extract campaign reference from transcript
            transcript_lower = transcript.lower()
            
            # Check if it mentions "campaign" with a reference
            if "campaign" in transcript_lower or "number" in transcript_lower:
                # Get campaign IDs from search session
                from voice.session_manager import SessionManager
                search_session = SessionManager.get_session(user_id)
                
                if search_session and search_session["data"].get("campaign_ids"):
                    campaign_ids = search_session["data"]["campaign_ids"]
                    
                    # Parse the campaign reference
                    parsed_id = SearchConversation._parse_campaign_ref(transcript, campaign_ids)
                    
                    if parsed_id:
                        campaign_id = parsed_id
        
        # If we found a campaign reference, skip to amount question
        if campaign_id:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            
            if campaign:
                # Check if amount was also provided
                amount = entities.get("amount")
                
                if amount:
                    # Both campaign and amount provided - start at payment method step
                    SessionManager.create_session(user_id, ConversationState.DONATING)
                    SessionManager.update_session(
                        user_id,
                        current_step=DonationStep.SELECT_PAYMENT.value,
                        data_update={
                            "campaign_id": campaign.id,
                            "campaign_title": campaign.title,
                            "amount": float(amount),
                            "currency": entities.get("currency", "USD")
                        },
                        message="Started donation with campaign and amount"
                    )
                    
                    return {
                        "success": True,
                        "message": f"Perfect! You want to donate ${amount} to {campaign.title}. How would you like to pay? (M-Pesa or Card)",
                        "data": {
                            "campaign": {"id": campaign.id, "title": campaign.title},
                            "amount": amount,
                            "step": DonationStep.SELECT_PAYMENT.value
                        }
                    }
                else:
                    # Only campaign provided - ask for amount
                    SessionManager.create_session(user_id, ConversationState.DONATING)
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
                        "success": True,
                        "message": f"Great! How much would you like to donate to {campaign.title}? 💰",
                        "data": {
                            "campaign": {"id": campaign.id, "title": campaign.title},
                            "step": DonationStep.ENTER_AMOUNT.value
                        }
                    }
        
        # Check if amount was provided without campaign
        amount = entities.get("amount")
        if amount:
            # Start at campaign selection with amount pre-filled
            result = await DonationConversation.start(user_id, db)
            result["message"] = f"Perfect! You want to donate ${amount}. {result['message']}"
            
            # Store amount in session
            SessionManager.update_session(
                user_id,
                data_update={
                    "amount": float(amount),
                    "currency": entities.get("currency", "USD")
                }
            )
            
            return {
                "success": True,
                "message": result["message"],
                "data": {
                    "campaigns": result.get("campaigns", []),
                    "amount": amount,
                    "step": result["step"]
                }
            }
        
        # Default: Start from the beginning
        result = await DonationConversation.start(user_id, db)
        
        return {
            "success": True,
            "message": result["message"],
            "data": {
                "campaigns": result.get("campaigns", []),
                "step": result["step"]
            }
        }
    
    except Exception as e:
        logger.error(f"Error starting donation conversation: {e}")
        return {
            "success": False,
            "message": "Sorry, I couldn't start the donation process. Please try again.",
            "error": str(e)
        }


    
    # This would normally be called from the bot
    # Example: User says "Donate $50 to clean water project"
    # NLU extracts: {amount: 50, currency: USD, campaign_name: "clean water"}
    # Bot finds campaign and calls initiate_voice_donation()
