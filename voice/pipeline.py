"""
Complete Voice Processing Pipeline
ASR → NLU → Intent Routing

This is the main entry point for voice message processing
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice.audio_utils import process_audio_for_asr, AudioProcessingError
from voice.asr.asr_infer import transcribe_audio, ASRError
from voice.nlu.nlu_infer import extract_intent_and_entities, check_required_entities, NLUError
from voice.nlu.context import ConversationContext
from voice.nlu.intents import IntentType

logger = logging.getLogger(__name__)


class VoiceProcessingError(Exception):
    """Custom exception for voice processing errors"""
    pass


def process_voice_message(
    audio_file_path: str,
    user_id: str,
    user_language: str = "en",
    cleanup_audio: bool = True
) -> Dict[str, Any]:
    """
    Complete voice processing pipeline
    
    Pipeline:
    1. Audio Processing: Validate and convert to optimal format
    2. ASR: Transcribe audio to text
    3. NLU: Extract intent and entities
    4. Context: Update conversation context
    5. Validation: Check for missing required entities
    
    Args:
        audio_file_path: Path to audio file
        user_id: Unique user identifier (phone/telegram_id)
        user_language: User's preferred language ('en' or 'am')
        cleanup_audio: Whether to delete audio files after processing
        
    Returns:
        Complete processing result with all pipeline stages
    """
    result = {
        "success": False,
        "user_id": user_id,
        "stages": {},
        "intent": None,
        "entities": {},
        "response": None,
        "error": None
    }
    
    try:
        logger.info(f"🎤 Processing voice message for user {user_id}")
        
        # Stage 1: Audio Processing
        logger.info("Stage 1: Audio processing...")
        converted_file, metadata = process_audio_for_asr(
            audio_file_path,
            cleanup_original=False  # Keep original for now
        )
        
        result["stages"]["audio"] = {
            "success": True,
            "duration": metadata.get("duration_seconds"),
            "sample_rate": metadata.get("sample_rate"),
            "file_size_mb": metadata.get("file_size_mb")
        }
        
        logger.info(f"✅ Audio: {metadata.get('duration_seconds')}s, {metadata.get('sample_rate')}Hz")
        
        # Stage 2: ASR (Automatic Speech Recognition)
        logger.info(f"Stage 2: ASR transcription (language: {user_language})...")
        
        # Get user context for better routing
        context = ConversationContext.get_context(user_id)
        
        asr_result = transcribe_audio(
            converted_file,
            language=user_language,
            user_preference=user_language
        )
        
        transcript = asr_result["text"]
        
        result["stages"]["asr"] = {
            "success": True,
            "transcript": transcript,
            "language": asr_result.get("language"),
            "method": asr_result.get("method"),
            "model": asr_result.get("model")
        }
        
        logger.info(f"✅ ASR: \"{transcript}\"")
        
        # Stage 3: NLU (Natural Language Understanding)
        logger.info("Stage 3: NLU intent extraction...")
        
        nlu_result = extract_intent_and_entities(
            transcript,
            language=user_language,
            user_context=context
        )
        
        intent = nlu_result["intent"]
        entities = nlu_result["entities"]
        confidence = nlu_result["confidence"]
        
        result["stages"]["nlu"] = {
            "success": True,
            "intent": intent,
            "entities": entities,
            "confidence": confidence
        }
        
        result["intent"] = intent
        result["entities"] = entities
        
        logger.info(f"✅ NLU: {intent} (confidence: {confidence:.2%})")
        
        # Stage 4: Context Management
        logger.info("Stage 4: Context update...")
        
        # Merge context entities with newly extracted ones
        collected_entities = ConversationContext.get_collected_entities(user_id)
        all_entities = {**collected_entities, **entities}
        
        # Update context
        ConversationContext.update_context(
            user_id,
            intent=intent,
            entities=entities
        )
        
        result["stages"]["context"] = {
            "success": True,
            "turn_count": ConversationContext.get_context(user_id).get("turn_count"),
            "collected_entities": all_entities
        }
        
        # Stage 5: Entity Validation
        logger.info("Stage 5: Entity validation...")
        
        is_complete, missing_question = check_required_entities(intent, all_entities)
        
        result["stages"]["validation"] = {
            "is_complete": is_complete,
            "missing_entity_question": missing_question
        }
        
        if not is_complete:
            result["response"] = {
                "type": "clarification",
                "message": missing_question
            }
            logger.info(f"❓ Missing entity: {missing_question}")
        else:
            result["response"] = {
                "type": "intent_ready",
                "message": f"Intent {intent} ready for execution",
                "entities": all_entities
            }
            logger.info(f"✅ Intent complete with all entities")
        
        # Cleanup audio files
        if cleanup_audio:
            from voice.audio_utils import cleanup_audio_file
            cleanup_audio_file(audio_file_path)
            cleanup_audio_file(converted_file)
        
        result["success"] = True
        logger.info(f"✅ Voice processing complete for {user_id}")
        
        return result
        
    except AudioProcessingError as e:
        result["error"] = f"Audio processing failed: {str(e)}"
        result["stages"]["audio"] = {"success": False, "error": str(e)}
        logger.error(result["error"])
        return result
        
    except ASRError as e:
        result["error"] = f"Speech recognition failed: {str(e)}"
        result["stages"]["asr"] = {"success": False, "error": str(e)}
        logger.error(result["error"])
        return result
        
    except NLUError as e:
        result["error"] = f"Intent extraction failed: {str(e)}"
        result["stages"]["nlu"] = {"success": False, "error": str(e)}
        logger.error(result["error"])
        return result
        
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.error(f"❌ Voice processing error: {str(e)}")
        return result


def format_response_for_user(result: Dict[str, Any], language: str = "en") -> str:
    """
    Format processing result into a user-friendly response
    
    Args:
        result: Processing result from process_voice_message
        language: User's language for response
        
    Returns:
        Formatted response message
    """
    if not result["success"]:
        return "Sorry, I couldn't process your voice message. Please try again."
    
    response = result.get("response", {})
    
    if response.get("type") == "clarification":
        return response.get("message", "Could you provide more details?")
    
    # Intent-specific responses
    intent = result.get("intent")
    entities = result.get("entities", {})
    
    if intent == IntentType.MAKE_DONATION.value:
        amount = entities.get("amount")
        currency = entities.get("currency", "USD")
        campaign = entities.get("campaign_name", "this campaign")
        return f"Great! You want to donate {currency} {amount} to {campaign}. Let me process that..."
    
    elif intent == IntentType.SEARCH_CAMPAIGNS.value:
        category = entities.get("category", "campaigns")
        location = entities.get("location")
        if location:
            return f"Searching for {category} in {location}..."
        return f"Searching for {category}..."
    
    elif intent == IntentType.VIEW_CAMPAIGN_DETAILS.value:
        campaign = entities.get("campaign_name", "the campaign")
        return f"Here are the details for {campaign}..."
    
    elif intent == IntentType.GREETING.value:
        return "Hello! How can I help you today? You can search for campaigns, make donations, or check your donation history."
    
    elif intent == IntentType.GET_HELP.value:
        return "I can help you find campaigns, make donations, check donation status, and more. What would you like to do?"
    
    else:
        return f"I understand you want to {intent.replace('_', ' ')}. Let me help with that."


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pipeline.py <audio_file> <user_id> [language]")
        print("\nExample:")
        print("  python pipeline.py uploads/audio/test.wav user_123 en")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    user_id = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 else "en"
    
    print(f"\n🎤 TrustVoice Voice Processing Pipeline\n")
    print(f"Audio: {audio_file}")
    print(f"User: {user_id}")
    print(f"Language: {language}\n")
    print("=" * 60)
    
    # Process the voice message
    result = process_voice_message(audio_file, user_id, language, cleanup_audio=False)
    
    print("\n" + "=" * 60)
    print("\n📊 RESULTS:\n")
    
    if result["success"]:
        print(f"✅ Success: {result['success']}")
        print(f"\n🎯 Intent: {result['intent']}")
        print(f"📝 Entities: {result['entities']}")
        
        print(f"\n📈 Pipeline Stages:")
        for stage, data in result["stages"].items():
            status = "✅" if data.get("success", False) else "❌"
            print(f"  {status} {stage.upper()}: {data}")
        
        print(f"\n💬 User Response:")
        user_response = format_response_for_user(result, language)
        print(f"  \"{user_response}\"")
    else:
        print(f"❌ Error: {result['error']}")
