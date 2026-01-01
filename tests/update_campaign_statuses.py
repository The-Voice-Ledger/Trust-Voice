"""
Check and update campaign statuses
"""
import os
from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import Campaign

db = SessionLocal()

campaigns = db.query(Campaign).all()

print(f"Total campaigns: {len(campaigns)}\n")
print("Current statuses:")
status_counts = {}
for c in campaigns:
    status = c.status or "None"
    status_counts[status] = status_counts.get(status, 0) + 1
    
for status, count in status_counts.items():
    print(f"  {status}: {count}")

print("\nUpdating all to 'active'...")
for c in campaigns:
    c.status = "active"

db.commit()
print(f"✅ Updated {len(campaigns)} campaigns to active status")

# Verify
active_count = db.query(Campaign).filter(Campaign.status == "active").count()
print(f"✅ Verified: {active_count} active campaigns")

db.close()
