"""
Voice Campaign Creation Flow
Multi-turn conversation to collect campaign information via voice
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

from voice.nlu.context import ConversationContext

logger = logging.getLogger(__name__)


class CampaignField(str, Enum):
    """Campaign fields to collect via voice interview"""
    TITLE = "title"
    CATEGORY = "category"
    PROBLEM = "problem"
    SOLUTION = "solution"
    GOAL_AMOUNT = "goal_amount"
    CURRENCY = "currency"
    BENEFICIARIES = "beneficiaries"
    LOCATION = "location"
    TIMELINE = "timeline"
    BUDGET_BREAKDOWN = "budget_breakdown"


# Available campaign categories
CAMPAIGN_CATEGORIES = [
    "Water & Sanitation",
    "Education",
    "Healthcare",
    "Agriculture",
    "Environment",
    "Infrastructure",
    "Emergency Relief",
    "Community Development"
]


class CampaignInterviewAgent:
    """
    Conducts multi-turn voice interview to collect campaign information.
    
    Flow:
    1. User says "I want to create a campaign"
    2. Bot asks questions one by one
    3. User responds via voice
    4. Extracted entities are accumulated
    5. When complete, campaign is created
    
    Example:
        agent = CampaignInterviewAgent(user_id="telegram_12345")
        
        # First turn
        question = agent.get_next_question()
        # "What is the name of your project?"
        
        # User responds: "Clean Water for Mwanza"
        agent.process_response("Clean Water for Mwanza", {"title": "Clean Water for Mwanza"})
        
        # Next turn
        question = agent.get_next_question()
        # "What category does this project fall under?"
    """
    
    # Interview questions in order
    INTERVIEW_QUESTIONS = [
        {
            "field": CampaignField.TITLE,
            "question": "🎯 What is the name of your project?\n\nFor example: 'Clean Water for Mwanza' or 'School Books for Children'",
            "validation": lambda x: len(x) >= 10,
            "error": "Please provide a more descriptive title (at least 10 characters)"
        },
        {
            "field": CampaignField.CATEGORY,
            "question": lambda: (
                "📂 What category does your project fall under?\n\n"
                f"Available categories:\n" +
                "\n".join(f"• {cat}" for cat in CAMPAIGN_CATEGORIES) +
                "\n\nJust say the category name."
            ),
            "validation": lambda x: any(cat.lower() in x.lower() for cat in CAMPAIGN_CATEGORIES),
            "error": f"Please choose one of these categories: {', '.join(CAMPAIGN_CATEGORIES)}"
        },
        {
            "field": CampaignField.PROBLEM,
            "question": "❓ What problem are you trying to solve?\n\nBe specific about the challenge facing your community.",
            "validation": lambda x: len(x) >= 20,
            "error": "Please provide more details about the problem (at least 20 characters)"
        },
        {
            "field": CampaignField.SOLUTION,
            "question": "💡 How will your project solve this problem?\n\nDescribe your approach and methodology.",
            "validation": lambda x: len(x) >= 20,
            "error": "Please provide more details about your solution (at least 20 characters)"
        },
        {
            "field": CampaignField.GOAL_AMOUNT,
            "question": "💰 How much funding do you need?\n\nFor example: '$10,000' or '5 million shillings'",
            "validation": lambda x: isinstance(x, (int, float)) and x > 0,
            "error": "Please provide a valid amount greater than zero"
        },
        {
            "field": CampaignField.BENEFICIARIES,
            "question": "👥 Who will benefit from this project?\n\nFor example: '450 families' or '200 school children' or 'Mwanza community'",
            "validation": lambda x: len(x) >= 5,
            "error": "Please describe who will benefit"
        },
        {
            "field": CampaignField.LOCATION,
            "question": "📍 Where is this project located?\n\nFor example: 'Mwanza, Tanzania' or 'Nairobi, Kenya'",
            "validation": lambda x: len(x) >= 3,
            "error": "Please provide a location"
        },
        {
            "field": CampaignField.TIMELINE,
            "question": "⏱️ How long will this project take?\n\nFor example: '6 months' or '1 year' or '3 weeks'",
            "validation": lambda x: len(x) >= 3,
            "error": "Please provide an estimated timeline"
        },
        {
            "field": CampaignField.BUDGET_BREAKDOWN,
            "question": "📊 How will you spend the money? Provide a brief budget breakdown.\n\nFor example: 'Equipment $5000, Labor $3000, Materials $2000'",
            "validation": lambda x: len(x) >= 20,
            "error": "Please provide more details about the budget (at least 20 characters)"
        }
    ]
    
    def __init__(self, user_id: str):
        """
        Initialize campaign interview agent
        
        Args:
            user_id: User's telegram_user_id or phone number
        """
        self.user_id = user_id
        self.context_key = f"campaign_creation_{user_id}"
    
    def start_interview(self) -> str:
        """
        Start the campaign creation interview
        
        Returns:
            Welcome message with first question
        """
        # Initialize context
        ConversationContext.update_context(
            self.user_id,
            intent="create_campaign",
            entities={},
            additional_data={
                "campaign_creation_step": 0,
                "campaign_data": {},
                "interview_started_at": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Started campaign creation interview for user {self.user_id}")
        
        # Return welcome message + first question
        welcome = (
            "🎉 <b>Create Your Campaign</b>\n\n"
            "I'll guide you through creating your campaign step by step.\n"
            "You can respond via voice or text.\n\n"
            "Let's get started! 📝\n\n"
        )
        
        first_question = self._get_question_text(0)
        return welcome + first_question
    
    def process_response(
        self,
        user_input: str,
        extracted_entities: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Process user's response to current question
        
        Args:
            user_input: Raw user input (transcript)
            extracted_entities: Entities extracted from input
            
        Returns:
            Tuple of (is_valid, response_message, error_message)
            - is_valid: True if response is valid
            - response_message: Next question or completion message
            - error_message: Validation error if invalid
        """
        context = ConversationContext.get_context(self.user_id)
        if not context:
            return False, "Interview session expired. Please start over with 'create campaign'", "Session expired"
        
        current_step = context.get("campaign_creation_step", 0)
        campaign_data = context.get("campaign_data", {})
        
        if current_step >= len(self.INTERVIEW_QUESTIONS):
            return False, "Interview already complete", None
        
        # Get current question config
        question_config = self.INTERVIEW_QUESTIONS[current_step]
        field = question_config["field"]
        
        # Extract value for this field
        field_value = self._extract_field_value(field, user_input, extracted_entities)
        
        # Validate
        validation_func = question_config["validation"]
        if not validation_func(field_value):
            error_msg = question_config["error"]
            logger.warning(f"Validation failed for {field}: {field_value}")
            return False, f"❌ {error_msg}\n\nPlease try again.", error_msg
        
        # Store value
        campaign_data[field.value] = field_value
        
        # Move to next step
        next_step = current_step + 1
        
        # Update context
        ConversationContext.update_context(
            self.user_id,
            intent="create_campaign",
            entities=extracted_entities,
            additional_data={
                "campaign_creation_step": next_step,
                "campaign_data": campaign_data
            }
        )
        
        logger.info(f"Campaign creation step {next_step}/{len(self.INTERVIEW_QUESTIONS)} for user {self.user_id}")
        
        # Check if interview complete
        if next_step >= len(self.INTERVIEW_QUESTIONS):
            summary = self._generate_summary(campaign_data)
            return True, summary, None
        
        # Get next question
        next_question = self._get_question_text(next_step)
        progress = f"✅ Step {next_step}/{len(self.INTERVIEW_QUESTIONS)} complete\n\n"
        
        return True, progress + next_question, None
    
    def get_current_step(self) -> int:
        """Get current interview step (0-based)"""
        context = ConversationContext.get_context(self.user_id)
        if not context:
            return -1
        return context.get("campaign_creation_step", 0)
    
    def get_collected_data(self) -> Dict[str, Any]:
        """Get all collected campaign data"""
        context = ConversationContext.get_context(self.user_id)
        if not context:
            return {}
        return context.get("campaign_data", {})
    
    def is_complete(self) -> bool:
        """Check if interview is complete"""
        current_step = self.get_current_step()
        return current_step >= len(self.INTERVIEW_QUESTIONS)
    
    def cancel_interview(self):
        """Cancel the interview and clear context"""
        ConversationContext.clear_context(self.user_id)
        logger.info(f"Cancelled campaign creation interview for user {self.user_id}")
    
    def _get_question_text(self, step: int) -> str:
        """Get question text for given step"""
        if step >= len(self.INTERVIEW_QUESTIONS):
            return ""
        
        question_config = self.INTERVIEW_QUESTIONS[step]
        question = question_config["question"]
        
        # Handle callable questions (e.g., dynamic category list)
        if callable(question):
            question = question()
        
        # Add step counter
        step_indicator = f"<b>Step {step + 1}/{len(self.INTERVIEW_QUESTIONS)}</b>\n\n"
        
        return step_indicator + question
    
    def _extract_field_value(
        self,
        field: CampaignField,
        user_input: str,
        entities: Dict[str, Any]
    ) -> Any:
        """
        Extract field value from user input and entities
        
        Args:
            field: Field to extract
            user_input: Raw user input
            entities: Extracted entities
            
        Returns:
            Extracted value
        """
        # For most fields, use the raw input
        if field == CampaignField.TITLE:
            return user_input.strip()
        
        elif field == CampaignField.CATEGORY:
            # Try to match category from input
            for cat in CAMPAIGN_CATEGORIES:
                if cat.lower() in user_input.lower():
                    return cat
            # Fallback to entity or input
            return entities.get("category", user_input.strip())
        
        elif field == CampaignField.GOAL_AMOUNT:
            # Try entity first
            amount = entities.get("amount")
            if amount and isinstance(amount, (int, float)):
                return amount
            
            # Try to extract number from input
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', user_input)
            if numbers:
                try:
                    # Remove commas and convert
                    return float(numbers[0].replace(',', ''))
                except ValueError:
                    pass
            
            return user_input.strip()
        
        elif field == CampaignField.LOCATION:
            return entities.get("location", user_input.strip())
        
        else:
            # For other fields, use raw input
            return user_input.strip()
    
    def _generate_summary(self, campaign_data: Dict[str, Any]) -> str:
        """
        Generate campaign summary for user confirmation
        
        Args:
            campaign_data: Collected campaign data
            
        Returns:
            Formatted summary message
        """
        summary = (
            "🎉 <b>Campaign Creation Complete!</b>\n\n"
            "Here's what you've created:\n\n"
        )
        
        # Add each field
        summary += f"<b>Title:</b> {campaign_data.get('title', 'N/A')}\n\n"
        summary += f"<b>Category:</b> {campaign_data.get('category', 'N/A')}\n\n"
        summary += f"<b>Problem:</b>\n{campaign_data.get('problem', 'N/A')}\n\n"
        summary += f"<b>Solution:</b>\n{campaign_data.get('solution', 'N/A')}\n\n"
        
        goal = campaign_data.get('goal_amount', 0)
        currency = campaign_data.get('currency', 'USD')
        summary += f"<b>Goal:</b> ${goal:,.0f} {currency}\n\n"
        
        summary += f"<b>Beneficiaries:</b> {campaign_data.get('beneficiaries', 'N/A')}\n\n"
        summary += f"<b>Location:</b> {campaign_data.get('location', 'N/A')}\n\n"
        summary += f"<b>Timeline:</b> {campaign_data.get('timeline', 'N/A')}\n\n"
        summary += f"<b>Budget:</b>\n{campaign_data.get('budget_breakdown', 'N/A')}\n\n"
        
        summary += (
            "✅ Your campaign has been created and submitted for admin approval!\n\n"
            "We'll notify you once it's reviewed (usually within 24 hours).\n\n"
            "You can check the status with: 'Show my campaigns'"
        )
        
        return summary
    
    @classmethod
    def get_progress_percentage(cls, step: int) -> int:
        """Calculate interview progress percentage"""
        return int((step / len(cls.INTERVIEW_QUESTIONS)) * 100)


