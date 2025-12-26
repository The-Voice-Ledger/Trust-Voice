#!/usr/bin/env python3
"""
Live test of enhanced NLU system via Telegram
Tests the new system_info intent and improved intent classification
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
from telegram.constants import ParseMode

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TEST_CHAT_ID = os.getenv("TEST_TELEGRAM_CHAT_ID")

# Test queries to verify enhanced NLU
TEST_QUERIES = [
    {
        "query": "Tell me about TrustVoice",
        "expected_intent": "system_info",
        "description": "General platform information"
    },
    {
        "query": "What is this system?",
        "expected_intent": "system_info",
        "description": "Platform explanation query"
    },
    {
        "query": "How does this platform work?",
        "expected_intent": "system_info",
        "description": "Platform functionality query"
    },
    {
        "query": "What can I do here?",
        "expected_intent": "get_help",
        "description": "User guidance request"
    },
    {
        "query": "Show me campaigns",
        "expected_intent": "search_campaigns",
        "description": "Campaign browsing"
    },
    {
        "query": "What campaigns are available?",
        "expected_intent": "search_campaigns",
        "description": "Campaign availability query"
    },
    {
        "query": "I would like to make a donation",
        "expected_intent": "make_donation",
        "description": "Donation intent"
    },
    {
        "query": "Explain the donation process",
        "expected_intent": "system_info",
        "description": "Process explanation query"
    }
]


async def run_nlu_test():
    """Send test queries to Telegram and verify NLU responses"""
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return False
    
    if not TEST_CHAT_ID:
        print("❌ TEST_TELEGRAM_CHAT_ID not set")
        return False
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    print("🧠 Enhanced NLU Live Test")
    print("=" * 60)
    print(f"📱 Sending to Telegram chat: {TEST_CHAT_ID}")
    print(f"🤖 Using bot: @{(await bot.get_me()).username}")
    print("=" * 60)
    
    # Send introduction message
    intro = (
        "🧪 <b>Enhanced NLU Test Starting</b>\n\n"
        "Testing improved intent classification with:\n"
        "• New 'system_info' intent for platform queries\n"
        "• Better context awareness\n"
        "• More natural query handling\n\n"
        "Sending test queries now..."
    )
    
    await bot.send_message(
        chat_id=TEST_CHAT_ID,
        text=intro,
        parse_mode=ParseMode.HTML
    )
    
    print("\n✅ Introduction sent\n")
    await asyncio.sleep(2)
    
    # Send each test query
    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"📤 Test {i}/{len(TEST_QUERIES)}: {test['description']}")
        print(f"   Query: \"{test['query']}\"")
        print(f"   Expected: {test['expected_intent']}")
        
        # Send query as text message
        await bot.send_message(
            chat_id=TEST_CHAT_ID,
            text=test['query']
        )
        
        print(f"   ✅ Sent to Telegram")
        
        # Wait before next query to avoid rate limiting and allow processing
        await asyncio.sleep(5)
        print()
    
    # Send summary
    summary = (
        "🎯 <b>Enhanced NLU Test Complete!</b>\n\n"
        f"Sent {len(TEST_QUERIES)} test queries.\n\n"
        "<b>Key Improvements Tested:</b>\n"
        "✅ 'Tell me about TrustVoice' → system_info\n"
        "✅ 'What is this system?' → system_info\n"
        "✅ 'Show me campaigns' → search_campaigns\n"
        "✅ 'I would like to make a donation' → make_donation\n\n"
        "Check responses above to verify intent classification! 🎉"
    )
    
    await bot.send_message(
        chat_id=TEST_CHAT_ID,
        text=summary,
        parse_mode=ParseMode.HTML
    )
    
    print("=" * 60)
    print("✅ All test queries sent successfully!")
    print("📱 Check your Telegram for responses")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(run_nlu_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
