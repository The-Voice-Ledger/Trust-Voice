"""
Impact Report Handler - Module 4 of Lab 5

Enables field agents to submit impact reports for campaigns they've visited.
Reports include photos, GPS coordinates, beneficiary testimonials, and observations.

Field agents receive $30 M-Pesa payment upon report approval.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from database.models import (
    ImpactVerification,
    Campaign,
    User,
    Donation
)

logger = logging.getLogger(__name__)


async def process_impact_report(
    db: Session,
    telegram_user_id: str,
    campaign_id: uuid.UUID,
    description: str,
    photo_urls: List[str],
    gps_latitude: Optional[float] = None,
    gps_longitude: Optional[float] = None,
    beneficiary_count: Optional[int] = None,
    testimonials: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an impact report from a field agent.
    
    GPS Verification Workflow:
    1. Campaign creator uploads transparency video with GPS (optional)
    2. Field agent visits site and submits verification with GPS
    3. System calculates distance between video GPS and verification GPS
    4. If within 500m → location verified (increases trust)
    5. GET /campaigns/{id}/verify-location shows verification status
    
    Args:
        db: Database session
        telegram_user_id: Field agent's Telegram ID
        campaign_id: Campaign being verified
        description: Agent's observations and notes
        photo_urls: List of uploaded photo URLs (Telegram file IDs)
        gps_latitude: Site visit latitude (compared against campaign video GPS)
        gps_longitude: Site visit longitude (compared against campaign video GPS)
        beneficiary_count: Number of beneficiaries observed
        testimonials: Quotes from beneficiaries
    
    Returns:
        Dict with success status, verification ID, and next steps
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
                "error": "Only Field Agents can submit impact reports. Your role: " + user.role
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
        
        # Check if campaign is active or completed (can verify both)
        if campaign.status not in ["active", "completed"]:
            return {
                "success": False,
                "error": f"Cannot verify {campaign.status} campaign. Must be active or completed."
            }
        
        # Check if agent already submitted report for this campaign
        existing = db.query(ImpactVerification).filter(
            ImpactVerification.campaign_id == campaign_id,
            ImpactVerification.field_agent_id == user.id
        ).first()
        
        if existing:
            return {
                "success": False,
                "error": f"You already submitted a report for this campaign on {existing.created_at.strftime('%b %d, %Y')}",
                "existing_verification_id": str(existing.id)
            }
        
        # Calculate initial trust score (0-100)
        trust_score = _calculate_trust_score(
            photo_count=len(photo_urls),
            has_gps=bool(gps_latitude and gps_longitude),
            has_testimonials=bool(testimonials),
            description_length=len(description) if description else 0,
            beneficiary_count=beneficiary_count
        )
        
        # Auto-approve if score >= 80
        auto_approved = trust_score >= 80
        status = "approved" if auto_approved else "pending"
        
        # Create verification record
        verification = ImpactVerification(
            campaign_id=campaign_id,
            field_agent_id=user.id,
            verification_date=datetime.utcnow(),
            photos=photo_urls,  # List of Telegram file IDs or URLs
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            beneficiary_count=beneficiary_count or 0,
            testimonials=testimonials,
            agent_notes=description,
            trust_score=trust_score,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(verification)
        
        # Update campaign metrics
        if not hasattr(campaign, 'verification_count'):
            campaign.verification_count = 0
        campaign.verification_count += 1
        
        if not hasattr(campaign, 'total_trust_score'):
            campaign.total_trust_score = 0
        campaign.total_trust_score += trust_score
        
        # Calculate average trust score
        campaign.avg_trust_score = campaign.total_trust_score / campaign.verification_count
        
        db.commit()
        db.refresh(verification)
        
        # Prepare response
        result = {
            "success": True,
            "verification_id": str(verification.id),
            "trust_score": trust_score,
            "status": status,
            "auto_approved": auto_approved,
            "campaign_title": campaign.title,
            "agent_name": getattr(user, 'preferred_name', None) or user.full_name
        }
        
        # If auto-approved, initiate agent payout
        if auto_approved:
            payout_result = await _initiate_agent_payout(
                db=db,
                agent=user,
                verification_id=verification.id,
                amount_usd=30.0  # Standard field agent fee
            )
            result["payout"] = payout_result
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing impact report: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": f"Failed to process report: {str(e)}"
        }


def _calculate_trust_score(
    photo_count: int,
    has_gps: bool,
    has_testimonials: bool,
    description_length: int,
    beneficiary_count: Optional[int]
) -> int:
    """
    Calculate trust score (0-100) based on report quality.
    
    Scoring rubric:
    - Photos: 30 points (10 per photo, max 3)
    - GPS: 25 points
    - Testimonials: 20 points
    - Description: 15 points (1 point per 20 chars, max 15)
    - Beneficiary count: 10 points
    
    Returns:
        Trust score from 0-100
    """
    score = 0
    
    # Photos (max 30 points)
    score += min(photo_count * 10, 30)
    
    # GPS coordinates (25 points)
    if has_gps:
        score += 25
    
    # Testimonials (20 points)
    if has_testimonials:
        score += 20
    
    # Description quality (max 15 points)
    description_points = min(description_length // 20, 15)
    score += description_points
    
    # Beneficiary count (10 points)
    if beneficiary_count and beneficiary_count > 0:
        score += 10
    
    return min(score, 100)


async def _initiate_agent_payout(
    db: Session,
    agent: User,
    verification_id: uuid.UUID,
    amount_usd: float
) -> Dict[str, Any]:
    """
    Initiate M-Pesa payout to field agent for approved verification.
    
    Standard fee: $30 USD (~3,900 KES)
    
    Args:
        db: Database session
        agent: Field agent User object
        verification_id: Verification that triggered payout
        amount_usd: Payout amount in USD
    
    Returns:
        Dict with payout status and transaction details
    """
    try:
        from services.mpesa import mpesa_b2c_payout
        
        # Validate agent has phone number
        if not agent.phone_number:
            return {
                "success": False,
                "error": "Agent phone number not found"
            }
        
        # Validate phone is Kenya number for M-Pesa
        if not agent.phone_number.startswith("+254"):
            return {
                "success": False,
                "error": "M-Pesa payouts only available for Kenya (+254) numbers"
            }
        
        # Convert USD to KES (approximate rate: 1 USD = 130 KES)
        amount_kes = int(amount_usd * 130)
        
        # Initiate M-Pesa B2C payout
        result = mpesa_b2c_payout(
            phone_number=agent.phone_number,
            amount=amount_kes,
            occasion=f"Impact Report Verification",
            remarks=f"TrustVoice field agent fee for verification {str(verification_id)[:8]}"
        )
        
        if result.get("success"):
            # Update verification with payout info
            verification = db.query(ImpactVerification).filter(
                ImpactVerification.id == verification_id
            ).first()
            
            if verification:
                verification.agent_payout_status = "initiated"
                verification.agent_payout_amount_usd = amount_usd
                verification.agent_payout_transaction_id = result.get("ConversationID")
                db.commit()
            
            return {
                "success": True,
                "amount_kes": amount_kes,
                "amount_usd": amount_usd,
                "phone_number": agent.phone_number,
                "transaction_id": result.get("ConversationID"),
                "message": f"KES {amount_kes:,} sent to {agent.phone_number}"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "M-Pesa payout failed")
            }
            
    except Exception as e:
        logger.error(f"Agent payout error: {str(e)}")
        return {
            "success": False,
            "error": f"Payout failed: {str(e)}"
        }


async def get_agent_verifications(
    db: Session,
    telegram_user_id: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get verification reports submitted by a field agent.
    
    Args:
        db: Database session
        telegram_user_id: Agent's Telegram ID
        limit: Max number of reports to return
    
    Returns:
        Dict with agent's verification history
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
        
        # Get verifications
        verifications = db.query(ImpactVerification).filter(
            ImpactVerification.field_agent_id == user.id
        ).order_by(ImpactVerification.created_at.desc()).limit(limit).all()
        
        if not verifications:
            return {
                "success": True,
                "verifications": [],
                "total_count": 0,
                "total_earned_usd": 0
            }
        
        # Calculate total earnings
        total_earned = sum(
            v.agent_payout_amount_usd or 0 
            for v in verifications 
            if v.agent_payout_status == "completed"
        )
        
        # Format verification data
        verification_list = []
        for v in verifications:
            campaign = db.query(Campaign).filter(
                Campaign.id == v.campaign_id
            ).first()
            
            verification_list.append({
                "id": str(v.id),
                "campaign_title": campaign.title if campaign else "Unknown",
                "trust_score": v.trust_score,
                "status": v.status,
                "created_at": v.created_at.strftime("%b %d, %Y"),
                "photo_count": len(v.photos) if v.photos else 0,
                "has_gps": bool(v.gps_latitude and v.gps_longitude),
                "payout_status": v.agent_payout_status,
                "payout_amount_usd": v.agent_payout_amount_usd or 0
            })
        
        return {
            "success": True,
            "verifications": verification_list,
            "total_count": len(verifications),
            "total_earned_usd": total_earned
        }
        
    except Exception as e:
        logger.error(f"Error getting agent verifications: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get verifications: {str(e)}"
        }


async def get_campaign_verifications(
    db: Session,
    campaign_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get all verification reports for a specific campaign.
    Used by campaign creators and admins to see verification status.
    
    Args:
        db: Database session
        campaign_id: Campaign to get verifications for
    
    Returns:
        Dict with campaign's verification reports
    """
    try:
        # Get campaign
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
        ).order_by(ImpactVerification.created_at.desc()).all()
        
        if not verifications:
            return {
                "success": True,
                "campaign_title": campaign.title,
                "verifications": [],
                "total_count": 0,
                "avg_trust_score": 0,
                "total_beneficiaries": 0
            }
        
        # Calculate metrics
        total_beneficiaries = sum(v.beneficiary_count or 0 for v in verifications)
        avg_trust_score = sum(v.trust_score for v in verifications) / len(verifications)
        
        # Format verification data
        verification_list = []
        for v in verifications:
            agent = db.query(User).filter(
                User.id == v.field_agent_id
            ).first()
            
            verification_list.append({
                "id": str(v.id),
                "agent_name": agent.full_name if agent else "Unknown",
                "trust_score": v.trust_score,
                "status": v.status,
                "verification_date": v.verification_date.strftime("%b %d, %Y"),
                "photo_count": len(v.photos) if v.photos else 0,
                "has_gps": bool(v.gps_latitude and v.gps_longitude),
                "beneficiary_count": v.beneficiary_count or 0,
                "has_testimonials": bool(v.testimonials)
            })
        
        return {
            "success": True,
            "campaign_title": campaign.title,
            "verifications": verification_list,
            "total_count": len(verifications),
            "avg_trust_score": round(avg_trust_score, 1),
            "total_beneficiaries": total_beneficiaries
        }
        
    except Exception as e:
        logger.error(f"Error getting campaign verifications: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get verifications: {str(e)}"
        }
