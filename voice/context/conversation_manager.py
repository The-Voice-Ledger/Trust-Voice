"""
Conversation Context Manager - Lab 6 Part 4

Maintains multi-turn conversation state for voice commands.
Tracks:
- Last search results (for "donate to number 1")
- Current campaign being discussed
- Multi-step workflows (campaign creation, donations)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# In-memory context storage (user_id -> context dict)
# In production, this would use Redis or database
_context_store: Dict[str, Dict[str, Any]] = {}

# Context expiration time (30 minutes)
CONTEXT_TTL = timedelta(minutes=30)


def get_context(user_id: str) -> Dict[str, Any]:
    """
    Get conversation context for a user.
    
    Args:
        user_id: User's UUID string
        
    Returns:
        Context dictionary with conversation state
        
    Example:
        >>> ctx = get_context("123e4567...")
        >>> last_results = ctx.get("last_search_campaigns", [])
    """
    try:
        if user_id not in _context_store:
            # Initialize new context
            _context_store[user_id] = {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_search_campaigns": [],
                "current_campaign": None,
                "workflow_state": None,
                "workflow_data": {}
            }
            logger.info(f"Initialized new context for user {user_id}")
        else:
            # Check if context expired
            context = _context_store[user_id]
            updated_at = context.get("updated_at", datetime.utcnow())
            
            if datetime.utcnow() - updated_at > CONTEXT_TTL:
                logger.info(f"Context expired for user {user_id}, resetting")
                _context_store[user_id] = {
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "last_search_campaigns": [],
                    "current_campaign": None,
                    "workflow_state": None,
                    "workflow_data": {}
                }
        
        return _context_store[user_id]
        
    except Exception as e:
        logger.error(f"Error getting context for user {user_id}: {str(e)}")
        # Return empty context on error
        return {
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_search_campaigns": [],
            "current_campaign": None,
            "workflow_state": None,
            "workflow_data": {}
        }


def update_context(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update conversation context for a user.
    
    Args:
        user_id: User's UUID string
        updates: Dictionary of fields to update
        
    Returns:
        Updated context dictionary
        
    Example:
        >>> update_context("123e4567...", {
        ...     "last_search_campaigns": ["abc123", "def456"],
        ...     "current_campaign": "abc123"
        ... })
    """
    try:
        # Get current context
        context = get_context(user_id)
        
        # Apply updates
        for key, value in updates.items():
            context[key] = value
        
        # Update timestamp
        context["updated_at"] = datetime.utcnow()
        
        _context_store[user_id] = context
        
        logger.debug(f"Updated context for user {user_id}: {list(updates.keys())}")
        
        return context
        
    except Exception as e:
        logger.error(f"Error updating context for user {user_id}: {str(e)}")
        return get_context(user_id)


def clear_context(user_id: str):
    """
    Clear conversation context for a user.
    
    Args:
        user_id: User's UUID string
        
    Example:
        >>> clear_context("123e4567...")
    """
    try:
        if user_id in _context_store:
            del _context_store[user_id]
            logger.info(f"Cleared context for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error clearing context for user {user_id}: {str(e)}")


def store_search_results(user_id: str, campaign_ids: List[str]):
    """
    Store campaign IDs from recent search for reference.
    
    Allows users to say "donate to number 1" to reference first result.
    
    Args:
        user_id: User's UUID string
        campaign_ids: List of campaign UUID strings
        
    Example:
        >>> store_search_results("123e4567...", ["abc123", "def456", "ghi789"])
        >>> # User can now say "number 1" to refer to "abc123"
    """
    update_context(user_id, {
        "last_search_campaigns": campaign_ids,
        "search_timestamp": datetime.utcnow()
    })


