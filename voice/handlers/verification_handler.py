"""
Campaign Verification Handler - Module 5 of Lab 5

Enables field agents to conduct comprehensive site visit verifications before campaigns go live.
Verifications check that campaigns are legitimate and ready to receive donations.

Field agents receive $30 M-Pesa payment upon verification approval.
Campaigns with verification trust_score >= 80 are auto-approved for fundraising.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from database.models import (
    Campaign,
    User,
    ImpactVerification
)

logger = logging.getLogger(__name__)


async def initiate_campaign_verification(
    db: Session,
    telegram_user_id: str,
    campaign_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Start a campaign verification process for a field agent.
    
    This guides the agent through required verification steps:
    1. Site visit confirmation
    2. Photo documentation
    3. GPS coordinates
    4. Beneficiary interviews
    5. Budget verification
    
    Args:
        db: Database session
        telegram_user_id: Field agent's Telegram ID
        campaign_id: Campaign to verify
    
    Returns:
        Dict with verification instructions and next steps
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
        
        # Verify user is field agent
        if user.role != "FIELD_AGENT":
            return {
                "success": False,
                "error": "Only Field Agents can verify campaigns. Your role: " + user.role
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
        
        # Check campaign status
        if campaign.status not in ["pending", "active"]:
            return {
                "success": False,
                "error": f"Cannot verify {campaign.status} campaign. Must be pending or active."
            }
        
        # Check if agent already verified this campaign
        existing = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_id,
            ImpactVerification.field_agent_id == user.id
        ).first()
        
        if existing:
            return {
                "success": False,
                "error": f"You already verified this campaign on {existing.created_at.strftime('%b %d, %Y')}",
                "verification_id": str(existing.id),
                "trust_score": existing.trust_score
            }
        
        # Return verification checklist
        return {
            "success": True,
            "campaign_id": str(campaign_id),
            "campaign_title": campaign.title,
            "campaign_location": campaign.location_region or "Unknown",
            "goal_amount": campaign.goal_amount_usd,
            "checklist": {
                "site_visit": "Visit the project site in person",
                "photos": "Take 3-5 photos showing project location and preparedness",
                "gps": "Share your location to confirm site visit",
                "beneficiaries": "Interview at least 3 potential beneficiaries",
                "budget": "Review budget breakdown with campaign creator",
                "testimonials": "Record beneficiary quotes about the need"
            },
            "instructions": (
                "📋 Campaign Verification Checklist\n\n"
                "To complete verification:\n\n"
                "1️⃣ Upload 3-5 photos of the site\n"
                "2️⃣ Share your GPS location\n"
                "3️⃣ Say 'Complete verification for [campaign name]'\n\n"
                "Include details about:\n"
                "• Beneficiaries you interviewed\n"
                "• Project readiness assessment\n"
                "• Budget verification notes\n"
                "• Community testimonials\n\n"
                "💰 Payout: $30 USD upon approval"
            )
        }
        
    except Exception as e:
        logger.error(f"Error initiating verification: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to initiate verification: {str(e)}"
        }


async def complete_campaign_verification(
    db: Session,
    telegram_user_id: str,
    campaign_id: uuid.UUID,
    site_visit_notes: str,
    photo_urls: List[str],
    gps_latitude: Optional[float] = None,
    gps_longitude: Optional[float] = None,
    beneficiary_count: Optional[int] = None,
    testimonials: Optional[str] = None,
    budget_verified: bool = False
) -> Dict[str, Any]:
    """
    Complete and submit a campaign verification report.
    
    Args:
        db: Database session
        telegram_user_id: Field agent's Telegram ID
        campaign_id: Campaign being verified
        site_visit_notes: Agent's detailed observations
        photo_urls: List of photo file IDs from Telegram
        gps_latitude: Site visit latitude
        gps_longitude: Site visit longitude
        beneficiary_count: Number of beneficiaries interviewed
        testimonials: Quotes from beneficiaries
        budget_verified: Whether agent reviewed budget with creator
    
    Returns:
        Dict with verification result, trust score, and payout status
    """
    try:
        # Get user
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not user or user.role != "FIELD_AGENT":
            return {
                "success": False,
                "error": "Only Field Agents can complete verifications"
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
        
        # Check for duplicate
        existing = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_id,
            ImpactVerification.field_agent_id == user.id
        ).first()
        
        if existing:
            return {
                "success": False,
                "error": "You already submitted a verification for this campaign"
            }
        
        # Calculate trust score for pre-launch verification
        trust_score = _calculate_verification_trust_score(
            photo_count=len(photo_urls),
            has_gps=bool(gps_latitude and gps_longitude),
            has_testimonials=bool(testimonials),
            notes_length=len(site_visit_notes) if site_visit_notes else 0,
            beneficiary_count=beneficiary_count,
            budget_verified=budget_verified
        )
        
        # Auto-approve if score >= 80
        auto_approved = trust_score >= 80
        verification_status = "approved" if auto_approved else "pending"
        
        # Create verification record
        verification = ImpactVerification(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            field_agent_id=user.id,
            verification_date=datetime.utcnow(),
            photos=photo_urls,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            beneficiary_count=beneficiary_count or 0,
            testimonials=testimonials,
            agent_notes=site_visit_notes,
            trust_score=trust_score,
            status=verification_status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(verification)
        
        # Update campaign
        if not hasattr(campaign, 'verification_count') or campaign.verification_count is None:
            campaign.verification_count = 0
        campaign.verification_count += 1
        
        if not hasattr(campaign, 'total_trust_score') or campaign.total_trust_score is None:
            campaign.total_trust_score = 0
        campaign.total_trust_score += trust_score
        
        campaign.avg_trust_score = campaign.total_trust_score / campaign.verification_count
        
        # Auto-approve campaign if verification passed
        if auto_approved and campaign.status == "pending":
            campaign.status = "active"
            logger.info(f"Campaign {campaign.id} auto-approved with trust score {trust_score}")
        
        db.commit()
        db.refresh(verification)
        
        # Prepare response
        result = {
            "success": True,
            "verification_id": str(verification.id),
            "trust_score": trust_score,
            "status": verification_status,
            "auto_approved": auto_approved,
            "campaign_title": campaign.title,
            "campaign_status": campaign.status,
            "agent_name": user.preferred_name or user.full_name
        }
        
        # If auto-approved, initiate agent payout
        if auto_approved:
            from voice.handlers.impact_handler import _initiate_agent_payout
            
            payout_result = await _initiate_agent_payout(
                db=db,
                agent=user,
                verification_id=verification.id,
                amount_usd=30.0
            )
            result["payout"] = payout_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error completing verification: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": f"Failed to complete verification: {str(e)}"
        }


def _calculate_verification_trust_score(
    photo_count: int,
    has_gps: bool,
    has_testimonials: bool,
    notes_length: int,
    beneficiary_count: Optional[int],
    budget_verified: bool
) -> int:
    """
    Calculate trust score for campaign verification (0-100).
    
    Scoring rubric:
    - Photos: 25 points (8-9 per photo, max 3)
    - GPS: 25 points
    - Testimonials: 20 points
    - Site visit notes: 15 points (1 per 20 chars, max 15)
    - Beneficiary interviews: 10 points
    - Budget verification: 5 points
    
    Returns:
        Trust score from 0-100
    """
    score = 0
    
    # Photos (max 25 points)
    score += min(photo_count * 8, 25)
    
    # GPS coordinates (25 points)
    if has_gps:
        score += 25
    
    # Testimonials (20 points)
    if has_testimonials:
        score += 20
    
    # Site visit notes quality (max 15 points)
    notes_points = min(notes_length // 20, 15)
    score += notes_points
    
    # Beneficiary interviews (10 points)
    if beneficiary_count and beneficiary_count >= 3:
        score += 10
    elif beneficiary_count and beneficiary_count > 0:
        score += 5
    
    # Budget verification (5 points)
    if budget_verified:
        score += 5
    
    return min(score, 100)


async def get_campaigns_pending_verification(
    db: Session,
    location_region: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get campaigns that need verification from field agents.
    
    Args:
        db: Database session
        location_region: Filter by region (optional)
        limit: Max number of campaigns to return
    
    Returns:
        Dict with list of campaigns needing verification
    """
    try:
        query = db.query(Campaign).filter(
            Campaign.status == "pending"
        )
        
        if location_region:
            query = query.filter(
                Campaign.location_region.ilike(f"%{location_region}%")
            )
        
        campaigns = query.order_by(Campaign.created_at.desc()).limit(limit).all()
        
        if not campaigns:
            return {
                "success": True,
                "campaigns": [],
                "total_count": 0,
                "message": "No campaigns pending verification"
            }
        
        # Format campaign data
        campaign_list = []
        for c in campaigns:
            # Check existing verifications
            verification_count = db.query(ImpactVerification).filter(
                ImpactVerification.campaign_id == c.id
            ).count()
            
            campaign_list.append({
                "id": str(c.id),
                "title": c.title,
                "category": c.category,
                "location": c.location_region or "Unknown",
                "goal_amount_usd": c.goal_amount_usd,
                "created_at": c.created_at.strftime("%b %d, %Y"),
                "verification_count": verification_count,
                "needs_verification": verification_count == 0
            })
        
        return {
            "success": True,
            "campaigns": campaign_list,
            "total_count": len(campaigns)
        }
        
    except Exception as e:
        logger.error(f"Error getting pending campaigns: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get campaigns: {str(e)}"
        }


