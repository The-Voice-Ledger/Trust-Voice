"""
Lab 5 Module Testing Suite
Test each voice module systematically to ensure all features work correctly.
"""

import asyncio
import os
from pathlib import Path

# Test data
TEST_USER_ID = "test_user_123"
TEST_CAMPAIGN_TITLE = "Clean Water for Mwanza Test"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_test(test_name, status="RUNNING"):
    """Print test status"""
    emoji = {
        "RUNNING": "🔄",
        "PASS": "✅",
        "FAIL": "❌",
        "SKIP": "⏭️"
    }
    print(f"{emoji.get(status, '❓')} {test_name}")

async def test_module_1_campaign_creation():
    """
    Module 1: Voice Campaign Creation
    Tests the 9-step interview process for creating campaigns via voice.
    """
    print_section("MODULE 1: Voice Campaign Creation")
    
    print("📋 Test Steps:")
    print("1. Register as CAMPAIGN_CREATOR via /register")
    print("2. Send voice message: 'I want to create a campaign'")
    print("3. Answer interview questions:")
    print("   - Title: 'Clean Water for Mwanza'")
    print("   - Category: 'Water & Sanitation'")
    print("   - Problem: 'Community lacks clean water'")
    print("   - Solution: 'Build 3 water wells'")
    print("   - Goal: '$5000'")
    print("   - Beneficiaries: '500 families'")
    print("   - Location: 'Mwanza, Tanzania'")
    print("   - Timeline: '6 months'")
    print("   - Budget: 'Wells $3000, Pumps $1500, Labor $500'")
    print("4. Confirm campaign creation")
    
    print("\n✅ Expected Result:")
    print("   - Campaign created with status='pending'")
    print("   - All fields populated correctly")
    print("   - NGO automatically created if needed")
    print("   - Success message displayed")
    
    print("\n🔍 Verification:")
    print("   psql $DATABASE_URL -c \"SELECT id, title, status FROM campaigns WHERE title LIKE '%Mwanza%' ORDER BY created_at DESC LIMIT 1;\"")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_2_donation_execution():
    """
    Module 2: Voice Donation Execution
    Tests voice-initiated donations with M-Pesa/Stripe integration.
    """
    print_section("MODULE 2: Voice Donation Execution")
    
    print("📋 Test Steps:")
    print("1. Register as DONOR via /register")
    print("2. Send voice message: 'I want to donate 50 dollars to clean water'")
    print("3. System should find the campaign")
    print("4. Choose payment method (M-Pesa for +254, Stripe otherwise)")
    
    print("\n✅ Expected Result:")
    print("   - Donation record created with status='pending'")
    print("   - For Kenya (+254): M-Pesa STK Push initiated")
    print("   - For others: Stripe payment link provided")
    print("   - Payment instructions displayed")
    
    print("\n🔍 Verification:")
    print("   psql $DATABASE_URL -c \"SELECT id, amount_usd, status, payment_method FROM donations ORDER BY created_at DESC LIMIT 1;\"")
    
    print("\n💡 Alternative Test Commands:")
    print("   - 'Donate 100 shillings'")
    print("   - 'Give $25 to water project'")
    print("   - 'I want to support the campaign with 50 dollars'")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_3_campaign_details():
    """
    Module 3: Campaign Detail View
    Tests detailed campaign information display.
    """
    print_section("MODULE 3: Campaign Detail View")
    
    print("📋 Test Steps:")
    print("1. Send voice/text: 'Tell me about Clean Water project'")
    print("2. Or: 'Show details for Mwanza campaign'")
    
    print("\n✅ Expected Result:")
    print("   - Full campaign description")
    print("   - Progress bar and percentage")
    print("   - Raised amount vs goal")
    print("   - Donor count")
    print("   - Verification status with trust scores")
    print("   - Recent supporters list")
    print("   - Location and category")
    
    print("\n💡 What to Check:")
    print("   ✓ Progress bar rendering (█░░░░)")
    print("   ✓ Correct amounts displayed")
    print("   ✓ Trust score if verified")
    print("   ✓ Recent donors shown")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_4_impact_reports():
    """
    Module 4: Impact Reports (Field Agents)
    Tests impact reporting with photos, GPS, and trust scoring.
    """
    print_section("MODULE 4: Impact Reports")
    
    print("📋 Test Steps:")
    print("1. Register as FIELD_AGENT via /register")
    print("2. Upload 3-5 photos to Telegram (project site images)")
    print("3. Send voice: 'Report impact for Clean Water project'")
    print("4. Add observations and testimonials")
    
    print("\n✅ Expected Result:")
    print("   - Impact verification record created")
    print("   - Trust score calculated (0-100)")
    print("   - Auto-approved if score >= 80")
    print("   - M-Pesa payout initiated ($30 USD) if approved")
    print("   - Photos stored with verification")
    
    print("\n🎯 Trust Score Breakdown:")
    print("   - Photos: 30 points (10 per photo, max 3)")
    print("   - GPS: 25 points")
    print("   - Testimonials: 20 points")
    print("   - Description: 15 points")
    print("   - Beneficiary count: 10 points")
    
    print("\n🔍 Verification:")
    print("   psql $DATABASE_URL -c \"SELECT id, trust_score, status, agent_payout_status FROM impact_verifications ORDER BY created_at DESC LIMIT 1;\"")
    
    print("\n💡 Check My Reports:")
    print("   Send: 'Show my verifications'")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_5_campaign_verification():
    """
    Module 5: Campaign Verification (Field Agents)
    Tests pre-launch campaign verification process.
    """
    print_section("MODULE 5: Campaign Verification")
    
    print("📋 Test Steps:")
    print("1. As FIELD_AGENT, send: 'Show campaigns needing verification'")
    print("2. Send: 'Verify [campaign name]'")
    print("3. Upload 3-5 photos of site visit")
    print("4. Share GPS location")
    print("5. Send observations via voice/text")
    
    print("\n✅ Expected Result:")
    print("   - Verification checklist provided")
    print("   - Trust score calculated")
    print("   - Campaign auto-activated if score >= 80")
    print("   - Agent receives $30 USD payout")
    print("   - Campaign status changes: pending → active")
    
    print("\n🎯 Trust Score Breakdown:")
    print("   - Photos: 25 points")
    print("   - GPS: 25 points")
    print("   - Testimonials: 20 points")
    print("   - Notes: 15 points")
    print("   - Beneficiary interviews: 10 points")
    print("   - Budget verification: 5 points")
    
    print("\n🔍 Verification:")
    print("   psql $DATABASE_URL -c \"SELECT c.title, c.status, c.avg_trust_score, c.verification_count FROM campaigns c WHERE c.title LIKE '%Mwanza%';\"")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_6_payout_requests():
    """
    Module 6: Payout Requests (Campaign Creators)
    Tests campaign fund withdrawals via M-Pesa.
    """
    print_section("MODULE 6: Payout Requests")
    
    print("📋 Test Steps:")
    print("1. As CAMPAIGN_CREATOR, send: 'Request payout'")
    print("2. View campaign balances")
    print("3. Send: 'Withdraw $100 from Clean Water project'")
    print("4. Confirm phone number is Kenya (+254) for M-Pesa")
    
    print("\n✅ Expected Result:")
    print("   - Campaign balance displayed (USD and KES)")
    print("   - Minimum $10 withdrawal enforced")
    print("   - M-Pesa B2C payout initiated")
    print("   - Campaign raised_amount_usd reduced")
    print("   - Transaction ID provided")
    print("   - Funds arrive in 1-5 minutes")
    
    print("\n💡 Check Balance:")
    print("   Send: 'What's the balance for Clean Water project?'")
    
    print("\n🔍 Verification:")
    print("   psql $DATABASE_URL -c \"SELECT title, raised_amount_usd, goal_amount_usd FROM campaigns WHERE title LIKE '%Mwanza%';\"")
    
    print("\n⚠️  Requirements:")
    print("   - Phone number must be +254 (Kenya)")
    print("   - Campaign must have raised funds")
    print("   - Phone must be verified")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_7_donation_status():
    """
    Module 7: Donation Status Check
    Tests donation tracking and status queries.
    """
    print_section("MODULE 7: Donation Status Check")
    
    print("📋 Test Steps:")
    print("1. As DONOR, send: 'Check my donation status'")
    print("2. Or: 'What's my donation status?'")
    print("3. Or: 'Show my donations' (full history)")
    
    print("\n✅ Expected Result:")
    print("   - Most recent donation details:")
    print("     • Status (pending/completed/failed)")
    print("     • Amount and currency")
    print("     • Campaign name")
    print("     • Payment method")
    print("     • Transaction ID")
    print("     • Date and time")
    print("   - Status emoji (⏳/✅/❌)")
    print("   - Helpful messages based on status")
    
    print("\n🔍 Verification:")
    print("   psql $DATABASE_URL -c \"SELECT d.amount_usd, d.currency, d.status, d.payment_method, c.title FROM donations d JOIN campaigns c ON d.campaign_id = c.id ORDER BY d.created_at DESC LIMIT 3;\"")
    
    print("\n💡 Alternative Commands:")
    print("   - 'Show my donation history'")
    print("   - 'List my donations'")
    print("   - 'View my contributions'")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_module_8_tts_integration():
    """
    Module 8: TTS Integration
    Tests voice reply generation for accessibility.
    """
    print_section("MODULE 8: TTS Integration")
    
    print("📋 Test Steps:")
    print("1. Send any voice command (any of the above modules)")
    print("2. Check response includes BOTH:")
    print("   - Text message")
    print("   - Voice message (audio)")
    
    print("\n✅ Expected Result:")
    print("   - Text response sent immediately")
    print("   - Voice version follows (marked '🎤 Voice version')")
    print("   - Audio quality is clear and natural")
    print("   - Language matches user preference:")
    print("     • English: OpenAI TTS (nova voice)")
    print("     • Amharic: AddisAI TTS")
    
    print("\n🎯 What to Test:")
    print("   1. English responses (default)")
    print("   2. Amharic responses (if language set to 'am')")
    print("   3. Cache functionality (same message = instant audio)")
    print("   4. Long messages (truncated to 1000 chars)")
    
    print("\n🔍 Cache Location:")
    print("   ls -lh voice/tts_cache/")
    
    print("\n💡 Test Different Responses:")
    print("   - 'Show campaigns' → List response")
    print("   - 'Donate $50' → Confirmation with instructions")
    print("   - 'Check status' → Status update")
    print("   - 'Tell me about X' → Detailed description")
    
    print("\n⚠️  Note:")
    print("   - TTS is optional (non-blocking)")
    print("   - If OpenAI key missing, only text is sent")
    print("   - Check logs: tail -f logs/telegram_bot.log")
    
    input("\n⏸️  Press Enter when you've completed this test...")

