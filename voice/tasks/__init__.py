"""Voice processing tasks package"""
from voice.tasks.celery_app import app
from voice.tasks.voice_tasks import (
    process_voice_message_task,
    send_notification_task,
    cleanup_old_audio_files
)

__all__ = [
    'app',
    'process_voice_message_task',
    'send_notification_task',
    'cleanup_old_audio_files'
]
