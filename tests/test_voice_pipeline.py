"""
Test voice processing pipeline end-to-end
"""
import requests
import time
import json
import os
from pathlib import Path

BASE_URL = os.getenv("BASE_URL", "https://web-production-dd7cf.up.railway.app")

def test_voice_wizard_step():
    """Test voice input through the wizard endpoint"""
    
    # Create a simple valid audio file (1-second silence WAV)
    import wave
    import struct
    
    test_audio = Path("test_audio.wav")
    with wave.open(str(test_audio), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(16000)  # 16kHz
        # Write 1 second of silence
        for _ in range(16000):
            wav_file.writeframes(struct.pack('h', 0))
    
    print(f"Testing voice wizard endpoint at {BASE_URL}/api/voice/wizard-step")
    
    # Test data - wizard-step requires field_name parameter
    payload = {
        "field_name": "title",
        "step_number": "1",
        "user_language": "en"
    }
    
    files = {
        "audio": ("test.ogg", open(test_audio, "rb"), "audio/ogg")
    }
    
    print(f"\n📤 Sending voice input...")
    print(f"   Field: {payload['field_name']}")
    print(f"   Step: {payload['step_number']}")
    print(f"   Language: {payload['user_language']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/voice/wizard-step",
            data=payload,
            files=files,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"\n📊 Response:")
            print(json.dumps(result, indent=2))
            
            if "task_id" in result:
                print(f"\n🎯 Task ID: {result['task_id']}")
                print(f"   Task queued successfully")
                return True
        else:
            print(f"❌ FAILED!")
            print(f"\n📄 Response:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT - Request took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        files["audio"][1].close()


def test_miniapp_voice():
    """Test donate-by-voice endpoint"""
    
    test_audio = Path("test_audio.ogg")
    if not test_audio.exists():
        test_audio.write_bytes(b'OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00')
    
    print(f"\n\nTesting donate-by-voice endpoint at {BASE_URL}/api/voice/donate-by-voice")
    
    payload = {
        "user_id": "test_user_456",
        "user_language": "en"
    }
    
    files = {
        "audio": ("test.ogg", open(test_audio, "rb"), "audio/ogg")
    }
    
    print(f"\n📤 Sending voice input...")
    print(f"   User ID: {payload['user_id']}")
    print(f"   Language: {payload['user_language']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/voice/donate-by-voice",
            data=payload,
            files=files,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"\n📊 Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ FAILED!")
            print(f"\n📄 Response:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT - Request took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        files["audio"][1].close()


def test_health_endpoints():
    """Test health check endpoints"""
    
    print(f"\n\nTesting health endpoints...")
    
    # Test main health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"\n✅ Main health: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Main health failed: {e}")
    
    # Test Redis health
    try:
        response = requests.get(f"{BASE_URL}/health/redis", timeout=10)
        print(f"\n✅ Redis health: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Redis health failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("VOICE PIPELINE TEST")
    print("=" * 60)
    
    # Test health first
    test_health_endpoints()
    
    # Test voice endpoints
    print("\n" + "=" * 60)
    print("TESTING VOICE ENDPOINTS")
    print("=" * 60)
    
    wizard_success = test_voice_wizard_step()
    miniapp_success = test_miniapp_voice()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Wizard endpoint: {'✅ PASS' if wizard_success else '❌ FAIL'}")
    print(f"Miniapp endpoint: {'✅ PASS' if miniapp_success else '❌ FAIL'}")
    print("=" * 60)
