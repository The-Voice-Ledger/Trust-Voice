"""
Lab 6 Comprehensive Test Suite

Tests all Lab 6 components:
- Command router with 14 handlers
- Context preservation (multi-turn conversations)
- Entity validation and clarification
- Guest vs registered user flows
- Lab 5 handler integration
- Error handling
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

YOUR_CHAT_ID = "5753848438"  # Update with your chat ID


async def test_lab6_handlers():
    """Test Lab 6 command router and handlers."""
    
    from telegram import Bot
    from voice.telegram.voice_responses import send_voice_reply
    
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    
    print("\n" + "=" * 80)
    print("LAB 6 COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"📱 Sending test messages to: {YOUR_CHAT_ID}")
    print()
    
    passed = 0
    total = 0
    
    # ========================================================================
    # TEST CATEGORY 1: GENERAL HANDLERS (4 handlers)
    # ========================================================================
    
    print("=" * 80)
    print("CATEGORY 1: GENERAL HANDLERS")
    print("=" * 80)
    
    # Test 1.1: get_help handler
    total += 1
    print(f"\nTEST {total}: get_help Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Help' (text or voice)\n\nExpected: Customized help menu based on your role",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 1.2: greeting handler
    total += 1
    print(f"\nTEST {total}: greeting Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send voice 'Hello' or 'Good morning'\n\nExpected: Personalized greeting with your name",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 1.3: change_language handler
    total += 1
    print(f"\nTEST {total}: change_language Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Switch to Amharic'\n\nExpected: Language preference updated in database",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 1.4: unknown handler (fallback)
    total += 1
    print(f"\nTEST {total}: unknown Handler (Fallback)")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'qwerty asdf nonsense'\n\nExpected: Fallback message suggesting help",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # ========================================================================
    # TEST CATEGORY 2: DONOR HANDLERS (6 handlers)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("CATEGORY 2: DONOR HANDLERS")
    print("=" * 80)
    
    # Test 2.1: search_campaigns handler
    total += 1
    print(f"\nTEST {total}: search_campaigns Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Show me education campaigns'\n\nExpected: List of campaigns with progress bars",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2.2: view_campaign_details handler
    total += 1
    print(f"\nTEST {total}: view_campaign_details Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: After search, send 'Tell me about number 1'\n\nExpected: Detailed campaign info with NGO, donations, verification",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2.3: view_donation_history handler
    total += 1
    print(f"\nTEST {total}: view_donation_history Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Show my donation history'\n\nExpected: List of past donations with total",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2.4: get_campaign_updates handler
    total += 1
    print(f"\nTEST {total}: get_campaign_updates Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Get updates for campaign number 1'\n\nExpected: Recent donations and progress for that campaign",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2.5: get_impact_report handler
    total += 1
    print(f"\nTEST {total}: get_impact_report Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Show impact report for campaign 1'\n\nExpected: Field verification details with GPS, trust score",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2.6: make_donation handler (Lab 5 integration)
    total += 1
    print(f"\nTEST {total}: make_donation Handler (Lab 5 Integration)")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Donate 10 dollars to campaign number 1'\n\nExpected: Payment initiation via Lab 5 donation_handler",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # ========================================================================
    # TEST CATEGORY 3: CONTEXT PRESERVATION (Multi-turn)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("CATEGORY 3: CONTEXT PRESERVATION")
    print("=" * 80)
    
    # Test 3.1: Multi-turn conversation
    total += 1
    print(f"\nTEST {total}: Multi-Turn Context (Search → Details)")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Multi-turn conversation\n\nStep 1: Send 'Show water campaigns'\nStep 2: Send 'Tell me about number 1'\n\nExpected: Context preserved, 'number 1' resolves to first search result",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3.2: Context-aware donation
    total += 1
    print(f"\nTEST {total}: Context-Aware Donation")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Context-aware donation\n\nStep 1: Search campaigns\nStep 2: Send 'Donate 50 to number 2'\n\nExpected: Campaign ID resolved from context",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # ========================================================================
    # TEST CATEGORY 4: ENTITY VALIDATION
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("CATEGORY 4: ENTITY VALIDATION")
    print("=" * 80)
    
    # Test 4.1: Missing required entities
    total += 1
    print(f"\nTEST {total}: Missing Entity - Amount")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'I want to donate' (no amount)\n\nExpected: Clarification question asking for amount",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4.2: Missing campaign reference
    total += 1
    print(f"\nTEST {total}: Missing Entity - Campaign")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Show campaign details' (no campaign specified)\n\nExpected: Ask which campaign or suggest searching first",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # ========================================================================
    # TEST CATEGORY 5: NGO HANDLERS (4 handlers)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("CATEGORY 5: NGO HANDLERS")
    print("=" * 80)
    
    # Test 5.1: view_my_campaigns handler
    total += 1
    print(f"\nTEST {total}: view_my_campaigns Handler (NGO Dashboard)")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Show my campaigns' or 'My dashboard'\n\nExpected: Role check + campaign list (if NGO) or permission error",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 5.2: create_campaign handler
    total += 1
    print(f"\nTEST {total}: create_campaign Handler")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Create campaign for clean water, goal 5000 dollars'\n\nExpected: Role check + campaign creation (if NGO/admin)",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 5.3: withdraw_funds handler (Lab 5 integration)
    total += 1
    print(f"\nTEST {total}: withdraw_funds Handler (Lab 5 Payout)")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Withdraw 100 dollars from campaign'\n\nExpected: Lab 5 payout_handler called for M-Pesa withdrawal",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 5.4: field_report handler (Lab 5 integration)
    total += 1
    print(f"\nTEST {total}: field_report Handler (Lab 5 Verification)")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Send 'Submit field report for campaign with 50 beneficiaries'\n\nExpected: Lab 5 impact_handler processes verification",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # ========================================================================
    # TEST CATEGORY 6: GUEST USER SUPPORT
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("CATEGORY 6: GUEST USER SUPPORT")
    print("=" * 80)
    
    # Test 6.1: Guest user search
    total += 1
    print(f"\nTEST {total}: Guest User - Search Campaigns")
    print("-" * 80)
    try:
        await send_voice_reply(
            bot=bot,
            chat_id=int(YOUR_CHAT_ID),
            message="🧪 LAB 6 TEST: Log out, then send 'Show campaigns'\n\nExpected: Works without registration (guest mode)",
            language="en",
            send_voice=False
        )
        print("✅ Test prompt sent")
        passed += 1
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # ========================================================================
    # RESULTS SUMMARY
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"✅ Tests initiated: {passed}/{total}")
    print(f"\n📱 Check your Telegram to verify responses!")
    print()
    print("What to verify:")
    print("  1. Each handler responds appropriately")
    print("  2. Context preserved across turns (search → 'number 1')")
    print("  3. Missing entities trigger clarification questions")
    print("  4. Role-based access works (NGO handlers check permissions)")
    print("  5. Lab 5 integration works (donations, payouts, verifications)")
    print("  6. Guest users can browse (no registration required)")
    print()
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(test_lab6_handlers())
