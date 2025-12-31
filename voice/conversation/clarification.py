"""
Clarification & Error Recovery Module

Handles ambiguous inputs with:
- Fuzzy campaign matching
- Disambiguation questions
- Correction handling
- Number parsing with units
"""

from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import re
from sqlalchemy.orm import Session

from database.models import Campaign
from voice.session_manager import SessionManager


class ClarificationHandler:
    """Handle ambiguous inputs with clarification questions"""
    
    SIMILARITY_THRESHOLD = 0.6  # 60% similarity for fuzzy matching
    HIGH_CONFIDENCE_THRESHOLD = 0.9  # 90% = treat as exact match
    
    @staticmethod
    def fuzzy_match_campaign(
        user_input: str,
        db: Session,
        threshold: float = None
    ) -> Tuple[Optional[Campaign], List[Campaign]]:
        """
        Fuzzy match campaign name using Levenshtein distance
        
        Args:
            user_input: User's input text (e.g., "educashun", "health care")
            db: Database session
            threshold: Similarity threshold (default: 0.6)
            
        Returns:
            (exact_match, similar_matches)
            - exact_match: Campaign if confidence > 90%
            - similar_matches: List of campaigns if 60-90% match
        """
        if threshold is None:
            threshold = ClarificationHandler.SIMILARITY_THRESHOLD
            
        user_input_lower = user_input.lower().strip()
        
        # Get active campaigns
        campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).all()
        
        matches = []
        for campaign in campaigns:
            # Calculate similarity with campaign title
            title_similarity = SequenceMatcher(
                None, 
                user_input_lower, 
                campaign.title.lower()
            ).ratio()
            
            # Also check category match
            category_similarity = 0.0
            if campaign.category:
                category_similarity = SequenceMatcher(
                    None,
                    user_input_lower,
                    campaign.category.lower()
                ).ratio()
            
            # Take best match
            best_similarity = max(title_similarity, category_similarity)
            
            if best_similarity > threshold:
                matches.append((campaign, best_similarity))
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        if not matches:
            return None, []
        
        # If top match > 90%, treat as exact
        if matches[0][1] > ClarificationHandler.HIGH_CONFIDENCE_THRESHOLD:
            return matches[0][0], []
        
        # If multiple good matches, need clarification
        similar = [m[0] for m in matches[:3]]  # Top 3
        return None, similar
    
    @staticmethod
    async def handle_ambiguous_campaign(
        user_id: str,
        user_input: str,
        db: Session
    ) -> Dict[str, any]:
        """
        Handle ambiguous campaign selection
        
        Returns response with clarification question or exact match
        
        Returns:
            {
                "type": "exact_match" | "clarification_needed" | "no_match",
                "campaign": {...} (if exact match),
                "options": [...] (if clarification needed),
                "message": "Response text"
            }
        """
        exact, similar = ClarificationHandler.fuzzy_match_campaign(
            user_input, db
        )
        
        if exact:
            # High confidence match
            return {
                "type": "exact_match",
                "campaign": {"id": exact.id, "title": exact.title},
                "message": f"Found: {exact.title}. How much would you like to donate?"
            }
        
        if similar:
            # Need clarification
            SessionManager.update_session(
                user_id,
                data_update={
                    "pending_clarification": "campaign_selection",
                    "clarification_options": [
                        {"id": c.id, "title": c.title} 
                        for c in similar
                    ]
                }
            )
            
            message = f"I found {len(similar)} campaigns matching '{user_input}':\n\n"
            for i, camp in enumerate(similar, 1):
                message += f"{i}. {camp.title}\n"
            message += "\nWhich one? (reply with number or full name)"
            
            return {
                "type": "clarification_needed",
                "options": [{"id": c.id, "title": c.title} for c in similar],
                "message": message
            }
        
        # No matches
        return {
            "type": "no_match",
            "message": f"I couldn't find campaigns matching '{user_input}'. "
                      f"Try 'education', 'health', 'water', or ask 'what campaigns do you have?'"
        }
    
    @staticmethod
    async def resolve_clarification(
        user_id: str,
        user_response: str,
        db: Session
    ) -> Optional[Campaign]:
        """
        Resolve pending clarification
        
        Args:
            user_response: e.g., "1", "2", "3" or full campaign name
            
        Returns:
            Selected campaign or None if still unclear
        """
        session = SessionManager.get_session(user_id)
        if not session or "pending_clarification" not in session["data"]:
            return None
        
        options = session["data"].get("clarification_options", [])
        
        # Try numeric selection (1, 2, 3)
        response_stripped = user_response.strip()
        if response_stripped.isdigit():
            idx = int(response_stripped) - 1
            if 0 <= idx < len(options):
                campaign_id = options[idx]["id"]
                campaign = db.query(Campaign).filter(
                    Campaign.id == campaign_id
                ).first()
                
                # Clear clarification state
                SessionManager.update_session(
                    user_id,
                    data_update={
                        "pending_clarification": None,
                        "clarification_options": None
                    }
                )
                
                return campaign
        
        # Try matching by title again
        for opt in options:
            if user_response.lower() in opt["title"].lower():
                campaign = db.query(Campaign).filter(
                    Campaign.id == opt["id"]
                ).first()
                
                SessionManager.update_session(
                    user_id,
                    data_update={
                        "pending_clarification": None,
                        "clarification_options": None
                    }
                )
                
                return campaign
        
        return None
    
    @staticmethod
    def parse_number_with_units(text: str) -> Optional[int]:
        """
        Parse numbers with various formats
        
        Examples:
            "50" -> 50
            "50 birr" -> 50
            "fifty" -> 50
            "$100" -> 100
            "five hundred" -> 500
        """
        # Word to number mapping
        word_numbers = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
            "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
            "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
            "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
            "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000
        }
        
        text_lower = text.lower().strip()
        
        # Try extracting numeric value first (most common)
        num_match = re.search(r'(\d+)', text)
        if num_match:
            return int(num_match.group(1))
        
        # Try word numbers
        total = 0
        current = 0
        
        words = text_lower.split()
        for word in words:
            if word in word_numbers:
                value = word_numbers[word]
                if value == 100:
                    current = current * 100 if current else 100
                elif value == 1000:
                    current = current * 1000 if current else 1000
                else:
                    current += value
        
        if current > 0:
            return current
        
        # Check for single word match
        for word, value in word_numbers.items():
            if word in text_lower:
                return value
        
        return None


