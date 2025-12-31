"""
Context Switching Module

Handles conversation interruptions and context management:
- Pause/resume conversations
- Context stack for nested conversations
- Intent detection for interrupts
- Graceful context switching
"""

from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

from voice.session_manager import SessionManager, ConversationState, DonationStep


class ContextAction(Enum):
    """Types of context switches"""
    PAUSE = "pause"          # Pause current, handle interrupt
    RESUME = "resume"        # Return to previous context
    CANCEL = "cancel"        # Abandon current conversation
    NESTED = "nested"        # Start related sub-conversation


class ConversationContext:
    """Manage conversation context stack"""
    
    @staticmethod
    def pause_current_conversation(user_id: str, reason: str = "user_interrupt") -> bool:
        """
        Pause current conversation and save state
        
        Stores current conversation on stack for later resume
        
        Args:
            user_id: User identifier
            reason: Reason for pausing (for analytics)
            
        Returns:
            True if successfully paused, False if no active conversation
        """
        session = SessionManager.get_session(user_id)
        if not session or session["state"] == ConversationState.IDLE.value:
            return False
        
        # Get existing context stack
        data = session.get("data", {})
        stack = data.get("context_stack", [])
        
        # Push current context onto stack
        current_context = {
            "state": session["state"],
            "step": session.get("current_step"),
            "data": {k: v for k, v in data.items() if k != "context_stack"},
            "paused_reason": reason,
            "paused_at": datetime.utcnow().isoformat()
        }
        
        stack.append(current_context)
        
        # Update session to IDLE state while keeping stack
        SessionManager.update_session(
            user_id,
            state=ConversationState.IDLE,
            current_step=None,
            data_update={
                "context_stack": stack,
                "previous_state": session["state"]
            },
            message=f"Paused conversation: {reason}"
        )
        
        return True
    
    @staticmethod
    def resume_conversation(user_id: str) -> Optional[Dict]:
        """
        Resume most recent paused conversation
        
        Returns:
            Restored context dict or None if no paused conversations
            {
                "state": ConversationState,
                "step": str,
                "data": dict,
                "paused_reason": str,
                "paused_at": str (ISO datetime)
            }
        """
        session = SessionManager.get_session(user_id)
        if not session:
            return None
        
        data = session.get("data", {})
        stack = data.get("context_stack", [])
        
        if not stack:
            return None
        
        # Pop most recent context
        restored_context = stack.pop()
        
        # Extract data and remove context_stack from it
        restored_data = restored_context["data"].copy()
        restored_data["context_stack"] = stack  # Keep remaining stack
        
        # Restore state
        SessionManager.update_session(
            user_id,
            state=ConversationState(restored_context["state"]),
            current_step=restored_context["step"],
            data_update=restored_data,
            message="Resumed conversation"
        )
        
        return restored_context
    
    @staticmethod
    def has_paused_conversation(user_id: str) -> bool:
        """Check if user has any paused conversations"""
        session = SessionManager.get_session(user_id)
        if not session:
            return False
        
        data = session.get("data", {})
        stack = data.get("context_stack", [])
        return len(stack) > 0
    
    @staticmethod
    def get_context_stack_depth(user_id: str) -> int:
        """Get number of paused conversations"""
        session = SessionManager.get_session(user_id)
        if not session:
            return 0
        
        data = session.get("data", {})
        stack = data.get("context_stack", [])
        return len(stack)
    
    @staticmethod
    def clear_all_contexts(user_id: str) -> int:
        """
        Clear all paused conversations
        
        Returns:
            Number of contexts cleared
        """
        session = SessionManager.get_session(user_id)
        if not session:
            return 0
        
        data = session.get("data", {})
        stack = data.get("context_stack", [])
        count = len(stack)
        
        if count > 0:
            SessionManager.update_session(
                user_id,
                data_update={"context_stack": []},
                message="Cleared all paused conversations"
            )
        
        return count


