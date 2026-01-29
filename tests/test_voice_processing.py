"""
Test Voice Processing Pipeline

Tests the complete voice pipeline with English audio files
"""

import os
import sys
import asyncio
import requests
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = os.getenv('API_BASE_URL', 'http://localhost:8001')
TEST_USER_ID = 'test_voice_user_123'

print("🎤 Voice Processing Pipeline Tests")
print(f"📍 API Base: {API_BASE}")
print("-" * 60)

# ============================================
# Test 1: Check voice endpoint exists
# ============================================

def test_voice_endpoint_exists():
    """Check if voice processing endpoint is accessible."""
    print("\n✅ Test 1: Voice Endpoint Exists")
    
    try:
        response = requests.post(f'{API_BASE}/api/miniapp-voice/process')
        # Expect 422 (missing data) or 200, not 404
        if response.status_code in [200, 422]:
            print(f"  ✓ Endpoint accessible (status {response.status_code})")
            return True
        elif response.status_code == 404:
            print(f"  ✗ Endpoint not found (404)")
            return False
        else:
            print(f"  ⚠ Unexpected status: {response.status_code}")
            return True  # Endpoint exists but has other issue
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


# ============================================
# Test 2: Test with sample audio
# ============================================

def test_voice_processing_with_audio():
    """Test voice processing with a generated audio file."""
    print("\n✅ Test 2: Voice Processing with Audio")
    
    try:
        # Create a minimal audio file (silence for testing)
        import wave
        import struct
        
        # Generate 1 second of silence at 16kHz
        sample_rate = 16000
        duration = 1
        num_samples = sample_rate * duration
        
        audio_path = Path("/tmp/test_voice.wav")
        with wave.open(str(audio_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write silence (zeros)
            for _ in range(num_samples):
                wav_file.writeframes(struct.pack('h', 0))
        
        print(f"  📁 Created test audio: {audio_path}")
        
        # Upload to voice endpoint
        with open(audio_path, 'rb') as audio_file:
            files = {'audio_file': ('test.wav', audio_file, 'audio/wav')}
            data = {
                'telegram_user_id': TEST_USER_ID,
                'language': 'en'
            }
            
            response = requests.post(
                f'{API_BASE}/api/miniapp-voice/process',
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"  📤 Upload response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Processing successful")
                print(f"  📝 Transcription: {result.get('transcription', 'N/A')}")
                print(f"  🎯 Intent: {result.get('intent', 'N/A')}")
                return True
            else:
                print(f"  ✗ Processing failed: {response.status_code}")
                print(f"  📄 Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# Test 3: Test bot voice handler
# ============================================

async def test_bot_voice_handler():
    """Test the Telegram bot voice handler directly."""
    print("\n✅ Test 3: Bot Voice Handler")
    
    try:
        from voice.pipeline import process_voice_message
        
        # Create a mock audio file path
        audio_path = "/tmp/test_voice.wav"
        
        print(f"  🤖 Testing voice pipeline directly...")
        
        result = await process_voice_message(
            audio_file_path=audio_path,
            telegram_user_id=TEST_USER_ID,
            language='en'
        )
        
        print(f"  ✓ Pipeline executed")
        print(f"  📝 Transcription: {result.get('transcription', 'N/A')}")
        print(f"  🎯 Intent: {result.get('intent', 'N/A')}")
        print(f"  💬 Response: {result.get('response_text', 'N/A')[:100]}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# Test 4: Check ASR model availability
# ============================================

def test_asr_model():
    """Check if ASR model is loaded and available."""
    print("\n✅ Test 4: ASR Model Availability")
    
    try:
        from voice.asr.asr_infer import get_asr_model
        
        print(f"  🔍 Loading ASR model...")
        model = get_asr_model('en')
        
        if model:
            print(f"  ✓ English ASR model loaded successfully")
            return True
        else:
            print(f"  ✗ Failed to load English ASR model")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


# ============================================
# Test 5: End-to-end test
# ============================================

async def test_end_to_end():
    """Complete end-to-end voice processing test."""
    print("\n✅ Test 5: End-to-End Voice Processing")
    
    try:
        # This would test the complete flow
        print(f"  🔄 Testing complete voice flow...")
        
        # Test voice endpoint
        endpoint_ok = test_voice_endpoint_exists()
        
        # Test with audio
        if endpoint_ok:
            audio_ok = test_voice_processing_with_audio()
            return audio_ok
        
        return False
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False


# ============================================
# Run All Tests
# ============================================

def run_all_tests():
    """Run all voice processing tests."""
    print("\n" + "=" * 60)
    print("🚀 RUNNING VOICE PROCESSING TESTS")
    print("=" * 60)
    
    tests = [
        ("Voice Endpoint Exists", test_voice_endpoint_exists),
        ("Voice Processing with Audio", test_voice_processing_with_audio),
        ("ASR Model", test_asr_model),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            results[test_name] = False
    
    # Run async test
    print("\nRunning async test...")
    try:
        results["Bot Voice Handler"] = asyncio.run(test_bot_voice_handler())
    except Exception as e:
        print(f"❌ Async test crashed: {str(e)}")
        results["Bot Voice Handler"] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All voice tests passed!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Voice processing needs attention.\n")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
