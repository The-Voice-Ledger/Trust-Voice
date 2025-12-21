"""
Seed data script for TrustVoice database
Creates sample NGOs, campaigns, and donors for testing
"""
import os
import sys
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models import NGOOrganization, Campaign, Donor


def seed_ngos(db: Session):
    """Create sample NGO organizations"""
    ngos_data = [
        {
            "name": "Water For All Kenya",
            "description": "Providing clean water to rural communities in Kenya",
            "website_url": "https://waterforallkenya.org",
            "contact_email": "contact@waterforallkenya.org",
            "blockchain_wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f01234"
        },
        {
            "name": "Education Ethiopia",
            "description": "Building schools and training teachers in rural Ethiopia",
            "website_url": "https://educationethiopia.org",
            "contact_email": "info@educationethiopia.org",
            "blockchain_wallet_address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c65678"
        },
        {
            "name": "Health For All Tanzania",
            "description": "Mobile clinics and medical supplies for remote Tanzania villages",
            "website_url": "https://healthtanzania.org",
            "contact_email": "support@healthtanzania.org",
            "blockchain_wallet_address": "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12"
        }
    ]
    
    created_ngos = []
    for ngo_data in ngos_data:
        # Check if already exists
        existing = db.query(NGOOrganization).filter(
            NGOOrganization.name == ngo_data["name"]
        ).first()
        
        if not existing:
            ngo = NGOOrganization(**ngo_data)
            db.add(ngo)
            db.commit()
            db.refresh(ngo)
            created_ngos.append(ngo)
            print(f"✅ Created NGO: {ngo.name} (ID: {ngo.id})")
        else:
            created_ngos.append(existing)
            print(f"⚠️  NGO already exists: {existing.name} (ID: {existing.id})")
    
    return created_ngos


def seed_campaigns(db: Session, ngos: list):
    """Create sample campaigns"""
    campaigns_data = [
        {
            "ngo": ngos[0],  # Water For All Kenya
            "title": "Clean Water Wells for Rural Kenya",
            "description": "Install 10 water wells in drought-affected villages in Turkana County. Each well serves 500 people.",
            "goal_amount_usd": 50000.0,
            "location_gps": "-1.286389,36.817223"
        },
        {
            "ngo": ngos[0],  # Water For All Kenya
            "title": "Water Filtration Systems",
            "description": "Distribute 200 portable water filtration systems to families in Kisumu region",
            "goal_amount_usd": 15000.0,
            "location_gps": "-0.091702,34.767956"
        },
        {
            "ngo": ngos[1],  # Education Ethiopia
            "title": "School Construction in Tigray",
            "description": "Build 3 primary schools for 600 students in post-conflict Tigray region",
            "goal_amount_usd": 120000.0,
            "location_gps": "14.270972,38.275575"
        },
        {
            "ngo": ngos[1],  # Education Ethiopia
            "title": "Teacher Training Program",
            "description": "Train 50 teachers in modern teaching methods and provide learning materials",
            "goal_amount_usd": 25000.0,
            "location_gps": "9.145000,40.489673"
        },
        {
            "ngo": ngos[2],  # Health For All Tanzania
            "title": "Mobile Medical Clinic",
            "description": "Operate mobile clinic serving 20 remote villages in Mbeya region for 1 year",
            "goal_amount_usd": 80000.0,
            "location_gps": "-8.900000,33.450000"
        }
    ]
    
    created_campaigns = []
    for campaign_data in campaigns_data:
        # Check if already exists
        existing = db.query(Campaign).filter(
            Campaign.title == campaign_data["title"]
        ).first()
        
        if not existing:
            ngo = campaign_data.pop("ngo")
            campaign = Campaign(
                ngo_id=ngo.id,
                raised_amount_usd=0.0,
                status="active",
                **campaign_data
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            created_campaigns.append(campaign)
            print(f"✅ Created Campaign: {campaign.title} (ID: {campaign.id})")
        else:
            created_campaigns.append(existing)
            print(f"⚠️  Campaign already exists: {existing.title} (ID: {existing.id})")
    
    return created_campaigns


def seed_donors(db: Session):
    """Create sample donors"""
    donors_data = [
        {
            "phone_number": "+254712345678",
            "telegram_user_id": "123456789",
            "whatsapp_number": "+254712345678",
            "preferred_language": "en"
        },
        {
            "phone_number": "+251911234567",
            "telegram_user_id": "987654321",
            "preferred_language": "am"  # Amharic
        },
        {
            "phone_number": "+255754123456",
            "whatsapp_number": "+255754123456",
            "preferred_language": "sw"  # Swahili
        },
        {
            "telegram_user_id": "555666777",
            "preferred_language": "en"
        },
        {
            "phone_number": "+4915123456789",
            "preferred_language": "de"  # German
        }
    ]
    
    created_donors = []
    for donor_data in donors_data:
        # Check if already exists
        phone = donor_data.get("phone_number")
        telegram = donor_data.get("telegram_user_id")
        
        existing = None
        if phone:
            existing = db.query(Donor).filter(Donor.phone_number == phone).first()
        if not existing and telegram:
            existing = db.query(Donor).filter(Donor.telegram_user_id == telegram).first()
        
        if not existing:
            donor = Donor(total_donated_usd=0.0, **donor_data)
            db.add(donor)
            db.commit()
            db.refresh(donor)
            created_donors.append(donor)
            contact = donor.phone_number or donor.telegram_user_id or donor.whatsapp_number
            print(f"✅ Created Donor: {contact} (ID: {donor.id})")
        else:
            created_donors.append(existing)
            contact = existing.phone_number or existing.telegram_user_id or existing.whatsapp_number
            print(f"⚠️  Donor already exists: {contact} (ID: {existing.id})")
    
    return created_donors


def main():
    """Run all seed functions"""
    print("\n🌱 Starting database seed...\n")
    
    db = SessionLocal()
    try:
        # Seed in order (NGOs first, then campaigns that reference them)
        print("📦 Seeding NGOs...")
        ngos = seed_ngos(db)
        
        print("\n📦 Seeding Campaigns...")
        campaigns = seed_campaigns(db, ngos)
        
        print("\n📦 Seeding Donors...")
        donors = seed_donors(db)
        
        print(f"\n✅ Seed complete!")
        print(f"   - {len(ngos)} NGOs")
        print(f"   - {len(campaigns)} Campaigns")
        print(f"   - {len(donors)} Donors")
        print("\nYou can now test the API with real data!\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
