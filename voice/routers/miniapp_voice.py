"""
Mini App Voice Search Router

Enables voice commands in Telegram Mini Apps using the existing TrustVoice
voice processing pipeline:
- ASR: Transcribe audio using voice.asr.asr_infer
- Language: User preference from database or text detection
- NLP: Search campaigns based on transcribed text
- TTS: Generate voice response using voice.tts.tts_provider

Architecture follows Option A: Self-contained voice processing in mini app
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse

# Database imports
from database.db import get_db
from database.models import Campaign, User

# Voice processing imports - using ACTUAL architecture
from voice.asr.asr_infer import transcribe_audio, ASRError
from voice.telegram.voice_responses import get_user_language_preference, detect_language, clean_text_for_tts
from voice.tts.tts_provider import TTSProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["miniapp-voice"])

# Initialize TTS provider
tts_provider = TTSProvider()


@router.post("/search-campaigns")
async def voice_search_campaigns(
    audio: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Process voice search command from campaigns mini app.
    
    Flow:
    1. Save uploaded audio to temporary file
    2. Transcribe using ASR (with user's language preference)
    3. Search campaigns based on transcribed text
    4. Generate text response
    5. Generate TTS audio response
    6. Return both text and audio URL
    
    Args:
        audio: Audio file from MediaRecorder (webm/ogg)
        user_id: Telegram user ID for language preference lookup
        
    Returns:
        JSON with transcription, results, and audio response URL
    """
    temp_audio_path = None
    
    try:
        logger.info(f"Voice search request from user {user_id}")
        
        # Step 1: Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        logger.info(f"Audio saved to {temp_audio_path} ({len(content)} bytes)")
        
        # Step 2: Get user's language preference
        db = next(get_db())
        user_language = get_user_language_preference(user_id)
        
        if not user_language:
            # Default to English if no preference set
            user_language = "en"
            logger.info(f"No language preference found for user {user_id}, defaulting to English")
        
        logger.info(f"User language preference: {user_language}")
        
        # Step 3: Transcribe audio using existing ASR pipeline
        try:
            transcription_result = transcribe_audio(
                temp_audio_path,
                language=user_language,
                user_preference=user_language
            )
            
            transcribed_text = transcription_result.get("text", "")
            detected_language = transcription_result.get("language", user_language)
            
            logger.info(f"Transcription successful: '{transcribed_text}' (language: {detected_language})")
            
        except ASRError as e:
            logger.error(f"ASR error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Speech recognition failed: {str(e)}")
        
        # Step 4: Search campaigns based on transcribed text
        search_query = transcribed_text.lower().strip()
        
        campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).filter(
            (Campaign.title.ilike(f"%{search_query}%")) |
            (Campaign.description.ilike(f"%{search_query}%"))
        ).limit(5).all()
        
        logger.info(f"Found {len(campaigns)} campaigns matching '{search_query}'")
        
        # Step 5: Generate text response
        if campaigns:
            if user_language == "am":
                response_text = f"ለ'{search_query}' {len(campaigns)} ዘመቻዎች አገኘሁ:\n\n"
            else:
                response_text = f"I found {len(campaigns)} campaigns for '{search_query}':\n\n"
            
            for i, campaign in enumerate(campaigns, 1):
                response_text += f"{i}. {campaign.title}\n"
                if campaign.goal_amount:
                    response_text += f"   Goal: KES {campaign.goal_amount:,}\n"
        else:
            if user_language == "am":
                response_text = f"ይቅርታ፣ ለ'{search_query}' ምንም ዘመቻ አላገኘሁም። እባክዎ እንደገና ይሞክሩ።"
            else:
                response_text = f"Sorry, I couldn't find any campaigns matching '{search_query}'. Please try another search."
        
        # Step 6: Generate TTS audio response
        tts_success = False
        audio_url = None
        
        try:
            # Clean text for TTS (remove markdown, URLs, etc.)
            clean_text = clean_text_for_tts(response_text)
            
            # Generate TTS audio
            success, audio_path, error = await tts_provider.text_to_speech(
                clean_text,
                language=detected_language
            )
            
            if success and audio_path:
                # Convert absolute path to URL path
                # The audio file is in voice/tts_cache/, need to serve it via static or endpoint
                audio_filename = Path(audio_path).name
                audio_url = f"/api/voice/audio/{audio_filename}"
                tts_success = True
                logger.info(f"TTS generated: {audio_url}")
            else:
                logger.warning(f"TTS failed: {error}")
                
        except Exception as tts_error:
            logger.error(f"TTS error: {str(tts_error)}")
            # Continue without audio - text response is still valuable
        
        # Step 7: Build response
        response_data = {
            "success": True,
            "transcription": transcribed_text,
            "language": detected_language,
            "response_text": response_text,
            "campaigns": [
                {
                    "id": c.id,
                    "title": c.title,
                    "description": c.description,
                    "goal_amount": c.goal_amount,
                    "current_amount": c.current_amount,
                    "ngo_id": c.ngo_id
                }
                for c in campaigns
            ],
            "has_audio": tts_success,
            "audio_url": audio_url if tts_success else None
        }
        
        logger.info(f"Voice search complete: {len(campaigns)} results, TTS: {tts_success}")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice search failed: {str(e)}")
        
    finally:
        # Cleanup temporary audio file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.debug(f"Cleaned up temp file: {temp_audio_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")


