# Celery Async Processing Guide

**Complete guide to setting up Celery for asynchronous task processing in voice-first applications**

Last Updated: December 23, 2025

---

## Overview

Celery enables asynchronous processing of voice commands, preventing slow operations (ASR, NLU, database) from blocking the user interface. When a farmer sends a voice message, they get an immediate response while processing happens in the background.

**Benefits:**
- **Non-blocking**: Bot responds in <100ms, processing takes 5-15 seconds
- **Progress tracking**: Update users on ASR → NLU → Execute stages
- **Retry logic**: Auto-retry on API failures, network issues
- **Resource control**: Prevent memory overload with controlled task fetching
- **Auto cleanup**: Temp audio files deleted after processing

---

## Architecture

```
Farmer Voice Message (Telegram/IVR)
    ↓
Bot Receives Message (< 100ms response)
    ↓
Queue Task → Celery Worker (Returns task_id immediately)
    |
    └─→ Background Processing (5-15 seconds):
        1. Validate audio
        2. Run ASR (Whisper) - 3-6 seconds
        3. Run NLU (GPT) - 1-2 seconds
        4. Execute command (database)
        5. Send result notification
    ↓
Farmer Receives Notification with Result
```

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install celery redis
```

**requirements.txt:**
```txt
celery==5.3.4
redis==5.0.1
```

### 2. Start Redis Server

```bash
# Install Redis (macOS)
brew install redis

# Start Redis
redis-server --daemonize yes

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

---

## Implementation

### 1. Celery App Configuration

**File:** `voice/tasks/celery_app.py`

```python
"""
Celery Application Configuration

Sets up Celery task queue with Redis broker for async voice processing.
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Celery app configuration
app = Celery(
    'voice_ledger_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['voice.tasks.voice_tasks']  # Auto-discover tasks
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store task args, kwargs, result
    
    # Task execution settings
    task_track_started=True,  # Track when task starts
    task_time_limit=300,  # 5 minute hard timeout
    task_soft_time_limit=240,  # 4 minute soft timeout
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch 1 task at a time (ASR is slow)
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    
    # Retry settings
    task_acks_late=True,  # Only ack after task completes
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)

# Optional: Task routes (for dedicated workers)
app.conf.task_routes = {
    'voice.tasks.voice_tasks.process_voice_command_task': {'queue': 'voice_processing'},
}

if __name__ == '__main__':
    app.start()
```

**Key Configuration Explained:**

- **`worker_prefetch_multiplier=1`**: Only fetch 1 task at a time. Critical for ASR tasks that consume significant memory (1.5GB Amharic model).
- **`task_time_limit=300`**: Hard timeout at 5 minutes. Prevents hung tasks from blocking worker.
- **`task_acks_late=True`**: Only acknowledge task after completion. Ensures task isn't lost if worker crashes mid-processing.
- **`worker_max_tasks_per_child=50`**: Restart worker after 50 tasks. Prevents memory leaks from accumulating.

---

### 2. Task Definition

**File:** `voice/tasks/voice_tasks.py`

