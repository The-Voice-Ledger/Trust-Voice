"""
Text-to-Speech (TTS) Provider - Module 8 of Lab 5

Converts bot text responses to voice messages for accessibility.
Supports multiple languages using different TTS providers:
- English: OpenAI TTS (high quality)
- Amharic: AddisAI TTS (local language support)

This makes TrustVoice accessible to non-literate users who can only interact via voice.
"""

import logging
import os
import hashlib
from typing import Optional, Tuple
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

# TTS audio cache directory
TTS_CACHE_DIR = Path("voice/tts_cache")
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TTSProvider:
    """Text-to-Speech provider supporting multiple languages and engines"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.addisai_api_key = os.getenv("ADDIS_AI_API_KEY")
        self.addisai_base_url = os.getenv("ADDIS_AI_BASE_URL", "https://api.addisassistant.com/api")
        self.addisai_tts_endpoint = os.getenv("ADDIS_AI_TTS_ENDPOINT", "/v1/audio")
        self.addisai_tts_url = f"{self.addisai_base_url}{self.addisai_tts_endpoint}"
        self.cache_enabled = True
        
    def _get_cache_path(self, text: str, language: str, voice: str) -> Path:
        """Generate cache file path based on text hash"""
        text_hash = hashlib.md5(f"{text}_{language}_{voice}".encode()).hexdigest()
        return TTS_CACHE_DIR / f"{text_hash}.mp3"
    
    async def text_to_speech(
        self, 
        text: str, 
        language: str = "en",
        voice: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convert text to speech audio file.
        
        Args:
            text: Text to convert to speech
            language: Language code ("en", "am")
            voice: Optional specific voice to use
            
        Returns:
            (success, audio_file_path, error_message)
        """
        try:
            # Truncate very long text (TTS has limits)
            max_chars = 1000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
                logger.warning(f"Text truncated to {max_chars} chars for TTS")
            
            # Set default voice based on language
            if not voice:
                if language == "am":
                    voice = "amharic_female"  # AddisAI default
                else:
                    voice = "nova"  # OpenAI default (warm, engaging)
            
            # Check cache first
            cache_path = self._get_cache_path(text, language, voice)
            if self.cache_enabled and cache_path.exists():
                logger.info(f"TTS cache hit: {cache_path}")
                return True, str(cache_path), None
            
            # Route to appropriate TTS engine
            if language == "am":
                success, audio_path, error = await self._addisai_tts(text, voice)
            else:
                success, audio_path, error = await self._openai_tts(text, voice)
            
            if success and audio_path:
                # Save to cache
                if self.cache_enabled and audio_path != str(cache_path):
                    import shutil
                    shutil.copy(audio_path, cache_path)
                    audio_path = str(cache_path)
                
                logger.info(f"TTS generated: {audio_path}")
                return True, audio_path, None
            else:
                return False, None, error
                
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            return False, None, f"TTS failed: {str(e)}"
    
    async def _openai_tts(self, text: str, voice: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate speech using OpenAI TTS API.
        
        Voices: alloy, echo, fable, onyx, nova, shimmer
        Best for engagement: nova (warm), shimmer (bright)
        """
        if not self.openai_api_key:
            return False, None, "OpenAI API key not configured"
        
        try:
            from openai import AsyncOpenAI
            # Add timeout to prevent hanging indefinitely
            client = AsyncOpenAI(
                api_key=self.openai_api_key,
                timeout=httpx.Timeout(30.0, connect=5.0)
            )
            
            # Generate unique filename
            filename = f"tts_openai_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            output_path = TTS_CACHE_DIR / filename
            
            # Call OpenAI TTS API - EXACTLY as in Voice Ledger guide
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Get audio bytes from response.content (synchronous property)
            audio_bytes = response.content
            
            # Write to file
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            
            return True, str(output_path), None
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {str(e)}")
            return False, None, f"OpenAI TTS failed: {str(e)}"
    
    async def _addisai_tts(self, text: str, voice: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate speech using AddisAI TTS API for Amharic.
        """
        if not self.addisai_api_key or not self.addisai_tts_url:
            logger.warning("AddisAI TTS not configured, using OpenAI for Amharic (English voice)")
            return await self._openai_tts(text, "nova")
        
        try:
            # Generate unique filename
            filename = f"tts_addisai_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            output_path = TTS_CACHE_DIR / filename
            
            # Call AddisAI TTS API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.addisai_tts_url,
                    headers={
                        "X-API-Key": self.addisai_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "language": "am"
                    }
                )
                
                if response.status_code == 200:
                    # AddisAI returns base64-encoded audio in JSON
                    import base64
                    response_data = response.json()
                    
                    if "audio" in response_data:
                        # Decode base64 audio
                        audio_bytes = base64.b64decode(response_data["audio"])
                        
                        # Save audio to file
                        with open(output_path, "wb") as f:
                            f.write(audio_bytes)
                        
                        logger.info(f"✅ AddisAI TTS generated: {output_path}")
                        return True, str(output_path), None
                    else:
                        error = "AddisAI TTS response missing 'audio' field"
                        logger.error(error)
                        logger.warning("Falling back to OpenAI for Amharic")
                        return await self._openai_tts(text, "nova")
                else:
                    error = f"AddisAI TTS failed: {response.status_code} - {response.text}"
                    logger.error(error)
                    # Fallback to OpenAI
                    logger.warning("Falling back to OpenAI for Amharic")
                    return await self._openai_tts(text, "nova")
                    
        except httpx.TimeoutException:
            logger.error("AddisAI TTS timeout")
            return await self._openai_tts(text, "nova")
        except Exception as e:
            logger.error(f"AddisAI TTS error: {str(e)}")
            return await self._openai_tts(text, "nova")
    
    def clear_cache(self, older_than_days: int = 7):
        """Clear TTS cache files older than specified days"""
        import time
        from datetime import datetime, timedelta
        
        cutoff = time.time() - (older_than_days * 86400)
        deleted_count = 0
        
        for cache_file in TTS_CACHE_DIR.glob("*.mp3"):
            if cache_file.stat().st_mtime < cutoff:
                cache_file.unlink()
                deleted_count += 1
        
        logger.info(f"Cleared {deleted_count} TTS cache files older than {older_than_days} days")
        return deleted_count


