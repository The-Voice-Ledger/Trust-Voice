"""
List all users in database
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import User

def list_users():
    """List all users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"📋 Found {len(users)} user(s):\n")
        
        for idx, user in enumerate(users, 1):
            print(f"{idx}. {user.telegram_first_name} {user.telegram_last_name or ''}")
            print(f"   ID: {user.id}")
            print(f"   Telegram: @{user.telegram_username} ({user.telegram_user_id})")
            print(f"   Role: {user.role.value}")
            print(f"   Approved: {user.is_approved}")
            print(f"   Email: {user.email or 'N/A'}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    list_users()
