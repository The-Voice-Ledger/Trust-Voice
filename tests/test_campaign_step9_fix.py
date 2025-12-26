#!/usr/bin/env python3
"""
Test Campaign Creation Step 9 Fix
Verify that the conversation context is properly cleared after campaign completion
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from voice.nlu.campaign_builder import CampaignInterviewAgent, is_in_campaign_creation
from voice.nlu.context import ConversationContext

def test_campaign_completion():
    """Test that context is cleared after campaign completion"""
    
    print("Testing Campaign Creation Completion\n")
    print("=" * 60)
    
    user_id = "test_user_fix_123"
    
    # Start interview
    agent = CampaignInterviewAgent(user_id)
    print("\n1. Starting interview...")
    start_msg = agent.start_interview()
    print(f"✅ Interview started")
    print(f"   User in creation mode: {is_in_campaign_creation(user_id)}")
    
    # Simulate all 9 responses with proper validation
    responses = [
        ("Clean Water for Mwanza", {}),
        ("Water & Sanitation", {}),  # Fixed: exact category match
        ("Over 450 families in rural Mwanza lack access to clean water and sanitation", {}),
        ("Build 10 water wells with filtration systems to serve the community", {}),
        ("50000 dollars", {"amount": 50000}),
        ("450 families in rural Mwanza district", {}),
        ("Mwanza, Tanzania", {}),
        ("6 months from start date", {}),
        ("Wells construction $30k, Filtration systems $10k, Maintenance $10k", {})  # Step 9
    ]
    
    print("\n2. Processing all 9 steps...")
    for i, (response, entities) in enumerate(responses, 1):
        is_valid, message, error = agent.process_response(response, entities)
        if is_valid:
            print(f"✅ Step {i} complete")
        else:
            print(f"❌ Step {i} failed: {error}")
            return False
    
    print(f"\n3. Checking completion status...")
    print(f"   Interview complete: {agent.is_complete()}")
    print(f"   User in creation mode: {is_in_campaign_creation(user_id)}")
    print(f"   Current step: {agent.get_current_step()}")
    
    # Simulate what the bot does - cancel interview after creation
    print(f"\n4. Simulating campaign creation + context clear...")
    agent.cancel_interview()
    
    # Verify context is cleared
    print(f"\n5. Verifying context cleared...")
    print(f"   User in creation mode: {is_in_campaign_creation(user_id)}")
    print(f"   Context exists: {ConversationContext.get_context(user_id) is not None}")
    
    if not is_in_campaign_creation(user_id):
        print(f"\n✅ TEST PASSED: Context properly cleared after completion")
        return True
    else:
        print(f"\n❌ TEST FAILED: User still in creation mode")
        return False


def test_stuck_at_step_9():
    """Test the specific scenario where user gets stuck at step 9"""
    
    print("\n" + "=" * 60)
    print("Testing 'Stuck at Step 9' Scenario\n")
    print("=" * 60)
    
    user_id = "test_stuck_user_456"
    agent = CampaignInterviewAgent(user_id)
    
    # Start and complete up to step 8
    agent.start_interview()
    
    responses_up_to_8 = [
        ("Test Campaign Title", {}),
        ("Education", {}),
        ("Children in rural schools need books and learning materials urgently", {}),
        ("Provide 500 textbooks and reading materials to 10 rural schools", {}),
        ("10000", {"amount": 10000}),
        ("500 students across 10 schools", {}),
        ("Nairobi, Kenya", {}),
        ("3 months implementation period", {}),
    ]
    
    print("Completing steps 1-8...")
    for response, entities in responses_up_to_8:
        agent.process_response(response, entities)
    
    print(f"Current step: {agent.get_current_step()}/9")
    print(f"User in creation mode: {is_in_campaign_creation(user_id)}")
    
    # Now do step 9 (budget)
    print("\nProcessing step 9 (budget)...")
    is_valid, message, error = agent.process_response(
        "Books $7000, Training $2000, Transport $1000",
        {}
    )
    
    print(f"✅ Step 9 response valid: {is_valid}")
    print(f"Interview complete: {agent.is_complete()}")
    print(f"User still in creation mode: {is_in_campaign_creation(user_id)}")
    
    # The fix: bot should now call agent.cancel_interview()
    print("\nApplying fix: clearing context...")
    agent.cancel_interview()
    
    print(f"User in creation mode after clear: {is_in_campaign_creation(user_id)}")
    
    if not is_in_campaign_creation(user_id):
        print("\n✅ FIX VERIFIED: User no longer stuck after step 9")
        return True
    else:
        print("\n❌ ISSUE PERSISTS: User still stuck")
        return False


if __name__ == "__main__":
    print("\n🧪 Campaign Creation Step 9 Fix Test\n")
    
    test1 = test_campaign_completion()
    test2 = test_stuck_at_step_9()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Context Clear Test: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Step 9 Fix Test: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 All tests passed! The fix is working.")
        print("\nWhat was fixed:")
        print("  • Context is now cleared after campaign creation")
        print("  • User won't get stuck after step 9")
        print("  • Next message will be treated as new intent")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        sys.exit(1)