@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """
    Serve TTS audio files from cache.
    
    Args:
        filename: Audio file name (hash.mp3)
        
    Returns:
        Audio file response
    """
    try:
        audio_path = Path("voice/tts_cache") / filename
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Security: Prevent directory traversal
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f"inline; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve audio")


@router.post("/donate-by-voice")
async def voice_donate(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    campaign_id: Optional[int] = Form(None)
):
    """
    Process voice donation command.
    
    Example: "Donate 500 shillings" or "አምስት መቶ ብር ለግስ"
    
    Args:
        audio: Audio file
        user_id: Telegram user ID
        campaign_id: Optional campaign ID if context is known
        
    Returns:
        JSON with donation intent and confirmation
    """
    temp_audio_path = None
    
    try:
        logger.info(f"Voice donation request from user {user_id}")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # Get user language
        db = next(get_db())
        user_language = get_user_language_preference(user_id) or "en"
        
        # Transcribe
        transcription_result = transcribe_audio(
            temp_audio_path,
            language=user_language,
            user_preference=user_language
        )
        
        transcribed_text = transcription_result.get("text", "")
        logger.info(f"Donation transcription: '{transcribed_text}'")
        
        # Parse donation amount (simple regex - can be enhanced)
        import re
        amount_match = re.search(r'(\d+)', transcribed_text)
        amount = int(amount_match.group(1)) if amount_match else None
        
        if not amount:
            if user_language == "am":
                response_text = "ይቅርታ፣ መጠኑን ሊገነዘብ አልቻለም። እባክዎ እንደገና ይሞክሩ።"
            else:
                response_text = "Sorry, I couldn't understand the amount. Please try again."
            
            return JSONResponse(content={
                "success": False,
                "error": "amount_not_recognized",
                "response_text": response_text,
                "transcription": transcribed_text
            })
        
        # Generate confirmation response
        if user_language == "am":
            response_text = f"ለማረጋገጥ፡ {amount} ብር መለገስ ይፈልጋሉ?"
        else:
            response_text = f"To confirm: You want to donate KES {amount}?"
        
        # Generate TTS
        clean_text = clean_text_for_tts(response_text)
        success, audio_path, _ = await tts_provider.text_to_speech(
            clean_text,
            language=user_language
        )
        
        audio_url = None
        if success and audio_path:
            audio_filename = Path(audio_path).name
            audio_url = f"/api/voice/audio/{audio_filename}"
        
        return JSONResponse(content={
            "success": True,
            "amount": amount,
            "currency": "KES",
            "campaign_id": campaign_id,
            "response_text": response_text,
            "audio_url": audio_url,
            "transcription": transcribed_text,
            "requires_confirmation": True
        })
        
    except Exception as e:
        logger.error(f"Voice donation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass
