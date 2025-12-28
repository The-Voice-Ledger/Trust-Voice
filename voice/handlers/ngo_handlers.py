"""
NGO Intent Handlers - Lab 6 Part 3

Handles 4 NGO-related voice commands:
1. create_campaign - Create new fundraising campaign
2. withdraw_funds - Request payout (uses Lab 5 payout_handler)
3. field_report - Submit impact verification (uses Lab 5 impact_handler)
4. ngo_dashboard - View NGO stats and campaigns
"""

import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from database.models import Campaign, User, NGOOrganization, Donation, ImpactVerification
from voice.command_router import register_handler
from voice.handlers.payout_handler import request_campaign_payout
from voice.handlers.impact_handler import process_impact_report

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER 1: CREATE CAMPAIGN
# ============================================================================

@register_handler("create_campaign")
async def handle_create_campaign(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new fundraising campaign.
    
    Required entities:
        - title: Campaign name
        - goal_amount: Fundraising goal in USD
        - category: education, health, water, environment
        
    Optional entities:
        - description: Campaign details
        - location: Campaign location
        - duration_days: How long campaign will run
    
    Returns campaign ID and next steps.
    """
    try:
        # Get user (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if not user:
            return {
                "success": False,
                "message": "I couldn't find your account. Please register first.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Verify user is campaign creator or admin
        if user.role not in ["CAMPAIGN_CREATOR", "SYSTEM_ADMIN"]:
            return {
                "success": False,
                "message": f"Only Campaign Creators can create campaigns. Your role is {user.role}. Say 'help' to learn what you can do.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Determine campaign type: NGO or Individual
        campaign_type = "NGO" if user.ngo_id else "Individual"
        ngo = None
        
        if user.ngo_id:
            # NGO Campaign
            ngo = db.query(NGOOrganization).filter(NGOOrganization.id == user.ngo_id).first()
            if not ngo:
                return {
                    "success": False,
                    "message": "I couldn't find your organization. Please contact support.",
                    "needs_clarification": False,
                    "missing_entities": [],
                    "data": {}
                }
        
        # Extract entities
        title = entities.get("title")
        goal_amount = entities.get("goal_amount")
        category = entities.get("category")
        description = entities.get("description", f"Campaign created via voice by {ngo.name}")
        location = entities.get("location", "Ethiopia")
        duration_days = entities.get("duration_days", 30)  # Default 30 days
        
        # Validate category
        valid_categories = ["education", "health", "water", "environment"]
        if category.lower() not in valid_categories:
            return {
                "success": False,
                "message": f"Invalid category. Please choose: education, health, water, or environment.",
                "needs_clarification": True,
                "missing_entities": ["category"],
                "data": {}
            }
        
        # Create campaign (NGO or Individual)
        campaign_id = uuid.uuid4()
        campaign = Campaign(
            id=campaign_id,
            ngo_id=user.ngo_id if user.ngo_id else None,  # Set if NGO campaign
            creator_user_id=user.id if not user.ngo_id else None,  # Set if individual campaign
            title=title,
            description=description,
            category=category.lower(),
            goal_amount_usd=float(goal_amount),
            raised_amount_usd=0.0,
            location=location,
            region="Ethiopia",  # TODO: Extract from location
            status="pending",  # Needs verification before active
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(campaign)
        db.commit()
        
        logger.info(f"Created {campaign_type} campaign {campaign_id} via voice: {title}")
        
        owner_name = ngo.name if ngo else user.full_name
        message = (
            f"Great! I've created your {campaign_type.lower()} campaign '{title}' for {owner_name} "
            f"with a goal of {int(goal_amount)} dollars in the {category} category. "
            f"Your campaign is pending verification by a field agent. "
            "Once verified, it will be active and donors can start contributing. "
            f"Campaign ID: {str(campaign_id)[:8]}. "
            "Would you like to add more details or create another campaign?"
        )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "campaign_id": str(campaign_id),
                "title": title,
                "goal_amount": goal_amount,
                "category": category,
                "status": "pending"
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble creating the campaign. Please try again or contact support.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 2: WITHDRAW FUNDS (uses Lab 5 payout handler)
# ============================================================================

@register_handler("withdraw_funds")
async def handle_withdraw_funds(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Request withdrawal/payout from campaign funds.
    
    Required entities:
        - amount: Amount to withdraw in USD
        
    Optional entities:
        - campaign_id: Which campaign (defaults to most recent)
        - reason: Withdrawal reason
    
    Uses Lab 5's payout_handler for M-Pesa processing.
    """
    try:
        amount = entities.get("amount")
        campaign_id = entities.get("campaign_id")
        reason = entities.get("reason", "Campaign expenses")
        
        # Get user (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if not user:
            return {
                "success": False,
                "message": "I couldn't find your account.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # If no campaign specified, use most recent campaign from this NGO
        if not campaign_id:
            # Get user's most recent campaign
            recent_campaign = db.query(Campaign).filter(
                Campaign.ngo_id == user.ngo_id
            ).order_by(Campaign.created_at.desc()).first()
            
            if not recent_campaign:
                return {
                    "success": False,
                    "message": "You don't have any campaigns yet. Create a campaign first.",
                    "needs_clarification": False,
                    "missing_entities": [],
                    "data": {}
                }
            
            campaign_uuid = recent_campaign.id
        else:
            campaign_uuid = None
            
            # Try using transcript with SearchConversation first
            transcript = context.get("transcript", "")
            if transcript:
                from voice.workflows.search_flow import SearchConversation
                from voice.session_manager import SessionManager
                
                search_session = SessionManager.get_session(user_id)
                if search_session and search_session["data"].get("campaign_ids"):
                    campaign_ids = search_session["data"]["campaign_ids"]
                    parsed_id = SearchConversation._parse_campaign_ref(transcript, campaign_ids)
                    if parsed_id:
                        campaign_uuid = parsed_id
            
            # Fallback: try direct UUID parsing
            if not campaign_uuid and campaign_id:
                try:
                    campaign_uuid = uuid.UUID(str(campaign_id))
                except (ValueError, AttributeError):
                    pass
            
            if not campaign_uuid:
                return {
                    "success": False,
                    "message": "Which campaign do you want to withdraw from? Say 'my latest campaign' or the campaign name.",
                    "needs_clarification": True,
                    "missing_entities": ["campaign_id"],
                    "data": {}
                }
        
        # Call Lab 5 payout handler
        result = await request_campaign_payout(
            db=db,
            telegram_user_id=user.telegram_user_id,
            campaign_id=campaign_uuid,
            amount_usd=float(amount),
            reason=reason
        )
        
        if result.get("success"):
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            campaign_name = campaign.title if campaign else "your campaign"
            
            message = (
                f"I've processed your withdrawal request for {int(amount)} dollars from {campaign_name}. "
                f"{result.get('message', 'Payment will be sent to your phone via M-Pesa.')} "
                "This may take a few minutes."
            )
            
            return {
                "success": True,
                "message": message,
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "campaign_id": str(campaign_uuid),
                    "amount": amount,
                    "payout_id": result.get("payout_id")
                }
            }
        else:
            return {
                "success": False,
                "message": f"I couldn't process the withdrawal. {result.get('error', 'Please try again.')}",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
            
    except Exception as e:
        logger.error(f"Error withdrawing funds: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble processing your withdrawal. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 3: FIELD REPORT (uses Lab 5 impact handler)
# ============================================================================

@register_handler("field_report")
async def handle_field_report(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Submit field report/impact verification.
    
    Required entities:
        - campaign_id: Campaign to verify
        - description: Agent observations
        
    Optional entities:
        - beneficiary_count: Number of beneficiaries
        - gps_latitude: Site visit coordinates
        - gps_longitude: Site visit coordinates
    
    Uses Lab 5's impact_handler for verification processing.
    """
    try:
        campaign_id = entities.get("campaign_id")
        description = entities.get("description")
        beneficiary_count = entities.get("beneficiary_count")
        gps_latitude = entities.get("gps_latitude")
        gps_longitude = entities.get("gps_longitude")
        
        # Get user (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if not user:
            return {
                "success": False,
                "message": "I couldn't find your account.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Verify user is field agent
        if user.role != "FIELD_AGENT":
            return {
                "success": False,
                "message": f"Only Field Agents can submit impact reports. Your role is {user.role}.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Resolve campaign using transcript and SearchConversation
        campaign_uuid = None
        
        # Try using transcript with SearchConversation first
        transcript = context.get("transcript", "")
        if transcript:
            from voice.workflows.search_flow import SearchConversation
            from voice.session_manager import SessionManager
            
            search_session = SessionManager.get_session(user_id)
            if search_session and search_session["data"].get("campaign_ids"):
                campaign_ids = search_session["data"]["campaign_ids"]
                parsed_id = SearchConversation._parse_campaign_ref(transcript, campaign_ids)
                if parsed_id:
                    campaign_uuid = parsed_id
        
        # Fallback: try direct UUID parsing
        if not campaign_uuid and campaign_id:
            try:
                campaign_uuid = uuid.UUID(str(campaign_id))
            except (ValueError, AttributeError):
                pass
        
        if not campaign_uuid:
            return {
                "success": False,
                "message": "Which campaign are you reporting on? Say the campaign name or search for campaigns first.",
                "needs_clarification": True,
                "missing_entities": ["campaign_id"],
                "data": {}
            }
        
        # Call Lab 5 impact handler
        result = await process_impact_report(
            db=db,
            telegram_user_id=user.telegram_user_id,
            campaign_id=campaign_uuid,
            description=description,
            photo_urls=[],  # TODO: Handle photo uploads in future
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            beneficiary_count=beneficiary_count,
            testimonials=None  # TODO: Extract from description
        )
        
        if result.get("success"):
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            campaign_name = campaign.title if campaign else "the campaign"
            
            message = (
                f"Thank you! Your impact report for {campaign_name} has been submitted. "
                f"{result.get('message', 'Your report will be reviewed and you will receive payment upon approval.')} "
                f"Verification ID: {str(result.get('verification_id', ''))[:8]}."
            )
            
            return {
                "success": True,
                "message": message,
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "campaign_id": str(campaign_uuid),
                    "verification_id": result.get("verification_id"),
                    "trust_score": result.get("trust_score")
                }
            }
        else:
            return {
                "success": False,
                "message": f"I couldn't submit the report. {result.get('error', 'Please try again.')}",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
            
    except Exception as e:
        logger.error(f"Error submitting field report: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble submitting your report. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 4: NGO DASHBOARD
# ============================================================================

@register_handler("view_my_campaigns")
async def handle_ngo_dashboard(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    View NGO statistics and campaigns.
    
    No required entities. Returns overview of NGO's campaigns and donations.
    """
    try:
        # Get user (registered UUID or guest telegram_user_id)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if not user:
            return {
                "success": False,
                "message": "I couldn't find your account.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Verify user is NGO staff
        if user.role not in ["CAMPAIGN_CREATOR", "SYSTEM_ADMIN"]:
            return {
                "success": False,
                "message": f"Dashboard is only for Campaign Creators. Your role is {user.role}. Say 'help' to see what you can do.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        if not user.ngo_id:
            return {
                "success": False,
                "message": "You're not associated with an NGO yet. Contact support to set up your organization.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Get NGO
        ngo = db.query(NGOOrganization).filter(NGOOrganization.id == user.ngo_id).first()
        if not ngo:
            return {
                "success": False,
                "message": "I couldn't find your organization.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Get campaign statistics
        campaigns = db.query(Campaign).filter(Campaign.ngo_id == user.ngo_id).all()
        
        if not campaigns:
            return {
                "success": True,
                "message": (
                    f"Welcome to {ngo.name}'s dashboard! You don't have any campaigns yet. "
                    "Say 'create campaign' to start your first fundraising campaign."
                ),
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "ngo_name": ngo.name,
                    "campaign_count": 0,
                    "total_raised": 0,
                    "active_campaigns": 0
                }
            }
        
        # Calculate stats
        total_raised = sum(c.raised_amount_usd or 0 for c in campaigns)
        active_count = sum(1 for c in campaigns if c.status == "active")
        pending_count = sum(1 for c in campaigns if c.status == "pending")
        completed_count = sum(1 for c in campaigns if c.status == "completed")
        
        # Get total donation count
        campaign_ids = [c.id for c in campaigns]
        total_donations = db.query(func.count(Donation.id)).filter(
            Donation.campaign_id.in_(campaign_ids)
        ).scalar() if campaign_ids else 0
        
        # Find top campaign
        top_campaign = max(campaigns, key=lambda c: c.raised_amount_usd or 0)
        
        # Build message
        message = (
            f"Dashboard for {ngo.name}: "
            f"You have {len(campaigns)} total campaign" + ("s" if len(campaigns) != 1 else "") + ". "
            f"{active_count} active, {pending_count} pending verification, {completed_count} completed. "
            f"Total raised across all campaigns: {int(total_raised)} dollars from {total_donations} donation" + ("s" if total_donations != 1 else "") + ". "
        )
        
        if top_campaign.raised_amount_usd and top_campaign.raised_amount_usd > 0:
            message += (
                f"Your top campaign is '{top_campaign.title}' with {int(top_campaign.raised_amount_usd)} dollars raised. "
            )
        
        message += "Say 'create campaign' to start a new one, or 'withdraw funds' to request a payout."
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "ngo_name": ngo.name,
                "campaign_count": len(campaigns),
                "active_campaigns": active_count,
                "pending_campaigns": pending_count,
                "completed_campaigns": completed_count,
                "total_raised": total_raised,
                "total_donations": total_donations,
                "top_campaign_id": str(top_campaign.id) if top_campaign else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error loading NGO dashboard: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble loading your dashboard. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 5: REGISTER NGO
# ============================================================================

@register_handler("register_ngo")
async def handle_register_ngo(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Submit NGO registration application.
    
    Required entities:
        - organization_name: NGO name
        - email: Contact email
        - country: Operating country
        
    Optional entities:
        - registration_number: Official registration ID
        - phone_number: Contact phone
        - mission_statement: NGO mission
        - focus_areas: e.g., "education, healthcare"
        - year_established: Founding year
        - website: Organization website
    
    Returns confirmation and next steps.
    """
    try:
        from database.models import PendingNGORegistration
        
        # Extract required entities
        org_name = entities.get("organization_name")
        email = entities.get("email")
        country = entities.get("country")
        
        # Check for missing required fields
        missing = []
        if not org_name:
            missing.append("organization_name")
        if not email:
            missing.append("email")
        if not country:
            missing.append("country")
        
        if missing:
            return {
                "success": False,
                "message": f"To register your NGO, I need: {', '.join(missing)}. Please provide these details.",
                "needs_clarification": True,
                "missing_entities": missing,
                "data": {}
            }
        
        # Get Telegram user info from context
        telegram_user = context.get("telegram_user", {})
        telegram_id = telegram_user.get("id") or user_id
        telegram_username = telegram_user.get("username")
        
        # Check if NGO already registered
        existing_ngo = db.query(NGOOrganization).filter(
            NGOOrganization.name == org_name
        ).first()
        
        if existing_ngo:
            return {
                "success": False,
                "message": f"'{org_name}' is already registered in our system. If you represent this organization, please contact support.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Check if application already pending
        existing_pending = db.query(PendingNGORegistration).filter(
            PendingNGORegistration.organization_name == org_name,
            PendingNGORegistration.status == 'PENDING'
        ).first()
        
        if existing_pending:
            return {
                "success": False,
                "message": f"An application for '{org_name}' is already pending review. We'll notify you once it's reviewed.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {"application_id": existing_pending.id}
            }
        
        # Create pending registration
        pending = PendingNGORegistration(
            submitted_by_telegram_id=str(telegram_id),
            submitted_by_telegram_username=telegram_username,
            submitted_by_name=entities.get("submitted_by_name"),
            organization_name=org_name,
            registration_number=entities.get("registration_number"),
            organization_type=entities.get("organization_type"),
            email=email,
            phone_number=entities.get("phone_number"),
            website=entities.get("website"),
            country=country,
            region=entities.get("region"),
            address=entities.get("address"),
            mission_statement=entities.get("mission_statement"),
            focus_areas=entities.get("focus_areas"),
            year_established=entities.get("year_established"),
            staff_size=entities.get("staff_size"),
            bank_name=entities.get("bank_name"),
            account_number=entities.get("account_number"),
            account_name=entities.get("account_name"),
            swift_code=entities.get("swift_code"),
            status='PENDING'
        )
        
        db.add(pending)
        db.commit()
        db.refresh(pending)
        
        message = (
            f"Great! I've submitted your registration for '{org_name}'. "
            f"Our admin team will review your application and get back to you within 2-3 business days. "
            f"Your application ID is {pending.id}. "
            f"We'll notify you via Telegram once it's approved. "
            f"In the meantime, you can complete your profile or upload verification documents using our registration form."
        )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "application_id": pending.id,
                "organization_name": org_name,
                "status": "PENDING",
                "review_time": "2-3 business days"
            }
        }
        
    except Exception as e:
        logger.error(f"Error registering NGO: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble submitting your NGO registration. Please try again or use the registration form in the menu.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }

