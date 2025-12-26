"""
Test dual delivery (text + voice) for Trust-Voice Telegram bot.

This test suite validates the TrustVoice pattern implementation:
- Text sent immediately (0ms latency)
- Voice generated in background (~2-3s)
- User preference-based language routing
- Fallback to text detection
- Both English (OpenAI) and Amharic (AddisAI) TTS
"""

import asyncio
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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def test_dual_delivery():
    """Test dual delivery (text + voice) to Telegram."""
    
    logger.info("=" * 70)
    logger.info("Trust-Voice Dual Delivery Test Suite")
    logger.info("=" * 70)
    
    # Get test chat ID from environment
    test_chat_id = os.getenv("TEST_TELEGRAM_CHAT_ID")
    
    if not test_chat_id:
        logger.error("❌ TEST_TELEGRAM_CHAT_ID not set in .env")
        logger.info("Add your Telegram chat ID to .env:")
        logger.info("TEST_TELEGRAM_CHAT_ID=your_chat_id_here")
        logger.info("")
        logger.info("To get your chat ID, send a message to your bot and check:")
        logger.info("https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        return False
    
    try:
        from telegram import Bot
        from voice.telegram.voice_responses import send_voice_reply
        
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        logger.info(f"✅ Telegram bot initialized")
        logger.info(f"📱 Test chat ID: {test_chat_id}")
        logger.info("")
        
        passed_tests = 0
        total_tests = 0
        
        # Test 1: English text + voice (OpenAI TTS)
        logger.info("=" * 70)
        logger.info("TEST 1: English Dual Delivery (OpenAI TTS)")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="✅ Hello! This is an English test. You should receive both text and voice.",
                language="en",
                send_voice=True
            )
            logger.info("✅ TEST 1 PASSED: English message sent")
            logger.info("   Expected: Text arrives instantly, English voice in ~2 seconds (OpenAI)")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 1 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 2: Amharic text + voice (AddisAI TTS)
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: Amharic Dual Delivery (AddisAI TTS)")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="✅ ሰላም! ይህ የአማርኛ ሙከራ ነው። ጽሑፍ እና ድምጽ መቀበል አለብዎት።",
                language="am",
                send_voice=True
            )
            logger.info("✅ TEST 2 PASSED: Amharic message sent")
            logger.info("   Expected: Text arrives instantly, Amharic voice in ~2 seconds (AddisAI)")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 2 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 3: Auto language detection (English - no explicit language)
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: Auto Language Detection (English)")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="This message has no explicit language parameter. Language should be auto-detected as English.",
                send_voice=True
            )
            logger.info("✅ TEST 3 PASSED: Auto-detection message sent")
            logger.info("   Expected: Text detection determines English → OpenAI TTS")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 3 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 4: Auto language detection (Amharic - no explicit language)
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: Auto Language Detection (Amharic)")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="የአማርኛ ቋንቋ ሙከራ - ቋንቋ በራስ-ሰር መታወቅ አለበት።",
                send_voice=True
            )
            logger.info("✅ TEST 4 PASSED: Auto-detection message sent")
            logger.info("   Expected: Text detection determines Amharic → AddisAI TTS")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 4 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 5: Text-only mode (voice disabled)
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: Text-Only Mode (Voice Disabled)")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="📝 This is a text-only message. Voice is disabled for this test.",
                send_voice=False
            )
            logger.info("✅ TEST 5 PASSED: Text-only message sent")
            logger.info("   Expected: Only text arrives, NO voice message")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 5 FAILED: {str(e)}")
        
        await asyncio.sleep(2)
        
        # Test 6: Long message with HTML formatting
        logger.info("\n" + "=" * 70)
        logger.info("TEST 6: HTML Formatting Cleanup")
        logger.info("=" * 70)
        total_tests += 1
        
        long_message = """
✅ <b>Transaction Recorded Successfully!</b>

Transaction ID: <code>TRX-20251226-001</code>
Amount: 5,000 ETB
Type: <b>Voice Donation</b>

Your transaction has been recorded in the blockchain.
You can track it using the transaction ID above.

<i>Thank you for using Trust-Voice!</i> 🎉
"""
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message=long_message.strip(),
                language="en",
                send_voice=True
            )
            logger.info("✅ TEST 6 PASSED: Formatted message sent")
            logger.info("   Expected: HTML preserved in text, cleaned in voice (no tags)")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 6 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 7: Mixed language content (user preference should win)
        logger.info("\n" + "=" * 70)
        logger.info("TEST 7: User Preference Priority (Mixed Content)")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            # Simulate user preference by explicitly setting language
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="Hello ሰላም! Mixed English and Amharic - but voice should be in English.",
                language="en",  # Explicit override
                send_voice=True
            )
            logger.info("✅ TEST 7 PASSED: User preference override sent")
            logger.info("   Expected: English voice despite mixed content (preference wins)")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 7 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 8: Voice message threading (reply_to_message_id)
        logger.info("\n" + "=" * 70)
        logger.info("TEST 8: Voice Message Threading")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            # First message
            from telegram import Bot as TelegramBot
            text_msg = await bot.send_message(
                chat_id=int(test_chat_id),
                text="🔗 Testing threading..."
            )
            
            # Reply with dual delivery
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="This voice message should reply to the previous text message.",
                language="en",
                send_voice=True,
                reply_to_message_id=text_msg.message_id
            )
            logger.info("✅ TEST 8 PASSED: Threaded message sent")
            logger.info("   Expected: Voice message replies to text (threaded in Telegram)")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 8 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 9: Amharic long message
        logger.info("\n" + "=" * 70)
        logger.info("TEST 9: Long Amharic Message (AddisAI TTS)")
        logger.info("=" * 70)
        total_tests += 1
        
        long_amharic = """
✅ <b>ስኬታማ ነው!</b>

የትራንዚክሽን መታወቂያ: <code>TRX-20251226-002</code>
መጠን: 5,000 ብር
አይነት: የድምጽ ልገሳ

የእርስዎ ትራንዚክሽን በብሎክቼይን ላይ ተመዝግቧል።
በላይ ያለውን መታወቂያ በመጠቀም መከታተል ይችላሉ።

<i>Trust-Voice ን ስለተጠቀሙ እናመሰግናለን!</i> 🎉
"""
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message=long_amharic.strip(),
                language="am",
                send_voice=True
            )
            logger.info("✅ TEST 9 PASSED: Long Amharic message sent")
            logger.info("   Expected: Full Amharic voice synthesis (AddisAI TTS)")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 9 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Test 10: Emoji and special characters
        logger.info("\n" + "=" * 70)
        logger.info("TEST 10: Emoji and Special Characters")
        logger.info("=" * 70)
        total_tests += 1
        
        try:
            await send_voice_reply(
                bot=bot,
                chat_id=int(test_chat_id),
                message="🎉 Success! 💰 Amount: 1,234.56 ETB ✅ Status: Approved 🚀",
                language="en",
                send_voice=True
            )
            logger.info("✅ TEST 10 PASSED: Special characters message sent")
            logger.info("   Expected: Emojis preserved in text, cleaned in voice")
            passed_tests += 1
        except Exception as e:
            logger.error(f"❌ TEST 10 FAILED: {str(e)}")
        
        await asyncio.sleep(4)
        
        # Final Summary
        logger.info("\n" + "=" * 70)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Tests passed: {passed_tests}/{total_tests}")
        logger.info(f"❌ Tests failed: {total_tests - passed_tests}/{total_tests}")
        logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Dual delivery working perfectly!")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} test(s) failed")
        
        logger.info("")
        logger.info("Expected Behavior:")
        logger.info("1. ⚡ Text messages arrive IMMEDIATELY (0ms perceived latency)")
        logger.info("2. 🎤 Voice messages follow ~2-3 seconds later")
        logger.info("3. 🧵 Voice messages reply to text messages (threaded)")
        logger.info("4. 🧹 HTML/formatting removed in voice synthesis")
        logger.info("5. 🌍 English → OpenAI TTS | Amharic → AddisAI TTS")
        logger.info("6. 👤 User preference > Text detection for language routing")
        logger.info("")
        logger.info("Check your Telegram to verify all messages received correctly!")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_dual_delivery())
    sys.exit(0 if success else 1)
