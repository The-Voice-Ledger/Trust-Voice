"""
Test Lab 8 - Complete Donation with Confirmation
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from voice.session_manager import SessionManager, is_in_conversation
from voice.workflows.donation_flow import route_donation_message, DonationConversation
from database.db import SessionLocal
from database.models import Donation

async def test_complete_donation():
    """Test donation flow through to completion"""
    
    print("=" * 60)
    print("Testing Complete Donation with Confirmation")
    print("=" * 60)
    
    # Use real user: Emmanuel (SYSTEM_ADMIN)
    user_id = "5753848438"
    db = SessionLocal()
    
    try:
        # Step 1: Start
        print("\n1. Starting donation...")
        result = await DonationConversation.start(user_id, db)
        print(f"   ✅ {result['step']}")
        
        # Step 2: Select campaign
        print("\n2. Selecting campaign 1...")
        result = await route_donation_message(user_id, "1", db)
        print(f"   ✅ {result['step']}")
        
        # Step 3: Enter amount
        print("\n3. Entering amount 1000...")
        result = await route_donation_message(user_id, "1000", db)
        print(f"   ✅ {result['step']}")
        
        # Step 4: Select payment
        print("\n4. Selecting Telebirr...")
        result = await route_donation_message(user_id, "Telebirr", db)
        print(f"   ✅ {result['step']}")
        print(f"   Summary shown: {result['message'][:100]}...")
        
        # Step 5: Confirm donation
        print("\n5. Confirming donation...")
        
        # Check initial donation count
        initial_count = db.query(Donation).count()
        print(f"   Donations before: {initial_count}")
        
        result = await route_donation_message(user_id, "confirm", db)
        print(f"   Bot: {result['message']}")
        print(f"   Step: {result['step']}")
        
        # Verify donation was created
        final_count = db.query(Donation).count()
        print(f"   Donations after: {final_count}")
        
        assert result['step'] == 'completed', "Should be completed"
        assert 'donation_id' in result, "Should return donation ID"
        assert not is_in_conversation(user_id), "Conversation should end"
        
        # Get the donation record
        donation_id = result['donation_id']
        donation = db.query(Donation).filter(Donation.id == donation_id).first()
        
        if donation:
            print(f"\n   ✅ Donation created:")
            print(f"      ID: {donation.id}")
            print(f"      Amount: ${donation.amount}")
            print(f"      Payment Method: {donation.payment_method}")
            print(f"      Status: {donation.status}")
        
        print("\n" + "=" * 60)
        print("✅ Complete donation flow successful!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Cleanup
        SessionManager.end_session(user_id)
        db.close()


if __name__ == "__main__":
    asyncio.run(test_complete_donation())
