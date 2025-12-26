#!/usr/bin/env python3
"""
Test voice routing with both English and Amharic audio files
Simulates Telegram bot voice message processing
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from voice.asr.asr_infer import transcribe_audio

def test_voice_routing():
    """Test voice routing with real audio files"""
    
    print("\n" + "="*60)
    print("🎤 TELEGRAM VOICE ROUTING TEST")
    print("="*60)
    
    # Test files
    tests = [
        {
            "name": "English Test",
            "file": "uploads/audio/test_english_donation.wav",
            "language": "en",
            "user_preference": "en"
        },
        {
            "name": "Amharic Test",
            "file": "documentation/amharic_speech_test.wav",
            "language": "am",
            "user_preference": "am"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n{'='*60}")
        print(f"📋 Test: {test['name']}")
        print(f"{'='*60}")
        print(f"📁 File: {test['file']}")
        print(f"🌍 Language: {test['language']}")
        print(f"👤 User Preference: {test['user_preference']}")
        
        # Check file exists
        if not os.path.exists(test['file']):
            print(f"❌ ERROR: File not found: {test['file']}")
            results.append({**test, "success": False, "error": "File not found"})
            continue
        
        print(f"\n📤 Processing audio...")
        
        try:
            # This simulates what Telegram bot does
            result = transcribe_audio(
                audio_file_path=test['file'],
                language=test['language'],
                user_preference=test['user_preference']
            )
            
            print(f"\n✅ SUCCESS!")
            print(f"   📝 Transcription: {result['text'][:100]}...")
            print(f"   🔧 Provider: {result.get('provider', 'unknown')}")
            print(f"   🌍 Language: {result.get('language', 'unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 'N/A')}")
            
            results.append({
                **test,
                "success": True,
                "text": result['text'],
                "provider": result.get('provider', 'unknown'),
                "confidence": result.get('confidence', 0)
            })
            
        except Exception as e:
            print(f"\n❌ FAILED!")
            print(f"   Error: {str(e)}")
            results.append({**test, "success": False, "error": str(e)})
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r.get('success'))
    total_count = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        print(f"\n{i}. {result['name']}: {status}")
        
        if result.get('success'):
            print(f"   - Text: {result['text'][:60]}...")
            print(f"   - Provider: {result['provider']}")
            print(f"   - Confidence: {result['confidence']}")
        else:
            print(f"   - Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{total_count} tests passed")
    print(f"{'='*60}\n")
    
    # Show routing configuration
    print("🔧 Current Configuration:")
    print(f"   - USE_LOCAL_AMHARIC_FALLBACK: {os.getenv('USE_LOCAL_AMHARIC_FALLBACK', 'not set')}")
    print(f"   - ADDIS_AI_API_KEY: {'✅ Set' if os.getenv('ADDIS_AI_API_KEY') else '❌ Not set'}")
    print(f"   - OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    
    return success_count == total_count


if __name__ == "__main__":
    success = test_voice_routing()
    sys.exit(0 if success else 1)
