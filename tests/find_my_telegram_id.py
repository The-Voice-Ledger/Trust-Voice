#!/usr/bin/env python3
"""
Helper script to find your Telegram user ID and set it for testing
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

print("🔍 Finding your Telegram user ID...\n")

# Option 1: Check .env file
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.startswith("TEST_TELEGRAM_CHAT_ID="):
                chat_id = line.split("=")[1].strip()
                if chat_id and chat_id != "your_chat_id":
                    print(f"✅ Found in .env: {chat_id}")
                    print(f"\n💡 Run test with:")
                    print(f"   python tests/test_dual_delivery_live.py\n")
                    sys.exit(0)

# Option 2: Check environment
chat_id = os.getenv("TEST_TELEGRAM_CHAT_ID")
if chat_id and chat_id != "your_chat_id":
    print(f"✅ Found in environment: {chat_id}")
    print(f"\n💡 Run test with:")
    print(f"   python tests/test_dual_delivery_live.py\n")
    sys.exit(0)

# Option 3: Try to get from database
try:
    from database.db import SessionLocal
    from database.models import User
    
    db = SessionLocal()
    users = db.query(User).filter(
        User.telegram_user_id.isnot(None)
    ).order_by(User.created_at.desc()).limit(5).all()
    
    if users:
        print("✅ Found registered users in database:\n")
        for i, user in enumerate(users, 1):
            role = user.role or "DONOR"
            print(f"   {i}. {user.first_name} (ID: {user.telegram_user_id}) - {role}")
        
        # Suggest the most recent user
        suggested_id = users[0].telegram_user_id
        print(f"\n💡 To run tests with {users[0].first_name}'s account:")
        print(f"   export TEST_TELEGRAM_CHAT_ID={suggested_id}")
        print(f"   python tests/test_dual_delivery_live.py")
        
        # Offer to add to .env
        print(f"\n📝 Or add to .env file:")
        print(f"   echo 'TEST_TELEGRAM_CHAT_ID={suggested_id}' >> .env")
        
    else:
        print("❌ No registered users found in database")
        print("\n💡 Next steps:")
        print("   1. Make sure bot is running: ./admin-scripts/START_SERVICES.sh")
        print("   2. Send /start to your bot in Telegram")
        print("   3. Run this script again")
    
    db.close()
    
except Exception as e:
    print(f"⚠️  Could not check database: {e}")
    print("\n💡 Alternative: Find your ID manually:")
    print("   1. Send /start to your bot")
    print("   2. Check logs: grep 'user.id' logs/telegram_bot.log")
    print("   3. Set: export TEST_TELEGRAM_CHAT_ID=your_id")

print()
