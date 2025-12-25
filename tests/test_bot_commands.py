#!/usr/bin/env python3
"""
Test Bot Commands - Programmatic Testing
Tests the new /campaigns, /donations, /my_campaigns commands
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Database imports - use SQLAlchemy directly
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, Campaign, Donation, Donor, PendingRegistration


def get_db():
    """Get database session"""
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    return session


async def test_bot_commands():
    """Test bot commands programmatically using Telegram Bot API"""
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    test_chat_id = os.getenv("TEST_TELEGRAM_CHAT_ID")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return False
    
    if not test_chat_id:
        print("⚠️  TEST_TELEGRAM_CHAT_ID not set in .env")
        print("   Please add your Telegram chat ID to test commands")
        print("   You can get it by messaging the bot and checking logs")
        return False
    
    print("\n🤖 Testing Bot Commands")
    print("=" * 70)
    
    bot = Bot(token=bot_token)
    
    # Commands to test
    commands = [
        {
            "command": "/start",
            "description": "Register or view menu",
            "expected": "Welcome to TrustVoice"
        },
        {
            "command": "/help",
            "description": "Show help message",
            "expected": "Available commands"
        },
        {
            "command": "/campaigns",
            "description": "Browse active campaigns",
            "expected": "Active Campaigns"
        },
        {
            "command": "/donations",
            "description": "View donation history",
            "expected": "Your Donations"
        },
        {
            "command": "/my_campaigns",
            "description": "View your campaigns",
            "expected": "Your Campaigns"
        }
    ]
    
    results = []
    
    for idx, cmd in enumerate(commands, 1):
        print(f"\n{idx}. Testing: {cmd['command']}")
        print(f"   Description: {cmd['description']}")
        
        try:
            # Send command to bot
            message = await bot.send_message(
                chat_id=test_chat_id,
                text=cmd['command']
            )
            
            print(f"   ✅ Command sent (Message ID: {message.message_id})")
            
            # Wait for bot to process (check logs)
            await asyncio.sleep(2)
            
            results.append({
                "command": cmd['command'],
                "status": "sent",
                "message_id": message.message_id
            })
            
        except TelegramError as e:
            print(f"   ❌ Telegram Error: {e}")
            results.append({
                "command": cmd['command'],
                "status": "error",
                "error": str(e)
            })
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")
            results.append({
                "command": cmd['command'],
                "status": "error",
                "error": str(e)
            })
    
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    sent_count = sum(1 for r in results if r['status'] == 'sent')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"✅ Commands Sent: {sent_count}/{len(commands)}")
    print(f"❌ Errors: {error_count}/{len(commands)}")
    
    if error_count > 0:
        print("\nErrors:")
        for r in results:
            if r['status'] == 'error':
                print(f"  • {r['command']}: {r['error']}")
    
    print("\n💡 Check bot logs for responses:")
    print("   tail -f logs/telegram_bot.log")
    
    return sent_count == len(commands)


async def verify_database_state():
    """Verify database has test data for commands"""
    
    print("\n📊 Database Verification")
    print("=" * 70)
    
    db = get_db()
    
    try:
        # Count campaigns
        campaign_count = db.query(Campaign).filter(
            Campaign.status == "active"
        ).count()
        
        active_campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).limit(5).all()
        
        print(f"\n✅ Active Campaigns: {campaign_count}")
        if active_campaigns:
            print("   Top 5 campaigns:")
            for c in active_campaigns:
                raised = c.raised_amount_usd or 0
                goal = c.goal_amount_usd or 1
                percent = (raised / goal) * 100
                location = c.location_region or c.location_country or "N/A"
                print(f"   • {c.title}")
                print(f"     Goal: USD {goal:,.2f} | Raised: USD {raised:,.2f} ({percent:.1f}%)")
                print(f"     Location: {location}")
        
        # Count donations
        donation_count = db.query(Donation).count()
        
        recent_donations = db.query(Donation).order_by(
            Donation.created_at.desc()
        ).limit(5).all()
        
        print(f"\n✅ Total Donations: {donation_count}")
        if recent_donations:
            print("   Recent 5 donations:")
            for d in recent_donations:
                donor = db.query(Donor).filter(Donor.id == d.donor_id).first()
                campaign = db.query(Campaign).filter(Campaign.id == d.campaign_id).first()
                
                donor_name = donor.preferred_name if donor else "Unknown"
                campaign_title = campaign.title if campaign else "Unknown Campaign"
                
                print(f"   • {donor_name} → {campaign_title}")
                print(f"     Amount: {d.currency} {d.amount:,.2f} | Status: {d.status}")
        
        # Check test user
        test_chat_id = os.getenv("TEST_TELEGRAM_CHAT_ID")
        if test_chat_id:
            test_user = db.query(User).filter(
                User.telegram_user_id == test_chat_id
            ).first()
            
            if test_user:
                print(f"\n✅ Test User Found:")
                print(f"   Name: {test_user.full_name}")
                print(f"   Role: {test_user.role}")
                print(f"   Language: {test_user.preferred_language}")
                
                # For Telegram users, donations link through Donor table
                # But Users table is for admin/campaign creators, not donors
                print(f"   User Type: Telegram Bot User")
            else:
                print(f"\n⚠️  Test user not found (Chat ID: {test_chat_id})")
                print("   User needs to /start the bot first")
        
        # Check pending registrations
        pending_count = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).count()
        
        print(f"\n✅ Pending Registrations: {pending_count}")
    
    finally:
        db.close()
    
    print("\n" + "=" * 70)


async def simulate_command_responses():
    """Simulate expected responses from commands"""
    
    print("\n📝 Expected Command Responses")
    print("=" * 70)
    
    db = get_db()
    
    try:
        test_chat_id = os.getenv("TEST_TELEGRAM_CHAT_ID")
        test_user = None
        
        if test_chat_id:
            test_user = db.query(User).filter(
                User.telegram_user_id == test_chat_id
            ).first()
        
        # /campaigns response
        print("\n1. /campaigns - Expected Response:")
        campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).limit(3).all()
        
        if campaigns:
            print("   📋 <b>Active Campaigns</b>\n")
            for c in campaigns:
                raised = c.raised_amount_usd or 0
                goal = c.goal_amount_usd or 1
                percent = (raised / goal) * 100
                bar_filled = int(percent / 10)
                bar = "█" * bar_filled + "░" * (10 - bar_filled)
                location = c.location_region or c.location_country or "N/A"
                
                print(f"   <b>{c.title}</b>")
                print(f"   {bar} {percent:.1f}%")
                print(f"   💰 USD {raised:,.2f} / {goal:,.2f}")
                print(f"   📍 {location}")
                print()
        else:
            print("   No active campaigns found.")
        
        # /donations response
        print("\n2. /donations - Expected Response:")
        if test_user:
            # Note: Bot donations link to Donor table, but test_user is in Users table
            # This simulates the expected output for a user with donations
            print(f"   💝 <b>Your Donations</b>")
            print(f"   [Note: Donations link to Donor table, not Users]")
            print(f"   Total donations shown for system test only\n")
            
            # Show sample donation format
            sample_donations = db.query(Donation).limit(3).all()
            if sample_donations:
                for d in sample_donations:
                    campaign = db.query(Campaign).filter(
                        Campaign.id == d.campaign_id
                    ).first()
                    
                    status_emoji = {
                        "completed": "✅",
                        "pending": "⏳",
                        "failed": "❌"
                    }.get(d.status, "❓")
                    
                    print(f"   {status_emoji} <b>{campaign.title if campaign else 'Unknown'}</b>")
                    print(f"   {d.currency} {d.amount:,.2f}")
                    print(f"   {d.created_at.strftime('%Y-%m-%d %H:%M')}\n")
        else:
            print("   [User not found - need to /start bot first]")
        
        # /my_campaigns response
        print("\n3. /my_campaigns - Expected Response:")
        if test_user and test_user.role in ["CAMPAIGN_CREATOR", "SYSTEM_ADMIN"]:
            campaigns = db.query(Campaign).filter(
                Campaign.ngo_id == test_user.ngo_id
            ).limit(5).all() if test_user.ngo_id else []
            
            if campaigns:
                print(f"   📋 <b>Your Campaigns</b>\n")
                for c in campaigns:
                    raised = c.raised_amount_usd or 0
                    goal = c.goal_amount_usd or 1
                    percent = (raised / goal) * 100
                    
                    status_emoji = "✅" if c.status == "active" else "⏸️"
                    
                    print(f"   {status_emoji} <b>{c.title}</b>")
                    print(f"   Progress: {percent:.1f}%")
                    print(f"   💰 USD {raised:,.2f} / {goal:,.2f}\n")
            else:
                print("   You haven't created any campaigns yet.")
        else:
            print("   [Access denied - user is not a creator/admin]")
    
    finally:
        db.close()
    
    print("\n" + "=" * 70)


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test TrustVoice Bot Commands")
    parser.add_argument(
        '--mode',
        choices=['send', 'verify', 'simulate', 'all'],
        default='all',
        help='Test mode to run'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🧪 TrustVoice Bot Command Testing")
    print("=" * 70)
    
    async def run_tests():
        if args.mode in ['verify', 'all']:
            await verify_database_state()
        
        if args.mode in ['simulate', 'all']:
            await simulate_command_responses()
        
        if args.mode in ['send', 'all']:
            print("\n⚠️  About to send commands to bot...")
            print("   Make sure TEST_TELEGRAM_CHAT_ID is set in .env")
            
            response = input("\nContinue? (y/n): ")
            if response.lower() == 'y':
                await test_bot_commands()
            else:
                print("   Skipped sending commands")
    
    try:
        asyncio.run(run_tests())
        
        print("\n✅ Testing Complete!")
        print("\n💡 Next Steps:")
        print("   1. Check bot logs: tail -f logs/telegram_bot.log")
        print("   2. Verify responses in Telegram app")
        print("   3. Test each command manually for UX")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
