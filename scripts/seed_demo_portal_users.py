"""
Seed demo users for each portal role so the portal can be tested.

All demo users use PIN 1234.

Run:
    python -m scripts.seed_demo_portal_users
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db
from database.models import User
from services.auth_service import hash_pin
from datetime import datetime

DEMO_USERS = [
    {
        "telegram_username": "demo_user",
        "full_name": "Demo Funder",
        "role": "DONOR",
        "phone_number": "+254700000001",
    },
    {
        "telegram_username": "demo_ngo",
        "full_name": "Demo NGO Admin",
        "role": "NGO_ADMIN",
        "phone_number": "+254700000002",
        "ngo_id": 23,  # Ukulima Collective
    },
    {
        "telegram_username": "demo_admin",
        "full_name": "Demo Platform Admin",
        "role": "SUPER_ADMIN",
        "phone_number": "+254700000003",
    },
    {
        "telegram_username": "demo_agent",
        "full_name": "Demo Field Agent",
        "role": "FIELD_AGENT",
        "phone_number": "+254700000004",
    },
]

PIN = "1234"


def main():
    db = next(get_db())
    hashed = hash_pin(PIN)

    for data in DEMO_USERS:
        username = data["telegram_username"]
        existing = db.query(User).filter(User.telegram_username == username).first()
        if existing:
            # Update role / pin in case it drifted
            existing.role = data["role"]
            existing.pin_hash = hashed
            existing.is_approved = True
            existing.full_name = data["full_name"]
            if data.get("ngo_id"):
                existing.ngo_id = data["ngo_id"]
            if data.get("phone_number"):
                # Only set phone if not already taken by another user
                conflict = db.query(User).filter(
                    User.phone_number == data["phone_number"],
                    User.id != existing.id,
                ).first()
                if not conflict:
                    existing.phone_number = data["phone_number"]
            db.commit()
            print(f"  Updated @{username} → role={data['role']}")
        else:
            # Check if phone already taken
            phone = data.get("phone_number")
            if phone:
                conflict = db.query(User).filter(User.phone_number == phone).first()
                if conflict:
                    phone = None  # skip phone to avoid unique violation
            user = User(
                telegram_username=username,
                full_name=data["full_name"],
                role=data["role"],
                phone_number=phone,
                ngo_id=data.get("ngo_id"),
                pin_hash=hashed,
                pin_set_at=datetime.utcnow(),
                is_approved=True,
                preferred_language="en",
            )
            db.add(user)
            db.commit()
            print(f"  Created @{username} → role={data['role']}")

    print("\n✅ Demo portal users ready. Login with any @username above + PIN 1234")


if __name__ == "__main__":
    main()
