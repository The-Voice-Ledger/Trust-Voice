"""
Conversation Context Manager for TrustVoice
Tracks user conversations across multiple voice messages.

Note: This module provides NLU-specific context (intents, entities, campaign focus).
For conversation flow state, see voice.session_manager.SessionManager (Redis-backed).
When Redis is available, get_context() merges data from both sources.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Manages conversation state for voice interactions
    
    Tracks:
    - Previous intents and entities
    - Campaigns user is viewing
    - Collected entities across multiple turns
    - Conversation timeouts
    
    Thread-safe for concurrent users
    """
    
    _conversations: Dict[str, Dict[str, Any]] = {}
    _lock = Lock()
    TIMEOUT = timedelta(minutes=5)  # 5 minute inactivity timeout
    
    @classmethod
    def get_context(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation context for a user.
        
        Merges in-memory NLU context with Redis session data when available,
        providing a unified view of the conversation state.
        
        Args:
            user_id: Unique user identifier (phone/telegram_id)
            
        Returns:
            Context dictionary or None if expired
        """
        with cls._lock:
            context = None
            
            if user_id in cls._conversations:
                ctx = cls._conversations[user_id]
                
                # Check if conversation has timed out
                last_activity = ctx.get("last_activity")
                if last_activity and datetime.now() - last_activity > cls.TIMEOUT:
                    logger.info(f"Conversation timeout for user {user_id}")
                    del cls._conversations[user_id]
                else:
                    context = ctx.copy()
            
            # Merge with Redis session data if available
            try:
                from voice.session_manager import SessionManager
                session = SessionManager.get_session(user_id)
                if session:
                    session_data = session.get("data", {})
                    if context is None:
                        context = {
                            "created_at": datetime.now(),
                            "turn_count": 0,
                            "intents_history": [],
                            "collected_entities": {}
                        }
                    # Add session state info to context for NLU awareness
                    context["session_state"] = session.get("state")
                    context["pending_intent"] = session_data.get("pending_intent")
                    context["pending_entities"] = session_data.get("pending_entities")
            except Exception:
                pass  # Redis unavailable, use in-memory only
            
            return context
    
    @classmethod
    def update_context(
        cls,
        user_id: str,
        intent: str,
        entities: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Update conversation context after processing a message
        
        Args:
            user_id: Unique user identifier
            intent: The extracted intent
            entities: Extracted entities
            additional_data: Any additional context to store
        """
        with cls._lock:
            if user_id not in cls._conversations:
                cls._conversations[user_id] = {
                    "created_at": datetime.now(),
                    "turn_count": 0,
                    "intents_history": [],
                    "collected_entities": {}
                }
            
            context = cls._conversations[user_id]
            
            # Update activity timestamp
            context["last_activity"] = datetime.now()
            context["turn_count"] += 1
            
            # Track intent history (last 5)
            context["intents_history"].append({
                "intent": intent,
                "timestamp": datetime.now(),
                "entities": entities
            })
            if len(context["intents_history"]) > 5:
                context["intents_history"].pop(0)
            
            # Store previous intent for reference
            context["previous_intent"] = intent
            
            # Accumulate entities across turns
            context["collected_entities"].update(entities)
            
            # Store additional data (e.g., campaign_in_focus)
            if additional_data:
                context.update(additional_data)
            
            logger.info(f"Context updated for {user_id}: turn {context['turn_count']}, intent={intent}")
    
    @classmethod
    def clear_context(cls, user_id: str):
        """Clear conversation context for a user"""
        with cls._lock:
            if user_id in cls._conversations:
                del cls._conversations[user_id]
                logger.info(f"Context cleared for {user_id}")
    
    @classmethod
    def get_collected_entities(cls, user_id: str) -> Dict[str, Any]:
        """Get all entities collected across the conversation"""
        context = cls.get_context(user_id)
        if context:
            return context.get("collected_entities", {})
        return {}
    
    @classmethod
    def set_campaign_focus(cls, user_id: str, campaign_id: int, campaign_name: str):
        """Set the campaign user is currently viewing/discussing"""
        with cls._lock:
            if user_id in cls._conversations:
                cls._conversations[user_id]["campaign_in_focus"] = {
                    "id": campaign_id,
                    "name": campaign_name
                }
                logger.info(f"Campaign focus set for {user_id}: {campaign_name}")
    
    @classmethod
    def get_campaign_focus(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the campaign user is currently focused on"""
        context = cls.get_context(user_id)
        if context:
            return context.get("campaign_in_focus")
        return None
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get conversation statistics"""
        with cls._lock:
            active_conversations = len(cls._conversations)
            total_turns = sum(c.get("turn_count", 0) for c in cls._conversations.values())
            
            return {
                "active_conversations": active_conversations,
                "total_turns": total_turns,
                "average_turns": total_turns / active_conversations if active_conversations > 0 else 0
            }
    
    @classmethod
    def cleanup_expired(cls):
        """Cleanup expired conversations"""
        with cls._lock:
            now = datetime.now()
            expired = [
                user_id for user_id, context in cls._conversations.items()
                if context.get("last_activity") and now - context["last_activity"] > cls.TIMEOUT
            ]
            
            for user_id in expired:
                del cls._conversations[user_id]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired conversations")


# Example usage
if __name__ == "__main__":
    # Simulate a multi-turn conversation
    user_id = "test_user_123"
    
    print("🗨️  Conversation Context Manager Test\n")
    
    # Turn 1: User searches for campaigns
    print("Turn 1: 'Show me water projects in Tanzania'")
    ConversationContext.update_context(
        user_id,
        intent="search_campaigns",
        entities={"category": "Water & Sanitation", "location": "Tanzania"}
    )
    
    context = ConversationContext.get_context(user_id)
    print(f"  Context: {context['turn_count']} turns, entities: {context['collected_entities']}\n")
    
    # Turn 2: User selects a campaign
    print("Turn 2: 'Tell me about the Mwanza project'")
    ConversationContext.update_context(
        user_id,
        intent="view_campaign_details",
        entities={"campaign_name": "Mwanza Water Project"}
    )
    ConversationContext.set_campaign_focus(user_id, 42, "Mwanza Water Project")
    
    context = ConversationContext.get_context(user_id)
    print(f"  Context: {context['turn_count']} turns")
    print(f"  Focus: {context.get('campaign_in_focus')['name']}")
    print(f"  Collected: {context['collected_entities']}\n")
    
    # Turn 3: User donates (can reference campaign in focus)
    print("Turn 3: 'Donate fifty dollars'")
    ConversationContext.update_context(
        user_id,
        intent="make_donation",
        entities={"amount": 50, "currency": "USD"}
    )
    
    collected = ConversationContext.get_collected_entities(user_id)
    print(f"  All collected entities: {collected}")
    print(f"    ✅ Has campaign: {'campaign_name' in collected}")
    print(f"    ✅ Has amount: {'amount' in collected}")
    print(f"    ✅ Has location: {'location' in collected}\n")
    
    # Stats
    stats = ConversationContext.get_stats()
    print(f"📊 Stats: {stats['active_conversations']} active, {stats['total_turns']} total turns")
    
    # Cleanup
    ConversationContext.clear_context(user_id)
    print(f"\n✅ Context cleared")
