"""
TrustVoice Celery Application
Handles async background tasks for voice processing, notifications, etc.
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery with Redis as broker and backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "trustvoice_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['voice.tasks.voice_tasks']  # Auto-discover tasks
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store task args, kwargs, result
    
    # Task execution settings
    task_track_started=True,  # Track when task starts
    task_time_limit=300,  # 5 minute hard timeout
    task_soft_time_limit=240,  # 4 minute soft timeout
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch 1 task at a time (ASR is memory intensive)
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    
    # Retry settings
    task_acks_late=True,  # Only ack after task completes
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)

# Task routing (optional - for dedicated workers)
app.conf.task_routes = {
    "voice.tasks.process_voice_message": {"queue": "voice"},
    "voice.tasks.send_notification": {"queue": "notifications"},
    "voice.tasks.cleanup_old_audio_files": {"queue": "voice"},
}

# Periodic task schedule (Celery Beat)
# Run cleanup tasks automatically to prevent disk space issues
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-audio-files-hourly': {
        'task': 'voice.tasks.cleanup_old_audio_files',
        'schedule': crontab(minute=0),  # Every hour at :00
        'options': {'queue': 'voice'}
    },
    'cleanup-tts-cache-daily': {
        'task': 'voice.tasks.cleanup_tts_cache',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3:00 AM
        'options': {'queue': 'voice'}
    },
}

if __name__ == "__main__":
    app.start()