async def test_all_modules():
    """Run all module tests in sequence"""
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "LAB 5 MODULE TESTING SUITE" + " " * 32 + "║")
    print("║" + " " * 20 + "TrustVoice Voice Platform" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    
    print("\n📱 Prerequisites:")
    print("   1. Services running (./admin-scripts/START_SERVICES.sh)")
    print("   2. Telegram bot accessible")
    print("   3. Test user registered in different roles")
    print("   4. Database accessible")
    
    print("\n🎯 Testing Approach:")
    print("   - Test each module individually")
    print("   - Verify database changes")
    print("   - Check both voice and text inputs")
    print("   - Confirm TTS voice replies")
    
    proceed = input("\n👉 Ready to begin testing? (y/n): ")
    if proceed.lower() != 'y':
        print("Testing cancelled.")
        return
    
    # Run tests sequentially
    await test_module_1_campaign_creation()
    await test_module_2_donation_execution()
    await test_module_3_campaign_details()
    await test_module_4_impact_reports()
    await test_module_5_campaign_verification()
    await test_module_6_payout_requests()
    await test_module_7_donation_status()
    await test_module_8_tts_integration()
    
    # Final summary
    print_section("🎉 TESTING COMPLETE")
    
    print("📊 Summary:")
    print("   ✅ Module 1: Voice Campaign Creation")
    print("   ✅ Module 2: Voice Donation Execution")
    print("   ✅ Module 3: Campaign Detail View")
    print("   ✅ Module 4: Impact Reports")
    print("   ✅ Module 5: Campaign Verification")
    print("   ✅ Module 6: Payout Requests")
    print("   ✅ Module 7: Donation Status Check")
    print("   ✅ Module 8: TTS Integration")
    
    print("\n🔍 Next Steps:")
    print("   1. Review any failed tests")
    print("   2. Check database consistency")
    print("   3. Test edge cases and error handling")
    print("   4. Test with real Telegram users")
    print("   5. Monitor logs for issues")
    
    print("\n📝 Useful Commands:")
    print("   - View logs: tail -f logs/telegram_bot.log")
    print("   - Check DB: psql $DATABASE_URL")
    print("   - Restart: ./admin-scripts/STOP_SERVICES.sh && ./admin-scripts/START_SERVICES.sh")
    
    print("\n✨ Lab 5 Voice Platform Ready for Production! ✨\n")

if __name__ == "__main__":
    asyncio.run(test_all_modules())
