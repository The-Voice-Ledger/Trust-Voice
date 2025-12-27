"""
Command Router - Intent to Handler Mapping

Routes NLU intents to appropriate handler functions.
Validates required entities and manages conversation flow.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# INTENT HANDLER REGISTRY
# ============================================================================

# Maps intent strings to handler functions
# Handlers will be imported and registered in Step 1.4
INTENT_HANDLERS: Dict[str, Callable] = {}


def register_handler(intent: str):
    """
    Decorator to register intent handlers.
    
    Usage:
        @register_handler("search_campaigns")
        async def handle_search_campaigns(entities, user_id, db):
            ...
    """
    def decorator(func: Callable):
        INTENT_HANDLERS[intent] = func
        logger.info(f"Registered handler for intent: {intent}")
        return func
    return decorator


# ============================================================================
# REQUIRED ENTITIES CONFIGURATION
# ============================================================================

# Define which entities are required for each intent
# If missing, router will request clarification
REQUIRED_ENTITIES: Dict[str, List[str]] = {
    # Donor intents
    "search_campaigns": [],  # All filters are optional
    "view_campaign_details": ["campaign_id"],  # Need to know which campaign
    "make_donation": ["amount", "campaign_id"],  # Must have both
    "view_donation_history": [],  # No required entities (fixed name)
    "get_campaign_updates": ["campaign_id"],  # Which campaign's updates? (fixed name)
    "get_impact_report": ["campaign_id"],  # Which campaign's impact? (fixed name)
    
    # NGO intents
    "create_campaign": ["title", "goal_amount", "category"],  # Core campaign data
    "withdraw_funds": ["amount"],  # How much to withdraw
    "field_report": ["campaign_id", "description"],  # Report details
    "view_my_campaigns": [],  # NGO dashboard (fixed name)
    
    # General intents
    "register_user": [],  # Handled separately in registration flow
    "get_help": [],  # Fixed name
    "greeting": [],
    "change_language": ["language"],  # Which language?
    "system_info": [],  # System information
    "unknown": []
}


# ============================================================================
# ENTITY VALIDATION
# ============================================================================

def validate_entities(intent: str, entities: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Check if all required entities are present for the intent.
    
    Args:
        intent: Intent string (e.g., "make_donation")
        entities: Extracted entities dict
        
    Returns:
        (is_valid, missing_entities)
        
    Example:
        >>> validate_entities("make_donation", {"amount": 50})
        (False, ["campaign_id"])
        
        >>> validate_entities("make_donation", {"amount": 50, "campaign_id": 123})
        (True, [])
    """
    required = REQUIRED_ENTITIES.get(intent, [])
    
    # Check each required entity exists and has a value
    missing = []
    for entity_name in required:
        if entity_name not in entities or entities[entity_name] is None:
            missing.append(entity_name)
    
    is_valid = len(missing) == 0
    return is_valid, missing


def generate_clarification_question(intent: str, missing_entities: List[str]) -> str:
    """
    Generate natural language question to collect missing entity.
    
    Args:
        intent: The current intent
        missing_entities: List of missing entity names
        
    Returns:
        Clarifying question string
        
    Example:
        >>> generate_clarification_question("make_donation", ["campaign_id"])
        "Which campaign would you like to donate to? You can say the campaign name or number."
    """
    # Clarification questions for common entities
    ENTITY_QUESTIONS = {
        "campaign_id": "Which campaign would you like to donate to? You can say the campaign name or number.",
        "amount": "How much would you like to donate?",
        "category": "What category is this campaign? For example: education, health, water, or environment.",
        "title": "What is the campaign title?",
        "goal_amount": "What is your fundraising goal amount?",
        "description": "Please provide a brief description.",
        "language": "Which language would you prefer? English or Amharic?",
        "location": "Which location or region?"
    }
    
    # Get first missing entity
    entity = missing_entities[0] if missing_entities else None
    
    if entity in ENTITY_QUESTIONS:
        return ENTITY_QUESTIONS[entity]
    else:
        # Generic fallback
        return f"I need more information. Please provide the {entity.replace('_', ' ')}."


# ============================================================================
# MAIN ROUTING FUNCTION
# ============================================================================

