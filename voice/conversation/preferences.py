"""
User Preference Management Module

LAB 9 Part 3: Handles user preferences for personalized conversations

Features:
- Store and retrieve user preferences
- Auto-fill preferences in donation flow
- Learn from user behavior
- Preference suggestions
"""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from database.models import User, UserPreference


class PreferenceManager:
    """Manage user preferences and defaults"""
    
    # Valid preference keys and their allowed values
    PREFERENCE_KEYS = {
        "payment_provider": ["chapa", "telebirr", "mpesa"],
        "donation_amount": None,  # No validation, store as string
        "language": ["en", "am"],
        "notification_preference": ["all", "major", "none"],
        "favorite_category": ["education", "health", "water", "food", "environment", "shelter"]
    }
    
    @staticmethod
    def set_preference(
        user_id: int,
        key: str,
        value: str,
        db: Session
    ) -> bool:
        """
        Set or update a user preference
        
        Args:
            user_id: User ID (from users table)
            key: Preference key (e.g., "payment_provider")
            value: Preference value (e.g., "chapa")
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        # Validate key
        if key not in PreferenceManager.PREFERENCE_KEYS:
            return False
        
        # Validate value (if validation rules exist)
        allowed_values = PreferenceManager.PREFERENCE_KEYS[key]
        if allowed_values and value not in allowed_values:
            return False
        
        try:
            # Check if preference exists
            existing = db.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == key
            ).first()
            
            if existing:
                # Update existing preference
                existing.preference_value = value
                existing.updated_at = datetime.utcnow()
            else:
                # Create new preference
                pref = UserPreference(
                    user_id=user_id,
                    preference_key=key,
                    preference_value=value
                )
                db.add(pref)
            
            db.commit()
            return True
            
        except IntegrityError:
            db.rollback()
            return False
    
    @staticmethod
    def get_preference(
        user_id: int,
        key: str,
        db: Session,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a user preference
        
        Args:
            user_id: User ID
            key: Preference key
            db: Database session
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_key == key
        ).first()
        
        return pref.preference_value if pref else default
    
    @staticmethod
    def get_all_preferences(
        user_id: int,
        db: Session
    ) -> Dict[str, str]:
        """
        Get all preferences for a user
        
        Returns:
            Dictionary of {key: value}
        """
        prefs = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()
        
        return {p.preference_key: p.preference_value for p in prefs}
    
    @staticmethod
    def delete_preference(
        user_id: int,
        key: str,
        db: Session
    ) -> bool:
        """
        Delete a user preference
        
        Returns:
            True if deleted, False if not found
        """
        pref = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_key == key
        ).first()
        
        if pref:
            db.delete(pref)
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def learn_from_donation(
        user_id: int,
        donation_data: Dict,
        db: Session
    ) -> None:
        """
        Learn preferences from completed donation
        
        Auto-saves payment provider and donation amount as preferences
        if user doesn't have them set yet
        
        Args:
            user_id: User ID
            donation_data: Dict with 'payment_provider' and 'amount'
            db: Database session
        """
        # Learn payment provider
        if "payment_provider" in donation_data:
            existing_provider = PreferenceManager.get_preference(
                user_id, "payment_provider", db
            )
            if not existing_provider:
                PreferenceManager.set_preference(
                    user_id,
                    "payment_provider",
                    donation_data["payment_provider"],
                    db
                )
        
        # Learn donation amount (if reasonable, between 10-10000)
        if "amount" in donation_data:
            amount = donation_data["amount"]
            if 10 <= amount <= 10000:
                existing_amount = PreferenceManager.get_preference(
                    user_id, "donation_amount", db
                )
                if not existing_amount:
                    PreferenceManager.set_preference(
                        user_id,
                        "donation_amount",
                        str(amount),
                        db
                    )
    
    @staticmethod
    def suggest_defaults(
        user_id: int,
        db: Session,
        current_step: str
    ) -> Dict[str, any]:
        """
        Suggest default values based on user preferences
        
        Args:
            user_id: User ID
            current_step: Current donation step
            db: Database session
            
        Returns:
            Dictionary of suggested values
        """
        suggestions = {}
        
        # Get all user preferences
        prefs = PreferenceManager.get_all_preferences(user_id, db)
        
        # Suggest payment provider
        if current_step == "select_payment" and "payment_provider" in prefs:
            suggestions["payment_provider"] = prefs["payment_provider"]
            suggestions["message"] = f"Use your usual {prefs['payment_provider'].title()}? (or choose another)"
        
        # Suggest donation amount
        if current_step == "enter_amount" and "donation_amount" in prefs:
            suggestions["amount"] = int(prefs["donation_amount"])
            suggestions["message"] = f"Your usual amount is {prefs['donation_amount']} birr. Use this or enter different amount?"
        
        # Suggest favorite category
        if current_step == "select_campaign" and "favorite_category" in prefs:
            suggestions["category"] = prefs["favorite_category"]
            suggestions["message"] = f"Show your favorite ({prefs['favorite_category']}) campaigns first?"
        
        return suggestions


class PreferenceLearner:
    """Auto-learn user preferences from behavior"""
    
    @staticmethod
    def analyze_donation_pattern(
        user_id: int,
        db: Session
    ) -> Dict[str, any]:
        """
        Analyze user's donation history to detect patterns
        
        Returns:
            Dictionary of detected patterns
        """
        from database.models import Donation
        
        # Get user's donations
        donations = db.query(Donation).filter(
            Donation.donor_id == user_id
        ).order_by(Donation.created_at.desc()).limit(10).all()
        
        if not donations:
            return {}
        
        patterns = {}
        
        # Most common payment provider
        payment_providers = [d.payment_method for d in donations if d.payment_method]
        if payment_providers:
            most_common_provider = max(set(payment_providers), key=payment_providers.count)
            patterns["preferred_payment"] = most_common_provider
        
        # Average donation amount
        amounts = [d.amount for d in donations if d.amount]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            patterns["typical_amount"] = int(avg_amount)
        
        # Most donated category
        categories = []
        for donation in donations:
            if donation.campaign and donation.campaign.category:
                categories.append(donation.campaign.category)
        
        if categories:
            most_common_category = max(set(categories), key=categories.count)
            patterns["favorite_category"] = most_common_category
        
        return patterns
    
    @staticmethod
    def auto_learn_preferences(
        user_id: int,
        db: Session
    ) -> int:
        """
        Automatically learn and save preferences from user history
        
        Returns:
            Number of preferences learned
        """
        patterns = PreferenceLearner.analyze_donation_pattern(user_id, db)
        learned_count = 0
        
        # Save detected patterns as preferences (if not already set)
        if "preferred_payment" in patterns:
            existing = PreferenceManager.get_preference(user_id, "payment_provider", db)
            if not existing:
                PreferenceManager.set_preference(
                    user_id,
                    "payment_provider",
                    patterns["preferred_payment"],
                    db
                )
                learned_count += 1
        
        if "typical_amount" in patterns:
            existing = PreferenceManager.get_preference(user_id, "donation_amount", db)
            if not existing:
                PreferenceManager.set_preference(
                    user_id,
                    "donation_amount",
                    str(patterns["typical_amount"]),
                    db
                )
                learned_count += 1
        
        if "favorite_category" in patterns:
            existing = PreferenceManager.get_preference(user_id, "favorite_category", db)
            if not existing:
                PreferenceManager.set_preference(
                    user_id,
                    "favorite_category",
                    patterns["favorite_category"],
                    db
                )
                learned_count += 1
        
        return learned_count