async def get_campaign_verification_status(
    db: Session,
    campaign_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get verification status and details for a specific campaign.
    Used by campaign creators to check verification progress.
    
    Args:
        db: Database session
        campaign_id: Campaign to check
    
    Returns:
        Dict with verification status and agent details
    """
    try:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()
        
        if not campaign:
            return {
                "success": False,
                "error": "Campaign not found"
            }
        
        # Get verifications
        verifications = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_id
        ).all()
        
        if not verifications:
            return {
                "success": True,
                "campaign_title": campaign.title,
                "verified": False,
                "verification_count": 0,
                "status": campaign.status,
                "message": "No verifications submitted yet"
            }
        
        # Get highest trust score verification
        best_verification = max(verifications, key=lambda v: v.trust_score)
        
        agent = db.query(User).filter(
            User.id == best_verification.field_agent_id
        ).first()
        
        return {
            "success": True,
            "campaign_title": campaign.title,
            "verified": campaign.status == "active",
            "verification_count": len(verifications),
            "status": campaign.status,
            "best_trust_score": best_verification.trust_score,
            "best_verification": {
                "agent_name": agent.preferred_name or agent.full_name if agent else "Unknown",
                "trust_score": best_verification.trust_score,
                "verification_date": best_verification.verification_date.strftime("%b %d, %Y"),
                "photo_count": len(best_verification.photos) if best_verification.photos else 0,
                "has_gps": bool(best_verification.gps_latitude),
                "beneficiary_count": best_verification.beneficiary_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting verification status: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get status: {str(e)}"
        }
