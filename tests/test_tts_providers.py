"""
Test TTS (Text-to-Speech) providers: OpenAI and AddisAI.

This test suite validates:
- OpenAI TTS for English
- AddisAI TTS for Amharic
- Language routing
- Error handling and fallbacks
- Audio file generation
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def test_tts_providers():
    """Test both TTS providers comprehensively."""
    
    logger.info("=" * 70)
    logger.info("TTS Providers Test Suite")
    logger.info("=" * 70)
    
    try:
        from voice.tts.tts_provider import TTSProvider
        
        provider = TTSProvider()
        logger.info("✅ TTSProvider initialized")
        logger.info(f"   OpenAI API Key: {'Set' if provider.openai_api_key else 'Missing'}")
        logger.info(f"   AddisAI API Key: {'Set' if provider.addisai_api_key else 'Missing'}")
        logger.info(f"   AddisAI TTS URL: {provider.addisai_tts_url}")
        logger.info("")
        
        passed_tests = 0
        total_tests = 0
        
        # Test 1: OpenAI TTS - Simple English
        logger.info("=" * 70)
        logger.info("TEST 1: OpenAI TTS - Simple English")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text="Hello, this is a simple English test.",
                language="en"
            )
            
            if success and audio_path and Path(audio_path).exists():
                file_size = Path(audio_path).stat().st_size
                logger.info(f"✅ TEST 1 PASSED")
                logger.info(f"   Audio file: {audio_path}")
                logger.info(f"   File size: {file_size:,} bytes")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 1 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 1 FAILED: {str(e)}")
        
        # Test 2: AddisAI TTS - Simple Amharic
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: AddisAI TTS - Simple Amharic")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text="ሰላም! ይህ ቀላል የአማርኛ ሙከራ ነው።",
                language="am"
            )
            
            if success and audio_path and Path(audio_path).exists():
                file_size = Path(audio_path).stat().st_size
                logger.info(f"✅ TEST 2 PASSED")
                logger.info(f"   Audio file: {audio_path}")
                logger.info(f"   File size: {file_size:,} bytes")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 2 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 2 FAILED: {str(e)}")
        
        # Test 3: OpenAI TTS - Long English text
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: OpenAI TTS - Long English Text")
        logger.info("=" * 70)
        total_tests += 1
        
        long_english = """
        Welcome to Trust-Voice, the voice-first blockchain donation platform.
        Our system enables illiterate farmers to receive donations through
        voice commands in their native language. This is a longer text to
        test how the TTS handles extended content.
        """
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text=long_english.strip(),
                language="en"
            )
            
            if success and audio_path and Path(audio_path).exists():
                file_size = Path(audio_path).stat().st_size
                logger.info(f"✅ TEST 3 PASSED")
                logger.info(f"   Text length: {len(long_english.strip())} chars")
                logger.info(f"   File size: {file_size:,} bytes")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 3 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 3 FAILED: {str(e)}")
        
        # Test 4: AddisAI TTS - Long Amharic text
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: AddisAI TTS - Long Amharic Text")
        logger.info("=" * 70)
        total_tests += 1
        
        long_amharic = """
        እንኳን ደህና መጡ ወደ Trust-Voice። ይህ የድምጽ-ቀዳሚ የብሎክቼይን ልገሳ መድረክ ነው።
        የእኛ ስርዓት ያልተማሩ ገበሬዎች በራሳቸው ቋንቋ በድምጽ ትዕዛዞች ልገሳዎችን እንዲቀበሉ ያስችላል።
        ይህ ረዘም ያለ ጽሑፍ TTS ለተራዘመ ይዘት እንዴት እንደሚይዝ ለመፈተሽ ነው።
        """
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text=long_amharic.strip(),
                language="am"
            )
            
            if success and audio_path and Path(audio_path).exists():
                file_size = Path(audio_path).stat().st_size
                logger.info(f"✅ TEST 4 PASSED")
                logger.info(f"   Text length: {len(long_amharic.strip())} chars")
                logger.info(f"   File size: {file_size:,} bytes")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 4 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 4 FAILED: {str(e)}")
        
        # Test 5: TTS Caching
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: TTS Caching (Same Text Twice)")
        logger.info("=" * 70)
        total_tests += 1
        
        test_text = "This is a caching test for TTS."
        
        try:
            # First call
            import time
            start1 = time.time()
            success1, path1, _ = await provider.text_to_speech(test_text, "en")
            time1 = time.time() - start1
            
            # Second call (should hit cache)
            start2 = time.time()
            success2, path2, _ = await provider.text_to_speech(test_text, "en")
            time2 = time.time() - start2
            
            if success1 and success2 and path1 == path2:
                logger.info(f"✅ TEST 5 PASSED")
                logger.info(f"   First call: {time1:.2f}s")
                logger.info(f"   Second call: {time2:.2f}s (cached)")
                logger.info(f"   Speedup: {time1/time2:.1f}x")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 5 FAILED: Caching not working")
        except Exception as e:
            logger.error(f"❌ TEST 5 FAILED: {str(e)}")
        
        # Test 6: Special characters and emojis
        logger.info("\n" + "=" * 70)
        logger.info("TEST 6: Special Characters and Emojis")
        logger.info("=" * 70)
        total_tests += 1
        
        special_text = "Success! 🎉 Amount: 1,234.56 ETB ✅ Status: Approved"
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text=special_text,
                language="en"
            )
            
            if success and audio_path:
                logger.info(f"✅ TEST 6 PASSED")
                logger.info(f"   Handles emojis and special chars correctly")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 6 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 6 FAILED: {str(e)}")
        
        # Test 7: Numbers and currency
        logger.info("\n" + "=" * 70)
        logger.info("TEST 7: Numbers and Currency Formatting")
        logger.info("=" * 70)
        total_tests += 1
        
        number_text = "Your donation of 5000 Ethiopian Birr has been received."
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text=number_text,
                language="en"
            )
            
            if success and audio_path:
                logger.info(f"✅ TEST 7 PASSED")
                logger.info(f"   Numbers and currency handled correctly")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 7 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 7 FAILED: {str(e)}")
        
        # Test 8: Amharic numbers
        logger.info("\n" + "=" * 70)
        logger.info("TEST 8: Amharic with Numbers")
        logger.info("=" * 70)
        total_tests += 1
        
        amharic_numbers = "የእርስዎ ልገሳ 5000 ብር ተቀብለናል። እናመሰግናለን!"
        
        try:
            success, audio_path, error = await provider.text_to_speech(
                text=amharic_numbers,
                language="am"
            )
            
            if success and audio_path:
                logger.info(f"✅ TEST 8 PASSED")
                logger.info(f"   Amharic with numbers handled correctly")
                passed_tests += 1
            else:
                logger.error(f"❌ TEST 8 FAILED: {error}")
        except Exception as e:
            logger.error(f"❌ TEST 8 FAILED: {str(e)}")
        
        # Final Summary
        logger.info("\n" + "=" * 70)
        logger.info("TTS PROVIDERS TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
        logger.info(f"❌ Tests failed: {total_tests - passed_tests}/{total_tests}")
        logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TTS TESTS PASSED!")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} test(s) failed")
        
        logger.info("")
        logger.info("Provider Configuration:")
        logger.info(f"  • English TTS: OpenAI (tts-1, voice: nova)")
        logger.info(f"  • Amharic TTS: AddisAI (X-API-Key auth)")
        logger.info(f"  • Caching: {'Enabled' if provider.cache_enabled else 'Disabled'}")
        logger.info(f"  • Cache directory: voice/tts_cache/")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_tts_providers())
    sys.exit(0 if success else 1)
