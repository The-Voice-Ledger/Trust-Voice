"""
Test Celery task queueing and processing
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from voice.tasks.celery_app import app
from voice.tasks.voice_tasks import process_voice_message_task

def test_task_queue():
    """Test that tasks can be queued and picked up by worker"""
    
    print("=" * 60)
    print("CELERY TASK QUEUE TEST")
    print("=" * 60)
    
    # Check Celery configuration
    print(f"\n📋 Celery Configuration:")
    print(f"   App name: {app.main}")
    print(f"   Broker URL: {app.conf.broker_url[:50]}...")
    print(f"   Backend URL: {app.conf.result_backend[:50]}...")
    
    # Check task routes
    print(f"\n🗺️  Task Routes:")
    for task_name, route in app.conf.task_routes.items():
        print(f"   {task_name} -> {route}")
    
    # Try to queue a test task
    print(f"\n🚀 Queueing test task...")
    print(f"   Task: process_voice_message_task")
    print(f"   Queue: voice (from task_routes)")
    
    # Create a fake audio file path for testing
    test_audio = Path("test_audio.ogg")
    if not test_audio.exists():
        test_audio.write_bytes(b'OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00')
    
    try:
        task = process_voice_message_task.delay(
            audio_file_path=str(test_audio),
            user_id="test_user_programmatic",
            language="en"
        )
        
        print(f"\n✅ Task queued successfully!")
        print(f"   Task ID: {task.id}")
        print(f"   Task state: {task.state}")
        
        # Wait for task completion
        print(f"\n⏳ Waiting for task to complete (max 30 seconds)...")
        
        start_time = time.time()
        max_wait = 30
        
        while not task.ready() and (time.time() - start_time) < max_wait:
            elapsed = int(time.time() - start_time)
            print(f"   [{elapsed}s] Task state: {task.state}")
            time.sleep(2)
        
        if task.ready():
            elapsed = int(time.time() - start_time)
            print(f"\n🎉 Task completed in {elapsed} seconds!")
            print(f"   Final state: {task.state}")
            
            if task.successful():
                result = task.get()
                print(f"\n📊 Task Result:")
                print(f"   Success: {result.get('success', False)}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                if 'text' in result:
                    print(f"   Transcription: {result['text']}")
            else:
                print(f"   Task failed!")
                try:
                    task.get()
                except Exception as e:
                    print(f"   Error: {e}")
        else:
            print(f"\n⏱️  Task did not complete within {max_wait} seconds")
            print(f"   Final state: {task.state}")
            print(f"\n❌ LIKELY ISSUE: Worker not consuming from 'voice' queue")
            print(f"   Check worker logs: railway logs --service worker")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error queueing task: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_redis_connection():
    """Test Redis connection"""
    print(f"\n🔌 Testing Redis connection...")
    
    try:
        # Use the Celery app's connection
        with app.connection() as conn:
            conn.connect()
            print(f"✅ Redis connection successful")
            
            # Try to get broker info
            print(f"   Broker: {conn.as_uri()[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def inspect_queues():
    """Inspect Celery queues"""
    print(f"\n🔍 Inspecting Celery queues...")
    
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        
        # Get active queues
        active = inspect.active_queues()
        if active:
            print(f"✅ Active queues on workers:")
            for worker, queues in active.items():
                print(f"   Worker: {worker}")
                for queue in queues:
                    print(f"     - {queue['name']}")
        else:
            print(f"❌ No active workers found")
            return False
        
        return True
    except Exception as e:
        print(f"⚠️  Could not inspect queues: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    
    # Test Redis connection
    redis_ok = check_redis_connection()
    
    # Inspect queues
    inspect_queues()
    
    # Run the main test
    if redis_ok:
        success = test_task_queue()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ TEST PASSED - Celery tasks are working!")
        else:
            print("❌ TEST FAILED - Check worker configuration")
        print("=" * 60)
    else:
        print("\n❌ Cannot run test - Redis connection failed")
