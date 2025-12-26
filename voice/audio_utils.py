"""
Audio Processing Utilities for TrustVoice
Handles audio validation, format conversion, and metadata extraction
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import soundfile as sf
from pydub import AudioSegment
from pydub.utils import which

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure pydub to use system ffmpeg
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

# Constants
MAX_AUDIO_SIZE_MB = 25  # 25 MB max file size
MAX_AUDIO_DURATION_SECONDS = 600  # 10 minutes max
TARGET_SAMPLE_RATE = 16000  # 16 kHz for Whisper
TARGET_CHANNELS = 1  # Mono audio
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'}


class AudioProcessingError(Exception):
    """Custom exception for audio processing errors"""
    pass


def check_disk_space(required_mb: float = 100.0) -> Tuple[bool, Optional[str]]:
    """
    Check if sufficient disk space is available for audio processing
    
    Args:
        required_mb: Minimum required disk space in MB (default 100 MB)
        
    Returns:
        Tuple of (has_space, error_message)
    """
    try:
        import shutil
        
        # Get disk usage for current working directory
        stat = shutil.disk_usage(Path.cwd())
        available_mb = stat.free / (1024 * 1024)
        
        if available_mb < required_mb:
            error_msg = f"Insufficient disk space: {available_mb:.1f} MB available, {required_mb:.1f} MB required"
            logger.error(error_msg)
            return False, error_msg
        
        logger.debug(f"Disk space check passed: {available_mb:.1f} MB available")
        return True, None
        
    except Exception as e:
        logger.error(f"Disk space check error: {str(e)}")
        return False, f"Failed to check disk space: {str(e)}"


def validate_audio_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate audio file size, format, and duration
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "Audio file not found"
        
        # Check file extension
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            return False, f"Unsupported audio format. Supported: {', '.join(SUPPORTED_FORMATS)}"
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            return False, f"Audio file too large ({file_size_mb:.2f}MB). Max: {MAX_AUDIO_SIZE_MB}MB"
        
        # Use ffprobe to check duration (avoid pydub hanging on macOS)
        import subprocess
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ]
        
        result = subprocess.run(
            probe_cmd,
            capture_output=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
            check=False
        )
        
        if result.returncode != 0:
            return False, f"Failed to read audio file: {result.stderr.decode()}"
        
        try:
            duration_seconds = float(result.stdout.decode().strip())
        except ValueError:
            return False, "Failed to parse audio duration"
        
        if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
            return False, f"Audio too long ({duration_seconds:.1f}s). Max: {MAX_AUDIO_DURATION_SECONDS}s"
        
        if duration_seconds < 1:
            return False, "Audio too short (minimum 1 second)"
        
        logger.info(f"Audio validation passed: {file_size_mb:.2f}MB, {duration_seconds:.1f}s")
        return True, None
        
    except Exception as e:
        logger.error(f"Audio validation error: {str(e)}")
        return False, f"Audio validation failed: {str(e)}"


def convert_to_whisper_format(
    input_path: str,
    output_path: Optional[str] = None,
    target_sr: int = TARGET_SAMPLE_RATE,
    target_channels: int = TARGET_CHANNELS
) -> str:
    """
    Convert audio file to format optimal for Whisper ASR
    Target: 16kHz, mono, WAV format
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output file (optional, will auto-generate)
        target_sr: Target sample rate (default 16000 Hz)
        target_channels: Target channels (default 1 = mono)
        
    Returns:
        Path to converted audio file
    """
    try:
        input_path = Path(input_path)
        
        # Check disk space before conversion (Issue #9 fix)
        # Estimate 3x input file size for safe conversion
        input_size_mb = input_path.stat().st_size / (1024 * 1024)
        required_mb = max(input_size_mb * 3, 50.0)  # At least 50 MB
        
        has_space, space_error = check_disk_space(required_mb)
        if not has_space:
            raise AudioProcessingError(space_error)
        
        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_converted.wav"
        else:
            output_path = Path(output_path)
        
        logger.info(f"Converting audio: {input_path} -> {output_path}")
        
        # Use ffmpeg directly to avoid pydub hanging issues on macOS
        import subprocess
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-ar", str(target_sr),
            "-ac", str(target_channels),
            "-acodec", "pcm_s16le",
            str(output_path)
        ]
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            timeout=30,
            stdin=subprocess.DEVNULL,
            check=False
        )
        
        if result.returncode != 0:
            raise AudioProcessingError(f"ffmpeg conversion failed: {result.stderr.decode()}")
        
        logger.info(f"Audio converted successfully: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Audio conversion error: {str(e)}")
        raise AudioProcessingError(f"Failed to convert audio: {str(e)}")


def get_audio_metadata(file_path: str) -> dict:
    """
    Extract metadata from audio file
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dictionary with audio metadata
    """
    try:
        import subprocess
        import json
        
        path = Path(file_path)
        
        # Use ffprobe to extract metadata (avoid pydub hanging on macOS)
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(path)
        ]
        
        result = subprocess.run(
            probe_cmd,
            capture_output=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
            check=False
        )
        
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr.decode()}")
        
        probe_data = json.loads(result.stdout.decode())
        format_info = probe_data.get("format", {})
        audio_stream = next(
            (s for s in probe_data.get("streams", []) if s.get("codec_type") == "audio"),
            {}
        )
        
        metadata = {
            "file_name": path.name,
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "duration_seconds": round(float(format_info.get("duration", 0)), 2),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": audio_stream.get("channels", 0),
            "format": path.suffix.lower(),
            "bit_depth": audio_stream.get("bits_per_sample", None)
        }
        
        logger.info(f"Audio metadata extracted: {metadata}")
        return metadata
        
    except Exception as e:
        logger.error(f"Metadata extraction error: {str(e)}")
        return {
            "error": str(e),
            "file_name": Path(file_path).name
        }


def cleanup_audio_file(file_path: str) -> bool:
    """
    Delete audio file (for cleanup after processing)
    
    Args:
        file_path: Path to audio file
        
    Returns:
        True if deleted successfully
    """
    try:
        path = Path(file_path)
        # Use missing_ok=True to avoid TOCTOU race condition
        # (file could be deleted between exists() check and unlink() call)
        path.unlink(missing_ok=True)
        logger.info(f"Audio file deleted: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Audio cleanup error: {str(e)}")
        return False


def process_audio_for_asr(
    input_file: str,
    cleanup_original: bool = False
) -> Tuple[str, dict]:
    """
    Complete audio processing pipeline for ASR
    1. Validate audio file
    2. Convert to Whisper-optimal format
    3. Extract metadata
    4. Optionally cleanup original
    
    Args:
        input_file: Path to input audio file
        cleanup_original: Whether to delete original after conversion
        
    Returns:
        Tuple of (converted_file_path, metadata)
    """
    try:
        # Step 1: Validate
        is_valid, error_msg = validate_audio_file(input_file)
        if not is_valid:
            raise AudioProcessingError(error_msg)
        
        # Step 2: Get metadata from original
        metadata = get_audio_metadata(input_file)
        
        # Step 3: Convert to optimal format
        converted_file = convert_to_whisper_format(input_file)
        
        # Step 4: Cleanup original if requested
        if cleanup_original and input_file != converted_file:
            cleanup_audio_file(input_file)
        
        logger.info(f"Audio processing complete: {converted_file}")
        return converted_file, metadata
        
    except AudioProcessingError:
        raise
    except Exception as e:
        logger.error(f"Audio processing pipeline error: {str(e)}")
        raise AudioProcessingError(f"Audio processing failed: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Test audio processing
    test_file = "test_audio.mp3"
    
    if Path(test_file).exists():
        try:
            converted, meta = process_audio_for_asr(test_file)
            print(f"✅ Conversion successful!")
            print(f"📁 Output: {converted}")
            print(f"📊 Metadata: {meta}")
        except AudioProcessingError as e:
            print(f"❌ Error: {e}")
    else:
        print(f"⚠️  Test file not found: {test_file}")
