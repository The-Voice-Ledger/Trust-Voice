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
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Database imports
from database.db import get_db, get_db_session
from database.models import Campaign, User

# Voice processing imports - using ACTUAL architecture
from voice.asr.asr_infer import transcribe_audio, ASRError
from voice.audio_utils import validate_audio_file
from voice.telegram.voice_responses import get_user_language_preference, detect_language, clean_text_for_tts
from voice.tts.tts_provider import TTSProvider
from voice.conversation.analytics import ConversationAnalytics
from voice.nlu.nlu_infer import extract_intent_and_entities, NLUError
from voice.nlu.intents import IntentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["miniapp-voice"])

# Initialize TTS provider
tts_provider = TTSProvider()


async def _try_agent(
    transcribed_text: str,
    user_id: str,
    db,
    language: str = "en",
    context: dict = None,
):
    """
    Try handling a voice command via the AI Agent.

    Returns a dict with response_text, audio_url, data, tools_used
    if the agent succeeds, or None to fall back to the legacy handler.
    """
    try:
        from voice.agent.executor import AgentExecutor

        _agent = AgentExecutor()
        user_record = db.query(User).filter(
            User.telegram_user_id == str(user_id)
        ).first()
        uid = str(user_record.id) if user_record else str(user_id)

        result = await _agent.run(
            user_message=transcribed_text,
            user_id=uid,
            db=db,
            language=language,
            context=context,
        )

        response_text = result.get("response_text", "")
        if not response_text:
            return None

        # Generate TTS for the agent's response
        audio_url = None
        try:
            clean = clean_text_for_tts(response_text)
            ok, apath, _ = await tts_provider.text_to_speech(
                clean, language=language
            )
            if ok and apath:
                audio_url = f"/api/voice/audio/{Path(apath).name}"
        except Exception:
            pass

        return {
            "response_text": response_text,
            "audio_url": audio_url,
            "data": result.get("data", {}),
            "tools_used": result.get("tools_used", []),
            "conversation_id": result.get("conversation_id", ""),
            "response_source": "agent",
        }
    except Exception as e:
        logger.error(f"Agent unavailable, falling back to legacy: {e}", exc_info=True)
        return None


def _audio_suffix(upload: UploadFile) -> str:
    """Derive file extension from upload content-type or filename."""
    ct = (upload.content_type or "").lower()
    if "mp4" in ct or "aac" in ct:
        return ".mp4"
    if "ogg" in ct:
        return ".ogg"
    if "wav" in ct:
        return ".wav"
    if "mp3" in ct or "mpeg" in ct:
        return ".mp3"
    if "flac" in ct:
        return ".flac"
    # Check filename extension as fallback
    if upload.filename:
        ext = Path(upload.filename).suffix.lower()
        if ext in (".mp4", ".m4a", ".ogg", ".wav", ".mp3", ".flac", ".webm", ".oga", ".mpga"):
            return ext
    return ".webm"


