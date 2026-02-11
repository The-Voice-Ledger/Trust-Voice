"""
AddisAI Provider for Amharic Voice Processing
Implements Speech-to-Text and Text-to-Speech using AddisAI API
"""
import asyncio
import os
import json
import httpx
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 1  # One retry (total 2 attempts)
RETRY_DELAY_SECONDS = 2.0
# HTTP status codes worth retrying (server errors, rate limits)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AddisAIError(Exception):
    """Exception raised for AddisAI API errors"""
    pass


class AddisAIProvider:
    """
    AddisAI API client for Amharic voice processing.
    
    Endpoints:
    - POST /api/v1/audio/transcribe - Speech-to-Text (STT)
    - POST /api/v1/audio/speech - Text-to-Speech (TTS)
    - POST /api/v1/chat_generate - Conversational AI
    """
    
    def __init__(self):
        """Initialize AddisAI provider with credentials from environment"""
        self.api_key = os.getenv("ADDIS_AI_API_KEY")
        if not self.api_key:
            raise ValueError("ADDIS_AI_API_KEY not set in environment")
        
        # Base URL - configurable endpoints
        self.base_url = os.getenv("ADDIS_AI_BASE_URL", "https://api.addisassistant.com/api")
        # AddisAI uses chat_generate with audio input for STT (no separate STT endpoint)
        self.stt_endpoint = os.getenv("ADDIS_AI_STT_ENDPOINT", "/v1/chat_generate")
        self.tts_endpoint = os.getenv("ADDIS_AI_TTS_ENDPOINT", "/v1/audio/speech")
        self.chat_endpoint = os.getenv("ADDIS_AI_CHAT_ENDPOINT", "/v1/chat_generate")
        
        self.timeout = 30.0  # 30 seconds timeout
        logger.info(f"AddisAI provider initialized")
        logger.info(f"  - Base URL: {self.base_url}")
        logger.info(f"  - STT: {self.stt_endpoint}")
    
    async def transcribe(
        self, 
        audio_path: str, 
        language: str = "am"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text using AddisAI STT.
        
        Args:
            audio_path: Path to audio file
            language: 'am' (Amharic) or 'om' (Afan Oromo)
            
        Returns:
            {
                "text": "transcribed text",
                "language": "am",
                "confidence": 0.95,
                "duration": 3.5
            }
            
        Raises:
            AddisAIError: If API call fails
        """
        logger.info(f"AddisAI transcription request - Language: {language}, File: {audio_path}")
        
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Verify file exists
                if not os.path.exists(audio_path):
                    raise AddisAIError(f"Audio file not found: {audio_path}")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Open file and prepare multipart upload
                    with open(audio_path, 'rb') as audio_file:
                        request_data = {
                            "target_language": language,
                            "generation_config": {
                                "temperature": 0.7
                            }
                        }
                        
                        files = {
                            "chat_audio_input": (Path(audio_path).name, audio_file, "audio/wav"),
                            "request_data": (None, json.dumps(request_data), "application/json")
                        }
                        
                        stt_url = f"{self.base_url}{self.stt_endpoint}"
                        if attempt > 0:
                            logger.info(f"Retrying AddisAI STT (attempt {attempt + 1}): {stt_url}")
                        else:
                            logger.info(f"Calling AddisAI STT: {stt_url}")
                        
                        response = await client.post(
                            stt_url,
                            headers={"X-API-Key": self.api_key},
                            files=files
                        )
                        
                        # Check for retryable errors
                        if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                            logger.warning(f"AddisAI STT returned {response.status_code}, retrying in {RETRY_DELAY_SECONDS}s...")
                            await asyncio.sleep(RETRY_DELAY_SECONDS)
                            continue
                        
                        # Check for non-retryable errors
                        if response.status_code != 200:
                            error_msg = f"AddisAI API error: {response.status_code} - {response.text}"
                            logger.error(error_msg)
                            raise AddisAIError(error_msg)
                        
                        result = response.json()
                        
                        # Extract transcription from response
                        data = result.get("data", result)
                        transcript = data.get("transcription_clean", data.get("text", ""))
                        
                        # Remove markdown code blocks if present
                        transcript = transcript.strip()
                        if transcript.startswith("```"):
                            lines = transcript.split('\n')
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].strip() == "```":
                                lines = lines[:-1]
                            transcript = '\n'.join(lines).strip()
                        
                        logger.info(f"AddisAI transcription successful: {len(transcript)} chars")
                        
                        return {
                            "text": transcript,
                            "language": language,
                            "confidence": data.get("confidence", 0.95),
                            "duration": data.get("duration", 0),
                            "provider": "addisai",
                            "raw_response": result
                        }
            
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    logger.warning(f"AddisAI STT {type(e).__name__}, retrying in {RETRY_DELAY_SECONDS}s...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    continue
                error_msg = f"AddisAI API {'timeout' if isinstance(e, httpx.TimeoutException) else 'connection error'} after {MAX_RETRIES + 1} attempts"
                logger.error(error_msg)
                raise AddisAIError(error_msg) from e
            
            except AddisAIError:
                raise
            
            except Exception as e:
                error_msg = f"AddisAI transcription failed: {str(e)}"
                logger.error(error_msg)
                raise AddisAIError(error_msg) from e
        
        # Should not reach here, but just in case
        raise AddisAIError(f"AddisAI transcription failed after {MAX_RETRIES + 1} attempts") from last_error
    
    async def text_to_speech(
        self, 
        text: str, 
        language: str = "am",
        voice_id: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using AddisAI TTS.
        
        Args:
            text: Text to convert
            language: 'am' (Amharic) or 'om' (Afan Oromo)
            voice_id: Voice ID (default: system default)
            
        Returns:
            Audio bytes (WAV format)
            
        Raises:
            AddisAIError: If API call fails
        """
        logger.info(f"AddisAI TTS request - Language: {language}, Text length: {len(text)}")
        
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    tts_url = f"{self.base_url}/audio/speech"
                    
                    payload = {
                        "text": text,
                        "language": language
                    }
                    
                    if voice_id:
                        payload["voice_id"] = voice_id
                    
                    if attempt > 0:
                        logger.info(f"Retrying AddisAI TTS (attempt {attempt + 1})")
                    
                    response = await client.post(
                        tts_url,
                        headers={
                            "X-API-Key": self.api_key,
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )
                    
                    # Check for retryable errors
                    if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                        logger.warning(f"AddisAI TTS returned {response.status_code}, retrying in {RETRY_DELAY_SECONDS}s...")
                        await asyncio.sleep(RETRY_DELAY_SECONDS)
                        continue
                    
                    if response.status_code != 200:
                        error_msg = f"AddisAI TTS error: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        raise AddisAIError(error_msg)
                    
                    logger.info(f"AddisAI TTS successful: {len(response.content)} bytes")
                    return response.content
            
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    logger.warning(f"AddisAI TTS {type(e).__name__}, retrying in {RETRY_DELAY_SECONDS}s...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    continue
                error_msg = f"AddisAI TTS {'timeout' if isinstance(e, httpx.TimeoutException) else 'connection error'} after {MAX_RETRIES + 1} attempts"
                logger.error(error_msg)
                raise AddisAIError(error_msg) from e
            
            except AddisAIError:
                raise
            
            except Exception as e:
                error_msg = f"AddisAI TTS failed: {str(e)}"
                logger.error(error_msg)
                raise AddisAIError(error_msg) from e
        
        raise AddisAIError(f"AddisAI TTS failed after {MAX_RETRIES + 1} attempts") from last_error
    
    async def chat_completion(
        self,
        message: str,
        conversation_history: Optional[list] = None,
        language: str = "am"
    ) -> str:
        """
        Get conversational AI response using AddisAI.
        
        Args:
            message: User message
            conversation_history: Previous messages
            language: 'am' (Amharic) or 'om' (Afan Oromo)
            
        Returns:
            AI response text
            
        Raises:
            AddisAIError: If API call fails
        """
        logger.info(f"AddisAI chat request - Language: {language}")
        
        try:
            # Use the full chat_generate URL from env
            chat_url = os.getenv("ADDIS_AI_URL", "https://api.addisassistant.com/api/v1/chat_generate")
            
            messages = conversation_history or []
            messages.append({"role": "user", "content": message})
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    chat_url,
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": messages,
                        "language": language
                    }
                )
                
                if response.status_code != 200:
                    error_msg = f"AddisAI chat error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise AddisAIError(error_msg)
                
                result = response.json()
                return result.get("response", result.get("message", ""))
        
        except Exception as e:
            error_msg = f"AddisAI chat failed: {str(e)}"
            logger.error(error_msg)
            raise AddisAIError(error_msg) from e


# Singleton instance
_addisai_provider: Optional[AddisAIProvider] = None

def get_addisai_provider() -> AddisAIProvider:
    """Get or create singleton AddisAI provider instance"""
    global _addisai_provider
    if _addisai_provider is None:
        _addisai_provider = AddisAIProvider()
    return _addisai_provider


def transcribe_sync(audio_path: str, language: str = "am") -> Dict[str, Any]:
    """
    Synchronous wrapper for AddisAI transcription.
    Uses asyncio.run() for clean event loop management.
    
    Args:
        audio_path: Path to audio file
        language: Language code ('am' or 'om')
        
    Returns:
        Transcription result dictionary
    """
    import asyncio
    
    provider = get_addisai_provider()
    
    # Use asyncio.run() which properly handles event loop lifecycle
    # This works even if called from sync context
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in a loop, we can't use asyncio.run()
            # Create a task and run it
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, provider.transcribe(audio_path, language))
                result = future.result(timeout=30)
            return result
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            result = asyncio.run(provider.transcribe(audio_path, language))
            return result
    except Exception as e:
        raise AddisAIError(f"AddisAI transcription failed: {str(e)}")
