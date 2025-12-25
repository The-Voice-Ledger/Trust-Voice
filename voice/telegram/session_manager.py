"""
Registration Session Manager
Redis-backed session storage for multi-step registration flows
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

from redis import Redis

logger = logging.getLogger(__name__)

# Redis connection (reuse from voice pipeline)
try:
    from voice.pipeline import redis_client
except ImportError:
    # Fallback for testing
    redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Session TTL
SESSION_TTL = timedelta(hours=1)


class RegistrationSession:
    """Manages registration session state in Redis"""
    
    def __init__(self, telegram_user_id: str):
        self.telegram_user_id = telegram_user_id
        self.key = f"registration:{telegram_user_id}"
    
    def set(self, data: Dict[str, Any]):
        """Store session data"""
        try:
            redis_client.setex(
                self.key,
                SESSION_TTL,
                json.dumps(data)
            )
            logger.info(f"Session saved for user {self.telegram_user_id}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def get(self) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        try:
            data = redis_client.get(self.key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def update(self, updates: Dict[str, Any]):
        """Update specific fields in session"""
        data = self.get() or {}
        data.update(updates)
        self.set(data)
    
    def delete(self):
        """Delete session"""
        try:
            redis_client.delete(self.key)
            logger.info(f"Session deleted for user {self.telegram_user_id}")
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
    
    def exists(self) -> bool:
        """Check if session exists"""
        try:
            return redis_client.exists(self.key) > 0
        except Exception as e:
            logger.error(f"Failed to check session: {e}")
            return False
