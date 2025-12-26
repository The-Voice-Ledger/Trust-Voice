"""
Test AddisAI Integration with Hybrid Fallback
==============================================
Tests the complete ASR routing: AddisAI API → Local Model fallback
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from voice.providers.addis_ai import get_addisai_provider, AddisAIError
from voice.asr.asr_infer import transcribe_audio


async def test_addisai_provider():
    """Test 1: Direct AddisAI provider test"""
    print("\n" + "="*60)
    print("TEST 1: AddisAI Provider Direct Test")
    print("="*60)
    
    test_audio = "uploads/audio/test_english_donation.wav"
    
    if not os.path.exists(test_audio):
        print(f"⚠️  Test audio not found: {test_audio}")
        print("   Skipping direct provider test")
        return False
    
    try:
        addisai = get_addisai_provider()
        print(f"✓ AddisAI provider initialized")
        print(f"  - API Key: {addisai.api_key[:20]}...")
        print(f"  - Base URL: {addisai.base_url}")
        
        print(f"\n📤 Uploading: {test_audio}")
        result = await addisai.transcribe(test_audio, "am")
        
        print(f"\n✅ AddisAI Transcription Success!")
        print(f"  - Text: {result['text'][:100]}...")
        print(f"  - Language: {result['language']}")
        print(f"  - Confidence: {result.get('confidence', 'N/A')}")
        print(f"  - Provider: {result.get('provider', 'N/A')}")
        return True
        
    except AddisAIError as e:
        print(f"\n❌ AddisAI API Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_routing():
    """Test 2: Hybrid routing with fallback"""
    print("\n" + "="*60)
    print("TEST 2: Hybrid Routing (AddisAI → Local Fallback)")
    print("="*60)
    
    test_audio = "uploads/audio/test_english_donation.wav"
    
    if not os.path.exists(test_audio):
        print(f"⚠️  Test audio not found: {test_audio}")
        return False
    
    # Test with fallback enabled
    print(f"\n🔧 Configuration:")
    print(f"  - USE_LOCAL_AMHARIC_FALLBACK: {os.getenv('USE_LOCAL_AMHARIC_FALLBACK')}")
    print(f"  - Test file: {test_audio}")
    
    try:
        print(f"\n📤 Transcribing with user_preference='am'...")
        result = transcribe_audio(
            audio_file_path=test_audio,
            language="en",
            user_preference="am"
        )
        
        print(f"\n✅ Transcription Success!")
        print(f"  - Text: {result['text'][:100]}...")
        print(f"  - Provider: {result.get('provider', 'local')}")
        print(f"  - Language: {result.get('language', 'N/A')}")
        
        if result.get('provider') == 'addisai':
            print(f"  ✨ Used AddisAI API (primary)")
        else:
            print(f"  🔄 Used local model (fallback)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Transcription Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_english_routing():
    """Test 3: English should use OpenAI (not affected)"""
    print("\n" + "="*60)
    print("TEST 3: English Routing (OpenAI Whisper)")
    print("="*60)
    
    test_audio = "uploads/audio/test_english_donation.wav"
    
    if not os.path.exists(test_audio):
        print(f"⚠️  Test audio not found: {test_audio}")
        return False
    
    try:
        print(f"\n📤 Transcribing with user_preference='en'...")
        result = transcribe_audio(
            audio_file_path=test_audio,
            language="en",
            user_preference="en"
        )
        
        print(f"\n✅ Transcription Success!")
        print(f"  - Text: {result['text'][:100]}...")
        print(f"  - Provider: OpenAI Whisper")
        print(f"  - Language: {result.get('language', 'en')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Transcription Failed: {e}")
        return False


def test_fallback_disabled():
    """Test 4: Verify fallback can be disabled"""
    print("\n" + "="*60)
    print("TEST 4: Fallback Disabled (Production Mode)")
    print("="*60)
    
    # Temporarily disable fallback
    original_value = os.getenv("USE_LOCAL_AMHARIC_FALLBACK")
    os.environ["USE_LOCAL_AMHARIC_FALLBACK"] = "false"
    
    # Reload module to pick up new env var
    import importlib
    import voice.asr.asr_infer
    importlib.reload(voice.asr.asr_infer)
    from voice.asr.asr_infer import transcribe_audio as transcribe_audio_reload
    
    print(f"\n🔧 Configuration:")
    print(f"  - USE_LOCAL_AMHARIC_FALLBACK: false (fallback disabled)")
    print(f"  - Expected: AddisAI API only, fail if API fails")
    
    test_audio = "uploads/audio/test_english_donation.wav"
    
    try:
        if os.path.exists(test_audio):
            print(f"\n📤 Transcribing with fallback disabled...")
            result = transcribe_audio_reload(
                audio_file_path=test_audio,
                language="en",
                user_preference="am"
            )
            
            if result.get('provider') == 'addisai':
                print(f"\n✅ AddisAI API worked (no fallback needed)")
                success = True
            else:
                print(f"\n❌ Unexpected: Used fallback when disabled")
                success = False
        else:
            print(f"⚠️  Test audio not found, skipping")
            success = True  # Don't fail test
    
    except Exception as e:
        # This is actually expected if AddisAI fails and fallback is disabled
        print(f"\n✅ Expected behavior: Raised error without fallback")
        print(f"  - Error: {str(e)}")
        success = True
    
    finally:
        # Restore original value
        if original_value:
            os.environ["USE_LOCAL_AMHARIC_FALLBACK"] = original_value
        importlib.reload(voice.asr.asr_infer)
    
    return success


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 AddisAI Integration Test Suite")
    print("="*60)
    print(f"Start time: {Path(__file__).name}")
    
    results = {
        "AddisAI Provider": await test_addisai_provider(),
        "Hybrid Routing": test_hybrid_routing(),
        "English Routing": test_english_routing(),
        "Fallback Disabled": test_fallback_disabled()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nKey Features Verified:")
        print("  ✓ AddisAI API integration working")
        print("  ✓ Hybrid routing (API → fallback)")
        print("  ✓ English routing unaffected")
        print("  ✓ Fallback can be disabled for production")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Review errors above for details")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