@router.post("/search-campaigns")
async def voice_search_campaigns(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    context: Optional[str] = Form(None),
    user_language: Optional[str] = Form(None)  # Optional - will use DB preference if not provided
):
    """
    Process voice search command from campaigns mini app.
    Supports Amharic via AddisAI.
    
    Flow:
    1. Save uploaded audio to temporary file
    2. Transcribe using ASR (with user's language preference from DB or parameter)
    3. Search campaigns based on transcribed text AND context
    4. Generate text response
    5. Generate TTS audio response
    6. Return both text and audio URL
    
    Args:
        audio: Audio file from MediaRecorder (webm/ogg)
        user_id: Telegram user ID for language preference lookup
        context: Optional JSON context (app state, selected items, available actions)
        user_language: Optional language override ('en' or 'am')
        
    Returns:
        JSON with transcription, results, and audio response URL
    """
    import json
    temp_audio_path = None
    context_data = None
    db = None
    
    try:
        # Parse context if provided
        if context:
            try:
                context_data = json.loads(context)
                logger.info(f"Voice search with context: view={context_data.get('view')}, app={context_data.get('app')}")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse context JSON: {context}")
        
        logger.info(f"Voice search request from user {user_id}")
        
        # Step 1: Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        logger.info(f"Audio saved to {temp_audio_path} ({len(content)} bytes)")
        
        # Step 1b: Validate audio file before processing
        is_valid, validation_error = validate_audio_file(temp_audio_path)
        if not is_valid:
            logger.warning(f"Audio validation failed: {validation_error}")
            raise HTTPException(status_code=400, detail=f"Invalid audio: {validation_error}")
        
        # Step 2: Get user's language preference (parameter → database → default)
        db = next(get_db())
        if not user_language:
            user_language = get_user_language_preference(user_id) or "en"
            logger.info(f"Using database language preference for user {user_id}: {user_language}")
        else:
            logger.info(f"Using provided language preference: {user_language}")
        
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
        except Exception as e:
            logger.error(f"Unexpected ASR error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
        
        # ── AI Agent (try first, fall back to legacy NLU) ──
        _agent_resp = await _try_agent(
            transcribed_text, user_id, db, detected_language, context_data
        )
        if _agent_resp:
            _ac = _agent_resp["data"].get("campaigns", [])
            return JSONResponse(content={
                "success": True,
                "transcription": transcribed_text,
                "language": detected_language,
                "response_text": _agent_resp["response_text"],
                "campaigns": [
                    {
                        "id": c.get("id"),
                        "title": c.get("title", ""),
                        "description": c.get("description_preview", c.get("description", "")),
                        "goal_amount": float(c.get("goal_usd", c.get("goal_amount", 0))),
                        "current_amount": float(c.get("raised_usd", c.get("current_amount", 0))),
                        "ngo_id": c.get("ngo_id"),
                    }
                    for c in _ac
                ],
                "has_audio": _agent_resp["audio_url"] is not None,
                "audio_url": _agent_resp["audio_url"],
                "response_source": "agent",
            })

        # ── Fallback: Legacy NLU pipeline ──
        # Step 4: Use NLU to extract intent and entities
        try:
            nlu_result = extract_intent_and_entities(
                transcript=transcribed_text,
                language=detected_language,
                user_context=context_data
            )
            
            intent = nlu_result.get('intent')
            entities = nlu_result.get('entities', {})
            logger.info(f"NLU extracted intent: {intent}, entities: {entities}")
            
        except NLUError as e:
            logger.error(f"NLU error: {str(e)}, falling back to keyword search")
            # Fallback to simple keyword extraction if NLU fails
            intent = IntentType.SEARCH_CAMPAIGNS
            entities = {}
        except Exception as e:
            logger.error(f"Unexpected NLU error: {str(e)}, using fallback")
            intent = IntentType.SEARCH_CAMPAIGNS
            entities = {}
        
        # Step 5: Build database query based on intent and entities
        query = db.query(Campaign).filter(Campaign.status == "active")
        
        # Extract search parameters from entities
        category = entities.get('category')
        campaign_name = entities.get('campaign_name')
        location = entities.get('location')
        
        # Context-aware: Check if referring to currently viewed campaign
        context_aware_response = False
        if context_data and context_data.get('view') == 'detail':
            selected_campaign_data = context_data.get('selected_campaign')
            if selected_campaign_data and intent == IntentType.VIEW_CAMPAIGN_DETAILS:
                campaign_id = selected_campaign_data.get('id')
                campaigns = db.query(Campaign).filter(Campaign.id == campaign_id).limit(1).all()
                context_aware_response = True
                logger.info(f"Context-aware: Using campaign {campaign_id}")
        
        if not context_aware_response:
            # Apply filters based on extracted entities
            if category:
                query = query.filter(Campaign.category.ilike(f"%{category}%"))
                logger.info(f"Filtering by category: {category}")
            
            if campaign_name:
                query = query.filter(
                    (Campaign.title.ilike(f"%{campaign_name}%")) |
                    (Campaign.description.ilike(f"%{campaign_name}%"))
                )
                logger.info(f"Filtering by campaign name: {campaign_name}")
            
            if location:
                query = query.filter(
                    (Campaign.location.ilike(f"%{location}%")) |
                    (Campaign.description.ilike(f"%{location}%"))
                )
                logger.info(f"Filtering by location: {location}")
            
            # If no specific filters, search in title and description
            if not any([category, campaign_name, location]):
                # Extract keywords from transcript (remove common words)
                keywords = [word for word in transcribed_text.lower().split() 
                           if word not in ['show', 'me', 'tell', 'about', 'find', 'search', 'for', 'the', 'a', 'an', 'campaigns', 'campaign']]
                
                if keywords:
                    # Build OR conditions for each keyword
                    from sqlalchemy import or_
                    conditions = []
                    for keyword in keywords:
                        conditions.extend([
                            Campaign.title.ilike(f"%{keyword}%"),
                            Campaign.description.ilike(f"%{keyword}%"),
                            Campaign.category.ilike(f"%{keyword}%")
                        ])
                    query = query.filter(or_(*conditions))
                    logger.info(f"Searching with keywords: {keywords}")
            
            campaigns = query.limit(5).all()
        
        logger.info(f"Found {len(campaigns)} campaigns for query: '{transcribed_text}'")
        
        # Step 6: Generate text response
        if campaigns:
            # Check if this is a context-aware response
            if context_aware_response and len(campaigns) == 1:
                campaign = campaigns[0]
                
                # Generate response about the specific campaign
                if intent == IntentType.MAKE_DONATION or 'donate' in transcribed_text.lower():
                    if user_language == "am":
                        response_text = f"በ{campaign.title} ላይ ለመለገስ፣ መለገስ ቁልፍን ይጫኑ።\n\n"
                        response_text += f"ግብ: ${campaign.goal_amount_usd:,.0f}\n"
                        response_text += f"የተሰበሰበ: ${campaign.raised_amount_usd:,.0f}"
                    else:
                        response_text = f"To donate to {campaign.title}, tap the Donate button.\n\n"
                        response_text += f"Goal: ${campaign.goal_amount_usd:,.0f}\n"
                        response_text += f"Raised: ${campaign.raised_amount_usd:,.0f}"
                elif intent == IntentType.VIEW_CAMPAIGN_DETAILS or 'detail' in transcribed_text.lower() or 'about' in transcribed_text.lower():
                    if user_language == "am":
                        response_text = f"{campaign.title}\n\n{campaign.description[:200]}"
                    else:
                        response_text = f"{campaign.title}\n\n{campaign.description[:200]}"
                else:
                    # Generic response about the campaign
                    if user_language == "am":
                        response_text = f"እርስዎ {campaign.title} እየተመለከቱ ነው።"
                    else:
                        response_text = f"You're viewing {campaign.title}."
            else:
                # Regular search results - use extracted entities for response
                search_term = category or campaign_name or location or "your search"
                if user_language == "am":
                    response_text = f"ለ'{search_term}' {len(campaigns)} ዘመቻዎች አገኘሁ:\n\n"
                else:
                    response_text = f"I found {len(campaigns)} campaigns for '{search_term}':\n\n"
                
                for i, campaign in enumerate(campaigns, 1):
                    response_text += f"{i}. {campaign.title}\n"
                    if campaign.goal_amount_usd:
                        response_text += f"   Goal: ${campaign.goal_amount_usd:,}\n"
        else:
            # No campaigns found - use extracted entities in response
            search_term = category or campaign_name or location or "your search"
            if user_language == "am":
                response_text = f"ይቅርታ፣ ለ'{search_term}' ምንም ዘመቻ አላገኘሁም። እባክዎ እንደገና ይሞክሩ።"
            else:
                response_text = f"Sorry, I couldn't find any campaigns matching '{search_term}'. Please try another search."
        
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
                    "goal_amount": float(c.goal_amount_usd or 0),
                    "current_amount": float(c.raised_amount_usd or 0),
                    "ngo_id": c.ngo_id
                }
                for c in campaigns
            ],
            "has_audio": tts_success,
            "audio_url": audio_url if tts_success else None,
            "response_source": "fallback_nlu",
        }
        
        # LAB 9 Part 4: Track voice search event
        try:
            user_record = db.query(User).filter(User.telegram_user_id == user_id).first()
            if user_record:
                session_id = str(uuid.uuid4())
                ConversationAnalytics.track_event(
                    db=db,
                    user_id=user_record.id,
                    session_id=session_id,
                    event_type="voice_search",
                    conversation_state="miniapp_search",
                    current_step="search_completed",
                    metadata={
                        "query": transcribed_text,
                        "results_count": len(campaigns),
                        "context_aware": context_aware_response,
                        "tts_success": tts_success
                    }
                )
        except Exception as analytics_error:
            logger.error(f"Analytics tracking failed: {analytics_error}")
        
        logger.info(f"Voice search complete: {len(campaigns)} results, TTS: {tts_success}")
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice search error: {str(e)}", exc_info=True)
        
        # LAB 9 Part 4: Track error
        db_err = None
        try:
            db_err = next(get_db())
            user_record = db_err.query(User).filter(User.telegram_user_id == user_id).first()
            if user_record:
                session_id = str(uuid.uuid4())
                ConversationAnalytics.track_event(
                    db=db_err,
                    user_id=user_record.id,
                    session_id=session_id,
                    event_type="error_occurred",
                    conversation_state="miniapp_search",
                    current_step="error",
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
        except Exception as analytics_error:
            logger.error(f"Analytics tracking failed: {analytics_error}")
        finally:
            if db_err:
                db_err.close()
        
        raise HTTPException(status_code=500, detail=f"Voice search failed: {str(e)}")
        
    finally:
        # Close database session
        if db:
            db.close()
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


@router.post("/analytics-query")
async def voice_analytics_query(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    time_range: str = Form("all")
):
    """
    Process voice query for analytics dashboard.
    
    Examples: "Show last month's donations", "Top campaigns", "How many donors?"
    
    Args:
        audio: Audio file
        user_id: Telegram user ID
        time_range: Time filter (all, today, week, month)
        
    Returns:
        JSON with query results and audio response
    """
    temp_audio_path = None
    db = None
    
    try:
        logger.info(f"Analytics voice query from user {user_id}")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
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
        logger.info(f"Analytics query: '{transcribed_text}'")
        
        # ── AI Agent (try first, fall back to legacy keyword pipeline) ──
        _agent_resp = await _try_agent(transcribed_text, user_id, db, user_language)
        if _agent_resp:
            return JSONResponse(content={
                "success": True,
                "transcription": transcribed_text,
                "query_type": "agent",
                "data": _agent_resp["data"],
                "response_text": _agent_resp["response_text"],
                "audio_url": _agent_resp["audio_url"],
                "response_source": "agent",
            })

        # ── Fallback: Legacy keyword pipeline ──
        # Classify query type
        query_type = _classify_analytics_query(transcribed_text)
        
        # Get relevant data
        from datetime import datetime, timedelta
        from database.models import Donation
        
        if query_type == "temporal":
            # Get metrics for time period
            if "today" in transcribed_text.lower():
                start_date = datetime.now().replace(hour=0, minute=0, second=0)
            elif "week" in transcribed_text.lower() or "last 7" in transcribed_text.lower():
                start_date = datetime.now() - timedelta(days=7)
            elif "month" in transcribed_text.lower():
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.min
            
            donations = db.query(Donation).filter(
                Donation.created_at >= start_date
            ).all()
            
            total = sum(d.amount for d in donations)
            count = len(donations)
            donors = len(set(d.donor_id for d in donations))
            
            if user_language == "am":
                response_text = f"በዚህ ጊዜ {count} ለግሶች ተደርሰዋል። አጠቃላይ {total:,.0f} ብር ከ {donors} ለጋሾች።"
            else:
                response_text = f"During this period, {count} donations were made. Total raised: KES {total:,.0f} from {donors} unique donors."
            
            data = {"total": total, "count": count, "donors": donors}
            
        elif query_type == "comparative":
            # Get top campaigns
            campaigns = db.query(Campaign).filter(Campaign.status == "active").all()
            campaign_totals = []
            for camp in campaigns:
                total = sum(d.amount for d in camp.donations)
                campaign_totals.append({"title": camp.title, "total": total})
            
            campaign_totals.sort(key=lambda x: x["total"], reverse=True)
            top = campaign_totals[:3] if campaign_totals else []
            
            if top:
                if user_language == "am":
                    response_text = f"ከፍተኛው ዘመቻ {top[0]['title']} ነው። {top[0]['total']:,.0f} ብር ተሰብስቧል።"
                else:
                    response_text = f"The top campaign is '{top[0]['title']}' with KES {top[0]['total']:,.0f} raised."
                    if len(top) > 1:
                        response_text += f" Second is '{top[1]['title']}' with KES {top[1]['total']:,.0f}."
            else:
                response_text = "No campaign data available yet."
            
            data = {"top_campaigns": top}
            
        else:
            # General metrics
            all_donations = db.query(Donation).all()
            total_raised = sum(d.amount for d in all_donations)
            active_camps = db.query(Campaign).filter(Campaign.status == "active").count()
            total_donors = db.query(User).filter(User.role.ilike("donor")).count()
            avg_donation = total_raised / len(all_donations) if all_donations else 0
            
            if user_language == "am":
                response_text = f"አጠቃላይ ለጋሾች {total_donors}፣ ንቁ ዘመቻዎች {active_camps}፣ አማካይ ለገሳ {avg_donation:,.0f} ብር።"
            else:
                response_text = f"Total donors: {total_donors}, Active campaigns: {active_camps}, Average donation: ${avg_donation:,.0f}."
            
            data = {
                "total_raised": total_raised,
                "active_campaigns": active_camps,
                "total_donors": total_donors,
                "average_donation": avg_donation
            }
        
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
            "transcription": transcribed_text,
            "query_type": query_type,
            "data": data,
            "response_text": response_text,
            "audio_url": audio_url
        })
        
    except Exception as e:
        logger.error(f"Analytics voice query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if db:
            db.close()
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


def _classify_analytics_query(text: str) -> str:
    """Classify the type of analytics query"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["last", "this", "today", "week", "month", "year"]):
        return "temporal"
    
    if any(word in text_lower for word in ["most", "top", "compare", "best", "highest"]):
        return "comparative"
    
    if any(word in text_lower for word in ["how many", "average", "total", "count"]):
        return "metric"
    
    return "overview"


@router.post("/donate-by-voice")
async def voice_donate(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    campaign_id: Optional[int] = Form(None),
    context: Optional[str] = Form(None),  # Voice Ledger: Accept context
    user_language: Optional[str] = Form("en")  # Language preference
):
    """
    Process voice donation command with preference learning.
    Supports Amharic via AddisAI.
    
    Example: "Donate 500 shillings" or "አምስት መቶ ብር ለግስ"
    
    Lab 9 Part 3: Auto-learns payment preferences from donations
    
    Args:
        audio: Audio file
        user_id: Telegram user ID
        campaign_id: Optional campaign ID if context is known
        context: Optional donation context (amount, payment, step)
        user_language: User's language preference ('en' or 'am')
        
    Returns:
        JSON with donation intent, confirmation, and suggested defaults
    """
    temp_audio_path = None
    db = None
    
    try:
        logger.info(f"Voice donation request from user {user_id}, lang: {user_language}")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # Get user language (prefer form parameter over database)
        db = next(get_db())
        if not user_language or user_language == "en":
            user_language = get_user_language_preference(user_id) or "en"
        
        # Lab 9 Part 3: Get user preferences for suggestions
        from voice.conversation.preferences import PreferenceManager
        from database.models import User
        
        user = db.query(User).filter(User.telegram_user_id == user_id).first()
        suggested_payment = None
        suggested_amount = None
        
        if user:
            suggested_payment = PreferenceManager.get_preference(user.id, "payment_provider", db)
            suggested_amount_str = PreferenceManager.get_preference(user.id, "donation_amount", db)
            if suggested_amount_str:
                try:
                    suggested_amount = int(suggested_amount_str)
                except ValueError:
                    pass
        
        # Transcribe
        transcription_result = transcribe_audio(
            temp_audio_path,
            language=user_language,
            user_preference=user_language
        )
        
        transcribed_text = transcription_result.get("text", "")
        logger.info(f"Donation transcription: '{transcribed_text}'")
        
        # ── AI Agent (try first, fall back to legacy regex) ──
        _agent_resp = await _try_agent(transcribed_text, user_id, db, user_language)
        if _agent_resp:
            return JSONResponse(content={
                "success": True,
                "transcription": transcribed_text,
                "response_text": _agent_resp["response_text"],
                "audio_url": _agent_resp["audio_url"],
                "data": _agent_resp["data"],
                "amount": _agent_resp["data"].get("amount"),
                "campaign_id": campaign_id,
                "requires_confirmation": True,
                "response_source": "agent",
            })

        # ── Fallback: Legacy regex pipeline ──
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
            response_text = f"To confirm: You want to donate ${amount}?"
        
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
        
        # LAB 9 Part 4: Track voice donation attempt
        try:
            if user:
                session_id = str(uuid.uuid4())
                ConversationAnalytics.track_event(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    event_type="voice_donation",
                    conversation_state="miniapp_donation",
                    current_step="amount_recognized",
                    metadata={
                        "amount": amount,
                        "campaign_id": campaign_id,
                        "suggested_payment": suggested_payment,
                        "suggested_amount": suggested_amount
                    }
                )
        except Exception as analytics_error:
            logger.error(f"Analytics tracking failed: {analytics_error}")
        
        return JSONResponse(content={
            "success": True,
            "amount": amount,
            "currency": "KES",
            "campaign_id": campaign_id,
            "response_text": response_text,
            "audio_url": audio_url,
            "transcription": transcribed_text,
            "requires_confirmation": True,
            # Lab 9 Part 3: Include preference suggestions
            "suggested_payment": suggested_payment,
            "suggested_amount": suggested_amount
        })
        
    except Exception as e:
        logger.error(f"Voice donation error: {str(e)}", exc_info=True)
        
        # LAB 9 Part 4: Track error
        db_err = None
        try:
            db_err = next(get_db())
            user_record = db_err.query(User).filter(User.telegram_user_id == user_id).first()
            if user_record:
                session_id = str(uuid.uuid4())
                ConversationAnalytics.track_event(
                    db=db_err,
                    user_id=user_record.id,
                    session_id=session_id,
                    event_type="error_occurred",
                    conversation_state="miniapp_donation",
                    current_step="error",
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
        except Exception as analytics_error:
            logger.error(f"Analytics tracking failed: {analytics_error}")
        finally:
            if db_err:
                db_err.close()
        
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if db:
            db.close()
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


@router.post("/admin-query")
async def voice_admin_query(
    audio: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Process voice query for admin dashboard.
    
    Examples: "Show pending registrations", "How many NGOs approved today?"
    
    Args:
        audio: Audio file
        user_id: Telegram user ID (must have admin role)
        
    Returns:
        JSON with query results and audio response
    """
    temp_audio_path = None
    db = None
    
    try:
        logger.info(f"Admin voice query from user {user_id}")
        
        # Verify user has admin role
        db = next(get_db())
        admin_user = db.query(User).filter(
            User.telegram_user_id == str(user_id)
        ).first()
        
        if not admin_user or admin_user.role not in ('SYSTEM_ADMIN', 'super_admin', 'ngo_admin'):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # Get user language (reuse existing db session)
        user_language = get_user_language_preference(user_id) or "en"
        
        # Transcribe
        transcription_result = transcribe_audio(
            temp_audio_path,
            language=user_language,
            user_preference=user_language
        )
        
        transcribed_text = transcription_result.get("text", "")
        logger.info(f"Admin query transcription: '{transcribed_text}'")
        
        # ── AI Agent (try first, fall back to legacy keyword pipeline) ──
        _agent_resp = await _try_agent(transcribed_text, str(user_id), db, user_language)
        if _agent_resp:
            return JSONResponse(content={
                "success": True,
                "transcription": transcribed_text,
                "query_type": "agent",
                "data": _agent_resp["data"],
                "response_text": _agent_resp["response_text"],
                "audio_url": _agent_resp["audio_url"],
                "response_source": "agent",
            })

        # ── Fallback: Legacy keyword pipeline ──
        # Classify query type
        query_type = _classify_admin_query(transcribed_text)
        
        # Execute query based on type
        data = {}
        if query_type == "pending":
            # Get pending registrations count
            from database.models import PendingNGORegistration
            pending_count = db.query(PendingNGORegistration).filter(
                PendingNGORegistration.status == "PENDING"
            ).count()
            data["pending_count"] = pending_count
            
            if user_language == "am":
                response_text = f"በመጠባበቅ ላይ {pending_count} ምዝገባዎች አሉ።"
            else:
                response_text = f"There are {pending_count} pending registrations."
                
        elif query_type == "approved_today":
            # Get today's approvals
            from database.models import PendingNGORegistration
            from datetime import datetime, timedelta
            today = datetime.utcnow().date()
            approved_today = db.query(PendingNGORegistration).filter(
                PendingNGORegistration.status == "APPROVED",
                PendingNGORegistration.reviewed_at >= today
            ).count()
            data["approved_today"] = approved_today
            
            if user_language == "am":
                response_text = f"ዛሬ {approved_today} ምዝገባዎች ጸድቀዋል።"
            else:
                response_text = f"{approved_today} registrations approved today."
                
        elif query_type == "total_ngos":
            # Get total NGOs
            from database.models import NGOOrganization
            total_ngos = db.query(NGOOrganization).count()
            data["total_ngos"] = total_ngos
            
            if user_language == "am":
                response_text = f"በድምሩ {total_ngos} NGOs ተመዝግበዋል።"
            else:
                response_text = f"Total of {total_ngos} NGOs registered."
        else:
            # General overview
            from database.models import PendingNGORegistration, NGOOrganization
            
            pending = db.query(PendingNGORegistration).filter(
                PendingNGORegistration.status == "PENDING"
            ).count()
            total_ngos = db.query(NGOOrganization).count()
            
            data = {"pending": pending, "total_ngos": total_ngos}
            
            if user_language == "am":
                response_text = f"በመጠባበቅ ላይ {pending} ምዝገባዎች፣ {total_ngos} NGOs ተመዝግበዋል።"
            else:
                response_text = f"{pending} pending registrations, {total_ngos} NGOs registered."
        
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
            "transcription": transcribed_text,
            "query_type": query_type,
            "data": data,
            "response_text": response_text,
            "audio_url": audio_url
        })
        
    except Exception as e:
        logger.error(f"Admin voice query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if db:
            db.close()
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


def _classify_admin_query(text: str) -> str:
    """Classify the type of admin query"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["pending", "waiting", "unapproved"]):
        return "pending"
    
    if any(word in text_lower for word in ["approved", "today", "this day"]):
        return "approved_today"
    
    if any(word in text_lower for word in ["total", "how many ngo", "all ngo"]):
        return "total_ngos"
    
    return "overview"


@router.post("/admin-command")
async def voice_admin_command(
    audio: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Process voice command for admin actions.
    
    Examples: "Approve request 123", "Reject registration 456"
    
    Args:
        audio: Audio file
        user_id: Telegram user ID (must have admin role)
        
    Returns:
        JSON with command confirmation (requires user confirmation before execution)
    """
    temp_audio_path = None
    db = None
    
    try:
        logger.info(f"Admin voice command from user {user_id}")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
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
        logger.info(f"Admin command transcription: '{transcribed_text}'")
        
        # ── AI Agent (try first, fall back to legacy regex) ──
        _agent_resp = await _try_agent(transcribed_text, str(user_id), db, user_language)
        if _agent_resp:
            return JSONResponse(content={
                "success": True,
                "transcription": transcribed_text,
                "response_text": _agent_resp["response_text"],
                "audio_url": _agent_resp["audio_url"],
                "data": _agent_resp["data"],
                "requires_confirmation": True,
                "response_source": "agent",
            })

        # ── Fallback: Legacy regex pipeline ──
        # Parse command
        import re
        text_lower = transcribed_text.lower()
        
        action = None
        registration_id = None
        
        # Detect action
        if any(word in text_lower for word in ["approve", "accept"]):
            action = "approve"
        elif any(word in text_lower for word in ["reject", "deny", "decline"]):
            action = "reject"
        
        # Extract ID
        id_match = re.search(r'\b(\d+)\b', transcribed_text)
        if id_match:
            registration_id = int(id_match.group(1))
        
        if not action or not registration_id:
            if user_language == "am":
                response_text = "ይቅርታ፣ ትእዛዙን ሊገነዘብ አልቻለም። እባክዎ እንደገና ይሞክሩ።"
            else:
                response_text = "Sorry, I couldn't understand the command. Please try again with 'Approve request [ID]' or 'Reject request [ID]'."
            
            return JSONResponse(content={
                "success": False,
                "error": "command_not_recognized",
                "response_text": response_text,
                "transcription": transcribed_text
            })
        
        # Generate confirmation response
        if user_language == "am":
            action_text = "ለማረጋገጥ" if action == "approve" else "ለመከልከል"
            response_text = f"ምዝገባ {registration_id} {action_text} ይፈልጋሉ?"
        else:
            action_text = "approve" if action == "approve" else "reject"
            response_text = f"To confirm: You want to {action_text} registration {registration_id}?"
        
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
            "action": action,
            "registration_id": registration_id,
            "response_text": response_text,
            "audio_url": audio_url,
            "transcription": transcribed_text,
            "requires_confirmation": True
        })
        
    except Exception as e:
        logger.error(f"Admin voice command error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if db:
            db.close()
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


@router.post("/dictate-text")
async def voice_dictate_text(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    field_name: Optional[str] = Form(None)
):
    """
    Process voice dictation for text fields (NGO registration form).
    
    Simple transcription service - no complex processing.
    
    Args:
        audio: Audio file
        user_id: Telegram user ID
        field_name: Optional field name for context
        
    Returns:
        JSON with transcribed text
    """
    temp_audio_path = None
    db = None
    
    try:
        logger.info(f"Voice dictation from user {user_id} for field: {field_name}")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
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
        logger.info(f"Dictation transcription: '{transcribed_text}'")
        
        if not transcribed_text:
            if user_language == "am":
                response_text = "ይቅርታ፣ ምንም ጽሑፍ አልተረዳም። እባክዎ እንደገና ይሞክሩ።"
            else:
                response_text = "Sorry, couldn't understand. Please try again."
            
            return JSONResponse(content={
                "success": False,
                "error": "no_transcription",
                "response_text": response_text
            })
        
        # Confirmation message
        if user_language == "am":
            response_text = "ጽሑፍ ተሰርዟል።"
        else:
            response_text = "Text transcribed successfully."
        
        return JSONResponse(content={
            "success": True,
            "transcription": transcribed_text,
            "response_text": response_text,
            "field_name": field_name
        })
        
    except Exception as e:
        logger.error(f"Voice dictation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if db:
            db.close()
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


@router.post("/wizard-step")
async def voice_wizard_step(
    audio: UploadFile = File(...),
    field_name: str = Form(...),
    step_number: Optional[int] = Form(None),
    user_language: Optional[str] = Form("en")
):
    """
    Process voice input for campaign creation wizard with AI suggestions.
    Supports Amharic via AddisAI for ASR.
    
    This endpoint:
    1. Transcribes the audio (supports Amharic)
    2. Validates the input for the specific field
    3. Generates AI suggestions for improvement (title, description only)
    4. Returns transcription + suggestion
    
    Args:
        audio: Audio file from wizard
        field_name: Field being filled (title, description, category, goal, deadline)
        step_number: Current step number (1-5)
        user_language: User's language preference ('en' or 'am')
        
    Returns:
        JSON with transcription and optional AI suggestion
    """
    temp_audio_path = None
    
    try:
        logger.info(f"Voice wizard step for field: {field_name}, step: {step_number}, lang: {user_language}")
        
        # Save audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=_audio_suffix(audio)) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        # Transcribe with user's language preference
        transcription_result = transcribe_audio(
            temp_audio_path,
            language=user_language,
            user_preference=user_language
        )
        
        transcribed_text = transcription_result.get("text", "").strip()
        logger.info(f"Wizard transcription ({field_name}): '{transcribed_text}'")
        
        if not transcribed_text:
            return JSONResponse(content={
                "success": False,
                "error": "no_transcription",
                "transcription": "",
                "suggestion": None
            })
        
        # Generate AI suggestions based on field
        suggestion = None
        
        if field_name == "title":
            # Check title length and quality
            if len(transcribed_text) > 60:
                suggestion = f"Consider shortening: \"{transcribed_text[:50]}...\""
            elif len(transcribed_text.split()) < 3:
                suggestion = "Add more detail to make the title clearer (e.g., 'Clean Water for Rural Schools in Addis')"
            elif not any(char.isupper() for char in transcribed_text):
                # Suggest title case
                suggestion = transcribed_text.title()
        
        elif field_name == "description":
            word_count = len(transcribed_text.split())
            if word_count < 20:
                suggestion = "Add more details: What problem are you solving? Who will benefit? What's your plan?"
            elif word_count > 200:
                suggestion = "Consider breaking this into paragraphs for better readability"
            
            # Check for key elements
            has_problem = any(word in transcribed_text.lower() for word in ['need', 'problem', 'lack', 'challenge'])
            has_solution = any(word in transcribed_text.lower() for word in ['will', 'plan', 'build', 'provide', 'create'])
            has_beneficiaries = any(word in transcribed_text.lower() for word in ['people', 'students', 'families', 'children', 'community'])
            
            if not (has_problem and has_solution):
                suggestion = "Try including: 1) What problem you're solving, 2) Your solution, 3) Who benefits"
        
        elif field_name == "goal":
            # Parse amount
            import re
            numbers = re.findall(r'\d+', transcribed_text)
            if numbers:
                amount = int(''.join(numbers))
                if amount < 1000:
                    suggestion = "This seems quite low. Consider if this is enough to achieve your goal."
                elif amount > 1000000:
                    suggestion = "This is a very large goal. Consider breaking it into phases."
        
        elif field_name == "category":
            # No suggestions needed - will be matched on frontend
            pass
        
        elif field_name == "deadline":
            # Parse date mentions
            if any(word in transcribed_text.lower() for word in ['tomorrow', 'next week', 'few days']):
                suggestion = "Most successful campaigns run for 30-60 days. Consider a longer timeline."
        
        # Generate TTS confirmation (dual delivery like Telegram bot)
        confirmation_text = f"I heard: {transcribed_text}"
        if suggestion:
            confirmation_text += f". {suggestion}"
        
        success_tts, audio_path, error_tts = await tts_provider.text_to_speech(
            text=confirmation_text,
            language=user_language
        )
        
        audio_url = None
        if success_tts and audio_path:
            audio_filename = os.path.basename(audio_path)
            audio_url = f"/tts_cache/{audio_filename}"
        
        return JSONResponse(content={
            "success": True,
            "transcription": transcribed_text,
            "suggestion": suggestion,
            "field_name": field_name,
            "audio_url": audio_url
        })
        
    except Exception as e:
        logger.error(f"Voice wizard error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "transcription": "",
                "suggestion": None
            }
        )
        
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class LanguagePreferenceRequest(BaseModel):
    user_id: str
    language: str


@router.post("/set-language")
async def set_language_preference(request: LanguagePreferenceRequest):
    """
    Save user's language preference to database.
    Called when user toggles language in miniapp.
    
    Args:
        request: LanguagePreferenceRequest with user_id and language
        
    Returns:
        JSON confirmation
    """
    db = None
    try:
        db = next(get_db())
        
        # Find or create user
        user = db.query(User).filter(User.telegram_user_id == request.user_id).first()
        
        if user:
            user.language_preference = request.language
            db.commit()
            logger.info(f"Updated language preference for user {request.user_id}: {request.language}")
        else:
            # Anonymous user - can't save to database, localStorage only
            logger.info(f"Anonymous user {request.user_id} language preference: {request.language} (localStorage only)")
        
        return JSONResponse(content={
            "success": True,
            "language": request.language,
            "saved_to_db": user is not None
        })
        
    except Exception as e:
        logger.error(f"Failed to save language preference: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
    finally:
        if db:
            db.close()


@router.post("/tts")
async def text_to_speech_miniapp(request: TTSRequest):
    """
    Generate TTS audio for miniapps (supports Amharic via AddisAI).
    
    Args:
        request: TTSRequest with text and language
        
    Returns:
        JSON with audio_url
    """
    try:
        logger.info(f"TTS request: lang={request.language}, text='{request.text[:50]}...'")
        
        # Generate TTS using TTSProvider (handles AddisAI for Amharic)
        success, audio_path, error = await tts_provider.text_to_speech(
            text=request.text,
            language=request.language
        )
        
        if not success or not audio_path:
            raise HTTPException(status_code=500, detail=error or "TTS generation failed")
        
        # Return URL to audio file
        audio_filename = os.path.basename(audio_path)
        audio_url = f"/tts_cache/{audio_filename}"
        
        return JSONResponse(content={
            "success": True,
            "audio_url": audio_url,
            "language": request.language
        })
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
