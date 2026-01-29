"""
Natural Language Understanding (NLU) Module for TrustVoice
Extracts intents and entities from transcribed voice input using GPT-4o-mini

Cost: ~$0.005 per request (highly efficient)
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

from .intents import (
    IntentType,
    EntityType,
    get_intent_schema,
    format_intent_for_llm,
    CAMPAIGN_CATEGORIES,
    SUPPORTED_CURRENCIES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NLU_MODEL = "gpt-4o-mini"  # Cost-effective for structured extraction


class NLUError(Exception):
    """Custom exception for NLU errors"""
    pass


def extract_intent_and_entities(
    transcript: str,
    language: str = "en",
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract intent and entities from transcribed text using GPT-4o-mini
    
    Args:
        transcript: The transcribed text from ASR
        language: Language of the transcript ('en' or 'am')
        user_context: Optional context (previous intents, user preferences)
        
    Returns:
        Dictionary with intent, entities, and confidence
        {
            "intent": "make_donation",
            "entities": {
                "amount": 50,
                "currency": "USD",
                "campaign_name": "Mwanza Water Project"
            },
            "confidence": 0.95,
            "requires_clarification": False,
            "clarification_question": None
        }
    """
    try:
        if not OPENAI_API_KEY:
            raise NLUError("OPENAI_API_KEY not set in environment")
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Build system prompt with intent definitions
        system_prompt = _build_system_prompt(language)
        
        # Build user prompt with context
        user_prompt = _build_user_prompt(transcript, user_context)
        
        logger.info(f"NLU extraction: '{transcript[:50]}...' (lang: {language})")
        
        # Call GPT-4o-mini with structured output
        response = client.chat.completions.create(
            model=NLU_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=500
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        # Validate and normalize
        result = _validate_and_normalize(result)
        
        logger.info(f"✅ Intent extracted: {result['intent']} (confidence: {result['confidence']})")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse NLU response: {e}")
        return _fallback_response(transcript)
    except Exception as e:
        logger.error(f"NLU extraction error: {str(e)}")
        raise NLUError(f"Intent extraction failed: {str(e)}")


def _build_system_prompt(language: str) -> str:
    """Build system prompt with intent definitions"""
    
    intent_definitions = format_intent_for_llm()
    
    prompt = f"""You are an NLU (Natural Language Understanding) system for TrustVoice, a voice-first donation platform for African NGOs.

ABOUT TRUSTVOICE:
TrustVoice is a transparent donation platform that connects donors with verified NGO campaigns across Africa. 
Key features:
- Voice-first interface (accessible via Telegram, IVR calls, web)
- Multi-language support (English, Amharic, more coming)
- Real-time impact verification by field agents using GPS
- M-Pesa and mobile payment integration
- Campaign categories: Water, Education, Healthcare, Agriculture, Women Empowerment, Youth Development, Emergency Relief, Infrastructure

Users can:
- Donors: Browse campaigns, make donations, track impact
- NGOs/Campaign Creators: Create and manage campaigns
- Field Agents: Report and verify project completion with GPS evidence

Your task: Extract the user's intent and relevant entities from their voice input.

{intent_definitions}

Categories: {', '.join(CAMPAIGN_CATEGORIES)}
Currencies: USD, EUR, GBP, KES, TZS, UGX, ETB

INTENT CLASSIFICATION GUIDELINES:
- "system_info": General questions about TrustVoice (what is this, how does it work, explain the platform, features, etc.)
- "get_help": User needs guidance on commands or wants to see options
- "search_campaigns": User wants to browse/find campaigns (show campaigns, what's available, list projects)
- "make_donation": Clear donation intent with amount or campaign
- "view_donation_history": User asks about their past donations
- Be GENEROUS with intent matching - if user mentions the platform, features, or asks general questions, use "system_info"
- Only use "unclear" if truly ambiguous and doesn't match any intent pattern

IMPORTANT:
- Return ONLY valid JSON
- Use intent values exactly as defined (e.g., "make_donation", not "donate")
- Extract all mentioned entities
- Prefer "system_info" over "unclear" for general platform questions
- For Amharic input, extract intent even if you need to translate
- Be generous with amounts - "fifty" = 50, "hundred" = 100

Response Format:
{{
    "intent": "intent_name",
    "entities": {{
        "amount": 50,
        "currency": "USD",
        "campaign_name": "Example Campaign"
    }},
    "confidence": 0.95,
    "requires_clarification": false,
    "clarification_question": null
}}"""
    
    return prompt


def _build_user_prompt(transcript: str, context: Optional[Dict[str, Any]]) -> str:
    """Build user prompt with transcript and context"""
    
    prompt = f"User said: \"{transcript}\"\n\n"
    
    if context:
        prompt += "Context:\n"
        if context.get("previous_intent"):
            prompt += f"- Previous intent: {context['previous_intent']}\n"
        if context.get("campaign_in_focus"):
            prompt += f"- Currently viewing: {context['campaign_in_focus']}\n"
        prompt += "\n"
    
    prompt += "Extract intent and entities:"
    
    return prompt


def _validate_and_normalize(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize NLU results"""
    
    # Ensure required fields exist
    if "intent" not in result:
        result["intent"] = IntentType.UNCLEAR.value
    
    if "entities" not in result:
        result["entities"] = {}
    
    if "confidence" not in result:
        result["confidence"] = 0.5
    
    if "requires_clarification" not in result:
        result["requires_clarification"] = False
    
    # Normalize intent to enum value
    try:
        intent = IntentType(result["intent"])
        result["intent"] = intent.value
    except ValueError:
        logger.warning(f"Invalid intent: {result['intent']}, using 'unclear'")
        result["intent"] = IntentType.UNCLEAR.value
    
    # Normalize currency codes
    if "currency" in result["entities"] and result["entities"]["currency"]:
        currency = result["entities"]["currency"].upper()
        if currency in SUPPORTED_CURRENCIES:
            result["entities"]["currency"] = currency
    
    # Normalize amounts to float
    if "amount" in result["entities"]:
        try:
            result["entities"]["amount"] = float(result["entities"]["amount"])
        except (ValueError, TypeError):
            del result["entities"]["amount"]
    
    return result


def _fallback_response(transcript: str) -> Dict[str, Any]:
    """Generate fallback response when NLU fails"""
    return {
        "intent": IntentType.UNCLEAR.value,
        "entities": {},
        "confidence": 0.0,
        "requires_clarification": True,
        "clarification_question": "I didn't quite understand that. Could you please rephrase?"
    }


def check_required_entities(
    intent: str,
    entities: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """
    Check if all required entities for an intent are present
    
    Returns:
        Tuple of (is_complete, missing_entity_question)
    """
    try:
        intent_enum = IntentType(intent)
        schema = get_intent_schema(intent_enum)
        
        required = schema.get("required_entities", [])
        
        for entity_type in required:
            entity_key = entity_type.value
            if entity_key not in entities:
                # Generate clarification question
                question = _generate_missing_entity_question(intent_enum, entity_type)
                return False, question
        
        return True, None
        
    except ValueError:
        return True, None


def _generate_missing_entity_question(
    intent: IntentType,
    missing_entity: EntityType
) -> str:
    """Generate a natural clarification question for missing entity"""
    
    questions = {
        (IntentType.MAKE_DONATION, EntityType.AMOUNT): "How much would you like to donate?",
        (IntentType.MAKE_DONATION, EntityType.CAMPAIGN_NAME): "Which campaign would you like to support?",
        (IntentType.VIEW_CAMPAIGN_DETAILS, EntityType.CAMPAIGN_NAME): "Which campaign would you like to learn about?",
        (IntentType.CREATE_CAMPAIGN, EntityType.CAMPAIGN_NAME): "What would you like to name this campaign?",
        (IntentType.CREATE_CAMPAIGN, EntityType.CATEGORY): "What category is this campaign? (e.g., Water, Education, Healthcare)",
        (IntentType.CHANGE_LANGUAGE, EntityType.LANGUAGE): "Which language would you prefer? English or Amharic?",
    }
    
    key = (intent, missing_entity)
    return questions.get(key, f"Could you provide the {missing_entity.value}?")


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python nlu_infer.py \"<transcript>\"")
        print("\nExample:")
        print('python nlu_infer.py "I want to donate fifty dollars to the water project"')
        sys.exit(1)
    
    transcript = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en"
    
    print(f"\n🧠 TrustVoice NLU")
    print(f"Transcript: \"{transcript}\"")
    print(f"Language: {language}\n")
    
    try:
        result = extract_intent_and_entities(transcript, language)
        
        print(f"✅ Intent: {result['intent']}")
        print(f"📊 Confidence: {result['confidence']:.2%}")
        
        if result['entities']:
            print(f"\n📝 Entities:")
            for key, value in result['entities'].items():
                print(f"   {key}: {value}")
        
        if result['requires_clarification']:
            print(f"\n❓ Clarification needed: {result['clarification_question']}")
        else:
            # Check for missing required entities
            is_complete, question = check_required_entities(
                result['intent'],
                result['entities']
            )
            
            if not is_complete:
                print(f"\n❓ Missing entity: {question}")
        
    except NLUError as e:
        print(f"\n❌ Error: {e}")