# Helper functions for bot integration

def is_in_campaign_creation(user_id: str) -> bool:
    """Check if user is currently in campaign creation flow"""
    context = ConversationContext.get_context(user_id)
    if not context:
        return False
    
    # Check if campaign creation is in progress
    step = context.get("campaign_creation_step", -1)
    return step >= 0 and step < len(CampaignInterviewAgent.INTERVIEW_QUESTIONS)


def get_campaign_creation_agent(user_id: str) -> Optional[CampaignInterviewAgent]:
    """Get campaign creation agent if in progress"""
    if is_in_campaign_creation(user_id):
        return CampaignInterviewAgent(user_id)
    return None


# Example usage
if __name__ == "__main__":
    print("🎤 Campaign Interview Agent Test\n")
    
    user_id = "test_user_123"
    agent = CampaignInterviewAgent(user_id)
    
    # Start interview
    print(agent.start_interview())
    print("\n" + "="*50 + "\n")
    
    # Simulate responses
    responses = [
        ("Clean Water for Mwanza", {"title": "Clean Water for Mwanza"}),
        ("Water and Sanitation", {"category": "Water & Sanitation"}),
        ("450 families in Mwanza lack access to clean water", {"problem": "water access"}),
        ("Build 10 water wells with filtration systems", {"solution": "water wells"}),
        ("50000 dollars", {"amount": 50000, "currency": "USD"}),
        ("450 families in rural Mwanza", {"beneficiaries": "450 families"}),
        ("Mwanza, Tanzania", {"location": "Mwanza, Tanzania"}),
        ("6 months", {"timeline": "6 months"}),
        ("Wells $30k, Filtration $10k, Maintenance $5k, Training $5k", {"budget": "breakdown"})
    ]
    
    for i, (response, entities) in enumerate(responses, 1):
        print(f"User response {i}: {response}")
        is_valid, message, error = agent.process_response(response, entities)
        
        if is_valid:
            print(f"✅ Valid")
            print(f"\n{message}\n")
        else:
            print(f"❌ Error: {error}")
        
        print("="*50 + "\n")
    
    # Check if complete
    if agent.is_complete():
        print("✅ Interview Complete!")
        print(f"Collected data: {agent.get_collected_data()}")