async def route_command(
    intent: str,
    entities: Dict[str, Any],
    user_id: str,
    db: Session,
    conversation_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Route intent to appropriate handler function.
    
    This is the main entry point called by the Telegram bot after NLU.
    
    Args:
        intent: Intent string from NLU (e.g., "make_donation")
        entities: Extracted entities dict
        user_id: User's database UUID string OR telegram_user_id for guests
        db: Database session
        conversation_context: Optional context from previous turns
        
    Returns:
        {
            "success": bool,
            "message": str,  # Response message for user
            "needs_clarification": bool,
            "missing_entities": List[str],
            "data": dict  # Additional data (campaign IDs, etc.)
        }
        
    Example:
        >>> result = await route_command(
        ...     intent="search_campaigns",
        ...     entities={"category": "education"},
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     db=db_session
        ... )
        >>> print(result["message"])
        "Found 5 education campaigns..."
    """
    try:
        logger.info(f"Routing command - Intent: {intent}, User: {user_id}")
        logger.debug(f"Entities: {entities}")
        
        # Step 1: Validate required entities
        is_valid, missing = validate_entities(intent, entities)
        
        if not is_valid:
            logger.warning(f"Missing entities for {intent}: {missing}")
            question = generate_clarification_question(intent, missing)
            
            return {
                "success": False,
                "message": question,
                "needs_clarification": True,
                "missing_entities": missing,
                "data": {}
            }
        
        # Step 2: Get handler for intent
        handler = INTENT_HANDLERS.get(intent)
        
        if not handler:
            logger.error(f"No handler registered for intent: {intent}")
            # Fall back to unknown handler
            handler = INTENT_HANDLERS.get("unknown")
            if not handler:
                return {
                    "success": False,
                    "message": "I'm not sure how to help with that. Try saying 'help' to see what I can do.",
                    "needs_clarification": False,
                    "missing_entities": [],
                    "data": {}
                }
        
        # Step 3: Execute handler
        logger.info(f"Executing handler for {intent}")
        result = await handler(
            entities=entities,
            user_id=user_id,
            db=db,
            context=conversation_context or {}
        )
        
        logger.info(f"Handler execution complete - Success: {result.get('success', False)}")
        return result
        
    except Exception as e:
        logger.error(f"Error routing command: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Sorry, I encountered an error processing your request. Please try again.",
            "needs_clarification": False,
            "missing_entities": [],
            "data": {},
            "error": str(e)
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_response_for_voice(text: str, max_length: int = 500) -> str:
    """
    Format response text for natural voice playback.
    
    Rules:
    - Keep sentences short
    - Use full words, not symbols
    - Spell out small numbers
    - Use ordinals for lists
    
    Args:
        text: Original response text
        max_length: Maximum character length for voice
        
    Returns:
        Voice-optimized text
    """
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length - 20] + "... Would you like to hear more?"
    
    # Replace symbols with words
    replacements = {
        "$": " dollars ",
        "€": " euros ",
        "£": " pounds ",
        "KES": " Kenyan shillings ",
        "%": " percent ",
        "&": " and ",
        "#": " number ",
        "@": " at "
    }
    
    for symbol, word in replacements.items():
        text = text.replace(symbol, word)
    
    return text


def extract_campaign_reference(text: str, last_results: List[int]) -> Optional[int]:
    """
    Extract campaign reference from user input when they say "first one", "number 2", etc.
    
    Args:
        text: User's message text
        last_results: List of campaign IDs from previous search
        
    Returns:
        Campaign ID or None
        
    Example:
        >>> extract_campaign_reference("the first one", [101, 102, 103])
        101
        
        >>> extract_campaign_reference("number 2", [101, 102, 103])
        102
    """
    text_lower = text.lower()
    
    # Ordinal words
    ordinals = {
        "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
        "1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "5th": 4
    }
    
    for word, index in ordinals.items():
        if word in text_lower and index < len(last_results):
            return last_results[index]
    
    # Number patterns
    import re
    
    # "number 2", "campaign 3"
    match = re.search(r'(?:number|campaign)\s*(\d+)', text_lower)
    if match:
        num = int(match.group(1)) - 1  # Convert to 0-based index
        if 0 <= num < len(last_results):
            return last_results[num]
    
    return None


# ============================================================================
# COMMAND EXECUTION STATS (for monitoring)
# ============================================================================

_command_stats = {
    "total_commands": 0,
    "successful_commands": 0,
    "failed_commands": 0,
    "commands_by_intent": {}
}


def record_command_execution(intent: str, success: bool):
    """Track command execution for monitoring."""
    _command_stats["total_commands"] += 1
    
    if success:
        _command_stats["successful_commands"] += 1
    else:
        _command_stats["failed_commands"] += 1
    
    if intent not in _command_stats["commands_by_intent"]:
        _command_stats["commands_by_intent"][intent] = {"success": 0, "failed": 0}
    
    if success:
        _command_stats["commands_by_intent"][intent]["success"] += 1
    else:
        _command_stats["commands_by_intent"][intent]["failed"] += 1


def get_command_stats() -> Dict[str, Any]:
    """Get command execution statistics."""
    return _command_stats.copy()


def reset_command_stats():
    """Reset statistics (for testing)."""
    global _command_stats
    _command_stats = {
        "total_commands": 0,
        "successful_commands": 0,
        "failed_commands": 0,
        "commands_by_intent": {}
    }