class InterruptDetector:
    """Detect when user wants to switch context"""
    
    # Question patterns that indicate information requests
    QUESTION_PATTERNS = [
        "what", "how", "which", "when", "where", "why",
        "show me", "tell me", "can i", "is there",
        "do you have", "are there", "how many",
        "can you", "could you", "would you"
    ]
    
    # Navigation patterns that indicate context changes
    NAVIGATION_PATTERNS = [
        "go back", "cancel", "stop", "never mind",
        "start over", "restart", "forget it",
        "exit", "quit", "end"
    ]
    
    # Resume patterns
    RESUME_PATTERNS = [
        "continue", "resume", "go on", "keep going",
        "back to", "return", "where was i"
    ]
    
    @staticmethod
    def is_interrupt(message: str, current_state: ConversationState) -> bool:
        """
        Determine if message is an interruption
        
        Returns True if user is asking a question or changing topic
        while in active conversation
        
        Args:
            message: User's message
            current_state: Current conversation state
            
        Returns:
            True if this is an interrupt, False otherwise
        """
        if current_state == ConversationState.IDLE:
            return False
        
        message_lower = message.lower().strip()
        
        # Check for question patterns
        if any(pattern in message_lower for pattern in InterruptDetector.QUESTION_PATTERNS):
            return True
        
        # Check for navigation
        if any(pattern in message_lower for pattern in InterruptDetector.NAVIGATION_PATTERNS):
            return True
        
        return False
    
    @staticmethod
    def is_resume_request(message: str) -> bool:
        """Check if user wants to resume paused conversation"""
        message_lower = message.lower().strip()
        return any(pattern in message_lower for pattern in InterruptDetector.RESUME_PATTERNS)
    
    @staticmethod
    def classify_interrupt(message: str) -> str:
        """
        Classify type of interruption
        
        Returns: "question", "navigation", or "clarification"
        """
        message_lower = message.lower().strip()
        
        # Navigation takes priority (cancel, stop, etc.)
        if any(pattern in message_lower for pattern in InterruptDetector.NAVIGATION_PATTERNS):
            return "navigation"
        
        # Then check for questions
        if any(pattern in message_lower for pattern in InterruptDetector.QUESTION_PATTERNS):
            return "question"
        
        # Default to clarification
        return "clarification"
    
    @staticmethod
    def get_interrupt_intent(message: str) -> Dict[str, any]:
        """
        Get detailed interrupt intent analysis
        
        Returns:
            {
                "is_interrupt": bool,
                "type": str ("question", "navigation", "clarification"),
                "is_resume": bool,
                "confidence": float
            }
        """
        message_lower = message.lower().strip()
        
        # Check if it's a resume request
        is_resume = InterruptDetector.is_resume_request(message)
        
        # Classify interrupt type
        interrupt_type = InterruptDetector.classify_interrupt(message)
        
        # Calculate confidence based on keyword matches
        confidence = 0.5  # Default
        
        if interrupt_type == "navigation":
            nav_matches = sum(1 for p in InterruptDetector.NAVIGATION_PATTERNS if p in message_lower)
            confidence = min(0.5 + (nav_matches * 0.2), 1.0)
        elif interrupt_type == "question":
            q_matches = sum(1 for p in InterruptDetector.QUESTION_PATTERNS if p in message_lower)
            confidence = min(0.5 + (q_matches * 0.15), 1.0)
        
        return {
            "is_interrupt": True,  # This method is called after is_interrupt()
            "type": interrupt_type,
            "is_resume": is_resume,
            "confidence": confidence
        }


# Helper function for generating step prompts after resume

def generate_resume_prompt(restored_context: Dict) -> str:
    """
    Generate appropriate prompt based on restored conversation state
    
    Args:
        restored_context: Context returned from resume_conversation()
        
    Returns:
        Prompt string to show user
    """
    step = restored_context.get("step")
    data = restored_context.get("data", {})
    
    if step == DonationStep.SELECT_CAMPAIGN.value:
        return "Welcome back! Which campaign would you like to support? 🎯"
    
    elif step == DonationStep.ENTER_AMOUNT.value:
        campaign_title = data.get("campaign_title", "this campaign")
        return f"Continuing your donation to {campaign_title}. How much would you like to donate? 💰"
    
    elif step == DonationStep.SELECT_PAYMENT.value:
        campaign_title = data.get("campaign_title", "")
        amount = data.get("amount", 0)
        return (
            f"Resuming donation:\n"
            f"• Campaign: {campaign_title}\n"
            f"• Amount: {amount} birr\n\n"
            f"How would you like to pay? (Chapa, Telebirr, M-Pesa) 💳"
        )
    
    elif step == DonationStep.CONFIRM.value:
        campaign_title = data.get("campaign_title", "")
        amount = data.get("amount", 0)
        provider = data.get("payment_provider", "")
        return (
            f"Let's complete your donation:\n"
            f"• Campaign: {campaign_title}\n"
            f"• Amount: {amount} birr\n"
            f"• Payment: {provider.title()}\n\n"
            f"Type 'confirm' to proceed. ✓"
        )
    
    else:
        return "Welcome back! Let's continue where we left off."
