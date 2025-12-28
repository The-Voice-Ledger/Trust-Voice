"""
Donor Intent Handlers - Lab 6 Part 2

Handles 6 donor-related voice commands:
1. search_campaigns - Find campaigns by category/location
2. view_campaign_details - Get details about specific campaign
3. make_donation - Initiate donation (uses Lab 5 donation_handler)
4. donation_history - View past donations
5. campaign_updates - Get updates from a campaign
6. impact_report - View impact verification for a campaign
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime

from database.models import (
    Campaign, Donation, Donor, User, ImpactVerification, NGOOrganization
)
from voice.command_router import register_handler
from voice.handlers.donation_handler import initiate_voice_donation

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER 1: SEARCH CAMPAIGNS
# ============================================================================

@register_handler("search_campaigns")
async def handle_search_campaigns(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Search campaigns by category, location, or keyword.
    
    LAB 8: Starts conversational search flow for multi-turn refinement.
    
    Entities:
        - category (optional): education, health, water, environment
        - location (optional): region/city filter
        - keyword (optional): text search
    
    Returns list of matching campaigns with relevance ranking.
    """
    try:
        logger.info(f"Searching campaigns for user {user_id}")
        
        # ============================================================
        # LAB 8: Start conversational search flow
        # ============================================================
        from voice.workflows.search_flow import SearchConversation
        
        # Build query string from entities
        query_parts = []
        if entities.get("category"):
            query_parts.append(entities["category"])
        if entities.get("keyword"):
            query_parts.append(entities["keyword"])
        if entities.get("location"):
            query_parts.append(f"in {entities['location']}")
        
        query_str = " ".join(query_parts) if query_parts else "all campaigns"
        
        # Start conversational search
        result = await SearchConversation.start_search(user_id, query_str, db)
        
        return {
            "success": True,
            "message": result["message"],
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "campaigns": [c["id"] for c in result.get("campaigns", [])],
                "count": len(result.get("campaigns", []))
            }
        }
        # ============================================================
        
        # Build query
        query = db.query(Campaign).filter(Campaign.status == "active")
        
        # Apply filters
        category = entities.get("category")
        location = entities.get("location")
        keyword = entities.get("keyword")
        
        if category:
            query = query.filter(Campaign.category == category)
            logger.debug(f"Filtering by category: {category}")
        
        if location:
            query = query.filter(
                or_(
                    Campaign.location.ilike(f"%{location}%"),
                    Campaign.region.ilike(f"%{location}%")
                )
            )
            logger.debug(f"Filtering by location: {location}")
        
        if keyword:
            query = query.filter(
                or_(
                    Campaign.title.ilike(f"%{keyword}%"),
                    Campaign.description.ilike(f"%{keyword}%")
                )
            )
            logger.debug(f"Filtering by keyword: {keyword}")
        
        # Get results (limit to 10)
        campaigns = query.order_by(Campaign.created_at.desc()).limit(10).all()
        
        if not campaigns:
            return {
                "success": True,
                "message": _build_no_results_message(category, location, keyword),
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "campaigns": [],
                    "count": 0
                }
            }
        
        # Format results for voice
        message = _format_search_results_for_voice(campaigns, category, location)
        
        # Store campaign IDs in context for follow-up commands
        campaign_ids = [str(c.id) for c in campaigns]
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "campaigns": campaign_ids,
                "count": len(campaigns),
                "search_filters": {
                    "category": category,
                    "location": location,
                    "keyword": keyword
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching campaigns: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble searching for campaigns. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


def _build_no_results_message(category, location, keyword):
    """Build user-friendly message when no campaigns found."""
    filters = []
    if category:
        filters.append(f"{category} category")
    if location:
        filters.append(f"in {location}")
    if keyword:
        filters.append(f"matching '{keyword}'")
    
    filter_text = " ".join(filters) if filters else "matching your search"
    
    return (
        f"I couldn't find any active campaigns {filter_text}. "
        "Would you like to search with different criteria? "
        "You can say 'show all campaigns' or try a different category."
    )


def _format_search_results_for_voice(campaigns: List[Campaign], category=None, location=None):
    """Format campaign list for natural voice playback."""
    count = len(campaigns)
    
    # Build intro
    intro_parts = [f"I found {count} active campaign" + ("s" if count > 1 else "")]
    if category:
        intro_parts.append(f"in the {category} category")
    if location:
        intro_parts.append(f"in {location}")
    intro = " ".join(intro_parts) + ". "
    
    # List campaigns (first 5)
    campaign_descriptions = []
    for i, campaign in enumerate(campaigns[:5], 1):
        # Calculate progress
        goal = campaign.goal_amount_usd or 0
        raised = campaign.raised_amount_usd or 0
        progress = int((raised / goal * 100)) if goal > 0 else 0
        
        desc = (
            f"Number {i}: {campaign.title}. "
            f"Goal: {int(goal)} dollars. "
            f"Raised: {int(raised)} dollars, which is {progress} percent. "
        )
        campaign_descriptions.append(desc)
    
    campaigns_text = " ".join(campaign_descriptions)
    
    # Add navigation hint
    if count > 5:
        footer = f"That's the first 5. Say 'show more' to hear the rest. "
    else:
        footer = ""
    
    footer += "To donate, say 'donate to number 1' or 'tell me more about number 2'."
    
    return intro + campaigns_text + footer


# ============================================================================
# HANDLER 2: VIEW CAMPAIGN DETAILS
# ============================================================================

@register_handler("view_campaign_details")
async def handle_view_campaign_details(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get detailed information about a specific campaign.
    
    Entities:
        - campaign_id (required): UUID or reference ("number 1")
    
    Returns campaign details, progress, and recent donations.
    """
    try:
        campaign_id = entities.get("campaign_id")
        
        # Try to parse UUID
        try:
            campaign_uuid = uuid.UUID(str(campaign_id))
        except (ValueError, AttributeError):
            # Maybe it's a reference to recent search ("number 1")
            last_results = context.get("last_search_campaigns", [])
            if last_results:
                # Try extracting from text (e.g., "number 1" -> index 0)
                from voice.command_router import extract_campaign_reference
                campaign_uuid_str = extract_campaign_reference(str(campaign_id), last_results)
                if campaign_uuid_str:
                    campaign_uuid = uuid.UUID(campaign_uuid_str)
                else:
                    return {
                        "success": False,
                        "message": "I couldn't understand which campaign you want. Try saying 'number 1' or the campaign name.",
                        "needs_clarification": True,
                        "missing_entities": ["campaign_id"],
                        "data": {}
                    }
            else:
                return {
                    "success": False,
                    "message": "I need to know which campaign. Try searching for campaigns first, then say 'number 1'.",
                    "needs_clarification": True,
                    "missing_entities": ["campaign_id"],
                    "data": {}
                }
        
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
        
        if not campaign:
            return {
                "success": False,
                "message": "I couldn't find that campaign. It may have ended or been removed.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Get NGO info
        ngo = db.query(NGOOrganization).filter(NGOOrganization.id == campaign.ngo_id).first()
        ngo_name = ngo.name if ngo else "Unknown Organization"
        
        # Get donation stats
        donation_count = db.query(func.count(Donation.id)).filter(
            Donation.campaign_id == campaign_uuid
        ).scalar()
        
        # Get verification status
        verification = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_uuid
        ).order_by(ImpactVerification.created_at.desc()).first()
        
        verified_text = ""
        if verification:
            score = verification.trust_score or 0
            verified_text = f" This campaign is verified with a trust score of {score} out of 100."
        
        # Build voice message
        goal = campaign.goal_amount_usd or 0
        raised = campaign.raised_amount_usd or 0
        progress = int((raised / goal * 100)) if goal > 0 else 0
        
        message = (
            f"Campaign: {campaign.title}. "
            f"Created by {ngo_name}. "
            f"Category: {campaign.category}. "
            f"Goal: {int(goal)} dollars. "
            f"Raised so far: {int(raised)} dollars from {donation_count} donor" + ("s" if donation_count != 1 else "") + ". "
            f"That's {progress} percent of the goal.{verified_text} "
            f"Description: {campaign.description[:200]}... "
            f"To donate, say 'donate 50 dollars to this campaign'."
        )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "campaign_id": str(campaign_uuid),
                "title": campaign.title,
                "ngo_name": ngo_name,
                "goal_usd": goal,
                "raised_usd": raised,
                "progress_percent": progress,
                "donor_count": donation_count,
                "trust_score": verification.trust_score if verification else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error viewing campaign details: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble loading campaign details. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 3: MAKE DONATION (uses Lab 5 handler)
# ============================================================================

@register_handler("make_donation")
async def handle_make_donation(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Initiate a donation to a campaign.
    
    Entities:
        - amount (required): Donation amount in USD
        - campaign_id (required): Campaign UUID or reference
        - payment_method (optional): "mpesa" or "stripe"
    
    LAB 8: If entities are missing, starts conversational donation flow.
    Uses Lab 5's donation_handler for payment processing when all details present.
    """
    try:
        amount = entities.get("amount")
        campaign_id = entities.get("campaign_id")
        payment_method = entities.get("payment_method", "mpesa")  # Default to M-Pesa
        
        # ============================================================
        # LAB 8: Start conversational flow if missing entities
        # ============================================================
        if not amount or not campaign_id:
            from voice.handlers.donation_handler import start_conversational_donation
            return await start_conversational_donation(entities, user_id, db, context)
        # ============================================================
        
        # Resolve campaign reference if needed
        try:
            campaign_uuid = uuid.UUID(str(campaign_id))
        except (ValueError, AttributeError):
            last_results = context.get("last_search_campaigns", [])
            if last_results:
                from voice.command_router import extract_campaign_reference
                campaign_uuid_str = extract_campaign_reference(str(campaign_id), last_results)
                if campaign_uuid_str:
                    campaign_uuid = uuid.UUID(campaign_uuid_str)
                else:
                    return {
                        "success": False,
                        "message": "Which campaign would you like to donate to? Say 'number 1' or the campaign name.",
                        "needs_clarification": True,
                        "missing_entities": ["campaign_id"],
                        "data": {}
                    }
            else:
                # Use current campaign from context
                current_campaign = context.get("current_campaign")
                if current_campaign:
                    campaign_uuid = uuid.UUID(current_campaign)
                else:
                    return {
                        "success": False,
                        "message": "Which campaign should I donate to? Search for campaigns first, then say 'donate to number 1'.",
                        "needs_clarification": True,
                        "missing_entities": ["campaign_id"],
                        "data": {}
                    }
        
        # Get user's telegram_user_id for Lab 5 handler
        # Try UUID (registered) or telegram_user_id (guest)
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Guest user - use telegram_user_id
            user = db.query(User).filter(User.telegram_user_id == user_id).first()
        
        if not user:
            return {
                "success": False,
                "message": "I couldn't find your account. Please register first with /start.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Call Lab 5 donation handler
        result = await initiate_voice_donation(
            db=db,
            telegram_user_id=user.telegram_user_id,
            campaign_id=campaign_uuid,
            amount=float(amount),
            currency="USD",
            payment_method=payment_method
        )
        
        if result.get("success"):
            campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
            campaign_name = campaign.title if campaign else "the campaign"
            
            message = (
                f"Great! I'm processing your donation of {int(amount)} dollars to {campaign_name}. "
                f"{result.get('instructions', 'Please check your phone for payment instructions.')}"
            )
            
            return {
                "success": True,
                "message": message,
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "donation_id": result.get("donation_id"),
                    "payment_method": result.get("payment_method"),
                    "checkout_url": result.get("checkout_url")
                }
            }
        else:
            return {
                "success": False,
                "message": f"I couldn't process the donation. {result.get('error', 'Please try again.')}",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
            
    except Exception as e:
        logger.error(f"Error making donation: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble processing your donation. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 4: DONATION HISTORY
# ============================================================================

@register_handler("view_donation_history")
async def handle_donation_history(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    View user's donation history.
    
    No required entities. Returns list of past donations.
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
                "data": {
                    "donations": [],
                    "total_donated": 0,
                    "donation_count": 0
                }
            }
        
        # Get donations
        donations = db.query(Donation).filter(
            Donation.donor_id == donor.id
        ).order_by(Donation.created_at.desc()).limit(10).all()
        
        if not donations:
            return {
                "success": True,
                "message": "You haven't made any donations yet. Say 'find campaigns' to discover worthy causes!",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "donations": [],
                    "total_donated": 0,
                    "donation_count": 0
                }
            }
        
        # Calculate stats
        total_donated = sum(d.amount_usd for d in donations)
        donation_count = len(donations)
        
        # Format for voice (first 5)
        donation_summaries = []
        for i, donation in enumerate(donations[:5], 1):
            campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
            campaign_name = campaign.title if campaign else "Unknown Campaign"
            
            date = donation.created_at.strftime("%B %d")
            summary = f"Number {i}: {int(donation.amount_usd)} dollars to {campaign_name} on {date}."
            donation_summaries.append(summary)
        
        donations_text = " ".join(donation_summaries)
        
        message = (
            f"You've donated {int(total_donated)} dollars across {donation_count} campaign" + ("s" if donation_count != 1 else "") + ". "
            f"Here are your recent donations: {donations_text} "
            "Thank you for your generosity!"
        )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "donations": [str(d.id) for d in donations],
                "total_donated": total_donated,
                "donation_count": donation_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting donation history: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble loading your donation history. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 5: CAMPAIGN UPDATES
# ============================================================================

@register_handler("get_campaign_updates")
async def handle_campaign_updates(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get recent updates/progress from a campaign.
    
    Entities:
        - campaign_id (required): Campaign UUID or reference
    
    Returns recent donations and progress milestones.
    """
    try:
        campaign_id = entities.get("campaign_id")
        
        # Resolve campaign reference
        try:
            campaign_uuid = uuid.UUID(str(campaign_id))
        except (ValueError, AttributeError):
            last_results = context.get("last_search_campaigns", [])
            current_campaign = context.get("current_campaign")
            
            if current_campaign:
                campaign_uuid = uuid.UUID(current_campaign)
            elif last_results:
                from voice.command_router import extract_campaign_reference
                campaign_uuid_str = extract_campaign_reference(str(campaign_id), last_results)
                if campaign_uuid_str:
                    campaign_uuid = uuid.UUID(campaign_uuid_str)
                else:
                    return {
                        "success": False,
                        "message": "Which campaign's updates do you want? Say 'number 1' or search for campaigns first.",
                        "needs_clarification": True,
                        "missing_entities": ["campaign_id"],
                        "data": {}
                    }
            else:
                return {
                    "success": False,
                    "message": "I need to know which campaign. Search for campaigns first, then say 'updates for number 1'.",
                    "needs_clarification": True,
                    "missing_entities": ["campaign_id"],
                    "data": {}
                }
        
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
        if not campaign:
            return {
                "success": False,
                "message": "I couldn't find that campaign.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Get recent donations (last 5)
        recent_donations = db.query(Donation).filter(
            Donation.campaign_id == campaign_uuid
        ).order_by(Donation.created_at.desc()).limit(5).all()
        
        # Build update message
        goal = campaign.goal_amount_usd or 0
        raised = campaign.raised_amount_usd or 0
        progress = int((raised / goal * 100)) if goal > 0 else 0
        
        if not recent_donations:
            message = (
                f"Campaign '{campaign.title}' hasn't received any donations yet. "
                f"Be the first to support this cause! Say 'donate 50 dollars'."
            )
        else:
            donor_count = db.query(func.count(Donation.id)).filter(
                Donation.campaign_id == campaign_uuid
            ).scalar()
            
            recent_text = f"The last donation was {int(recent_donations[0].amount_usd)} dollars on {recent_donations[0].created_at.strftime('%B %d')}. "
            
            message = (
                f"Campaign '{campaign.title}' has raised {int(raised)} out of {int(goal)} dollars. "
                f"That's {progress} percent of the goal from {donor_count} donor" + ("s" if donor_count != 1 else "") + ". "
                f"{recent_text}"
                "Want to contribute? Say 'donate 50 dollars to this campaign'."
            )
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "campaign_id": str(campaign_uuid),
                "progress_percent": progress,
                "recent_donations": [str(d.id) for d in recent_donations]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting campaign updates: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble loading campaign updates. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }


# ============================================================================
# HANDLER 6: IMPACT REPORT (uses Lab 5 impact data)
# ============================================================================

@register_handler("get_impact_report")
async def handle_impact_report(
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    View impact verification report for a campaign.
    
    Entities:
        - campaign_id (required): Campaign UUID or reference
    
    Returns verification details from field agent visits.
    """
    try:
        campaign_id = entities.get("campaign_id")
        
        # Resolve campaign reference
        try:
            campaign_uuid = uuid.UUID(str(campaign_id))
        except (ValueError, AttributeError):
            last_results = context.get("last_search_campaigns", [])
            current_campaign = context.get("current_campaign")
            
            if current_campaign:
                campaign_uuid = uuid.UUID(current_campaign)
            elif last_results:
                from voice.command_router import extract_campaign_reference
                campaign_uuid_str = extract_campaign_reference(str(campaign_id), last_results)
                if campaign_uuid_str:
                    campaign_uuid = uuid.UUID(campaign_uuid_str)
                else:
                    return {
                        "success": False,
                        "message": "Which campaign's impact do you want to see? Say 'number 1' or search first.",
                        "needs_clarification": True,
                        "missing_entities": ["campaign_id"],
                        "data": {}
                    }
            else:
                return {
                    "success": False,
                    "message": "I need to know which campaign. Search for campaigns first, then say 'impact for number 1'.",
                    "needs_clarification": True,
                    "missing_entities": ["campaign_id"],
                    "data": {}
                }
        
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_uuid).first()
        if not campaign:
            return {
                "success": False,
                "message": "I couldn't find that campaign.",
                "needs_clarification": False,
                "missing_entities": [],
                "data": {}
            }
        
        # Get impact verification
        verification = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_uuid
        ).order_by(ImpactVerification.created_at.desc()).first()
        
        if not verification:
            return {
                "success": True,
                "message": (
                    f"Campaign '{campaign.title}' doesn't have an impact report yet. "
                    "Impact reports are created by field agents who visit the campaign site."
                ),
                "needs_clarification": False,
                "missing_entities": [],
                "data": {
                    "campaign_id": str(campaign_uuid),
                    "has_verification": False
                }
            }
        
        # Get field agent info
        agent = db.query(User).filter(User.id == verification.field_agent_id).first()
        agent_name = agent.full_name if agent else "Field Agent"
        
        # Build impact message
        trust_score = verification.trust_score or 0
        beneficiary_count = verification.beneficiary_count or 0
        visit_date = verification.created_at.strftime("%B %d, %Y")
        
        message = (
            f"Impact Report for '{campaign.title}': "
            f"Verified by {agent_name} on {visit_date}. "
            f"Trust score: {trust_score} out of 100. "
        )
        
        if beneficiary_count > 0:
            message += f"This campaign has helped {beneficiary_count} beneficiaries. "
        
        if verification.description:
            message += f"Field agent notes: {verification.description[:200]}... "
        
        message += "This verification confirms the campaign is legitimate and making real impact."
        
        return {
            "success": True,
            "message": message,
            "needs_clarification": False,
            "missing_entities": [],
            "data": {
                "campaign_id": str(campaign_uuid),
                "verification_id": str(verification.id),
                "trust_score": trust_score,
                "beneficiary_count": beneficiary_count,
                "verified_date": visit_date,
                "has_verification": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting impact report: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I had trouble loading the impact report. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {}
        }
