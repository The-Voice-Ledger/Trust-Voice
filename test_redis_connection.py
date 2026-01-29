"""
Quick Redis Connection Test
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔍 Testing Redis Connection")
print("-" * 60)

# Test 1: Check environment variable
redis_url = os.getenv('REDIS_URL')
print(f"REDIS_URL env var: {'✓ Set' if redis_url else '✗ Not set'}")
if redis_url:
    # Mask password
    masked = redis_url.split('@')[1] if '@' in redis_url else redis_url
    print(f"  URL (masked): redis://...@{masked}")

# Test 2: Try to connect
try:
    from voice.session_manager import redis_client
    
    # Test ping
    response = redis_client.ping()
    print(f"\n✅ Redis PING: {response}")
    
    # Test set/get
    test_key = "test:connection:check"
    redis_client.setex(test_key, 10, "hello")
    value = redis_client.get(test_key)
    print(f"✅ Redis SET/GET: {value}")
    redis_client.delete(test_key)
    
    # Get info
    info = redis_client.info('server')
    print(f"✅ Redis version: {info.get('redis_version', 'unknown')}")
    
    print("\n🎉 Redis is properly connected!")
    
except Exception as e:
    print(f"\n❌ Redis connection failed: {str(e)}")
    import traceback
    traceback.print_exc()
