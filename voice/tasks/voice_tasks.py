"""
Celery tasks for voice processing
"""

import os
import sys
import logging
from typing import Dict, Any
from pathlib import Path
from celery import Task

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from voice.tasks.celery_app import app
from voice.pipeline import process_voice_message

logger = logging.getLogger(__name__)


class VoiceProcessingTask(Task):
    """Base task with error handling for voice processing"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failures"""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Exception info: {einfo}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")


@app.task(
    bind=True,
    base=VoiceProcessingTask,
    name="voice.tasks.process_voice_message",
    max_retries=2,
    default_retry_delay=5
)
def process_voice_message_task(
    self,
    audio_key: str,
    user_id: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Process voice message asynchronously
    
    Args:
        audio_key: Redis key containing base64-encoded audio data
        user_id: User identifier (telegram_user_id or phone number)
        language: User's preferred language (en/am)
    
    Returns:
        Dict with processing results and response text
    """
    import tempfile
    import base64
    from voice.session_manager import redis_client
    
    try:
        logger.info(f"Processing voice message for user {user_id}, language: {language}")
        
        # Retrieve audio from Redis
        audio_data_b64 = redis_client.get(audio_key)
        if not audio_data_b64:
            raise ValueError(f"Audio data not found in Redis for key: {audio_key}")
        
        # Decode base64 audio
        audio_data = base64.b64decode(audio_data_b64)
        logger.info(f"Retrieved {len(audio_data)} bytes from Redis")
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_file.write(audio_data)
            audio_file_path = temp_file.name
        
        # Run the async voice pipeline in sync context
        result = process_voice_message(
            audio_file_path=audio_file_path,
            user_id=user_id,
            user_language=language  # Fixed: use 'user_language' not 'language'
        )
        
        # Clean up temp file
        os.unlink(audio_file_path)
        
        # Clean up Redis key
        redis_client.delete(audio_key)
        
        logger.info(f"Voice processing complete for user {user_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Error processing voice for user {user_id}: {exc}")
        # Retry on failure
        raise self.retry(exc=exc)


@app.task(
    name="voice.tasks.send_notification",
    max_retries=3,
    default_retry_delay=10
)
def send_notification_task(
    user_id: str,
    message: str,
    channel: str = "telegram"
) -> Dict[str, Any]:
    """
    Send notification to user
    
    Args:
        user_id: User identifier
        message: Notification message
        channel: Communication channel (telegram/whatsapp/sms)
    
    Returns:
        Dict with status and details
    """
    try:
        logger.info(f"Sending {channel} notification to user {user_id}")
        
        # TODO: Implement actual notification sending
        # For now, just log
        logger.info(f"Notification sent: {message}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "channel": channel,
            "message": message
        }
        
    except Exception as exc:
        logger.error(f"Error sending notification to {user_id}: {exc}")
        raise


@app.task(name="voice.tasks.cleanup_old_audio_files")
def cleanup_old_audio_files() -> Dict[str, Any]:
    """
    Clean up old temporary audio files (run periodically)
    
    Returns:
        Dict with cleanup statistics
    """
    import os
    import time
    from pathlib import Path
    
    try:
        logger.info("Starting audio file cleanup")
        
        audio_dir = Path("uploads/voice")
        if not audio_dir.exists():
            return {"status": "skipped", "reason": "no uploads directory"}
        
        # Delete files older than 24 hours
        now = time.time()
        deleted_count = 0
        
        for file_path in audio_dir.glob("*.ogg"):
            if os.path.getmtime(file_path) < now - 86400:  # 24 hours
                os.remove(file_path)
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old audio files")
        
        return {
            "status": "success",
            "deleted_count": deleted_count
        }
        
    except Exception as exc:
        logger.error(f"Error during cleanup: {exc}")
        return {"status": "error", "error": str(exc)}


@app.task(name="voice.tasks.cleanup_tts_cache")
def cleanup_tts_cache() -> Dict[str, Any]:
    """
    Clean up old TTS cache files (run daily)
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        logger.info("Starting TTS cache cleanup")
        
        from voice.tts.tts_provider import tts_provider
        
        # Clear cache files older than 7 days
        deleted_count = tts_provider.clear_cache(older_than_days=7)
        
        logger.info(f"Cleaned up {deleted_count} old TTS cache files")
        
        return {
            "status": "success",
            "deleted_count": deleted_count
        }
        
    except Exception as exc:
        logger.error(f"Error during TTS cache cleanup: {exc}")
        return {"status": "error", "error": str(exc)}
