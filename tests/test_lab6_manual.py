"""
Manual Lab 6 Testing Script
Tests Lab 6 handlers with both text and voice messages using your credentials
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

YOUR_TELEGRAM_CHAT_ID = "478816890"  # Your chat ID


async def test_lab6():
    """Test Lab 6 with text and voice messages."""
    
    from telegram import Bot
    from voice.telegram.voice_responses import send_voice_reply
    
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    
    print("\n" + "=" * 70)
    print("LAB 6 MANUAL TEST - Text & Voice Messages")
    print("=" * 70)
    print(f"📱 Sending to your Telegram: {YOUR_TELEGRAM_CHAT_ID}")
    print()
    
    # Test 1: Help command (via dual delivery)
    print("TEST 1: Help Command (get_help handler)")
    print("-" * 70)
    await send_voice_reply(
        bot=bot,
        chat_id=int(YOUR_TELEGRAM_CHAT_ID),
        message="🧪 LAB 6 TEST 1\n\nPlease respond with: 'Help'",
        language="en",
        send_voice=False
    )
    print("✅ Sent test prompt. Now send 'Help' via Telegram.")
    print()
    await asyncio.sleep(2)
    
    # Test 2: Search campaigns
    print("TEST 2: Search Campaigns (search_campaigns handler)")
    print("-" * 70)
    await send_voice_reply(
        bot=bot,
        chat_id=int(YOUR_TELEGRAM_CHAT_ID),
        message="🧪 LAB 6 TEST 2\n\nPlease respond with text: 'Show me education campaigns'\nor send voice message saying: 'Find water campaigns'",
        language="en",
        send_voice=False
    )
    print("✅ Sent test prompt. Now send campaign search.")
    print()
    await asyncio.sleep(2)
    
    # Test 3: Greeting
    print("TEST 3: Greeting (greeting handler)")
    print("-" * 70)
    await send_voice_reply(
        bot=bot,
        chat_id=int(YOUR_TELEGRAM_CHAT_ID),
        message="🧪 LAB 6 TEST 3\n\nPlease send voice message saying: 'Hello' or 'Good morning'",
        language="en",
        send_voice=False
    )
    print("✅ Sent test prompt. Now send greeting.")
    print()
    
    print("=" * 70)
    print("✅ All test prompts sent to your Telegram!")
    print()
    print("📋 Next steps:")
    print("   1. Check your Telegram for the test prompts")
    print("   2. Respond with the suggested text/voice messages")
    print("   3. Verify Lab 6 handlers respond correctly")
    print()
    print("💡 Monitor logs with: tail -f logs/telegram_bot.log")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_lab6())
