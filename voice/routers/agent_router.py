"""
TrustVoice Agent — FastAPI Router

Unified AI Agent endpoint that replaces the seven separate miniapp
voice endpoints with a single intelligent entry point.

Endpoints:
    POST /voice/agent       — voice input  (audio file → ASR → agent)
    POST /voice/agent/text  — text input   (JSON body  → agent)

Both call the same AgentExecutor and return the same response shape:
    {
        "success": true,
        "conversation_id": "uuid",
        "transcription": "find education campaigns",   // voice only
        "response_text": "I found 3 campaigns...",
        "audio_url": "/api/voice/audio/abc.mp3",       // if TTS succeeds
        "data": { ... },                                // structured tool data
        "tools_used": ["search_campaigns"]
    }

Fallback: if the agent errors, the old NLU → command_router pipeline
is attempted so the user always gets a response.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database.db import get_db
from voice.agent.executor import AgentExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["agent"])

# Singleton agent executor
_agent = AgentExecutor()


# ── Helpers ─────────────────────────────────────────────────────

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
    if upload.filename:
        ext = Path(upload.filename).suffix.lower()
        if ext in (
            ".mp4", ".m4a", ".ogg", ".wav", ".mp3",
            ".flac", ".webm", ".oga", ".mpga",
        ):
            return ext
    return ".webm"


async def _generate_tts(text: str, language: str = "en"):
    """Generate TTS audio and return the URL (or None)."""
    try:
        from voice.tts.tts_provider import TTSProvider
        from voice.telegram.voice_responses import clean_text_for_tts

        tts = TTSProvider()
        clean = clean_text_for_tts(text)
        success, audio_path, _err = await tts.text_to_speech(
            clean, language=language
        )
        if success and audio_path:
            return f"/api/voice/audio/{Path(audio_path).name}"
    except Exception as e:
        logger.warning(f"TTS generation failed: {e}")
    return None


async def _run_agent_with_fallback(
    user_message: str,
    user_id: str,
    db,
    language: str = "en",
    conversation_id: Optional[str] = None,
    context: Optional[dict] = None,
) -> dict:
    """
    Try the agent first.  If it fails, fall back to NLU → command_router.
    """
    agent_error_detail = None
    try:
        result = await _agent.run(
            user_message=user_message,
            user_id=user_id,
            db=db,
            language=language,
            conversation_id=conversation_id,
            context=context,
        )
        result["response_source"] = "agent"
        return result
    except Exception as agent_err:
        agent_error_detail = f"{type(agent_err).__name__}: {agent_err}"
        logger.error(
            f"Agent failed, falling back to NLU pipeline: {agent_err}",
            exc_info=True,
        )

    # ── Fallback: old NLU → command_router ──────────────────────
    try:
        from voice.nlu.nlu_infer import extract_intent_and_entities
        from voice.command_router import route_command

        nlu_result = extract_intent_and_entities(
            transcript=user_message,
            language=language,
        )
        route_result = await route_command(
            intent=nlu_result.get("intent", "unknown"),
            entities=nlu_result.get("entities", {}),
            user_id=user_id,
            db=db,
            conversation_context={"transcript": user_message, "language": language},
        )
        return {
            "conversation_id": conversation_id or "",
            "response_text": route_result.get("message", ""),
            "data": route_result.get("data", {}),
            "tools_used": ["fallback_nlu"],
            "response_source": "fallback_nlu",
            "agent_error": agent_error_detail,
        }
    except Exception as fallback_err:
        logger.error(f"Fallback pipeline also failed: {fallback_err}", exc_info=True)
        return {
            "conversation_id": conversation_id or "",
            "response_text": (
                "Sorry, I'm having trouble processing your request. "
                "Please try again."
            ),
            "data": {},
            "tools_used": [],
            "response_source": "fallback_failed",
            "agent_error": agent_error_detail,
            "fallback_error": f"{type(fallback_err).__name__}: {fallback_err}",
        }


# ── Voice endpoint ──────────────────────────────────────────────

@router.post("/agent")
async def voice_agent(
    audio: UploadFile = File(...),
    user_id: str = Form("web_anonymous"),
    user_language: Optional[str] = Form("en"),
    conversation_id: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
):
    """
    AI Agent endpoint with **voice** input.

    1. Transcribe audio via ASR
    2. Run the agent on the transcript
    3. Generate TTS of the response
    4. Return text + audio + structured data
    """
    temp_path = None
    db = None

    try:
        # ── Parse context ───────────────────────────────────────
        ctx = None
        if context:
            try:
                ctx = json.loads(context)
            except json.JSONDecodeError:
                pass

        language = user_language or "en"

        # ── Save & transcribe audio ─────────────────────────────
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=_audio_suffix(audio)
        ) as tmp:
            content = await audio.read()
            tmp.write(content)
            temp_path = tmp.name

        from voice.asr.asr_infer import transcribe_audio

        asr_result = transcribe_audio(
            temp_path, language=language, user_preference=language
        )
        transcript = asr_result.get("text", "")
        detected_lang = asr_result.get("language", language)

        if not transcript.strip():
            return JSONResponse(content={
                "success": False,
                "error": "no_speech",
                "response_text": (
                    "ምንም ድምጽ አልተገነዘበም።" if language == "am"
                    else "No speech detected. Please try again."
                ),
            })

        # ── Run agent ───────────────────────────────────────────
        db = next(get_db())
        result = await _run_agent_with_fallback(
            user_message=transcript,
            user_id=user_id,
            db=db,
            language=detected_lang,
            conversation_id=conversation_id,
            context=ctx,
        )

        # ── TTS ─────────────────────────────────────────────────
        audio_url = await _generate_tts(
            result["response_text"], language=detected_lang
        )

        return JSONResponse(content={
            "success": True,
            "conversation_id": result["conversation_id"],
            "transcription": transcript,
            "language": detected_lang,
            "response_text": result["response_text"],
            "audio_url": audio_url,
            "data": result.get("data", {}),
            "tools_used": result.get("tools_used", []),
            "response_source": result.get("response_source", "agent"),
            "agent_error": result.get("agent_error"),
            "fallback_error": result.get("fallback_error"),
        })

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Voice agent error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if db:
            db.close()
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ── Text endpoint ───────────────────────────────────────────────

class TextAgentRequest(BaseModel):
    text: str
    user_id: str = "web_anonymous"
    user_language: str = "en"
    conversation_id: Optional[str] = None
    context: Optional[str] = None


@router.post("/agent/text")
async def text_agent(request: TextAgentRequest):
    """
    AI Agent endpoint with **text** input.

    Skips ASR — sends text directly to the agent.
    Useful for the web chat interface and testing.
    """
    db = None
    try:
        ctx = None
        if request.context:
            try:
                ctx = json.loads(request.context)
            except json.JSONDecodeError:
                pass

        db = next(get_db())
        result = await _run_agent_with_fallback(
            user_message=request.text,
            user_id=request.user_id,
            db=db,
            language=request.user_language,
            conversation_id=request.conversation_id,
            context=ctx,
        )

        # Generate TTS for text input too (optional, for accessibility)
        audio_url = await _generate_tts(
            result["response_text"], language=request.user_language
        )

        return JSONResponse(content={
            "success": True,
            "conversation_id": result["conversation_id"],
            "response_text": result["response_text"],
            "audio_url": audio_url,
            "data": result.get("data", {}),
            "tools_used": result.get("tools_used", []),
            "response_source": result.get("response_source", "agent"),
            "agent_error": result.get("agent_error"),
            "fallback_error": result.get("fallback_error"),
        })

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Text agent error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if db:
            db.close()
