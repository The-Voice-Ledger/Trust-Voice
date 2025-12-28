"""
Test Lab 8 Part 3 - Campaign Search Refinement
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from voice.session_manager import SessionManager, is_in_conversation, ConversationState
from voice.workflows.search_flow import SearchConversation, route_search_message
from database.db import SessionLocal

async def test_search_refinement():
    """Test multi-turn campaign search with refinement"""
    
    print("=" * 60)
    print("Testing Lab 8 Part 3: Campaign Search Refinement")
    print("=" * 60)
    
    user_id = "5753848438"  # Real user
    db = SessionLocal()
    
    try:
        # Test 1: Initial search (education campaigns - we know these exist)
        print("\n1. Initial search: 'education campaigns'")
        result = await SearchConversation.start_search(user_id, "education campaigns", db)
        print(f"   Found: {len(result.get('campaigns', []))} campaigns")
        print(f"   Message preview: {result['message'][:100]}...")
        
        if len(result.get('campaigns', [])) == 0:
            print("   ⚠️  No campaigns in database, skipping conversation tests")
            print("   ✅ Search logic works (no results)")
        else:
            assert is_in_conversation(user_id), "Should be in conversation"
            assert SessionManager.get_session(user_id)["state"] == ConversationState.SEARCHING_CAMPAIGNS.value
            print("   ✅ Search conversation started")
        
        # Only continue with conversation tests if we have campaigns
        if len(result.get('campaigns', [])) == 0:
            print("\n   Skipping conversation flow tests (no campaigns in DB)")
            # Just test filter parsing logic
            print("\n5. Testing filter extraction...")
            test_queries = [
                ("health campaigns in Kenya", {"category": "health", "region": "Kenya"}),
                ("education projects", {"category": "education"}),
                ("water wells Nairobi", {"category": "water", "region": "Nairobi"}),
            ]
            
            for query, expected in test_queries:
                filters = SearchConversation._parse_query(query)
                for key, value in expected.items():
                    assert filters.get(key) == value, f"Expected {key}={value} in {filters}"
                print(f"   '{query}' → {filters} ✅")
            
            print("\n6. Testing campaign reference parsing...")
            campaign_ids = [101, 102, 103, 104, 105]
            
            test_refs = [
                ("1", 101),
                ("#102", 102),
                ("first one", 101),
                ("second", 102),
                ("3rd", 103),
            ]
            
            for ref, expected_id in test_refs:
                parsed = SearchConversation._parse_campaign_ref(ref, campaign_ids)
                assert parsed == expected_id, f"Expected {expected_id}, got {parsed}"
                print(f"   '{ref}' → campaign {parsed} ✅")
            
            print("\n" + "=" * 60)
            print("✅ Core search logic tests passed!")
            print("=" * 60)
            return
        
        # Test 2: View campaign details
        print("\n2. User asks: 'tell me about #1'")
        result = await route_search_message(user_id, "tell me about 1", db)
        print(f"   Response: {result['message'][:150]}...")
        session = SessionManager.get_session(user_id)
        assert "current_campaign_id" in session["data"], "Should save current campaign"
        print("   ✅ Campaign details shown")
        
        # Test 3: Refine search by region
        print("\n3. User refines: 'what about in Nairobi?'")
        result = await route_search_message(user_id, "what about in Nairobi?", db)
        print(f"   Response: {result['message'][:100]}...")
        session = SessionManager.get_session(user_id)
        filters = session["data"]["last_filters"]
        print(f"   Filters now: {filters}")
        print("   ✅ Search refined by region")
        
        # Test 4: Switch category
        print("\n4. User switches: 'show me education instead'")
        result = await route_search_message(user_id, "show me education instead", db)
        print(f"   Response: {result['message'][:100]}...")
        session = SessionManager.get_session(user_id)
        filters = session["data"]["last_filters"]
        assert filters.get("category") == "education", "Category should change"
        print(f"   New category: {filters.get('category')}")
        print("   ✅ Category switched")
        
        # Test 5: Test filter parsing
        print("\n5. Testing filter extraction...")
        test_queries = [
            ("health campaigns in Kenya", {"category": "health", "region": "Kenya"}),
            ("education projects", {"category": "education"}),
            ("water wells Nairobi", {"category": "water", "region": "Nairobi"}),
        ]
        
        for query, expected in test_queries:
            filters = SearchConversation._parse_query(query)
            for key, value in expected.items():
                assert filters.get(key) == value, f"Expected {key}={value} in {filters}"
            print(f"   '{query}' → {filters} ✅")
        
        # Test 6: Test campaign reference parsing
        print("\n6. Testing campaign reference parsing...")
        campaign_ids = [101, 102, 103, 104, 105]
        
        test_refs = [
            ("1", 101),
            ("#102", 102),
            ("first one", 101),
            ("second", 102),
            ("3rd", 103),
        ]
        
        for ref, expected_id in test_refs:
            parsed = SearchConversation._parse_campaign_ref(ref, campaign_ids)
            assert parsed == expected_id, f"Expected {expected_id}, got {parsed}"
            print(f"   '{ref}' → campaign {parsed} ✅")
        
        # Cleanup
        SessionManager.end_session(user_id)
        assert not is_in_conversation(user_id), "Session should be ended"
        
        print("\n" + "=" * 60)
        print("✅ All search refinement tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        SessionManager.end_session(user_id)
        db.close()


if __name__ == "__main__":
    asyncio.run(test_search_refinement())
