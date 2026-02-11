"""
General Intent Handlers - Lab 6 Part 4

Handles 4 general voice commands:
1. help - Show available commands
2. greeting - Welcome message
3. change_language - Switch between English/Amharic
4. unknown - Fallback for unrecognized intents
"""

import logging
import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session

from database.models import User
from voice.command_router import register_handler

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER 1: HELP
# ============================================================================

@register_handler("get_help")
async def handle_help(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Provide help and list available commands.
    
    Customizes help based on user role.
    """
    try:
        # Get user to determine role (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if not user:
            # Guest user (not registered)
            message = (
                "Welcome to Trust Voice! "
                "I can help you donate to campaigns using your voice. "
                "Here's what you can say: "
                "Find education campaigns. "
                "Show me campaign details. "
                "Donate 50 dollars. "
                "Show my donation history. "
                "To get started, say 'Find campaigns' or 'Show me education campaigns in Addis Ababa'."
            )
            
            return {
                "success": True,
                "message": message,
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "role": "guest",
                    "available_commands": [
                        "find campaigns",
                        "campaign details",
                        "donate",
                        "donation history"
                    ]
                }
            }
        
        # Build help based on role
        role = user.role
        
        if role == "DONOR":
            message = (
                "Hello! I'm your voice assistant for Trust Voice. "
                "Here's what you can say: "
                "Find education campaigns. "
                "Tell me more about campaign number 1. "
                "Donate 100 dollars to this campaign. "
                "Show my donation history. "
                "Get campaign updates. "
                "Show impact report. "
                "To start, try saying 'Find campaigns' or 'Show me health campaigns'."
            )
            commands = [
                "search campaigns", "view details", "make donation",
                "donation history", "campaign updates", "impact report"
            ]
            
        elif role == "CAMPAIGN_CREATOR":
            message = (
                "Welcome Campaign Creator! "
                "Here's what you can say: "
                "Create a new campaign. "
                "Show my dashboard. "
                "Withdraw 500 dollars. "
                "You can also search and view campaigns like donors do. "
                "To get started, say 'Create campaign' or 'Show dashboard'."
            )
            commands = [
                "create campaign", "ngo dashboard", "withdraw funds",
                "search campaigns", "view campaign"
            ]
            
        elif role == "FIELD_AGENT":
            message = (
                "Hello Field Agent! "
                "Here's what you can say: "
                "Search for campaigns to verify. "
                "Submit field report for campaign. "
                "View campaign details. "
                "To start, say 'Find pending campaigns' then 'Submit report for number 1'."
            )
            commands = [
                "search campaigns", "field report", "view details"
            ]
            
        elif role == "SYSTEM_ADMIN":
            message = (
                "Welcome Admin! You have full access to all commands: "
                "Search and view campaigns. "
                "Create campaigns. "
                "Submit field reports. "
                "Withdraw funds. "
                "View dashboard. "
                "Make donations. "
                "You can do everything donors, creators, and field agents can do."
            )
            commands = [
                "all commands", "search", "create", "donate",
                "withdraw", "report", "dashboard"
            ]
            
        else:
            message = (
                "Hello! Say 'Find campaigns' to get started, "
                "or 'Help' to learn more about what I can do."
            )
            commands = ["search campaigns", "help"]
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "role": role,
                "available_commands": commands
            }
        }
        
    except Exception as e:
        logger.error(f"Error providing help: {str(e)}", exc_info=True)
        return {
            "success": True,
            "message": (
                "I can help you with campaigns! "
                "Try saying 'Find campaigns' or 'Show me education campaigns'."
            ),
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 2: GREETING
# ============================================================================

@register_handler("greeting")
async def handle_greeting(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Respond to greetings (hello, hi, good morning, etc.).
    
    Provides warm welcome and suggests next action.
    """
    try:
        # Get user for personalization (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if user and user.full_name:
            greeting = f"Hello {user.full_name}! "
        else:
            greeting = "Hello! "
        
        # Build message
        message = (
            greeting +
            "Welcome to Trust Voice. I can help you find and support charitable campaigns using your voice. "
            "Say 'Find campaigns' to see what's available, or 'Help' to learn what I can do."
        )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "user_name": user.full_name if user else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling greeting: {str(e)}", exc_info=True)
        return {
            "success": True,
            "message": "Hello! Welcome to Trust Voice. Say 'Help' to get started.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 3: CHANGE LANGUAGE
# ============================================================================

@register_handler("change_language")
async def handle_change_language(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Change user's preferred language.
    
    Required entities:
        - language: "english" or "amharic"
    
    Updates user preferences in database.
    """
    try:
        language = entities.get("language", "").lower()
        
        # Validate language
        supported_languages = {
            "english": "en",
            "amharic": "am",
            "en": "en",
            "am": "am"
        }
        
        if language not in supported_languages:
            return {
                "success": False,
                "message": "I support English and Amharic. Which language would you prefer?",
                "needs_clarification": True,
                "missing_entities": ["language"],
                "data": {
                    "supported_languages": ["english", "amharic"]
                }
            }
        
        language_code = supported_languages[language]
        language_name = "English" if language_code == "en" else "Amharic"
        
        # Update user preference (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if user:
            user.preferred_language = language_code
            user.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Updated language for user {user_id} to {language_code}")
        
        # Respond in chosen language
        if language_code == "am":
            message = "ቋንቋ ወደ አማርኛ ተቀይሯል። እንዴት ልረዳዎ እችላለሁ?"  # "Language changed to Amharic. How can I help you?"
        else:
            message = "Language changed to English. How can I help you?"
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "language_code": language_code,
                "language_name": language_name
            }
        }
        
    except Exception as e:
        logger.error(f"Error changing language: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble changing the language. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 4: UNKNOWN INTENT
# ============================================================================

@register_handler("unknown")
async def handle_unknown(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle unrecognized intents.
    
    Provides helpful fallback suggestions.
    """
    try:
        # Build helpful message
        message = (
            "I'm not sure I understood that. "
            "Here are some things you can say: "
            "Find education campaigns. "
            "Show campaign details. "
            "Donate 50 dollars. "
            "Show my donation history. "
            "Or say 'Help' to hear all available commands."
        )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "suggestions": [
                    "find campaigns",
                    "campaign details",
                    "donate",
                    "donation history",
                    "help"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling unknown intent: {str(e)}", exc_info=True)
        return {
            "success": True,
            "message": "I didn't catch that. Try saying 'Help' to see what I can do.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 5: SYSTEM INFO
# ============================================================================

@register_handler("system_info")
async def handle_system_info(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Respond to questions about TrustVoice platform.
    
    Handles: "What is TrustVoice?", "How does this work?", "Tell me about this platform"
    """
    try:
        message = (
            "TrustVoice is a voice-first donation platform that connects donors with verified NGO campaigns across Africa. "
            "Here's how it works: "
            "Donors can search for campaigns, donate using mobile money or card, and track the impact of their contributions. "
            "Campaign creators can create fundraising campaigns and manage their funds. "
            "Field agents visit campaign sites to verify that funds are being used correctly, providing trust scores and impact reports. "
            "Everything is designed to work through voice, so you can use it even without reading or typing. "
            "We support English and Amharic. "
            "To get started, say 'find campaigns' or 'help' to see all available commands."
        )

        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "topic": "platform_overview"
            }
        }

    except Exception as e:
        logger.error(f"Error providing system info: {str(e)}", exc_info=True)
        return {
            "success": True,
            "message": "TrustVoice is a voice-first donation platform. Say 'help' to learn what I can do.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 6: THANK YOU
# ============================================================================

@register_handler("thank_you")
async def handle_thank_you(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Respond to thank you messages warmly.
    """
    try:
        # Get user for personalization
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            user = db.query(User).filter(User.telegram_user_id == user_id).first()

        name = user.full_name.split()[0] if user and user.full_name else ""
        greeting = f"You're welcome, {name}! " if name else "You're welcome! "

        message = (
            greeting +
            "I'm always here to help. "
            "Is there anything else you'd like to do? "
            "You can search for campaigns, check your donations, or just say 'help'."
        )

        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }

    except Exception as e:
        logger.error(f"Error handling thank you: {str(e)}", exc_info=True)
        return {
            "success": True,
            "message": "You're welcome! Let me know if you need anything else.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 7: CHECK DONATION STATUS
# ============================================================================

@register_handler("check_donation_status")
async def handle_check_donation_status(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check the status of the user's most recent donation.
    """
    try:
        from database.models import Donor, Donation, Campaign

        # Get user
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            user = db.query(User).filter(User.telegram_user_id == user_id).first()

        if not user:
            return {
                "success": False,
                "message": "I couldn't find your account. Please register first.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }

        # Get donor record
        donor = db.query(Donor).filter(
            Donor.telegram_user_id == user.telegram_user_id
        ).first()

        if not donor:
            return {
                "success": True,
                "message": "You haven't made any donations yet. Say 'find campaigns' to get started!",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }

        # Get most recent donation
        donation = db.query(Donation).filter(
            Donation.donor_id == donor.id
        ).order_by(Donation.created_at.desc()).first()

        if not donation:
            return {
                "success": True,
                "message": "You haven't made any donations yet. Say 'find campaigns' to discover worthy causes!",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }

        campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
        campaign_name = campaign.title if campaign else "a campaign"
        date_str = donation.created_at.strftime("%B %d")

        status_messages = {
            "pending": f"Your donation of {int(donation.amount_usd)} dollars to {campaign_name} on {date_str} is still being processed.",
            "completed": f"Great news! Your donation of {int(donation.amount_usd)} dollars to {campaign_name} on {date_str} was completed successfully. Thank you!",
            "failed": f"Unfortunately, your donation of {int(donation.amount_usd)} dollars to {campaign_name} on {date_str} failed. Please try again.",
            "refunded": f"Your donation of {int(donation.amount_usd)} dollars to {campaign_name} on {date_str} has been refunded."
        }

        message = status_messages.get(
            donation.status,
            f"Your last donation of {int(donation.amount_usd)} dollars to {campaign_name} has status: {donation.status}."
        )

        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "donation_id": str(donation.id),
                "status": donation.status,
                "amount": float(donation.amount_usd)
            }
        }

    except Exception as e:
        logger.error(f"Error checking donation status: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble checking your donation status. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# Import datetime for language handler
from datetime import datetime
