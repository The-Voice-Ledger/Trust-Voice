"""
End-to-end test for voice processing with Redis storage
"""
import redis
import os
import time

REDIS_URL = "redis://default:kgWFUUFcrdtLouBpdtlsWswwaIIQaAMt@ballast.proxy.rlwy.net:30997"

r = redis.from_url(REDIS_URL, decode_responses=False)

print("Checking Redis for voice tasks...")
print()

# Check for audio files in Redis
audio_keys = r.keys("audio:*")
print(f"Audio files in Redis: {len(audio_keys)}")
for key in audio_keys[:5]:  # Show first 5
    ttl = r.ttl(key)
    print(f"  - {key.decode()} (TTL: {ttl}s)")

print()

# Check voice queue
voice_queue_len = r.llen("voice")
print(f"Tasks in 'voice' queue: {voice_queue_len}")

if voice_queue_len > 0:
    print("\nQueued tasks:")
    for i in range(min(5, voice_queue_len)):
        task = r.lindex("voice", i)
        print(f"  {i+1}. {task[:100]}...")

print()
print("Send a voice message to the bot and run this script again!")
