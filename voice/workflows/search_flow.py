"""
Multi-turn campaign search with refinement

Enables users to:
- Search campaigns by category, region, keyword
- Ask follow-up questions ("show me more")
- Refine searches ("what about in Nairobi?")
- View details on specific results ("tell me about #1")
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.models import Campaign
from voice.session_manager import SessionManager, ConversationState
import re


class SearchConversation:
    """Handle campaign search refinement"""
    
    @staticmethod
    async def start_search(
        user_id: str,
        query: str,
        db: Session
    ) -> Dict:
        """
        Initial campaign search
        
        Args:
            user_id: Telegram user ID
            query: Search query (e.g., "health campaigns in Nairobi")
            db: Database session
        """
        # Create search session
        SessionManager.create_session(user_id, ConversationState.SEARCHING_CAMPAIGNS)
        
        # Parse query for filters
        filters = SearchConversation._parse_query(query)
        
        # Debug: Log what filters were extracted
        print(f"[DEBUG] Search query: '{query}'")
        print(f"[DEBUG] Extracted filters: {filters}")
        
        # Search campaigns
        campaigns = SearchConversation._search_with_filters(filters, db)
        
        # Save results to session
        SessionManager.update_session(
            user_id,
            data_update={
                "last_filters": filters,
                "result_count": len(campaigns),
                "campaign_ids": [c.id for c in campaigns],
                "current_page": 1
            },
            message=f"Searched: {query}"
        )
        
        # Format response
        if not campaigns:
            message = (
                "No campaigns found matching your criteria. 🔍\n\n"
                "Try:\n"
                "• Different category (education, health, water)\n"
                "• Broader region\n"
                "• Different keywords"
            )
            SessionManager.end_session(user_id)
            return {"message": message, "campaigns": []}
        
        message = f"I found {len(campaigns)} campaigns:\n\n"
        for i, camp in enumerate(campaigns, 1):
            raised = camp.raised_amount_usd or 0
            goal = camp.goal_amount_usd or 1
            progress = int((raised / goal) * 100)
            region = camp.location_region or camp.location_country or "N/A"
            
            message += (
                f"{i}. {camp.title} (#{camp.id})\n"
                f"   {progress}% funded | 📍 {region}\n\n"
            )
        
        message += "💬 Want to:\n"
        message += "• See details? (\"tell me about #1\")\n"
        message += "• Refine search? (\"show me education only\")\n"
        message += "• Donate? (\"donate to #2\")"
        
        return {
            "message": message,
            "campaigns": [{"id": c.id, "title": c.title} for c in campaigns],
            "filters": filters
        }
    
    @staticmethod
    async def refine_search(
        user_id: str,
        refinement: str,
        db: Session
    ) -> Dict:
        """
        Refine existing search
        
        Examples:
        - "what about in Nairobi?"
        - "show me education instead"
        - "only active campaigns"
        """
        session = SessionManager.get_session(user_id)
        
        if not session:
            return {"message": "Start a search first! Try 'search campaigns'"}
        
        # Get previous filters
        previous_filters = session["data"].get("last_filters", {})
        
        # Parse refinement
        new_filters = SearchConversation._parse_query(refinement)
        
        # Merge filters (new overrides old)
        filters = {**previous_filters, **new_filters}
        
        # Search with refined filters
        campaigns = SearchConversation._search_with_filters(filters, db)
        
        # Update session
        SessionManager.update_session(
            user_id,
            data_update={
                "last_filters": filters,
                "campaign_ids": [c.id for c in campaigns],
                "current_page": 1
            },
            message=f"Refined: {refinement}"
        )
        
        # Format response
        if not campaigns:
            return {
                "message": "No campaigns match those criteria. Try different filters?",
                "campaigns": []
            }
        
        message = f"Found {len(campaigns)} campaigns with your filters:\n\n"
        for i, camp in enumerate(campaigns, 1):
            raised = camp.raised_amount_usd or 0
            goal = camp.goal_amount_usd or 1
            progress = int((raised / goal) * 100)
            
            message += f"{i}. {camp.title} (#{camp.id}) - {progress}%\n"
        
        return {
            "message": message,
            "campaigns": [{"id": c.id, "title": c.title} for c in campaigns]
        }
    
    @staticmethod
    async def show_campaign_details(
        user_id: str,
        campaign_ref: str,
        db: Session
    ) -> Dict:
        """
        Show details for specific campaign
        
        Args:
            campaign_ref: "1", "#42", "first one"
        """
        session = SessionManager.get_session(user_id)
        
        if not session:
            return {"message": "Search for campaigns first!"}
        
        # Get campaign IDs from search results
        campaign_ids = session["data"].get("campaign_ids", [])
        
        if not campaign_ids:
            return {"message": "No search results to show details for."}
        
        # Parse campaign reference
        campaign_id = SearchConversation._parse_campaign_ref(campaign_ref, campaign_ids)
        
        if not campaign_id:
            return {"message": "I couldn't find that campaign. Try a number like '1' or '#42'"}
        
        # Get campaign details
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        if not campaign:
            return {"message": "Campaign not found."}
        
        # Format detailed response
        raised = campaign.raised_amount_usd or 0
        goal = campaign.goal_amount_usd or 1
        progress = int((raised / goal) * 100)
        
        message = (
            f"📊 {campaign.title} (#{campaign.id})\n\n"
            f"Goal: ${goal:,.0f} | Raised: ${raised:,.0f} ({progress}%)\n"
            f"Category: {campaign.category}\n"
            f"Location: {campaign.location_region or campaign.location_country}\n\n"
            f"{campaign.description[:200]}...\n\n"
            f"💬 Type 'donate to #{campaign.id}' to support this campaign!"
        )
        
        # Save current campaign to context
        SessionManager.update_session(
            user_id,
            data_update={"current_campaign_id": campaign_id},
            message=f"Viewed details: {campaign.title}"
        )
        
        return {
            "message": message,
            "campaign": {"id": campaign.id, "title": campaign.title},
            "data": {"campaign_id": campaign_id}
        }
    
    @staticmethod
    def _parse_query(query: str) -> Dict[str, str]:
        """
        Extract filters from natural language query
        
        Examples:
        - "health campaigns" -> {category: health}
        - "education in Nairobi" -> {category: education, region: Nairobi}
        - "water projects Kenya" -> {category: water, region: Kenya}
        """
        query_lower = query.lower()
        filters = {}
        
        # Categories
        categories = {
            "education": ["education", "school", "learning", "students"],
            "health": ["health", "medical", "hospital", "clinic", "healthcare"],
            "water": ["water", "sanitation", "clean water", "wells"],
            "environment": ["environment", "climate", "trees", "green"],
            "food": ["food", "hunger", "nutrition", "feeding"]
        }
        
        for category, keywords in categories.items():
            if any(kw in query_lower for kw in keywords):
                filters["category"] = category
                break
        
        # Regions (Kenya-specific, expand as needed)
        regions = [
            "nairobi", "mombasa", "kisumu", "nakuru", "eldoret",
            "kenya", "uganda", "tanzania", "ethiopia"
        ]
        
        for region in regions:
            if region in query_lower:
                filters["region"] = region.title()
                break
        
        # Keywords (anything not category/region)
        # Remove category/region words and generic terms
        keyword = query_lower
        for cat_words in categories.values():
            for word in cat_words:
                keyword = keyword.replace(word, "")
        for region in regions:
            keyword = keyword.replace(region, "")
        
        # Remove generic terms that don't help search
        generic_terms = ["campaign", "campaigns", "project", "projects", "show", "me", "find", "search", "in", "for", "active", "available", "current", "can", "you", "please", "tell", "what", "are", "the"]
        for term in generic_terms:
            keyword = keyword.replace(term, "")
        
        keyword = keyword.strip()
        if keyword and len(keyword) > 3:
            filters["keyword"] = keyword
        
        return filters
    
    @staticmethod
    def _search_with_filters(filters: Dict[str, str], db: Session) -> List[Campaign]:
        """Execute search with filters"""
        query = db.query(Campaign).filter(Campaign.status == "active")
        
        if filters.get("category"):
            query = query.filter(Campaign.category == filters["category"])
        
        if filters.get("region"):
            region = filters["region"]
            query = query.filter(
                or_(
                    Campaign.location_region.ilike(f"%{region}%"),
                    Campaign.location_country.ilike(f"%{region}%")
                )
            )
        
        if filters.get("keyword"):
            keyword = f"%{filters['keyword']}%"
            query = query.filter(
                or_(
                    Campaign.title.ilike(keyword),
                    Campaign.description.ilike(keyword)
                )
            )
        
        return query.order_by(Campaign.created_at.desc()).limit(10).all()
    
    @staticmethod
    def _parse_campaign_ref(ref: str, campaign_ids: List[int]) -> Optional[int]:
        """
        Parse campaign reference to ID
        
        Examples:
        - "1" -> campaign_ids[0]
        - "number one" -> campaign_ids[0]
        - "#42" -> 42
        - "first one" -> campaign_ids[0]
        """
        ref_lower = ref.lower()
        
        # Word numbers (handles "number one", "number two", etc.)
        word_numbers = {
            "one": 1, "1": 1,
            "two": 2, "2": 2,
            "three": 3, "3": 3,
            "four": 4, "4": 4,
            "five": 5, "5": 5,
            "six": 6, "6": 6,
            "seven": 7, "7": 7,
            "eight": 8, "8": 8,
            "nine": 9, "9": 9,
            "ten": 10, "10": 10
        }
        
        # Check for word numbers in the reference
        for word, num in word_numbers.items():
            if word in ref_lower and num <= len(campaign_ids):
                return campaign_ids[num - 1]
        
        # Ordinals (handles "first", "second", "third", etc.)
        ordinals = {
            "first": 0, "1st": 0,
            "second": 1, "2nd": 1,
            "third": 2, "3rd": 2,
            "fourth": 3, "4th": 3,
            "fifth": 4, "5th": 4,
            "sixth": 5, "6th": 5,
            "seventh": 6, "7th": 6,
            "eighth": 7, "8th": 7,
            "ninth": 8, "9th": 8,
            "tenth": 9, "10th": 9
        }
        
        for word, idx in ordinals.items():
            if word in ref_lower and idx < len(campaign_ids):
                return campaign_ids[idx]
        
        # Direct number with regex (handles "#42", "42", etc.)
        match = re.search(r'#?(\d+)', ref)
        if match:
            num = int(match.group(1))
            
            # Check if it's an index (1-10) or campaign ID
            if num <= len(campaign_ids):
                return campaign_ids[num - 1]
            elif num in campaign_ids:
                return num
        
        return None


# Main router for search conversations

async def route_search_message(
    user_id: str,
    message: str,
    db: Session
) -> Dict[str, str]:
    """
    Route search-related messages
    
    Detects:
    - Initial searches ("search campaigns", "show me health")
    - Refinements ("what about education?", "in Nairobi")
    - Detail requests ("tell me about #1")
    """
    message_lower = message.lower()
    session = SessionManager.get_session(user_id)
    
    # Check for detail request
    if any(phrase in message_lower for phrase in ["tell me about", "details", "more info"]):
        # Extract campaign reference
        return await SearchConversation.show_campaign_details(user_id, message, db)
    
    # Check for refinement keywords
    if session and any(word in message_lower for word in ["what about", "show me", "filter", "only"]):
        return await SearchConversation.refine_search(user_id, message, db)
    
    # Default: new search
    return await SearchConversation.start_search(user_id, message, db)
