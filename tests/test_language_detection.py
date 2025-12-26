"""
Test language detection for text-based routing.

This test suite validates:
- English text detection
- Amharic text detection
- Mixed language detection
- Edge cases (emojis, numbers, etc.)
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_language_detection():
    """Test language detection with various inputs."""
    
    logger.info("=" * 70)
    logger.info("Language Detection Test Suite")
    logger.info("=" * 70)
    
    try:
        from voice.telegram.voice_responses import detect_language
        
        logger.info("✅ Language detection module imported")
        logger.info("")
        
        passed_tests = 0
        total_tests = 0
        
        test_cases = [
            # (text, expected_language, description)
            ("Hello, how are you?", "en", "Simple English"),
            ("ሰላም እንደምን ነህ?", "am", "Simple Amharic"),
            ("This is a longer English sentence with multiple words.", "en", "Long English"),
            ("ይህ ረጅም የአማርኛ ዓረፍተ ነገር ብዙ ቃላትን የያዘ ነው።", "am", "Long Amharic"),
            ("Hello ሰላም!", "am", "Mixed (>30% Amharic)"),
            ("ሰላም Hello!", "am", "Mixed (>30% Amharic, reversed)"),
            ("123456", "en", "Numbers only (default to English)"),
            ("🎉 ✅ 💰", "en", "Emojis only (default to English)"),
            ("", "en", "Empty string (default to English)"),
            ("Hello! 123", "en", "English with numbers"),
            ("ሰላም! 123", "am", "Amharic with numbers"),
            ("Welcome to Trust-Voice", "en", "Brand name"),
            ("እንኳን ደህና መጡ", "am", "Amharic greeting"),
            ("M-Pesa payment", "en", "Service name"),
            ("A b c d e", "en", "Single letters"),
            ("እ ን ኳ", "am", "Single Amharic letters"),
            ("Hello world! This is a test of the language detection system with a longer text to ensure accuracy.", "en", "Very long English"),
            ("ሰላም ለሁሉም! ይህ የቋንቋ ፈልጎ ማግኛ ስርዓት ሙከራ ነው። ትክክለኛነቱን ለማረጋገጥ ረዘም ያለ ጽሑፍ ነው።", "am", "Very long Amharic"),
        ]
        
        for text, expected, description in test_cases:
            total_tests += 1
            logger.info(f"\nTest {total_tests}: {description}")
            logger.info(f"  Input: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            try:
                detected = detect_language(text)
                logger.info(f"  Expected: {expected}, Detected: {detected}")
                
                if detected == expected:
                    logger.info(f"  ✅ PASSED")
                    passed_tests += 1
                else:
                    logger.error(f"  ❌ FAILED - Wrong language detected")
            except Exception as e:
                logger.error(f"  ❌ FAILED - Exception: {str(e)}")
        
        # Final Summary
        logger.info("\n" + "=" * 70)
        logger.info("LANGUAGE DETECTION TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
        logger.info(f"❌ Tests failed: {total_tests - passed_tests}/{total_tests}")
        logger.info(f"📊 Accuracy: {passed_tests/total_tests*100:.1f}%")
        logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL LANGUAGE DETECTION TESTS PASSED!")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} test(s) failed")
        
        logger.info("")
        logger.info("Detection Algorithm:")
        logger.info("  • Unicode range: U+1200-U+137F (Ethiopic)")
        logger.info("  • Threshold: 30% Amharic characters")
        logger.info("  • Default: English (for ambiguous cases)")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_language_detection()
    sys.exit(0 if success else 1)
