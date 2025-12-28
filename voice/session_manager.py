"""
Session Management for Multi-Turn Conversations

Handles conversation state, user context, and session lifecycle using Redis.
"""

import os
import json
import redis
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', None),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True  # Return strings instead of bytes
)

# Session TTL (time to live) - 30 minutes
SESSION_TTL = int(os.getenv('REDIS_SESSION_TTL', 1800))


class ConversationState(Enum):
    """Possible conversation states"""
    IDLE = "idle"                          # No active conversation
    DONATING = "donating"                  # In donation flow
    SEARCHING_CAMPAIGNS = "searching"      # Refining campaign search
    CREATING_CAMPAIGN = "creating"         # Creating new campaign
    REGISTERING_NGO = "registering_ngo"    # NGO registration
    ASKING_ANALYTICS = "analytics"         # Analytics queries


class DonationStep(Enum):
    """Steps in donation conversation"""
    SELECT_CAMPAIGN = "select_campaign"
    ENTER_AMOUNT = "enter_amount"
    SELECT_PAYMENT = "select_payment"
    CONFIRM = "confirm"


class SessionManager:
    """Manage conversation sessions in Redis"""
    
    @staticmethod
    def _get_key(user_id: str) -> str:
        """Generate Redis key for user session"""
        return f"session:{user_id}"
    
    @staticmethod
    def create_session(user_id: str, state: ConversationState) -> Dict[str, Any]:
        """
        Create new conversation session
        
        Args:
            user_id: Telegram user ID
            state: Initial conversation state
            
        Returns:
            Session data dictionary
        """
        session = {
            "user_id": user_id,
            "state": state.value,
            "current_step": None,
            "data": {},
            "history": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        key = SessionManager._get_key(user_id)
        redis_client.setex(
            key,
            SESSION_TTL,
            json.dumps(session)
        )
        
        return session
    
    @staticmethod
    def get_session(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve existing session
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Session data or None if expired/not found
        """
        key = SessionManager._get_key(user_id)
        data = redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    @staticmethod
    def update_session(
        user_id: str,
        state: Optional[ConversationState] = None,
        current_step: Optional[str] = None,
        data_update: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update existing session
        
        Args:
            user_id: Telegram user ID
            state: New conversation state (optional)
            current_step: New step in workflow (optional)
            data_update: Dictionary to merge into session data
            message: Add message to history
            
        Returns:
            Updated session data
        """
        session = SessionManager.get_session(user_id)
        
        if not session:
            # Create new session if none exists
            session = SessionManager.create_session(
                user_id, 
                state or ConversationState.IDLE
            )
        
        # Update fields
        if state:
            session["state"] = state.value
        if current_step:
            session["current_step"] = current_step
        if data_update:
            session["data"].update(data_update)
        if message:
            session["history"].append({
                "timestamp": datetime.now().isoformat(),
                "message": message
            })
        
        session["updated_at"] = datetime.now().isoformat()
        
        # Save back to Redis
        key = SessionManager._get_key(user_id)
        redis_client.setex(
            key,
            SESSION_TTL,
            json.dumps(session)
        )
        
        return session
    
    @staticmethod
    def end_session(user_id: str) -> bool:
        """
        End conversation session
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if session existed and was deleted
        """
        key = SessionManager._get_key(user_id)
        return redis_client.delete(key) > 0
    
    @staticmethod
    def extend_session(user_id: str) -> bool:
        """
        Extend session TTL (reset timeout)
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if session was extended
        """
        key = SessionManager._get_key(user_id)
        return redis_client.expire(key, SESSION_TTL)
    
    @staticmethod
    def get_all_active_sessions() -> List[Dict[str, Any]]:
        """
        Get all active sessions (admin/debugging)
        
        Returns:
            List of all session dictionaries
        """
        sessions = []
        for key in redis_client.scan_iter("session:*"):
            data = redis_client.get(key)
            if data:
                sessions.append(json.loads(data))
        return sessions


# Helper functions for specific workflows

def start_donation_flow(user_id: str) -> Dict[str, Any]:
    """Start donation conversation"""
    return SessionManager.create_session(
        user_id,
        ConversationState.DONATING
    )


def is_in_conversation(user_id: str) -> bool:
    """Check if user has active session"""
    session = SessionManager.get_session(user_id)
    return session is not None and session["state"] != ConversationState.IDLE.value


def get_conversation_state(user_id: str) -> Optional[ConversationState]:
    """Get current conversation state"""
    session = SessionManager.get_session(user_id)
    if session:
        try:
            return ConversationState(session["state"])
        except ValueError:
            return None
    return None
