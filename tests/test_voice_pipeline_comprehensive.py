"""
Comprehensive Voice Pipeline Test Suite
Tests all voice interfaces in English: Campaign Creation, Donation, Verification

Tests:
1. Voice Campaign Search (Mini App)
2. Voice Donation Intent (Mini App)
3. Voice Campaign Creation (Bot Flow)
4. Voice Verification Submission (Field Agent)
5. End-to-End Voice Pipeline

Usage:
    python tests/test_voice_pipeline_comprehensive.py
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Database
from database.db import get_db
from database.models import User, Campaign, Donation, ImpactVerification

# Voice pipeline components
from voice.asr.asr_infer import transcribe_audio, ASRError
from voice.nlu.nlu_infer import extract_intent_and_entities
from voice.tts.tts_provider import TTSProvider
from voice.pipeline import process_voice_message


# Test configuration
TEST_USER_ID = "test_voice_user_12345"
TEST_FIELD_AGENT_ID = "test_agent_67890"
TEST_AUDIO_DIR = Path(__file__).parent / "test_audio"


class VoicePipelineTests:
    """Comprehensive voice pipeline test suite"""
    
    def __init__(self):
        self.tts = TTSProvider()
        self.results = []
        self.db = next(get_db())
        
        # Ensure test audio directory exists
        TEST_AUDIO_DIR.mkdir(exist_ok=True)
        
        # Event loop for async operations
        self.loop = asyncio.get_event_loop()
        
    def log_test(self, name, status, details="", duration=0):
        """Log test result"""
        result = {
            "test": name,
            "status": status,  # ✅ PASS, ❌ FAIL, ⚠️ SKIP
            "details": details,
            "duration": f"{duration:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {name} ({duration:.2f}s)")
        if details:
            print(f"   {details}")
        
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIP")
        total = len(self.results)
        
        print("\n" + "="*70)
        print("VOICE PIPELINE TEST SUMMARY")
        print("="*70)
        print(f"Total Tests:   {total}")
        print(f"✅ Passed:     {passed}")
        print(f"❌ Failed:     {failed}")
        print(f"⚠️  Skipped:    {skipped}")
        print(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        print("="*70)
        
        # Failed tests details
        if failed > 0:
            print("\nFAILED TESTS:")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  ❌ {r['test']}")
                    print(f"     {r['details']}")
        
        return passed, failed, skipped
    
    # =============================================================================
    # TEST 1: ASR (Speech-to-Text)
    # =============================================================================
    
    def test_1_asr_english(self):
        """Test ASR with synthesized English audio"""
        start = time.time()
        
        try:
            # Create test audio using TTS
            test_text = "Show me water projects in Kenya"
            success, audio_path, error = self.loop.run_until_complete(
                self.tts.text_to_speech(
                    text=test_text,
                    language="en",
                    voice="nova"
                )
            )
            
            if not success:
                self.log_test(
                    "1. ASR - English TTS Generation",
                    "FAIL",
                    f"TTS failed: {error}",
                    time.time() - start
                )
                return None
            
            # Test ASR transcription
            result = transcribe_audio(
                audio_file_path=audio_path,
                language="en"
            )
            
            print(f"   DEBUG: ASR result = {result}")
            
            transcript = result.get("text")  # ASR returns "text" not "transcript"
            language = result.get("language")
            method = result.get("method")
            confidence = result.get("confidence", 0)
            
            # Validate results
            if not transcript:
                self.log_test(
                    "1. ASR - English Transcription",
                    "FAIL",
                    "Empty transcript returned",
                    time.time() - start
                )
                return None
            
            # Check similarity (ASR may not be perfect)
            words_in = set(test_text.lower().split())
            words_out = set(transcript.lower().split())
            overlap = len(words_in & words_out)
            
            if overlap >= len(words_in) * 0.6:  # 60% word overlap
                self.log_test(
                    "1. ASR - English Transcription",
                    "PASS",
                    f"Input: '{test_text}'\nOutput: '{transcript}'\nMethod: {method}, Confidence: {confidence:.2%}",
                    time.time() - start
                )
                return transcript
            else:
                self.log_test(
                    "1. ASR - English Transcription",
                    "FAIL",
                    f"Low accuracy: '{test_text}' → '{transcript}' ({overlap}/{len(words_in)} words)",
                    time.time() - start
                )
                return None
                
        except Exception as e:
            self.log_test(
                "1. ASR - English Transcription",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return None
    
    # =============================================================================
    # TEST 2: NLU (Intent Extraction)
    # =============================================================================
    
    def test_2_nlu_campaign_search(self):
        """Test NLU intent extraction for campaign search"""
        start = time.time()
        
        try:
            test_queries = [
                ("show me education campaigns in Ethiopia", "search_campaigns"),
                ("I want to donate to water projects", "make_donation"),
                ("create a new campaign for my school", "create_campaign"),
                ("what are the active campaigns", "search_campaigns"),
            ]
            
            passed = 0
            for query, expected_intent in test_queries:
                try:
                    result = extract_intent_and_entities(
                        transcript=query,
                        language="en",
                        user_context={"user_id": TEST_USER_ID}
                    )
                    
                    detected_intent = result.get("intent")
                    confidence = result.get("confidence", 0)
                    
                    if detected_intent == expected_intent:
                        passed += 1
                        print(f"   ✓ '{query}' → {detected_intent} ({confidence:.0%})")
                    else:
                        print(f"   ✗ '{query}' → {detected_intent} (expected {expected_intent})")
                except Exception as e:
                    print(f"   ✗ '{query}' → Error: {str(e)[:50]}")
            
            if passed == len(test_queries):
                self.log_test(
                    "2. NLU - Intent Extraction",
                    "PASS",
                    f"All {len(test_queries)} intents correctly classified",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "2. NLU - Intent Extraction",
                    "FAIL",
                    f"Only {passed}/{len(test_queries)} intents correct",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "2. NLU - Intent Extraction",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 3: TTS (Text-to-Speech)
    # =============================================================================
    
    def test_3_tts_english(self):
        """Test TTS audio generation in English"""
        start = time.time()
        
        try:
            test_responses = [
                "I found 5 active campaigns in the education category.",
                "Your donation of 50 dollars has been processed successfully.",
                "Please provide the GPS coordinates for verification."
            ]
            
            passed = 0
            for text in test_responses:
                success, audio_path, error = self.loop.run_until_complete(
                    self.tts.text_to_speech(
                        text=text,
                        language="en",
                        voice="nova"
                    )
                )
                
                if success and audio_path and Path(audio_path).exists():
                    file_size = Path(audio_path).stat().st_size
                    passed += 1
                    print(f"   ✓ Generated {file_size:,} bytes: '{text[:50]}...'")
                else:
                    print(f"   ✗ Failed: {error}")
            
            if passed == len(test_responses):
                self.log_test(
                    "3. TTS - English Audio Generation",
                    "PASS",
                    f"All {len(test_responses)} audio files generated",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "3. TTS - English Audio Generation",
                    "FAIL",
                    f"Only {passed}/{len(test_responses)} files generated",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "3. TTS - English Audio Generation",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 4: Voice Campaign Search (Mini App Endpoint)
    # =============================================================================
    
    def test_4_voice_campaign_search(self):
        """Test voice campaign search via mini app endpoint simulation"""
        start = time.time()
        
        try:
            # Simulate voice command
            voice_command = "Show me all water campaigns"
            
            # Step 1: Transcribe (simulated - we'll use text directly)
            transcript = voice_command
            
            # Step 2: Search campaigns
            campaigns = self.db.query(Campaign).filter(
                Campaign.status == "active"
            ).limit(5).all()
            
            if not campaigns:
                self.log_test(
                    "4. Voice Campaign Search",
                    "SKIP",
                    "No campaigns in database - run seed_data.py first",
                    time.time() - start
                )
                return False
            
            # Step 3: Generate response
            campaign_count = len(campaigns)
            response_text = f"I found {campaign_count} active campaigns. The first one is {campaigns[0].title}."
            
            # Step 4: Generate TTS
            success, audio_path, error = self.loop.run_until_complete(
                self.tts.text_to_speech(
                    text=response_text,
                    language="en",
                    voice="nova"
                )
            )
            
            if success and audio_path:
                self.log_test(
                    "4. Voice Campaign Search",
                    "PASS",
                    f"Found {campaign_count} campaigns, generated audio response",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "4. Voice Campaign Search",
                    "FAIL",
                    f"TTS generation failed: {error}",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "4. Voice Campaign Search",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 5: Voice Donation Intent
    # =============================================================================
    
    def test_5_voice_donation_intent(self):
        """Test voice donation intent extraction"""
        start = time.time()
        
        try:
            # Get a campaign to donate to
            campaign = self.db.query(Campaign).filter(
                Campaign.status == "active"
            ).first()
            
            if not campaign:
                self.log_test(
                    "5. Voice Donation Intent",
                    "SKIP",
                    "No campaigns available - run seed_data.py first",
                    time.time() - start
                )
                return False
            
            # Voice command
            voice_command = f"I want to donate 50 dollars to {campaign.title}"
            
            # Extract intent and entities
            result = extract_intent_and_entities(
                transcript=voice_command,
                language="en",
                user_context={"user_id": TEST_USER_ID}
            )
            
            intent = result.get("intent")
            entities = result.get("entities", {})
            amount = entities.get("amount")
            currency = entities.get("currency", "USD")
            
            if intent == "make_donation" and amount == 50:
                self.log_test(
                    "5. Voice Donation Intent",
                    "PASS",
                    f"Intent: {intent}, Amount: {amount} {currency}",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "5. Voice Donation Intent",
                    "FAIL",
                    f"Intent: {intent}, Amount: {amount} (expected 50)",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "5. Voice Donation Intent",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 6: Voice Campaign Creation Intent
    # =============================================================================
    
    def test_6_voice_campaign_creation(self):
        """Test voice campaign creation intent extraction"""
        start = time.time()
        
        try:
            voice_command = "I want to create a campaign for building a school in Addis Ababa"
            
            result = extract_intent_and_entities(
                transcript=voice_command,
                language="en",
                user_context={"user_id": TEST_USER_ID}
            )
            
            intent = result.get("intent")
            entities = result.get("entities", {})
            category = entities.get("category")
            
            if intent == "create_campaign":
                self.log_test(
                    "6. Voice Campaign Creation",
                    "PASS",
                    f"Intent: {intent}, Category: {category}",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "6. Voice Campaign Creation",
                    "FAIL",
                    f"Expected 'create_campaign', got '{intent}'",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "6. Voice Campaign Creation",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 7: Voice Verification Report
    # =============================================================================
    
    def test_7_voice_verification_report(self):
        """Test voice verification report intent"""
        start = time.time()
        
        try:
            # Get a campaign to verify
            campaign = self.db.query(Campaign).filter(
                Campaign.status == "active"
            ).first()
            
            if not campaign:
                self.log_test(
                    "7. Voice Verification Report",
                    "SKIP",
                    "No campaigns available",
                    time.time() - start
                )
                return False
            
            voice_command = f"I need to submit a verification report for the {campaign.title} project"
            
            result = extract_intent_and_entities(
                transcript=voice_command,
                language="en",
                user_context={"user_id": TEST_FIELD_AGENT_ID}
            )
            
            intent = result.get("intent")
            
            if intent in ["field_report", "impact_report", "report_impact"]:
                self.log_test(
                    "7. Voice Verification Report",
                    "PASS",
                    f"Intent: {intent}",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "7. Voice Verification Report",
                    "FAIL",
                    f"Expected verification intent, got '{intent}'",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "7. Voice Verification Report",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 8: End-to-End Voice Pipeline
    # =============================================================================
    
    def test_8_end_to_end_pipeline(self):
        """Test complete voice pipeline with real audio"""
        start = time.time()
        
        try:
            # Create test audio
            test_command = "What campaigns are available"
            success, audio_path, error = self.loop.run_until_complete(
                self.tts.text_to_speech(
                    text=test_command,
                    language="en",
                    voice="nova"
                )
            )
            
            if not success:
                self.log_test(
                    "8. End-to-End Pipeline",
                    "FAIL",
                    f"Test audio creation failed: {error}",
                    time.time() - start
                )
                return False
            
            # Process through full pipeline
            result = process_voice_message(
                audio_file_path=audio_path,
                user_id=TEST_USER_ID,
                user_language="en",
                cleanup_audio=False
            )
            
            if not result.get("success"):
                self.log_test(
                    "8. End-to-End Pipeline",
                    "FAIL",
                    f"Pipeline failed: {result.get('error')}",
                    time.time() - start
                )
                return False
            
            # Validate pipeline stages
            stages = result.get("stages", {})
            print(f"   DEBUG: Pipeline stages = {list(stages.keys())}")
            print(f"   DEBUG: Full result keys = {list(result.keys())}")
            
            required_stages = ["asr", "nlu"]
            
            missing_stages = [s for s in required_stages if s not in stages]
            if missing_stages:
                self.log_test(
                    "8. End-to-End Pipeline",
                    "FAIL",
                    f"Missing stages: {missing_stages}",
                    time.time() - start
                )
                return False
            
            transcript = stages.get("asr", {}).get("transcript")
            intent = result.get("intent")
            response = result.get("response")
            
            # Handle None response safely
            if response:
                response_preview = response[:100] + "..." if len(response) > 100 else response
            else:
                response_preview = "None"
            
            self.log_test(
                "8. End-to-End Pipeline",
                "PASS",
                f"Transcript: '{transcript}'\nIntent: {intent}\nResponse: '{response_preview}'",
                time.time() - start
            )
            return True
                
        except Exception as e:
            import traceback
            self.log_test(
                "8. End-to-End Pipeline",
                "FAIL",
                f"Exception: {str(e)}\n{traceback.format_exc()}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 9: Database Integration
    # =============================================================================
    
    def test_9_database_integration(self):
        """Test database queries for voice operations"""
        start = time.time()
        
        try:
            # Check campaigns
            campaign_count = self.db.query(Campaign).filter(
                Campaign.status == "active"
            ).count()
            
            # Check users
            user_count = self.db.query(User).count()
            
            # Check verifications
            verification_count = self.db.query(ImpactVerification).count()
            
            if campaign_count > 0:
                self.log_test(
                    "9. Database Integration",
                    "PASS",
                    f"Found {campaign_count} campaigns, {user_count} users, {verification_count} verifications",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "9. Database Integration",
                    "SKIP",
                    "No data in database - run seed_data.py first",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "9. Database Integration",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # TEST 10: API Keys & Credentials
    # =============================================================================
    
    def test_10_api_credentials(self):
        """Test API credentials are configured"""
        start = time.time()
        
        try:
            missing = []
            
            # Check OpenAI
            if not os.getenv("OPENAI_API_KEY"):
                missing.append("OPENAI_API_KEY")
            
            # Check AddisAI
            if not os.getenv("ADDIS_AI_API_KEY"):
                missing.append("ADDIS_AI_API_KEY (optional for English-only)")
            
            # Check Database
            if not os.getenv("DATABASE_URL"):
                missing.append("DATABASE_URL")
            
            if not missing:
                self.log_test(
                    "10. API Credentials",
                    "PASS",
                    "All required API keys configured",
                    time.time() - start
                )
                return True
            else:
                self.log_test(
                    "10. API Credentials",
                    "FAIL",
                    f"Missing: {', '.join(missing)}",
                    time.time() - start
                )
                return False
                
        except Exception as e:
            self.log_test(
                "10. API Credentials",
                "FAIL",
                f"Exception: {str(e)}",
                time.time() - start
            )
            return False
    
    # =============================================================================
    # Run All Tests
    # =============================================================================
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*70)
        print("TRUST VOICE - COMPREHENSIVE VOICE PIPELINE TEST SUITE")
        print("="*70)
        print(f"Test User ID: {TEST_USER_ID}")
        print(f"Language: English")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")
        
        # Run tests
        print("Running tests...\n")
        
        self.test_10_api_credentials()
        self.test_9_database_integration()
        self.test_1_asr_english()
        self.test_2_nlu_campaign_search()
        self.test_3_tts_english()
        self.test_4_voice_campaign_search()
        self.test_5_voice_donation_intent()
        self.test_6_voice_campaign_creation()
        self.test_7_voice_verification_report()
        self.test_8_end_to_end_pipeline()
        
        # Print summary
        passed, failed, skipped = self.print_summary()
        
        # Export results
        self.export_results()
        
        return passed, failed, skipped
    
    def export_results(self):
        """Export results to JSON"""
        output_file = Path(__file__).parent / "voice_pipeline_test_results.json"
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r["status"] == "PASS"),
                "failed": sum(1 for r in self.results if r["status"] == "FAIL"),
                "skipped": sum(1 for r in self.results if r["status"] == "SKIP"),
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Results exported to: {output_file}")


def main():
    """Main test runner"""
    print("\n🎤 Trust Voice - Voice Pipeline Test Suite\n")
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("   Please ensure .env file is loaded")
        return 1
    
    # Run tests
    tester = VoicePipelineTests()
    passed, failed, skipped = tester.run_all_tests()
    
    # Exit code
    if failed > 0:
        print("\n❌ Some tests failed. Review errors above.")
        return 1
    elif skipped > 0 and passed == 0:
        print("\n⚠️  All tests skipped. Ensure database is seeded.")
        return 2
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
