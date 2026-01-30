"""
TrustVoice Intent & Entity Definitions
Defines all supported voice commands and their entity schemas
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class IntentType(str, Enum):
    """All supported voice intents in TrustVoice"""
    
    # Discovery & Search
    SEARCH_CAMPAIGNS = "search_campaigns"
    VIEW_CAMPAIGN_DETAILS = "view_campaign_details"
    LIST_CATEGORIES = "list_categories"
    
    # Donation Actions
    MAKE_DONATION = "make_donation"
    CHECK_DONATION_STATUS = "check_donation_status"
    VIEW_DONATION_HISTORY = "view_donation_history"
    
    # Campaign Management (NGO)
    CREATE_CAMPAIGN = "create_campaign"
    UPDATE_CAMPAIGN = "update_campaign"
    VIEW_MY_CAMPAIGNS = "view_my_campaigns"
    
    # Impact Verification
    REPORT_IMPACT = "report_impact"
    VIEW_IMPACT_UPDATES = "view_impact_updates"
    
    # User Account
    UPDATE_PROFILE = "update_profile"
    CHANGE_LANGUAGE = "change_language"
    GET_HELP = "get_help"
    SYSTEM_INFO = "system_info"  # General questions about the platform
    
    # Conversational
    GREETING = "greeting"
    THANK_YOU = "thank_you"
    UNCLEAR = "unclear"


class EntityType(str, Enum):
    """Entity types that can be extracted from voice input"""
    
    AMOUNT = "amount"
    CURRENCY = "currency"
    CAMPAIGN_ID = "campaign_id"
    CAMPAIGN_NAME = "campaign_name"
    TITLE = "title"  # Campaign title (alias for campaign_name)
    CATEGORY = "category"
    GOAL_AMOUNT = "goal_amount"  # Fundraising goal
    LOCATION = "location"
    DATE = "date"
    LANGUAGE = "language"
    PAYMENT_METHOD = "payment_method"


# Intent Entity Schemas
INTENT_SCHEMAS: Dict[IntentType, Dict[str, Any]] = {
    IntentType.SEARCH_CAMPAIGNS: {
        "description": "User wants to find campaigns to support",
        "required_entities": [],
        "optional_entities": [
            EntityType.CATEGORY,
            EntityType.LOCATION,
            EntityType.AMOUNT
        ],
        "examples": [
            "Show me water projects in Tanzania",
            "Find education campaigns under $100",
            "I want to support healthcare in Kenya",
            "What campaigns are available?",
            "Show active campaigns",
            "List all projects",
            "Browse campaigns",
            "What can I donate to?"
        ]
    },
    
    IntentType.VIEW_CAMPAIGN_DETAILS: {
        "description": "User wants details about a specific campaign",
        "required_entities": [EntityType.CAMPAIGN_NAME],
        "optional_entities": [],
        "examples": [
            "Tell me more about the Mwanza Water Project",
            "What's the progress on the school in Nairobi?",
            "Details on campaign ID 42"
        ]
    },
    
    IntentType.MAKE_DONATION: {
        "description": "User wants to donate to a campaign",
        "required_entities": [EntityType.AMOUNT],
        "optional_entities": [
            EntityType.CURRENCY,
            EntityType.CAMPAIGN_NAME,
            EntityType.PAYMENT_METHOD
        ],
        "examples": [
            "I want to donate $50 to the water project",
            "Donate 100 euros to education",
            "Give 5000 shillings via M-Pesa"
        ]
    },
    
    IntentType.CHECK_DONATION_STATUS: {
        "description": "User wants to check their donation status",
        "required_entities": [],
        "optional_entities": [EntityType.DATE],
        "examples": [
            "Did my donation go through?",
            "What's the status of my last donation?",
            "Check my donation from yesterday"
        ]
    },
    
    IntentType.VIEW_DONATION_HISTORY: {
        "description": "User wants to see their past donations",
        "required_entities": [],
        "optional_entities": [EntityType.DATE, EntityType.CAMPAIGN_NAME],
        "examples": [
            "Show my donation history",
            "What have I donated this year?",
            "List my past contributions"
        ]
    },
    
    IntentType.CREATE_CAMPAIGN: {
        "description": "NGO wants to create a new campaign",
        "required_entities": [EntityType.CAMPAIGN_NAME, EntityType.GOAL_AMOUNT, EntityType.CATEGORY],
        "optional_entities": [EntityType.LOCATION],
        "examples": [
            "Create a new water project campaign with a goal of 5000 dollars",
            "Start a school building campaign in Nairobi needing $10,000",
            "Register health project with 20000 dollar goal"
        ]
    },
    
    IntentType.REPORT_IMPACT: {
        "description": "Field officer reports project completion",
        "required_entities": [EntityType.CAMPAIGN_NAME],
        "optional_entities": [EntityType.LOCATION, EntityType.DATE],
        "examples": [
            "Report completion for Mwanza well project",
            "Well number 3 completed today",
            "Update: school construction finished"
        ]
    },
    
    IntentType.VIEW_IMPACT_UPDATES: {
        "description": "Donor wants impact updates on their donations",
        "required_entities": [],
        "optional_entities": [EntityType.CAMPAIGN_NAME],
        "examples": [
            "Any updates on projects I supported?",
            "Show me impact from the water project",
            "What's happened with my donations?"
        ]
    },
    
    IntentType.CHANGE_LANGUAGE: {
        "description": "User wants to change their language preference",
        "required_entities": [EntityType.LANGUAGE],
        "optional_entities": [],
        "examples": [
            "Switch to Amharic",
            "Change language to English",
            "I prefer Amharic"
        ]
    },
    
    IntentType.GET_HELP: {
        "description": "User needs help or guidance on using the system",
        "required_entities": [],
        "optional_entities": [],
        "examples": [
            "Help me",
            "What can I do?",
            "How does this work?",
            "Show me the commands",
            "What are my options?",
            "Guide me",
            "I need assistance",
            "How do I use this?"
        ]
    },
    
    IntentType.SYSTEM_INFO: {
        "description": "User asks general questions about TrustVoice platform, its features, purpose, or how it works",
        "required_entities": [],
        "optional_entities": [],
        "examples": [
            "Tell me about TrustVoice",
            "What is this system?",
            "How does the platform work?",
            "Explain this service",
            "What does TrustVoice do?",
            "Tell me more about this",
            "What's this all about?",
            "Describe the platform",
            "What is this donation platform?",
            "How does verification work?",
            "What makes TrustVoice different?",
            "Who can use this system?",
            "What features do you have?",
            "How do donations work here?"
        ]
    },
    
    IntentType.GREETING: {
        "description": "User greets the system",
        "required_entities": [],
        "optional_entities": [],
        "examples": [
            "Hello",
            "Hi",
            "Good morning"
        ]
    },
    
    IntentType.UNCLEAR: {
        "description": "Intent could not be determined",
        "required_entities": [],
        "optional_entities": [],
        "examples": []
    }
}


# Category mappings
CAMPAIGN_CATEGORIES = [
    "Water & Sanitation",
    "Education",
    "Healthcare",
    "Agriculture",
    "Women Empowerment",
    "Youth Development",
    "Emergency Relief",
    "Infrastructure"
]


# Currency mappings
SUPPORTED_CURRENCIES = {
    "USD": ["dollars", "usd", "$"],
    "EUR": ["euros", "eur", "€"],
    "GBP": ["pounds", "gbp", "£"],
    "KES": ["shillings", "kes", "ksh", "kenyan shillings"],
    "TZS": ["tanzanian shillings", "tzs"],
    "UGX": ["ugandan shillings", "ugx"],
    "ETB": ["birr", "etb", "ethiopian birr"]
}


# Payment method mappings
PAYMENT_METHODS = {
    "mpesa": ["mpesa", "m-pesa", "mobile money"],
    "card": ["card", "credit card", "debit card"],
    "bank": ["bank transfer", "wire transfer", "bank"]
}


def get_intent_schema(intent: IntentType) -> Dict[str, Any]:
    """Get the entity schema for an intent"""
    return INTENT_SCHEMAS.get(intent, {})


def get_all_intents() -> List[IntentType]:
    """Get list of all supported intents"""
    return list(IntentType)


def get_intent_examples(intent: IntentType) -> List[str]:
    """Get example phrases for an intent"""
    schema = INTENT_SCHEMAS.get(intent, {})
    return schema.get("examples", [])


def format_intent_for_llm() -> str:
    """
    Format intent definitions for LLM prompt
    Returns a string describing all intents and their examples
    """
    lines = ["Available Intents:\n"]
    
    for intent in IntentType:
        if intent == IntentType.UNCLEAR:
            continue
            
        schema = INTENT_SCHEMAS.get(intent, {})
        lines.append(f"\n{intent.value}:")
        lines.append(f"  Description: {schema.get('description', '')}")
        
        examples = schema.get('examples', [])
        if examples:
            lines.append("  Examples:")
            for ex in examples[:3]:  # Show max 3 examples
                lines.append(f"    - \"{ex}\"")
    
    return "\n".join(lines)
