from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User, NGOOrganization
from voice.routers.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me/ngo-status")
def get_user_ngo_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if current user has an approved NGO.
    
    Returns NGO status and details if user has an approved NGO.
    Used by frontend to determine if user can create campaigns.
    """
    try:
        # Check if user has ngo_id
        if not current_user.ngo_id:
            return {
                "has_ngo": False,
                "ngo_id": None,
                "ngo_name": None,
                "message": "No NGO assigned to user"
            }
        
        # Check if NGO exists and is verified
        ngo = db.query(NGOOrganization).filter(
            NGOOrganization.id == current_user.ngo_id,
            NGOOrganization.verification_status == 'VERIFIED'
        ).first()
        
        if not ngo:
            return {
                "has_ngo": False,
                "ngo_id": current_user.ngo_id,
                "ngo_name": None,
                "message": "NGO not found or not verified"
            }
        
        return {
            "has_ngo": True,
            "ngo_id": ngo.id,
            "ngo_name": ngo.name,
            "ngo": {
                "id": ngo.id,
                "name": ngo.name,
                "email": ngo.contact_email,
                "country": ngo.country,
                "verification_status": ngo.verification_status
            },
            "message": "User has approved NGO"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking NGO status: {str(e)}"
        )
