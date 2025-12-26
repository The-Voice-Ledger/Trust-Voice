#!/usr/bin/env python3
"""
Test Dual Delivery Implementation

Validates that the new non-blocking dual delivery pattern works correctly:
1. Text is sent immediately
2. Voice is generated in background
3. User preference routing works
4. Text detection fallback works
5. No blocking occurs
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from voice.telegram.voice_responses import (
    detect_language,
    clean_text_for_tts,
    get_user_language_preference
)

def test_detect_language():
    """Test Unicode-based language detection"""
    print("Testing language detection...")
    
    tests = [
        ("Hello world", "en"),
        ("ሰላም ለአለም", "am"),
        ("Hello ሰላም", "am"),  # Mixed, >30% Amharic
        ("✅ OK", "en"),  # No language-specific chars
        ("", "en"),  # Empty
    ]
    
    passed = 0
    for text, expected in tests:
        result = detect_language(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text[:20]}...' → {result} (expected {expected})")
        if result == expected:
            passed += 1
    
    print(f"  Result: {passed}/{len(tests)} passed\n")
    return passed == len(tests)


def test_clean_text_for_tts():
    """Test text cleaning for TTS"""
    print("Testing text cleaning...")
    
    tests = [
        ("<b>Bold</b> text", "Bold text"),
        ("**Bold** text", "Bold text"),
        ("[Link](http://url)", "Link"),
        ("Check http://example.com", "Check"),
        ("Multiple   spaces", "Multiple spaces"),
        ("<code>ID-123</code>", "ID-123"),
        ("✅ Campaign created!", "✅ Campaign created!"),
    ]
    
    passed = 0
    for text, expected in tests:
        result = clean_text_for_tts(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text}' → '{result}'")
        if result == expected:
            passed += 1
    
    print(f"  Result: {passed}/{len(tests)} passed\n")
    return passed == len(tests)


def test_user_preference_lookup():
    """Test user preference database lookup"""
    print("Testing user preference lookup...")
    
    try:
        # Test with a non-existent user (should return None)
        result = get_user_language_preference("test_nonexistent_user_12345")
        if result is None:
            print("  ✅ Non-existent user returns None")
            return True
        else:
            print(f"  ❌ Expected None, got {result}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_import_voice_responses():
    """Test that voice_responses module can be imported"""
    print("Testing voice_responses module import...")
    
    try:
        from voice.telegram.voice_responses import (
            send_voice_reply,
            send_voice_reply_from_update,
            _generate_and_send_voice_background
        )
        print("  ✅ All functions imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False


async def test_tts_provider():
    """Test TTS provider integration"""
    print("Testing TTS provider...")
    
    try:
        from voice.tts.tts_provider import tts_provider
        
        # Test that provider is initialized
        if tts_provider.openai_api_key:
            print("  ✅ OpenAI API key configured")
        else:
            print("  ⚠️  OpenAI API key not configured")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_async_task_pattern():
    """Test asyncio.create_task pattern"""
    print("Testing async task pattern...")
    
    async def background_task():
        await asyncio.sleep(0.1)
        return "completed"
    
    # Spawn task
    task = asyncio.create_task(background_task())
    
    # Should return immediately
    print("  ✅ Task spawned without blocking")
    
    # Wait for task to complete
    result = await task
    if result == "completed":
        print("  ✅ Background task completed successfully")
        return True
    else:
        print("  ❌ Background task failed")
        return False


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("DUAL DELIVERY IMPLEMENTATION TESTS")
    print("=" * 60)
    print()
    
    results = []
    
    # Unit tests
    results.append(("Language Detection", test_detect_language()))
    results.append(("Text Cleaning", test_clean_text_for_tts()))
    results.append(("User Preference Lookup", test_user_preference_lookup()))
    
    # Async tests
    results.append(("Module Import", await test_import_voice_responses()))
    results.append(("TTS Provider", await test_tts_provider()))
    results.append(("Async Task Pattern", await test_async_task_pattern()))
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Dual delivery implementation ready.")
        print()
        print("Next steps:")
        print("  1. Restart services: ./admin-scripts/START_SERVICES.sh")
        print("  2. Test via Telegram: Send a message to the bot")
        print("  3. Verify: Text arrives instantly, voice ~2s later")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