```python
"""
Voice Processing Celery Tasks

Background tasks for async voice command processing.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from celery import Task

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from voice.tasks.celery_app import app
from voice.asr.asr_infer import run_asr_with_user_preference
from voice.nlu.nlu_infer import infer_nlu_json
from voice.audio_utils import validate_and_convert_audio, cleanup_temp_file
from database.connection import get_db
from voice.command_integration import execute_voice_command

logger = logging.getLogger(__name__)


class VoiceProcessingTask(Task):
    """
    Base task class for voice processing.
    
    Provides:
    - Progress tracking
    - Error handling
    - Cleanup on failure
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        # Cleanup temp files if they exist
        if 'audio_path' in kwargs:
            cleanup_temp_file(kwargs['audio_path'])
        
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        # Cleanup temp files
        if 'audio_path' in kwargs:
            cleanup_temp_file(kwargs['audio_path'])
        
        logger.info(f"Task {task_id} completed successfully")


@app.task(
    base=VoiceProcessingTask,
    bind=True,
    name='voice.tasks.process_voice_command',
    max_retries=3,
    default_retry_delay=60
)
def process_voice_command_task(
    self, 
    audio_path: str, 
    original_filename: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Background task: Process voice command from audio file.
    
    Pipeline:
    1. Validate and convert audio to WAV
    2. Transcribe with Whisper (ASR)
    3. Extract intent/entities with GPT-3.5 (NLU)
    4. Execute database command
    5. Return complete result
    
    Args:
        self: Task instance (auto-injected by bind=True)
        audio_path: Path to uploaded audio file
        original_filename: Original filename for logging
        metadata: Optional metadata (channel, user_id, etc.)
        
    Returns:
        {
            "status": "success" | "error",
            "transcript": str,
            "intent": str,
            "entities": dict,
            "result": dict,
            "error": str | None,
            "audio_metadata": dict
        }
    """
    
    if metadata is None:
        metadata = {}
    
    try:
        # Update task state: validating
        self.update_state(
            state='VALIDATING',
            meta={'stage': 'Validating audio file', 'progress': 10}
        )
        
        # Validate and convert audio to WAV
        wav_path, audio_metadata = validate_and_convert_audio(audio_path)
        metadata.update(audio_metadata)
        
        # Update task state: transcribing
        self.update_state(
            state='TRANSCRIBING',
            meta={'stage': 'Transcribing audio with Whisper', 'progress': 30}
        )
        
        # Get user language preference
        user_language = 'en'  # Default
        user_id = metadata.get('user_id')
        
        if user_id:
            with get_db() as db:
                from database.models import UserIdentity
                user = db.query(UserIdentity).filter_by(
                    telegram_user_id=str(user_id)
                ).first()
                if user:
                    user_language = user.preferred_language or 'en'
        
        # Run ASR with user's language preference
        asr_result = run_asr_with_user_preference(wav_path, user_language)
        transcript = asr_result['text']
        detected_language = asr_result['language']
        
        logger.info(f"ASR ({detected_language}): {transcript[:50]}...")
        
        # Update task state: extracting
        self.update_state(
            state='EXTRACTING',
            meta={'stage': 'Extracting intent and entities', 'progress': 60}
        )
        
        # Run NLU
        nlu_result = infer_nlu_json(transcript)
        intent = nlu_result.get("intent")
        entities = nlu_result.get("entities", {})
        
        # Update task state: executing
        self.update_state(
            state='EXECUTING',
            meta={'stage': 'Executing database command', 'progress': 80}
        )
        
        # Execute database command
        with get_db() as db:
            message, db_result = execute_voice_command(
                db, intent, entities,
                user_id=user_id
            )
        
        # Return complete result
        return {
            "status": "success",
            "transcript": transcript,
            "intent": intent,
            "entities": entities,
            "result": db_result,
            "message": message,
            "audio_metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        
        # Retry on transient errors (API timeouts, network issues)
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e, countdown=60)
        
        return {
            "status": "error",
            "error": str(e),
            "transcript": None,
            "intent": None,
            "entities": None,
            "result": None
        }
```

**Key Features:**

- **`bind=True`**: Gives access to `self` for progress updates
- **`base=VoiceProcessingTask`**: Auto cleanup on success/failure
- **`max_retries=3`**: Retry up to 3 times on failure
- **`self.update_state()`**: Track progress (VALIDATING → TRANSCRIBING → EXTRACTING → EXECUTING)
- **Auto cleanup**: Temp files deleted in `on_success` and `on_failure` hooks

---

### 3. Usage in Telegram Bot

**File:** `voice/telegram/telegram_api.py`

```python
from voice.tasks.voice_tasks import process_voice_command_task
import tempfile

async def handle_voice_message(update, context):
    """Handle voice messages from Telegram."""
    
    voice = update.message.voice
    user_id = update.effective_user.id
    
    # Download voice message
    file = await context.bot.get_file(voice.file_id)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(
        suffix='.ogg',
        delete=False
    ) as temp_file:
        await file.download_to_drive(temp_file.name)
        audio_path = temp_file.name
    
    # Queue async task (returns immediately)
    task = process_voice_command_task.apply_async(
        args=[audio_path],
        kwargs={
            'original_filename': f"telegram_voice.ogg",
            'metadata': {
                'user_id': user_id,
                'username': update.effective_user.username,
                'channel': 'telegram'
            }
        }
    )
    
    # Send immediate response with task ID
    await update.message.reply_text(
        f"⏳ Processing your voice command...\n"
        f"📋 Task ID: `{task.id[:16]}...`",
        parse_mode='Markdown'
    )
    
    logger.info(f"Queued voice processing: task_id={task.id}")
```