# Global TTS provider instance
tts_provider = TTSProvider()


async def generate_voice_response(
    text: str,
    language: str = "en",
    enable_tts: bool = True
) -> Optional[str]:
    """
    Generate voice response from text.
    
    Args:
        text: Response text to convert to speech
        language: Language code ("en", "am")
        enable_tts: Whether to enable TTS (can be disabled for testing)
        
    Returns:
        Path to audio file or None if TTS disabled/failed
    """
    if not enable_tts:
        return None
    
    # Strip HTML tags for TTS (Telegram formatting)
    import re
    text_clean = re.sub(r'<[^>]+>', '', text)
    
    # Remove markdown formatting
    text_clean = text_clean.replace('**', '').replace('*', '')
    
    # Limit length for TTS
    if len(text_clean) > 1000:
        text_clean = text_clean[:1000] + "..."
    
    success, audio_path, error = await tts_provider.text_to_speech(
        text_clean,
        language=language
    )
    
    if success:
        return audio_path
    else:
        logger.warning(f"TTS generation failed: {error}")
        return None


# Example usage for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_tts():
        print("🎤 Testing TTS Provider\n")
        
        # Test English
        print("Testing English (OpenAI)...")
        success, path, error = await tts_provider.text_to_speech(
            "Thank you for your donation! Your support helps build clean water wells in Tanzania.",
            language="en",
            voice="nova"
        )
        print(f"English: {'✅' if success else '❌'} {path or error}\n")
        
        # Test Amharic
        print("Testing Amharic (AddisAI)...")
        success, path, error = await tts_provider.text_to_speech(
            "እንኳን ደህና መጡ። ለልገሳዎ እናመሰግናለን።",
            language="am"
        )
        print(f"Amharic: {'✅' if success else '❌'} {path or error}\n")
        
        # Test cache
        print("Testing cache...")
        success, path, error = await tts_provider.text_to_speech(
            "Thank you for your donation! Your support helps build clean water wells in Tanzania.",
            language="en",
            voice="nova"
        )
        print(f"Cache: {'✅' if success else '❌'} {path or error}")
    
    asyncio.run(test_tts())
