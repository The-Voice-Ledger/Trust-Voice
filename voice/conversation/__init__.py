"""
Conversation Management Module

Handles advanced conversational features:
- Clarification and error recovery
- Context switching
- User preferences
- Conversation analytics
"""

from .clarification import ClarificationHandler, ConversationRepair
from .context_switcher import (
    ConversationContext,
    InterruptDetector,
    generate_resume_prompt
)
from .preferences import PreferenceManager, PreferenceLearner

__all__ = [
    'ClarificationHandler',
    'ConversationRepair',
    'ConversationContext',
    'InterruptDetector',
    'generate_resume_prompt',
    'PreferenceManager',
    'PreferenceLearner'
]
