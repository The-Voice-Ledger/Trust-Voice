"""
Test actual search with filters
"""
import os
from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import Campaign
from sqlalchemy import or_

db = SessionLocal()

# Test 1: All active campaigns
print("Test 1: All active campaigns")
all_active = db.query(Campaign).filter(Campaign.status == "active").all()
print(f"  Total active: {len(all_active)}")

# Test 2: Filter by category = education
print("\nTest 2: Category = education")
education = db.query(Campaign).filter(
    Campaign.status == "active",
    Campaign.category == "education"
).all()
print(f"  Found: {len(education)}")
if education:
    print(f"  Example: {education[0].title}")

# Test 3: Filter by category = health
print("\nTest 3: Category = health")
health = db.query(Campaign).filter(
    Campaign.status == "active",
    Campaign.category == "health"
).all()
print(f"  Found: {len(health)}")
if health:
    print(f"  Example: {health[0].title}")

# Test 4: Filter by category = water
print("\nTest 4: Category = water")
water = db.query(Campaign).filter(
    Campaign.status == "active",
    Campaign.category == "water"
).all()
print(f"  Found: {len(water)}")
if water:
    print(f"  Example: {water[0].title}")

# Test 5: Keyword search in title/description
print("\nTest 5: Keyword = 'campaigns' in title/description")
keyword_search = db.query(Campaign).filter(
    Campaign.status == "active"
).filter(
    or_(
        Campaign.title.ilike("%campaigns%"),
        Campaign.description.ilike("%campaigns%")
    )
).all()
print(f"  Found: {len(keyword_search)}")

db.close()
