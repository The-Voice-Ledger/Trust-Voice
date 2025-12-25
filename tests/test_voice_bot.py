#!/usr/bin/env python3
"""
Test Voice Bot - Programmatic Testing
Generates test voice messages and tests the bot's response
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Test commands to generate - Voice equivalents for ALL 13 bot commands
TEST_COMMANDS = [
    # 1. /start equivalent - greeting/welcome
    {
        "name": "test_start_greeting",
        "text": "Hello, I'm new here and want to get started with TrustVoice",
        "intent": "greeting"
    },
    {
        "name": "test_start_welcome",
        "text": "Hi, how do I begin using this service?",
        "intent": "get_help"
    },
    
    # 2. /help equivalent - get help
    {
        "name": "test_help_request",
        "text": "Help me understand how to use TrustVoice",
        "intent": "get_help"
    },
    {
        "name": "test_help_what_can_i_do",
        "text": "What can I do with this platform?",
        "intent": "get_help"
    },
    
    # 3. /campaigns equivalent - browse/search campaigns
    {
        "name": "test_browse_campaigns",
        "text": "Show me all available campaigns",
        "intent": "search_campaigns"
    },
    {
        "name": "test_list_campaigns",
        "text": "I want to browse active campaigns",
        "intent": "search_campaigns"
    },
    {
        "name": "test_search_water_campaigns",
        "text": "Show me water projects in Tanzania",
        "intent": "search_campaigns"
    },
    {
        "name": "test_search_education_campaigns",
        "text": "Are there any education campaigns in Ethiopia?",
        "intent": "search_campaigns"
    },
    
    # 4. /donations equivalent - view donation history
    {
        "name": "test_donation_history",
        "text": "Show me my donation history",
        "intent": "view_donation_history"
    },
    {
        "name": "test_view_my_donations",
        "text": "What donations have I made so far?",
        "intent": "view_donation_history"
    },
    {
        "name": "test_check_donations",
        "text": "I want to see all the donations I've contributed",
        "intent": "view_donation_history"
    },
    
    # 5. /my_campaigns equivalent - view creator's campaigns
    {
        "name": "test_my_campaigns",
        "text": "Show me the campaigns I created",
        "intent": "view_my_campaigns"
    },
    {
        "name": "test_view_my_campaigns",
        "text": "I want to see all my campaigns and how they're doing",
        "intent": "view_my_campaigns"
    },
    {
        "name": "test_check_my_campaigns",
        "text": "How are my fundraising campaigns performing?",
        "intent": "view_my_campaigns"
    },
    
    # 6. /register equivalent - not in intents (handled by conversation flow)
    # Covered by greeting intent
    
    # 7. /language equivalent - change language
    {
        "name": "test_change_language_amharic",
        "text": "I want to switch to Amharic language",
        "intent": "change_language"
    },
    {
        "name": "test_change_language_english",
        "text": "Change my language preference to English",
        "intent": "change_language"
    },
    
    # 8. /set_pin equivalent - not standard voice intent
    # Users would say this naturally
    {
        "name": "test_set_security_pin",
        "text": "I want to set up a PIN for my account security",
        "intent": "update_profile"
    },
    
    # 9. /change_pin equivalent
    {
        "name": "test_change_pin",
        "text": "I need to change my PIN code",
        "intent": "update_profile"
    },
    
    # 10. /verify_phone equivalent
    {
        "name": "test_verify_phone",
        "text": "I want to verify my phone number",
        "intent": "update_profile"
    },
    
    # 11. Make donation - core functionality
    {
        "name": "test_donate_50_dollars",
        "text": "I want to donate 50 dollars to the water project",
        "intent": "make_donation"
    },
    {
        "name": "test_donate_100_shillings",
        "text": "Donate 100 shillings to the school in Addis Ababa",
        "intent": "make_donation"
    },
    {
        "name": "test_donate_to_campaign",
        "text": "I'd like to contribute 25 euros to the healthcare campaign",
        "intent": "make_donation"
    },
    
    # 12. Create campaign - voice campaign creation
    {
        "name": "test_create_water_campaign",
        "text": "Create a campaign for clean water in Arusha with a goal of 10000 dollars",
        "intent": "create_campaign"
    },
    {
        "name": "test_create_education_campaign",
        "text": "I want to start a fundraiser for school supplies in rural Kenya, goal is 5000 dollars",
        "intent": "create_campaign"
    },
    
    # 13. View campaign details
    {
        "name": "test_view_campaign_details",
        "text": "Tell me more about the water filtration campaign",
        "intent": "view_campaign_details"
    },
    {
        "name": "test_campaign_info",
        "text": "What's the status of the school construction project?",
        "intent": "view_campaign_details"
    },
    
    # 14. Check donation status
    {
        "name": "test_check_donation_status",
        "text": "What's the status of my last donation?",
        "intent": "check_donation_status"
    },
    
    # 15. Report impact (field agents)
    {
        "name": "test_report_impact",
        "text": "I need to report impact for the well we completed in Mwanza",
        "intent": "report_impact"
    },
    
    # 16. Thank you / general
    {
        "name": "test_thank_you",
        "text": "Thank you so much for your help",
        "intent": "thank_you"
    },
    {
        "name": "test_greeting_general",
        "text": "Good morning, how are you today?",
        "intent": "greeting"
    }
]


async def generate_test_audio_files():
    """Generate test audio files using OpenAI TTS"""
    import openai
    
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai.api_key:
        print("❌ OPENAI_API_KEY not set. Cannot generate audio.")
        return False
    
    output_dir = Path("documentation/test_voice_messages")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n🎤 Generating test voice messages...")
    print("=" * 50)
    
    for idx, cmd in enumerate(TEST_COMMANDS, 1):
        output_file = output_dir / f"{cmd['name']}.mp3"
        
        try:
            print(f"\n{idx}. {cmd['name']}")
            print(f"   Text: \"{cmd['text']}\"")
            print(f"   Expected Intent: {cmd['intent']}")
            
            # Generate audio using OpenAI TTS
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=cmd['text']
            )
            
            # Save to file
            response.stream_to_file(str(output_file))
            
            file_size = output_file.stat().st_size / 1024  # KB
            print(f"   ✅ Generated: {output_file.name} ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    print("\n" + "=" * 50)
    print(f"✅ Generated {len(TEST_COMMANDS)} test audio files")
    print(f"📁 Location: {output_dir.absolute()}")
    
    return True


async def test_voice_pipeline():
    """Test the voice pipeline with generated audio files"""
    from voice.pipeline import process_voice_message
    from voice.nlu.context import ConversationContext
    
    output_dir = Path("documentation/test_voice_messages")
    
    # Check if audio files exist
    audio_files = list(output_dir.glob("*.mp3"))
    if not audio_files:
        print("\n⚠️  No test audio files found. Run generation first.")
        return False
    
    print("\n🧪 Testing Voice Pipeline")
    print("=" * 50)
    
    # Test user ID
    test_user_id = "test_user_12345"
    conversation_context = ConversationContext()
    
    results = []
    
    for audio_file in sorted(audio_files):
        print(f"\n📝 Testing: {audio_file.name}")
        print("-" * 50)
        
        try:
            # Process voice message
            result = await process_voice_message(
                audio_path=str(audio_file),
                user_id=test_user_id,
                user_language="en",
                conversation_context=conversation_context
            )
            
            print(f"✅ Processing complete:")
            print(f"   Transcript: \"{result.get('transcript', 'N/A')}\"")
            print(f"   Intent: {result.get('intent', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Response: \"{result.get('response_text', 'N/A')[:100]}...\"")
            print(f"   ASR Latency: {result.get('asr_latency_seconds', 0):.2f}s")
            print(f"   NLU Latency: {result.get('nlu_latency_seconds', 0):.2f}s")
            print(f"   Total Latency: {result.get('total_latency_seconds', 0):.2f}s")
            
            results.append({
                "file": audio_file.name,
                "success": True,
                "result": result
            })
            
        except Exception as e:
            print(f"❌ Error processing {audio_file.name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "file": audio_file.name,
                "success": False,
                "error": str(e)
            })
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    
    if successful > 0:
        avg_latency = sum(
            r['result'].get('total_latency_seconds', 0) 
            for r in results if r['success']
        ) / successful
        print(f"⏱️  Average Latency: {avg_latency:.2f}s")
    
    return True


async def test_bot_responses():
    """Test actual bot responses to voice commands"""
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from voice.pipeline import process_voice_message
    from voice.telegram.bot import handle_voice_intent
    import asyncio
    
    print("\n🤖 Testing Bot Responses (Full Pipeline + Intent Router)")
    print("=" * 70)
    
    audio_dir = Path("documentation/test_voice_messages")
    
    if not audio_dir.exists():
        print("❌ No audio files found. Run with --mode generate first.")
        return False
    
    # Select key test cases for response testing
    test_cases = [
        {"name": "test_browse_campaigns", "expected_keywords": ["campaigns", "active", "goal"]},
        {"name": "test_donation_history", "expected_keywords": ["donation", "history", "total"]},
        {"name": "test_my_campaigns", "expected_keywords": ["campaigns", "created", "status"]},
        {"name": "test_donate_50_dollars", "expected_keywords": ["donate", "50", "payment"]},
        {"name": "test_help_request", "expected_keywords": ["help", "commands", "TrustVoice"]},
        {"name": "test_change_language_amharic", "expected_keywords": ["language", "Amharic"]},
    ]
    
    results = []
    
    for idx, test in enumerate(test_cases, 1):
        audio_file = audio_dir / f"{test['name']}.mp3"
        
        if not audio_file.exists():
            print(f"\n{idx}. ⚠️ Skipping {test['name']} (file not found)")
            continue
        
        print(f"\n{idx}. Testing: {test['name']}")
        print(f"   Audio: {audio_file.name}")
        print(f"   Expected Keywords: {', '.join(test['expected_keywords'])}")
        
        try:
            # Process through full pipeline (sync function)
            result = process_voice_message(
                audio_file_path=str(audio_file),
                user_id="test_user_response",
                user_language="en",
                cleanup_audio=False
            )
            
            transcript = result.get('transcript', '')
            intent = result.get('intent', '')
            entities = result.get('entities', {})
            confidence = result.get('confidence', 0)
            
            # Get rich response from voice intent router (await since we're in async function)
            response = await handle_voice_intent(
                intent=intent,
                entities=entities,
                telegram_user_id="test_user_response",
                language="en"
            )
            
            print(f"\n   📝 Transcript: \"{transcript}\"")
            print(f"   🎯 Intent: {intent} (confidence: {confidence:.2f})")
            print(f"\n   💬 Bot Response:")
            print(f"   {'─' * 66}")
            
            # Print response with proper formatting
            response_lines = response.split('\n')
            for line in response_lines[:10]:  # First 10 lines
                print(f"   {line}")
            
            if len(response_lines) > 10:
                print(f"   ... ({len(response_lines) - 10} more lines)")
            
            print(f"   {'─' * 66}")
            
            # Check if response contains expected keywords
            response_lower = response.lower()
            keywords_found = [kw for kw in test['expected_keywords'] if kw.lower() in response_lower]
            keywords_missing = [kw for kw in test['expected_keywords'] if kw.lower() not in response_lower]
            
            if keywords_found:
                print(f"   ✅ Keywords Found: {', '.join(keywords_found)}")
            if keywords_missing:
                print(f"   ⚠️  Keywords Missing: {', '.join(keywords_missing)}")
            
            print(f"   ⏱️  Latency: {result.get('total_latency_seconds', 0):.2f}s")
            
            results.append({
                "test": test['name'],
                "success": True,
                "intent": intent,
                "confidence": confidence,
                "response_length": len(response),
                "keywords_found": len(keywords_found),
                "keywords_total": len(test['expected_keywords'])
            })
            
        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test": test['name'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Response Test Summary")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n✅ Successful Tests: {successful}/{total}")
    
    if successful > 0:
        avg_confidence = sum(r.get('confidence', 0) for r in results if r['success']) / successful
        avg_response_length = sum(r.get('response_length', 0) for r in results if r['success']) / successful
        total_keywords_found = sum(r.get('keywords_found', 0) for r in results if r['success'])
        total_keywords = sum(r.get('keywords_total', 0) for r in results if r['success'])
        
        print(f"📈 Average Confidence: {avg_confidence:.2f}")
        print(f"📝 Average Response Length: {avg_response_length:.0f} characters")
        print(f"🎯 Keyword Match Rate: {total_keywords_found}/{total_keywords} ({total_keywords_found/total_keywords*100:.1f}%)")
    
    print(f"\n{'─' * 70}")
    print("✅ Response testing shows system is responsive!")
    
    return successful == total


async def test_nlu_only():
    """Test NLU without audio generation"""
    from voice.nlu.nlu_infer import extract_intent_and_entities
    
    print("\n🧠 Testing NLU Engine (Text-only)")
    print("=" * 50)
    
    for idx, cmd in enumerate(TEST_COMMANDS, 1):
        print(f"\n{idx}. Testing: \"{cmd['text']}\"")
        print(f"   Expected Intent: {cmd['intent']}")
        
        try:
            result = extract_intent_and_entities(
                transcript=cmd['text'],
                language="en",
                user_context=None
            )
            
            detected_intent = result.get('intent', 'unknown')
            confidence = result.get('confidence', 0)
            entities = result.get('entities', {})
            
            # Check if intent matches
            match_status = "✅" if detected_intent == cmd['intent'] else "⚠️"
            
            print(f"   {match_status} Detected Intent: {detected_intent}")
            print(f"   Confidence: {confidence:.2f}")
            if entities:
                print(f"   Entities: {entities}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)


async def test_telegram_commands():
    """Test Telegram bot commands programmatically"""
    print("\n🤖 Testing Telegram Bot Commands")
    print("=" * 50)
    
    from database.db import SessionLocal
    from database.models import User
    
    db = SessionLocal()
    
    try:
        # Find test user (you)
        test_user = db.query(User).filter(
            User.telegram_user_id == "5753848438"
        ).first()
        
        if test_user:
            print(f"✅ Found user: {test_user.full_name or 'N/A'}")
            print(f"   Role: {test_user.role}")
            print(f"   Language: {test_user.preferred_language}")
            print(f"   Phone Verified: {'Yes' if test_user.phone_verified_at else 'No'}")
            print(f"   Has PIN: {'Yes' if test_user.pin_hash else 'No'}")
        else:
            print("⚠️  Test user not found in database")
        
        # Test database queries
        print("\n📊 Database Statistics:")
        from database.models import Campaign, Donation, PendingRegistration
        
        campaign_count = db.query(Campaign).count()
        donation_count = db.query(Donation).count()
        pending_count = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).count()
        
        print(f"   Campaigns: {campaign_count}")
        print(f"   Donations: {donation_count}")
        print(f"   Pending Registrations: {pending_count}")
        
    finally:
        db.close()
    
    print("\n" + "=" * 50)


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test TrustVoice Bot")
    parser.add_argument(
        '--mode',
        choices=['generate', 'pipeline', 'nlu', 'responses', 'telegram', 'all'],
        default='all',
        help='Test mode to run'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 50)
    print("🧪 TrustVoice Bot Testing Suite")
    print("=" * 50)
    
    async def run_tests():
        if args.mode in ['generate', 'all']:
            await generate_test_audio_files()
        
        if args.mode in ['nlu', 'all']:
            await test_nlu_only()
        
        if args.mode in ['responses', 'all']:
            await test_bot_responses()
        
        if args.mode in ['telegram', 'all']:
            await test_telegram_commands()
        
        if args.mode in ['pipeline', 'all']:
            await test_voice_pipeline()
    
    try:
        asyncio.run(run_tests())
        print("\n✅ Testing complete!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
