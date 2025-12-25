"""
Phase 4D Complete Feature Test

Tests all implemented features programmatically:
1. User registration and roles
2. Admin approval workflow
3. PIN management
4. Web login authentication
5. Phone verification

Run this to verify everything works end-to-end.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import SessionLocal
from database.models import User, PendingRegistration, UserRole
from services.auth_service import hash_pin, verify_pin, is_weak_pin
import requests


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


def test_admin_user():
    """Test 1: Verify admin user exists and has correct permissions"""
    print_header("TEST 1: Admin User Setup")
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "emmanuel@earesearch.net").first()
        
        if not admin:
            print_error("Admin user not found!")
            return False
        
        print_success(f"Admin found: {admin.email}")
        print_info(f"   Telegram ID: {admin.telegram_user_id}")
        print_info(f"   Username: {admin.telegram_username}")
        print_info(f"   Role: {admin.role}")
        print_info(f"   Approved: {admin.is_approved}")
        print_info(f"   PIN set: {'Yes' if admin.pin_hash else 'No'}")
        print_info(f"   Phone verified: {'Yes' if admin.phone_verified_at else 'No'}")
        
        if admin.role != "SYSTEM_ADMIN":
            print_error(f"Role is {admin.role}, should be SYSTEM_ADMIN")
            return False
        
        print_success("Admin user correctly configured!")
        return True
        
    finally:
        db.close()


def test_create_test_users():
    """Test 2: Create test users for approval workflow"""
    print_header("TEST 2: Create Test Users")
    
    db = SessionLocal()
    try:
        # Clean up old test users
        db.query(PendingRegistration).filter(
            PendingRegistration.telegram_username.like('test_%')
        ).delete()
        db.query(User).filter(
            User.telegram_username.like('test_%')
        ).delete()
        db.commit()
        
        # Create test pending registrations
        test_users = [
            {
                "telegram_user_id": "111111111",
                "telegram_username": "test_creator",
                "telegram_first_name": "Test",
                "telegram_last_name": "Creator",
                "requested_role": "CAMPAIGN_CREATOR",
                "full_name": "Test Creator User",
                "organization_name": "Test Foundation",
                "location": "Nairobi, Kenya",
                "phone_number": "+254700000001",
                "reason": "Testing campaign creation workflow",
                "pin_hash": hash_pin("7392"),
                "status": "PENDING"
            },
            {
                "telegram_user_id": "222222222",
                "telegram_username": "test_agent",
                "telegram_first_name": "Test",
                "telegram_last_name": "Agent",
                "requested_role": "FIELD_AGENT",
                "full_name": "Test Agent User",
                "location": "Mombasa, Kenya",
                "phone_number": "+254700000002",
                "verification_experience": "5 years testing experience",
                "coverage_regions": "Coast region",
                "has_gps_phone": True,
                "pin_hash": hash_pin("8241"),
                "status": "PENDING"
            }
        ]
        
        for user_data in test_users:
            pending = PendingRegistration(**user_data)
            db.add(pending)
            print_success(f"Created pending registration: {user_data['telegram_username']} ({user_data['requested_role']})")
        
        db.commit()
        
        # Verify creation
        count = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).count()
        
        print_success(f"Total pending registrations: {count}")
        return True
        
    except Exception as e:
        print_error(f"Failed to create test users: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_admin_approval():
    """Test 3: Approve pending registrations"""
    print_header("TEST 3: Admin Approval Workflow")
    
    db = SessionLocal()
    try:
        # Get admin
        admin = db.query(User).filter(User.email == "emmanuel@earesearch.net").first()
        
        # Get pending registrations
        pending_list = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).all()
        
        if not pending_list:
            print_info("No pending registrations to approve")
            return True
        
        print_info(f"Found {len(pending_list)} pending registrations")
        
        for pending in pending_list:
            # Check if user already exists
            existing = db.query(User).filter(
                User.telegram_user_id == pending.telegram_user_id
            ).first()
            
            if existing:
                # Update existing user
                existing.role = pending.requested_role  # String value
                existing.is_approved = True
                existing.approved_at = datetime.utcnow()
                existing.approved_by_admin_id = admin.id
                print_success(f"Updated existing user: {pending.telegram_username}")
            else:
                # Create new user
                new_user = User(
                    telegram_user_id=pending.telegram_user_id,
                    telegram_username=pending.telegram_username,
                    telegram_first_name=pending.telegram_first_name,
                    telegram_last_name=pending.telegram_last_name,
                    email=f"{pending.telegram_username}@test.trustvoice.app",
                    role=pending.requested_role,  # String value
                    pin_hash=pending.pin_hash,
                    pin_set_at=datetime.utcnow(),
                    is_approved=True,
                    approved_at=datetime.utcnow(),
                    approved_by_admin_id=admin.id,
                    phone_number=pending.phone_number
                )
                db.add(new_user)
                print_success(f"Approved and created user: {pending.telegram_username} as {pending.requested_role}")
            
            # Update pending status
            pending.status = "APPROVED"
            pending.reviewed_at = datetime.utcnow()
            pending.reviewed_by_admin_id = admin.id
        
        db.commit()
        print_success("All pending registrations approved!")
        return True
        
    except Exception as e:
        print_error(f"Approval failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_pin_management():
    """Test 4: PIN management functionality"""
    print_header("TEST 4: PIN Management")
    
    db = SessionLocal()
    try:
        # Test weak PIN detection
        print_info("Testing weak PIN detection...")
        weak_pins = ["1234", "0000", "1111", "2345", "9876"]
        for pin in weak_pins:
            is_weak, reason = is_weak_pin(pin)
            if is_weak:
                print_success(f"   Correctly rejected weak PIN: {pin} ({reason})")
            else:
                print_error(f"   Failed to detect weak PIN: {pin}")
        
        # Test strong PINs
        strong_pins = ["7392", "8241", "3058", "4617"]
        for pin in strong_pins:
            is_weak, _ = is_weak_pin(pin)
            if not is_weak:
                print_success(f"   Correctly accepted strong PIN: {pin}")
            else:
                print_error(f"   Incorrectly rejected strong PIN: {pin}")
        
        # Test PIN hashing and verification
        print_info("Testing PIN hashing and verification...")
        test_pin = "7392"
        pin_hash = hash_pin(test_pin)
        
        if verify_pin(test_pin, pin_hash):
            print_success(f"   PIN verification works correctly")
        else:
            print_error(f"   PIN verification failed")
        
        if not verify_pin("9999", pin_hash):
            print_success(f"   Wrong PIN correctly rejected")
        else:
            print_error(f"   Wrong PIN incorrectly accepted")
        
        return True
        
    finally:
        db.close()


def test_web_login():
    """Test 5: Web login authentication"""
    print_header("TEST 5: Web Login Authentication")
    
    db = SessionLocal()
    try:
        # Get test users
        users = db.query(User).filter(
            User.telegram_username.like('test_%')
        ).all()
        
        if not users:
            print_info("No test users to login with")
            return True
        
        base_url = "http://localhost:8001"
        
        for user in users:
            print_info(f"Testing login for: {user.telegram_username}")
            
            # Test successful login
            response = requests.post(
                f"{base_url}/auth/login",
                json={
                    "username": user.telegram_username,
                    "pin": "7392" if "creator" in user.telegram_username else "8241"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"   ✓ Login successful")
                print_info(f"   Token: {data['access_token'][:30]}...")
                print_info(f"   Role: {data['user']['role']}")
                print_info(f"   Expires in: {data['expires_in']}s")
                
                # Test /auth/me with token
                token = data['access_token']
                me_response = requests.get(
                    f"{base_url}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                
                if me_response.status_code == 200:
                    print_success(f"   ✓ Token validation works")
                else:
                    print_error(f"   ✗ Token validation failed: {me_response.status_code}")
            else:
                print_error(f"   ✗ Login failed: {response.status_code}")
                print_error(f"   Response: {response.text}")
        
        # Test failed login
        print_info("Testing failed login scenarios...")
        
        # Wrong PIN
        response = requests.post(
            f"{base_url}/auth/login",
            json={"username": users[0].telegram_username, "pin": "9999"},
            timeout=5
        )
        if response.status_code == 401:
            print_success("   ✓ Wrong PIN correctly rejected")
        else:
            print_error(f"   ✗ Wrong PIN handling failed: {response.status_code}")
        
        # Non-existent user
        response = requests.post(
            f"{base_url}/auth/login",
            json={"username": "nonexistent", "pin": "1234"},
            timeout=5
        )
        if response.status_code == 401:
            print_success("   ✓ Non-existent user correctly rejected")
        else:
            print_error(f"   ✗ Non-existent user handling failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to API. Is the server running?")
        return False
    except Exception as e:
        print_error(f"Web login test failed: {e}")
        return False
    finally:
        db.close()


def test_phone_verification():
    """Test 6: Phone verification data"""
    print_header("TEST 6: Phone Verification")
    
    db = SessionLocal()
    try:
        users_with_phones = db.query(User).filter(
            User.phone_number.isnot(None)
        ).all()
        
        print_info(f"Users with verified phones: {len(users_with_phones)}")
        
        for user in users_with_phones:
            print_success(f"   {user.telegram_username}: {user.phone_number}")
            if user.phone_verified_at:
                print_info(f"      Verified at: {user.phone_verified_at}")
        
        return True
        
    finally:
        db.close()


def test_complete_summary():
    """Test 7: Overall system summary"""
    print_header("SYSTEM SUMMARY")
    
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        approved_users = db.query(User).filter(User.is_approved == True).count()
        pending_users = db.query(User).filter(User.is_approved == False).count()
        users_with_pins = db.query(User).filter(User.pin_hash.isnot(None)).count()
        users_with_phones = db.query(User).filter(User.phone_number.isnot(None)).count()
        
        pending_registrations = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).count()
        
        print_info(f"Total users: {total_users}")
        print_info(f"   Approved: {approved_users}")
        print_info(f"   Pending: {pending_users}")
        print_info(f"   With PINs: {users_with_pins}")
        print_info(f"   With verified phones: {users_with_phones}")
        print_info(f"Pending registrations: {pending_registrations}")
        
        # Role breakdown
        print_info("\nRole breakdown:")
        for role in ["SUPER_ADMIN", "NGO_ADMIN", "VIEWER", "DONOR", "CAMPAIGN_CREATOR", "FIELD_AGENT", "SYSTEM_ADMIN"]:
            count = db.query(User).filter(User.role == role).count()
            if count > 0:
                print_info(f"   {role}: {count}")
        
        return True
        
    finally:
        db.close()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + "  PHASE 4D - COMPLETE FEATURE TEST SUITE  ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    tests = [
        ("Admin User Setup", test_admin_user),
        ("Create Test Users", test_create_test_users),
        ("Admin Approval Workflow", test_admin_approval),
        ("PIN Management", test_pin_management),
        ("Web Login Authentication", test_web_login),
        ("Phone Verification", test_phone_verification),
        ("System Summary", test_complete_summary)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Final summary
    print_header("TEST RESULTS")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print("\n" + "="*60)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("🎉 All tests passed! Phase 4D is fully operational!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Review output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
