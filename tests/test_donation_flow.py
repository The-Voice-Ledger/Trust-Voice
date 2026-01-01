"""
Test Lab 8 - Multi-turn Donation Flow
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from voice.session_manager import SessionManager, is_in_conversation, get_conversation_state
from voice.workflows.donation_flow import route_donation_message, DonationConversation
from database.db import SessionLocal

async def test_donation_conversation():
    """Test complete donation conversation flow"""
    
    print("=" * 60)
    print("Testing Lab 8: Multi-turn Donation Conversation")
    print("=" * 60)
    
    user_id = "test_user_456"
    db = SessionLocal()
    
    try:
        # Test 1: Start donation flow
        print("\n1. Starting donation conversation...")
        result = await DonationConversation.start(user_id, db)
        print(f"   Bot: {result['message'][:100]}...")
        print(f"   Step: {result['step']}")
        print(f"   Campaigns offered: {len(result['campaigns'])}")
        assert is_in_conversation(user_id), "User should be in conversation"
        print("   ✅ Conversation started")
        
        # Test 2: Select campaign (simulate user saying "education" or "campaign 1")
        print("\n2. User selects campaign...")
        result = await route_donation_message(user_id, "campaign 1", db)
        print(f"   Bot: {result['message']}")
        print(f"   Step: {result['step']}")
        session = SessionManager.get_session(user_id)
        assert "campaign_id" in session["data"], "Campaign should be saved"
        print(f"   Selected: {session['data'].get('campaign_title', 'Unknown')}")
        print("   ✅ Campaign selected")
        
        # Test 3: Enter amount
        print("\n3. User enters amount...")
        result = await route_donation_message(user_id, "500", db)
        print(f"   Bot: {result['message']}")
        print(f"   Step: {result['step']}")
        session = SessionManager.get_session(user_id)
        assert session["data"]["amount"] == 500, "Amount should be saved"
        print("   ✅ Amount entered: 500")
        
        # Test 4: Select payment method
        print("\n4. User selects payment method...")
        result = await route_donation_message(user_id, "Chapa", db)
        print(f"   Bot: {result['message'][:200]}...")
        print(f"   Step: {result['step']}")
        session = SessionManager.get_session(user_id)
        assert session["data"]["payment_provider"] == "chapa", "Payment method should be saved"
        print("   ✅ Payment method selected: Chapa")
        
        # Test 5: Cancel donation
        print("\n5. User cancels...")
        result = await route_donation_message(user_id, "cancel", db)
        print(f"   Bot: {result['message']}")
        assert not is_in_conversation(user_id), "Conversation should be ended"
        print("   ✅ Donation cancelled, conversation ended")
        
        # Test 6: Test amount extraction with text
        print("\n6. Testing amount extraction...")
        test_amounts = [
            ("100", 100),
            ("500 birr", 500),
            ("donate 1000", 1000),
            ("I want to give 250", 250)
        ]
        
        for text, expected in test_amounts:
            from voice.workflows.donation_flow import DonationConversation as DC
            amount = DC._extract_amount(text)
            assert amount == expected, f"Expected {expected}, got {amount}"
            print(f"   '{text}' → {amount} ✅")
        
        print("\n" + "=" * 60)
        print("✅ All donation flow tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    
    finally:
        # Cleanup
        SessionManager.end_session(user_id)
        db.close()


if __name__ == "__main__":
    asyncio.run(test_donation_conversation())