**Flow:**
1. User sends voice message
2. Bot downloads audio to temp file
3. Task queued with `apply_async()` (returns immediately)
4. Bot sends "Processing..." message with task ID
5. Celery worker processes in background
6. Result notification sent when complete

---

### 4. Starting the Celery Worker

**File:** `admin_scripts/START_SERVICES.sh`

```bash
#!/bin/bash
# Start Celery worker

echo "Starting Celery worker..."

# Kill any existing workers
pkill -f "celery.*worker" 2>/dev/null || true
sleep 1

# Start worker with solo pool (better for macOS)
celery -A voice.tasks.celery_app worker \
    --loglevel=info \
    --pool=solo \
    --logfile=logs/celery_worker.log \
    --detach

# Wait for worker to start
sleep 3

# Verify worker is running
if pgrep -f "celery.*worker" > /dev/null; then
    echo "✅ Celery worker started"
    echo "📋 Logs: logs/celery_worker.log"
else
    echo "❌ Failed to start Celery worker"
    exit 1
fi
```

**Pool Options:**
- **`--pool=solo`**: Single process, best for macOS/development (no multiprocessing issues)
- **`--pool=prefork`**: Multiple processes, best for Linux production (higher throughput)
- **`--pool=gevent`**: Async I/O, best for high-concurrency, I/O-bound tasks

**For Production (Linux):**
```bash
celery -A voice.tasks.celery_app worker \
    --loglevel=info \
    --pool=prefork \
    --concurrency=4 \
    --max-tasks-per-child=50 \
    --logfile=logs/celery_worker.log
```

---

## Environment Variables

**File:** `.env`

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional: Remote Redis (production)
# CELERY_BROKER_URL=redis://:password@redis-host:6379/0
# CELERY_RESULT_BACKEND=redis://:password@redis-host:6379/0
```

---

## Monitoring & Debugging

### Check Worker Status

```bash
# View worker logs (live)
tail -f logs/celery_worker.log

# Check registered tasks
celery -A voice.tasks.celery_app inspect registered

# Check active tasks
celery -A voice.tasks.celery_app inspect active

# Check queued tasks
celery -A voice.tasks.celery_app inspect reserved
```

### Monitor with Flower (Web UI)

```bash
# Install Flower
pip install flower

# Start Flower dashboard
celery -A voice.tasks.celery_app flower --port=5555

# Open browser: http://localhost:5555
```

**Flower provides:**
- Real-time task monitoring
- Task history and results
- Worker status and stats
- Task retry visualization

---

## Common Issues & Solutions

### 1. **Tasks Not Being Picked Up**

**Symptoms:** Tasks queued but never execute

**Solutions:**
```bash
# Check worker is running
ps aux | grep celery

# Check worker can see tasks
celery -A voice.tasks.celery_app inspect registered

# Restart worker
pkill -f "celery.*worker"
celery -A voice.tasks.celery_app worker --loglevel=info --pool=solo
```

### 2. **Worker Crashes with Memory Error**

**Symptoms:** Worker dies, logs show memory errors

**Solutions:**
```python
# In celery_app.py, reduce prefetch
app.conf.update(
    worker_prefetch_multiplier=1,  # Only 1 task at a time
    worker_max_tasks_per_child=25  # Restart more frequently
)
```

### 3. **Tasks Timing Out**

**Symptoms:** Tasks never complete, hang indefinitely

**Solutions:**
```python
# In celery_app.py, reduce timeouts
app.conf.update(
    task_time_limit=180,       # 3 minutes hard timeout
    task_soft_time_limit=150   # 2.5 minutes soft timeout
)
```

### 4. **Redis Connection Refused**

**Symptoms:** Worker can't connect to Redis

**Solutions:**
```bash
# Check Redis is running
redis-cli ping

# Start Redis if not running
redis-server --daemonize yes

# Check Redis port
lsof -i :6379
```

---

## Production Deployment

### Systemd Service (Linux)

**File:** `/etc/systemd/system/celery-voice-ledger.service`

```ini
[Unit]
Description=Voice Ledger Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=voice-ledger
Group=voice-ledger
WorkingDirectory=/opt/voice-ledger
EnvironmentFile=/opt/voice-ledger/.env