class ConversationRepair:
    """Handle conversation repairs and corrections"""
    
    CORRECTION_KEYWORDS = [
        "actually", "change", "meant", "no wait", "correction",
        "i mean", "sorry", "wait", "no", "instead"
    ]
    
    @staticmethod
    def is_correction(message: str) -> bool:
        """Check if message is a correction"""
        message_lower = message.lower()
        return any(kw in message_lower for kw in ConversationRepair.CORRECTION_KEYWORDS)
    
    @staticmethod
    async def handle_correction(
        user_id: str,
        correction: str,
        db: Session
    ) -> Dict[str, any]:
        """
        Handle user corrections
        
        Examples:
            "I meant 500, not 50"
            "Actually, change that to Chapa"
            "No, the education campaign"
        """
        session = SessionManager.get_session(user_id)
        if not session:
            return {"message": "No active session to correct."}
        
        current_step = session.get("current_step")
        data = session.get("data", {})
        
        correction_lower = correction.lower()
        
        # Amount correction
        if current_step in ["select_payment", "confirm"]:
            new_amount = ClarificationHandler.parse_number_with_units(correction)
            if new_amount:
                SessionManager.update_session(
                    user_id,
                    current_step="select_payment",
                    data_update={"amount": new_amount},
                    message=f"Corrected amount to {new_amount}"
                )
                return {
                    "message": f"✓ Updated to {new_amount} birr. How would you like to pay?",
                    "step": "select_payment"
                }
        
        # Payment method correction
        payment_providers = {
            "chapa": ["chapa"],
            "telebirr": ["telebirr", "tele birr"],
            "mpesa": ["mpesa", "m-pesa", "m pesa"]
        }
        
        for provider, keywords in payment_providers.items():
            if any(kw in correction_lower for kw in keywords):
                SessionManager.update_session(
                    user_id,
                    data_update={"payment_provider": provider},
                    message=f"Corrected payment to {provider}"
                )
                
                return {
                    "message": f"✓ Changed payment method to {provider.title()}. "
                              f"Type 'confirm' to proceed.",
                    "step": "confirm"
                }
        
        # Campaign correction (fuzzy match)
        if any(word in correction_lower for word in ["campaign", "education", "health", "water", "shelter"]):
            result = await ClarificationHandler.handle_ambiguous_campaign(
                user_id, correction, db
            )
            return result
        
        return {
            "message": "I'm not sure what to correct. Can you be more specific? "
                      "(e.g., 'change amount to 500' or 'use Chapa instead')"
        }
