"""
Automatic Speech Recognition (ASR) Module for TrustVoice
Supports three ASR methods:
1. AddisAI API (Amharic) - Primary, fast (300-800ms)
2. Local Amharic Model - Fallback if AddisAI fails (3-5s)
3. OpenAI Whisper API (English) - All other languages

Based on Voice Ledger architecture - routes ASR requests based on user language preference
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Literal
import torch
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from openai import OpenAI
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Language type
LanguageCode = Literal["en", "am"]

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
AMHARIC_MODEL_NAME = "b1n1yam/shook-medium-amharic-2k"
USE_LOCAL_AMHARIC_FALLBACK = os.getenv("USE_LOCAL_AMHARIC_FALLBACK", "true").lower() == "true"

# Cache for loaded models
_model_cache = {}


class ASRError(Exception):
    """Custom exception for ASR errors"""
    pass


def load_amharic_model():
    """
    Load Amharic Whisper model from HuggingFace
    Model is cached at ~/.cache/huggingface/ and shared across projects
    
    Returns:
        Tuple of (processor, model)
    """
    try:
        if 'amharic_model' in _model_cache:
            logger.info("Using cached Amharic model")
            return _model_cache['amharic_model']
        
        logger.info(f"Loading Amharic model: {AMHARIC_MODEL_NAME}")
        logger.info("This may take a few minutes on first run (~1.5GB download)")
        logger.info("Model will be cached at ~/.cache/huggingface/ for future use")
        
        # Load processor and model
        processor = AutoProcessor.from_pretrained(AMHARIC_MODEL_NAME)
        
        # Determine device (MPS for Mac, CUDA for GPU, CPU otherwise)
        if torch.backends.mps.is_available():
            device = "mps"
            logger.info("Using Apple Silicon (MPS) acceleration")
        elif torch.cuda.is_available():
            device = "cuda"
            logger.info("Using CUDA (GPU) acceleration")
        else:
            device = "cpu"
            logger.info("Using CPU (no GPU acceleration)")
        
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            AMHARIC_MODEL_NAME,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            low_cpu_mem_usage=True,
        ).to(device)
        
        # Cache the model
        _model_cache['amharic_model'] = (processor, model, device)
        
        logger.info(f"✅ Amharic model loaded successfully on {device}")
        return processor, model, device
        
    except Exception as e:
        logger.error(f"Failed to load Amharic model: {str(e)}")
        raise ASRError(f"Amharic model loading failed: {str(e)}")


def transcribe_with_whisper_api(
    audio_file_path: str,
    language: str = "en"
) -> Dict[str, any]:
    """
    Transcribe audio using OpenAI Whisper API
    Best for English and other major languages
    
    Args:
        audio_file_path: Path to audio file
        language: Language code (e.g., 'en', 'sw', 'fr')
        
    Returns:
        Dictionary with transcription results
    """
    try:
        if not OPENAI_API_KEY:
            raise ASRError("OPENAI_API_KEY not set in environment")
        
        # Add timeout to prevent hanging indefinitely
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=httpx.Timeout(30.0, connect=5.0)
        )
        
        logger.info(f"Transcribing with Whisper API (language: {language})")
        
        with open(audio_file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json"
            )
        
        result = {
            "text": response.text,
            "language": response.language,
            "duration": response.duration if hasattr(response, 'duration') else None,
            "method": "whisper_api",
            "model": "whisper-1"
        }
        
        logger.info(f"✅ Whisper API transcription complete: {len(result['text'])} chars")
        return result
        
    except Exception as e:
        logger.error(f"Whisper API transcription error: {str(e)}")
        raise ASRError(f"Whisper API failed: {str(e)}")


def transcribe_with_amharic_model(audio_file_path: str) -> Dict[str, any]:
    """
    Transcribe audio using local Amharic Whisper model
    Optimized for Amharic language (Ethiopian)
    
    Args:
        audio_file_path: Path to audio file (should be 16kHz WAV)
        
    Returns:
        Dictionary with transcription results
    """
    try:
        import librosa
        
        # Load the model
        processor, model, device = load_amharic_model()
        
        logger.info(f"Transcribing with Amharic model on {device}")
        
        # Load and preprocess audio
        audio_array, sample_rate = librosa.load(audio_file_path, sr=16000, mono=True)
        
        # Process audio
        inputs = processor(
            audio_array,
            sampling_rate=16000,
            return_tensors="pt"
        ).to(device)
        
        # Generate transcription
        with torch.no_grad():
            generated_ids = model.generate(inputs["input_features"])
        
        # Decode transcription
        transcription = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]
        
        result = {
            "text": transcription,
            "language": "am",
            "duration": len(audio_array) / sample_rate,
            "method": "local_model",
            "model": AMHARIC_MODEL_NAME,
            "device": device
        }
        
        logger.info(f"✅ Amharic model transcription complete: {len(result['text'])} chars")
        return result
        
    except Exception as e:
        logger.error(f"Amharic model transcription error: {str(e)}")
        raise ASRError(f"Amharic model failed: {str(e)}")


def transcribe_audio(
    audio_file_path: str,
    language: LanguageCode = "en",
    user_preference: Optional[LanguageCode] = None
) -> Dict[str, any]:
    """
    Main ASR function - routes to appropriate transcription method
    
    Routing logic:
    1. If user_preference is set, use that (PRIMARY method)
    2. Otherwise use language parameter
    3. 'am' -> Try AddisAI API first, fallback to local model if enabled
    4. 'en' or others -> OpenAI Whisper API
    
    Args:
        audio_file_path: Path to audio file
        language: Default language code
        user_preference: User's preferred language from database
        
    Returns:
        Dictionary with transcription results
    """
    try:
        # Determine which language to use (user preference takes priority)
        selected_language = user_preference if user_preference else language
        
        logger.info(f"ASR Request - Language: {selected_language}, User Preference: {user_preference}")
        
        # Route to appropriate transcription method
        if selected_language == "am":
            # Try AddisAI first (fast, cloud-based)
            try:
                # Import AddisAI - handle import failure gracefully
                try:
                    from voice.providers.addis_ai import transcribe_sync, AddisAIError
                except ImportError as import_err:
                    logger.warning(f"AddisAI module not available: {import_err}")
                    # Fall back to local model if available
                    if USE_LOCAL_AMHARIC_FALLBACK:
                        logger.info("AddisAI not available, using local Amharic model")
                        return transcribe_with_amharic_model(audio_file_path)
                    else:
                        raise ASRError(
                            "Amharic ASR unavailable. AddisAI module not installed and "
                            "local fallback disabled."
                        )
                
                logger.info("Attempting AddisAI transcription (primary)")
                result = transcribe_sync(audio_file_path, "am")
                
                logger.info(f"✅ AddisAI transcription successful: {len(result['text'])} chars")
                return result
                
            except (AddisAIError, Exception) as e:
                logger.warning(f"AddisAI transcription failed: {str(e)}")
                
                # Conditional fallback to local model
                if USE_LOCAL_AMHARIC_FALLBACK:
                    logger.info("Falling back to local Amharic model")
                    return transcribe_with_amharic_model(audio_file_path)
                else:
                    logger.error("Local fallback disabled, raising error")
                    raise ASRError(
                        f"Amharic transcription temporarily unavailable. "
                        f"AddisAI API error: {str(e)}"
                    )
        else:
            # Use Whisper API for English and other languages
            return transcribe_with_whisper_api(audio_file_path, language=selected_language)
            
    except ASRError:
        raise
    except Exception as e:
        logger.error(f"ASR routing error: {str(e)}")
        raise ASRError(f"Transcription failed: {str(e)}")


def get_supported_languages() -> Dict[str, str]:
    """
    Get list of supported languages
    
    Returns:
        Dictionary mapping language codes to names
    """
    return {
        "en": "English",
        "am": "Amharic (አማርኛ)",
        # Future expansion:
        # "sw": "Swahili",
        # "fr": "French",
        # "ar": "Arabic"
    }


def verify_amharic_model_cached() -> bool:
    """
    Check if Amharic model is already cached locally
    Useful for pre-flight checks before transcription
    
    Returns:
        True if model is cached, False otherwise
    """
    try:
        from transformers import AutoProcessor
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        model_cache_path = cache_dir / f"models--{AMHARIC_MODEL_NAME.replace('/', '--')}"
        
        exists = model_cache_path.exists()
        logger.info(f"Amharic model cache check: {'✅ Found' if exists else '❌ Not cached'}")
        return exists
        
    except Exception as e:
        logger.error(f"Cache verification error: {str(e)}")
        return False


# Example usage
if __name__ == "__main__":
    import sys
    
    print("🎤 TrustVoice ASR Module")
    print(f"Supported languages: {get_supported_languages()}")
    print(f"\nAmharic model cached: {verify_amharic_model_cached()}")
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) > 2 else "en"
        
        print(f"\nTranscribing: {audio_file} (language: {language})")
        
        try:
            result = transcribe_audio(audio_file, language=language)
            print(f"\n✅ Transcription Result:")
            print(f"📝 Text: {result['text']}")
            print(f"🌍 Language: {result['language']}")
            print(f"⏱️  Duration: {result['duration']:.2f}s")
            print(f"🔧 Method: {result['method']}")
            
        except ASRError as e:
            print(f"\n❌ Error: {e}")
    else:
        print("\nUsage: python asr_infer.py <audio_file> [language]")
        print("Example: python asr_infer.py audio.wav am")
