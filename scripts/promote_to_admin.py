"""
One-time script to promote Emmanuel Acho to SYSTEM_ADMIN
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import User, UserRole
from datetime import datetime

def promote_to_admin(identifier: str, identifier_type: str = "name"):
    """
    Promote user to SYSTEM_ADMIN role
    
    Args:
        identifier: User's name, email, or telegram_username
        identifier_type: 'name', 'email', or 'username'
    """
    db = SessionLocal()
    try:
        # Find user
        if identifier_type == "name":
            user = db.query(User).filter(
                User.telegram_first_name.ilike(f"%{identifier}%")
            ).first()
        elif identifier_type == "email":
            user = db.query(User).filter(
                User.email == identifier
            ).first()
        elif identifier_type == "username":
            user = db.query(User).filter(
                User.telegram_username == identifier
            ).first()
        else:
            print(f"❌ Invalid identifier_type: {identifier_type}")
            return
        
        if not user:
            print(f"❌ User not found: {identifier}")
            return
        
        print(f"📋 Found user:")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.telegram_first_name} {user.telegram_last_name or ''}")
        print(f"   Username: @{user.telegram_username}")
        print(f"   Current Role: {user.role.value}")
        print(f"   Approved: {user.is_approved}")
        print()
        
        # Update to admin
        old_role = user.role.value
        user.role = UserRole.SYSTEM_ADMIN
        user.is_approved = True
        user.approved_at = datetime.utcnow()
        
        db.commit()
        
        print(f"✅ User promoted to SYSTEM_ADMIN")
        print(f"   {old_role} → SYSTEM_ADMIN")
        print()
        print(f"🎉 {user.telegram_first_name} can now use admin commands:")
        print(f"   /admin_requests")
        print(f"   /admin_approve <id>")
        print(f"   /admin_reject <id> <reason>")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    promote_to_admin("Emmanuel", "name")
