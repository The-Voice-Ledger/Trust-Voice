"""
Context Management Module

Provides conversation context tracking for multi-turn voice interactions.
"""

from voice.context.conversation_manager import (
    get_context,
    update_context,
    clear_context,
    store_search_results,
    set_current_campaign,
    start_workflow,
    update_workflow_data,
    complete_workflow,
    get_workflow_state,
    get_workflow_data,
    clear_expired_contexts,
    get_context_stats
)

__all__ = [
    "get_context",
    "update_context",
    "clear_context",
    "store_search_results",
    "set_current_campaign",
    "start_workflow",
    "update_workflow_data",
    "complete_workflow",
    "get_workflow_state",
    "get_workflow_data",
    "clear_expired_contexts",
    "get_context_stats"
]
