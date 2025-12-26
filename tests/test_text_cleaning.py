"""
Test text cleaning for TTS (Text-to-Speech).

This test suite validates:
- HTML tag removal
- Markdown formatting removal
- URL removal
- Emoji handling
- Whitespace normalization
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


def test_text_cleaning():
    """Test text cleaning for TTS synthesis."""
    
    logger.info("=" * 70)
    logger.info("Text Cleaning Test Suite")
    logger.info("=" * 70)
    
    try:
        from voice.telegram.voice_responses import clean_text_for_tts
        
        logger.info("✅ Text cleaning module imported")
        logger.info("")
        
        passed_tests = 0
        total_tests = 0
        
        test_cases = [
            # (input, expected_output, description)
            ("<b>Bold text</b>", "Bold text", "HTML bold tags"),
            ("<i>Italic text</i>", "Italic text", "HTML italic tags"),
            ("<code>CODE-123</code>", "CODE-123", "HTML code tags"),
            ("**Bold** text", "Bold text", "Markdown bold"),
            ("*Italic* text", "Italic text", "Markdown italic"),
            ("[Link text](https://example.com)", "Link text", "Markdown link"),
            ("Visit https://example.com", "Visit", "URL removal"),
            ("Check http://test.com for info", "Check for info", "HTTP URL"),
            ("Multiple   spaces", "Multiple spaces", "Multiple spaces"),
            ("  Leading and trailing  ", "Leading and trailing", "Trim whitespace"),
            ("<b>Mixed</b> **formatting**", "Mixed formatting", "HTML + Markdown"),
            ("Text with\nmultiple\nlines", "Text with multiple lines", "Newlines to spaces"),
            ("Amount: <code>5,000 ETB</code>", "Amount: 5,000 ETB", "Currency in code tags"),
            ("<b>Success!</b> 🎉", "Success!", "HTML + emoji"),
            ("`inline code`", "inline code", "Inline code"),
            ("<b>Step 1:</b>\n1. Do this\n2. Do that", "Step 1: 1. Do this 2. Do that", "Lists"),
            ("", "", "Empty string"),
            ("Plain text", "Plain text", "No formatting"),
        ]
        
        for input_text, expected, description in test_cases:
            total_tests += 1
            logger.info(f"\nTest {total_tests}: {description}")
            logger.info(f"  Input:    '{input_text}'")
            logger.info(f"  Expected: '{expected}'")
            
            try:
                cleaned = clean_text_for_tts(input_text)
                logger.info(f"  Cleaned:  '{cleaned}'")
                
                if cleaned == expected:
                    logger.info(f"  ✅ PASSED")
                    passed_tests += 1
                else:
                    logger.error(f"  ❌ FAILED - Output doesn't match")
            except Exception as e:
                logger.error(f"  ❌ FAILED - Exception: {str(e)}")
        
        # Final Summary
        logger.info("\n" + "=" * 70)
        logger.info("TEXT CLEANING TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
        logger.info(f"❌ Tests failed: {total_tests - passed_tests}/{total_tests}")
        logger.info(f"📊 Accuracy: {passed_tests/total_tests*100:.1f}%")
        logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TEXT CLEANING TESTS PASSED!")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} test(s) failed")
        
        logger.info("")
        logger.info("Cleaning Operations:")
        logger.info("  • HTML tags → Removed (<b>, <i>, <code>, etc.)")
        logger.info("  • Markdown → Removed (**, *, [], etc.)")
        logger.info("  • URLs → Removed (http://, https://)")
        logger.info("  • Whitespace → Normalized (multiple spaces, newlines)")
        logger.info("  • Emojis → Removed")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_text_cleaning()
    sys.exit(0 if success else 1)
