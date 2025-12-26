"""
Test Phase 4D Registration
Verify database models and registration flows
"""

from database.db import SessionLocal
from database.models import User, PendingRegistration, UserRole
from services.auth_service import hash_pin, verify_pin, is_weak_pin
from datetime import datetime

def test_database_models():
    """Test database models and queries"""
    print("=" * 60)
    print("Testing Phase 4D Database Models")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test 1: Query users table
        print("\n1. Query users table...")
        users = db.query(User).all()
        print(f"   ✅ Found {len(users)} users")
        
        # Test 2: Query pending_registrations table
        print("\n2. Query pending_registrations table...")
        pending = db.query(PendingRegistration).all()
        print(f"   ✅ Found {len(pending)} pending registrations")
        
        # Test 3: Create test donor
        print("\n3. Creating test donor...")
        test_donor = User(
            telegram_user_id="TEST_DONOR_123",
            telegram_username="test_donor",
            telegram_first_name="Test",
            telegram_last_name="Donor",
            role=UserRole.DONOR,
            is_approved=True,
            approved_at=datetime.utcnow()
        )
        db.add(test_donor)
        db.commit()
        print("   ✅ Donor created successfully")
        
        # Test 4: Query by telegram_user_id
        print("\n4. Query by telegram_user_id...")
        found_donor = db.query(User).filter(
            User.telegram_user_id == "TEST_DONOR_123"
        ).first()
        print(f"   ✅ Found donor: {found_donor.telegram_first_name} (Role: {found_donor.role.value})")
        
        # Test 5: Create pending registration
        print("\n5. Creating pending campaign creator...")
        test_pin = "1357"
        pin_hash = hash_pin(test_pin)
        
        pending_creator = PendingRegistration(
            telegram_user_id="TEST_CREATOR_456",
            telegram_username="test_creator",
            telegram_first_name="Test",
            telegram_last_name="Creator",
            requested_role="CAMPAIGN_CREATOR",
            full_name="Test Campaign Creator",
            organization_name="Test NGO",
            location="Addis Ababa, Ethiopia",
            phone_number="+251911234567",
            reason="Need funding for clean water project",
            verification_experience="Yes, worked with local NGOs",
            pin_hash=pin_hash,
            status="PENDING"
        )
        db.add(pending_creator)
        db.commit()
        print("   ✅ Pending registration created")
        
        # Test 6: Query pending by status
        print("\n6. Query pending registrations by status...")
        pending_list = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).all()
        print(f"   ✅ Found {len(pending_list)} pending approvals")
        for p in pending_list:
            print(f"      - {p.full_name} ({p.requested_role})")
        
        # Test 7: PIN authentication
        print("\n7. Testing PIN authentication...")
        assert verify_pin(test_pin, pin_hash), "PIN verification failed"
        assert not verify_pin("9999", pin_hash), "Wrong PIN should fail"
        print("   ✅ PIN authentication works")
        
        # Test 8: Weak PIN detection
        print("\n8. Testing weak PIN detection...")
        weak_pins = ["0000", "1234", "1111", "4321"]
        for pin in weak_pins:
            is_weak, reason = is_weak_pin(pin)
            assert is_weak, f"Should detect {pin} as weak"
        is_weak, reason = is_weak_pin("1357")
        assert not is_weak, "1357 should be strong"
        print("   ✅ Weak PIN detection works")
        
        # Test 9: Role-based queries
        print("\n9. Testing role-based queries...")
        donors = db.query(User).filter(User.role == UserRole.DONOR).count()
        print(f"   ✅ Donors: {donors}")
        
        # Cleanup
        print("\n10. Cleaning up test data...")
        db.query(User).filter(User.telegram_user_id.like("TEST_%")).delete()
        db.query(PendingRegistration).filter(PendingRegistration.telegram_user_id.like("TEST_%")).delete()
        db.commit()
        print("   ✅ Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_database_models()