def set_current_campaign(user_id: str, campaign_id: str):
    """
    Set the campaign currently being discussed.
    
    Allows follow-up commands without repeating campaign ID.
    
    Args:
        user_id: User's UUID string
        campaign_id: Campaign UUID string
        
    Example:
        >>> set_current_campaign("123e4567...", "abc123")
        >>> # User can now say "donate 50 dollars" without specifying campaign
    """
    update_context(user_id, {
        "current_campaign": campaign_id
    })


def start_workflow(user_id: str, workflow_name: str, initial_data: Dict[str, Any] = None):
    """
    Start a multi-step workflow.
    
    Used for complex operations like campaign creation or donations
    that require multiple conversational turns.
    
    Args:
        user_id: User's UUID string
        workflow_name: Name of workflow ("create_campaign", "make_donation", etc.)
        initial_data: Optional initial workflow data
        
    Example:
        >>> start_workflow("123e4567...", "create_campaign", {
        ...     "title": "School Supplies Drive"
        ... })
    """
    update_context(user_id, {
        "workflow_state": workflow_name,
        "workflow_data": initial_data or {},
        "workflow_started_at": datetime.utcnow()
    })
    
    logger.info(f"Started workflow '{workflow_name}' for user {user_id}")


def update_workflow_data(user_id: str, updates: Dict[str, Any]):
    """
    Update data for active workflow.
    
    Args:
        user_id: User's UUID string
        updates: Fields to update in workflow_data
        
    Example:
        >>> update_workflow_data("123e4567...", {
        ...     "goal_amount": 5000,
        ...     "category": "education"
        ... })
    """
    context = get_context(user_id)
    workflow_data = context.get("workflow_data", {})
    workflow_data.update(updates)
    
    update_context(user_id, {
        "workflow_data": workflow_data
    })


def complete_workflow(user_id: str):
    """
    Mark workflow as complete and clear workflow state.
    
    Args:
        user_id: User's UUID string
        
    Example:
        >>> complete_workflow("123e4567...")
    """
    context = get_context(user_id)
    workflow_name = context.get("workflow_state")
    
    if workflow_name:
        logger.info(f"Completed workflow '{workflow_name}' for user {user_id}")
    
    update_context(user_id, {
        "workflow_state": None,
        "workflow_data": {},
        "workflow_completed_at": datetime.utcnow()
    })


def get_workflow_state(user_id: str) -> Optional[str]:
    """
    Get current workflow name if one is active.
    
    Args:
        user_id: User's UUID string
        
    Returns:
        Workflow name or None
        
    Example:
        >>> get_workflow_state("123e4567...")
        "create_campaign"
    """
    context = get_context(user_id)
    return context.get("workflow_state")


def get_workflow_data(user_id: str) -> Dict[str, Any]:
    """
    Get data for active workflow.
    
    Args:
        user_id: User's UUID string
        
    Returns:
        Workflow data dictionary
        
    Example:
        >>> data = get_workflow_data("123e4567...")
        >>> print(data["title"])
        "School Supplies Drive"
    """
    context = get_context(user_id)
    return context.get("workflow_data", {})


def clear_expired_contexts():
    """
    Remove expired contexts from memory.
    
    Should be called periodically (e.g., by background task).
    """
    try:
        now = datetime.utcnow()
        expired_users = []
        
        for user_id, context in _context_store.items():
            updated_at = context.get("updated_at", now)
            if now - updated_at > CONTEXT_TTL:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del _context_store[user_id]
            logger.debug(f"Removed expired context for user {user_id}")
        
        if expired_users:
            logger.info(f"Cleared {len(expired_users)} expired contexts")
            
    except Exception as e:
        logger.error(f"Error clearing expired contexts: {str(e)}")


def get_context_stats() -> Dict[str, Any]:
    """
    Get statistics about context store (for monitoring).
    
    Returns:
        Stats dictionary with counts and memory usage
    """
    return {
        "active_contexts": len(_context_store),
        "total_memory_kb": sum(
            len(str(ctx)) for ctx in _context_store.values()
        ) / 1024
    }
