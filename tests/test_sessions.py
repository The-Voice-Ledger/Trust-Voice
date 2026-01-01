"""Test session management"""

from voice.session_manager import (
    SessionManager, 
    ConversationState,
    start_donation_flow,
    is_in_conversation
)

def test_session_lifecycle():
    """Test creating, updating, and ending sessions"""
    
    user_id = "test_user_123"
    
    # 1. Create session
    print("1. Creating donation session...")
    session = start_donation_flow(user_id)
    print(f"   State: {session['state']}")
    assert session['state'] == ConversationState.DONATING.value
    print("   ✅ Session created")
    
    # 2. Check if in conversation
    print("\n2. Checking conversation status...")
    assert is_in_conversation(user_id) == True
    print("   ✅ User is in conversation")
    
    # 3. Update session with data
    print("\n3. Updating session with campaign selection...")
    session = SessionManager.update_session(
        user_id,
        current_step="enter_amount",
        data_update={"campaign_id": 42, "campaign_name": "Clean Water Kenya"},
        message="User selected Clean Water campaign"
    )
    print(f"   Step: {session['current_step']}")
    print(f"   Data: {session['data']}")
    print("   ✅ Session updated")
    
    # 4. Add more data
    print("\n4. Adding amount...")
    session = SessionManager.update_session(
        user_id,
        current_step="select_payment",
        data_update={"amount": 500},
        message="User entered amount: 500"
    )
    print(f"   Amount: {session['data']['amount']}")
    print("   ✅ Amount added")
    
    # 5. Check history
    print("\n5. Conversation history:")
    for entry in session['history']:
        print(f"   - {entry['message']}")
    
    # 6. End session
    print("\n6. Ending session...")
    SessionManager.end_session(user_id)
    assert is_in_conversation(user_id) == False
    print("   ✅ Session ended")
    
    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50)


if __name__ == "__main__":
    test_session_lifecycle()