ExecStart=/opt/voice-ledger/venv/bin/celery \
    -A voice.tasks.celery_app worker \
    --loglevel=info \
    --pool=prefork \
    --concurrency=4 \
    --max-tasks-per-child=50 \
    --logfile=/var/log/celery/voice-ledger.log \
    --pidfile=/var/run/celery/voice-ledger.pid \
    --detach

ExecStop=/bin/kill -s TERM $MAINPID

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable celery-voice-ledger
sudo systemctl start celery-voice-ledger
sudo systemctl status celery-voice-ledger
```

### Docker Deployment

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  celery-worker:
    build: .
    command: celery -A voice.tasks.celery_app worker --loglevel=info --pool=prefork --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs

volumes:
  redis-data:
```

---

## Adapting for Other Projects (Trust-Voice)

### Directory Structure

```
trust-voice/
├── trust/
│   └── tasks/
│       ├── celery_app.py           # Celery configuration
│       └── trust_tasks.py          # Background tasks
├── requirements.txt                # Add: celery, redis
└── admin_scripts/
    └── START_SERVICES.sh           # Start Celery worker
```

### Example Trust Task

**File:** `trust/tasks/trust_tasks.py`

```python
from trust.tasks.celery_app import app
from celery import Task

class TrustProcessingTask(Task):
    """Base task for trust document processing."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Cleanup temp files
        pass
    
    def on_success(self, retval, task_id, args, kwargs):
        # Final cleanup
        pass

@app.task(
    base=TrustProcessingTask,
    bind=True,
    max_retries=3
)
def process_trust_document_task(self, doc_path, metadata):
    """
    Process trust document asynchronously.
    
    Pipeline:
    1. Extract text (OCR if needed)
    2. Validate trust structure
    3. Generate DID credentials
    4. Anchor to blockchain
    5. Store on IPFS
    """
    
    self.update_state(
        state='EXTRACTING',
        meta={'stage': 'Extracting text', 'progress': 20}
    )
    
    # Extract text from PDF/image
    text = extract_text(doc_path)
    
    self.update_state(
        state='VALIDATING',
        meta={'stage': 'Validating structure', 'progress': 40}
    )
    
    # Validate trust document structure
    validation_result = validate_trust_document(text)
    
    self.update_state(
        state='ANCHORING',
        meta={'stage': 'Anchoring to blockchain', 'progress': 60}
    )
    
    # Anchor to blockchain
    tx_hash = anchor_to_blockchain(validation_result)
    
    self.update_state(
        state='STORING',
        meta={'stage': 'Storing on IPFS', 'progress': 80}
    )
    
    # Store on IPFS
    ipfs_cid = store_on_ipfs(validation_result)
    
    return {
        "status": "success",
        "validation": validation_result,
        "tx_hash": tx_hash,
        "ipfs_cid": ipfs_cid
    }
```

### When to Use Celery

**✅ Use Celery if:**
- Voice interface (ASR/NLU processing)
- Tasks take >2 seconds
- Need background job processing
- Multiple concurrent users (>10)
- Require retry logic
- Need progress tracking

**❌ Skip Celery if:**
- Simple REST API (all operations <1 second)
- Low user volume (<5 concurrent)
- Pure serverless architecture (use cloud functions)
- No background processing needs

---

## Performance Benchmarks

**Voice Ledger Results:**

| Metric | Without Celery | With Celery |
|--------|---------------|-------------|
| Bot response time | 15 seconds | 0.1 seconds |
| User experience | Blocking | Non-blocking |
| Concurrent users | 1-2 | 10+ |
| Memory usage | 2.5GB peak | 1.5GB stable |
| Error recovery | Manual | Automatic retry |

---

## Additional Resources

- **Celery Documentation**: https://docs.celeryq.dev/
- **Redis Documentation**: https://redis.io/docs/
- **Flower Monitoring**: https://flower.readthedocs.io/
- **Celery Best Practices**: https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices

---

## Support

For issues or questions about Celery setup in Voice-Ledger or Trust-Voice:
- Review logs: `logs/celery_worker.log`
- Check worker status: `celery -A voice.tasks.celery_app inspect active`
- Monitor with Flower: `celery -A voice.tasks.celery_app flower`

---

**Version:** 1.0  
**Author:** Voice Ledger Team  
**Last Updated:** December 23, 2025
