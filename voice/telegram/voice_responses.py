"""
Voice Response Dual Delivery Module

Implements the TrustVoice dual delivery pattern:
1. Send text immediately (0ms perceived latency)
2. Generate and send voice in background (~2-3s)

This ensures instant feedback for literate users while maintaining
accessibility for illiterate users through voice responses.

Key Features:
- Non-blocking async TTS generation
- Preference-first language routing (user preference > text detection)
- Message threading (voice replies to text)
- Graceful error handling (TTS failure doesn't break UX)
- Text cleaning for natural TTS output
"""

import asyncio
import logging
import re
import os
from typing import Optional
from pathlib import Path

from telegram import Bot, Update
# Database imports moved to function level to avoid import-time dependency

logger = logging.getLogger(__name__)

# Import TTS provider
from voice.tts.tts_provider import tts_provider


def detect_language(text: str) -> str:
    """
    Detect language from text using Unicode character ranges.
    
    Used as fallback when user preference is not available.
    
    Args:
        text: Text to analyze
        
    Returns:
        'am' for Amharic, 'en' for English (default)
    """
    if not text:
        return "en"
    
    # Count Amharic characters (Unicode range U+1200 to U+137F)
    amharic_chars = sum(1 for char in text if '\u1200' <= char <= '\u137F')
    
    # If >30% of characters are Amharic, classify as Amharic
    if amharic_chars > len(text) * 0.3:
        return "am"
    
    return "en"  # Default to English


