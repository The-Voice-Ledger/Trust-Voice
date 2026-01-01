"""
Update campaigns to have categories
"""
import os
from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import Campaign

db = SessionLocal()

# Define category mapping based on campaign titles
category_mapping = {
    "Water Filtration Systems": "water",
    "School Construction in Tigray": "education",
    "Teacher Training Program": "education",
    "Mobile Medical Clinic": "health",
    "Test Campaign": "education"  # Default for test campaigns
}

campaigns = db.query(Campaign).all()

print("Updating campaign categories...\n")

for campaign in campaigns:
    # Find matching category
    category = None
    for keyword, cat in category_mapping.items():
        if keyword.lower() in campaign.title.lower():
            category = cat
            break
    
    if not category:
        category = "education"  # Default fallback
    
    campaign.category = category
    print(f"✓ {campaign.title[:40]:45} → {category}")

db.commit()
print(f"\n✅ Updated {len(campaigns)} campaigns")
db.close()