def clean_text_for_tts(text: str) -> str:
    """
    Clean text for natural TTS synthesis.
    
    Removes HTML tags, Markdown formatting, URLs, and normalizes whitespace
    to make text sound natural when read aloud.
    
    Args:
        text: Raw text with formatting
        
    Returns:
        Cleaned text suitable for TTS
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove Markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove Markdown links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remove inline code markers
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def get_user_language_preference(telegram_user_id: str) -> Optional[str]:
    """
    Get user's preferred language from database.
    
    This is the source of truth for language routing to ensure
    consistent experience across STT and TTS.
    
    Args:
        telegram_user_id: Telegram user ID
        
    Returns:
        Language code ('en', 'am') or None if not set
    """
    try:
        from database.db import SessionLocal
        from database.models import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.telegram_user_id == telegram_user_id
            ).first()
            
            if user and user.preferred_language:
                return user.preferred_language
            
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not retrieve user language preference: {e}")
        return None


async def _generate_and_send_voice_background(
    bot: Bot,
    chat_id: int,
    text: str,
    language: Optional[str],
    reply_to_message_id: int,
    user_preference_language: Optional[str]
) -> None:
    """
    Background task to generate and send voice message.
    
    This runs asynchronously without blocking the main bot response.
    Failures are logged but don't affect the user experience (text already sent).
    
    Args:
        bot: Telegram Bot instance
        chat_id: Chat ID to send voice to
        text: Text to convert to speech
        language: Explicit language override (optional)
        reply_to_message_id: Message ID to reply to (threading)
        user_preference_language: User's preferred language from DB
    """
    try:
        logger.info(f"🎬 Starting background TTS for chat {chat_id}")
        logger.info(f"📋 Task received: text_len={len(text)}, lang={language}, pref={user_preference_language}")
        
        # Step 1: Clean text for TTS
        clean_text = clean_text_for_tts(text)
        
        if not clean_text or len(clean_text) < 3:
            logger.warning(f"Text too short for TTS after cleaning: '{text}'")
            return
        
        # Step 2: Determine language (priority: explicit > user preference > text detection)
        if language is None:
            if user_preference_language:
                language = user_preference_language
                logger.info(f"Using user preference: {language}")
            else:
                language = detect_language(clean_text)
                logger.info(f"Using text detection: {language}")
        else:
            logger.info(f"Using explicit language: {language}")
        
        # Step 3: Generate TTS audio
        logger.info(f"🎤 Generating TTS: {len(clean_text)} chars, lang: {language}")
        
        success, audio_path, error = await tts_provider.text_to_speech(
            clean_text,
            language=language
        )
        
        if not success or not audio_path:
            logger.warning(f"TTS generation failed: {error}")
            logger.error(f"❌ TTS FAILED - success={success}, path={audio_path}, error={error}")
            return
        
        logger.info(f"✅ TTS file generated: {audio_path}")
        
        # Step 4: Send voice message (threaded to original text)
        audio_file = Path(audio_path)
        if not audio_file.exists():
            logger.error(f"TTS audio file not found: {audio_path}")
            return
        
        with open(audio_file, 'rb') as f:
            await bot.send_voice(
                chat_id=chat_id,
                voice=f,
                reply_to_message_id=reply_to_message_id,
                caption="🎤 Voice version"
            )
        
        logger.info(f"✅ Voice reply sent: {len(clean_text)} chars, lang: {language}")
        
    except Exception as e:
        # Background task failure - log but don't crash
        logger.warning(f"Background TTS task failed (non-critical): {str(e)}")


async def send_voice_reply(
    bot: Bot,
    chat_id: int,
    message: str,
    parse_mode: str = "HTML",
    language: Optional[str] = None,
    send_voice: bool = True,
    reply_to_message_id: Optional[int] = None
):
    """
    Send dual delivery response (text immediately + voice in background).
    
    This is the main API for dual delivery. Text is sent instantly for
    immediate feedback, then voice is generated asynchronously without
    blocking.
    
    Args:
        bot: Telegram Bot instance
        chat_id: Chat ID to send to
        message: Message text (with formatting)
        parse_mode: Telegram parse mode (HTML/Markdown)
        language: Language override (optional, uses user preference if None)
        send_voice: Whether to send voice (can disable for testing)
        reply_to_message_id: Optional message to reply to
    
    Returns:
        The text message object sent (for testing/verification)
    """
    # Step 1: Send text immediately (0ms latency)
    text_msg = await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=parse_mode,
        reply_to_message_id=reply_to_message_id
    )
    
    logger.info(f"✅ Text sent: {len(message)} chars to chat {chat_id}")
    
    # Step 2: Look up user preference and spawn background TTS task
    if send_voice:
        # Look up user preference from database (only if language not explicitly provided)
        user_preference_language = None if language else get_user_language_preference(str(chat_id))
        
        # Callback to log background task exceptions
        def log_task_exception(task):
            """Log exceptions from background TTS tasks"""
            try:
                task.result()
            except Exception as e:
                logger.error(f"Background TTS task failed: {e}", exc_info=True)
        
        # Spawn background task (returns immediately)
        task = asyncio.create_task(
            _generate_and_send_voice_background(
                bot=bot,
                chat_id=chat_id,
                text=message,
                language=language,
                reply_to_message_id=text_msg.message_id,
                user_preference_language=user_preference_language
            )
        )
        # Add exception handler to prevent silent failures
        task.add_done_callback(log_task_exception)
        # ↑ Function returns here immediately (non-blocking)
    
    # Return text message for verification/testing
    return text_msg


async def send_voice_reply_from_update(
    update: Update,
    text: str,
    language: Optional[str] = None,
    parse_mode: str = "HTML",
    send_voice: bool = True
) -> None:
    """
    Convenience wrapper for sending dual delivery from Update object.
    
    Extracts bot and chat_id from update and calls send_voice_reply.
    
    Args:
        update: Telegram Update object
        text: Message text
        language: Language override (optional)
        parse_mode: Telegram parse mode
        send_voice: Whether to send voice
    """
    await send_voice_reply(
        bot=update.get_bot(),
        chat_id=update.effective_chat.id,
        message=text,
        parse_mode=parse_mode,
        language=language,
        send_voice=send_voice
    )


# Backward compatibility: Keep the old function signature but use new implementation
async def send_voice_reply_legacy(
    update: Update,
    text: str,
    language: str = "en",
    parse_mode: str = "HTML"
) -> None:
    """
    Legacy function signature for backward compatibility.
    
    Redirects to new implementation with non-blocking TTS.
    
    Args:
        update: Telegram update object
        text: Message text to send
        language: Language code for TTS
        parse_mode: Telegram parse mode
    """
    await send_voice_reply_from_update(
        update=update,
        text=text,
        language=language,
        parse_mode=parse_mode,
        send_voice=True
    )
