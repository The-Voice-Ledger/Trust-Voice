"""
Debug search flow
"""
import os
from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import Campaign
from voice.workflows.search_flow import SearchConversation

db = SessionLocal()

# Test parsing
query = "campaigns"
filters = SearchConversation._parse_query(query)
print(f"Query: '{query}'")
print(f"Parsed filters: {filters}")

# Test search with those filters
campaigns = SearchConversation._search_with_filters(filters, db)
print(f"Found: {len(campaigns)} campaigns")

# Test with empty filters (should return all)
print("\nDirect DB query (no filters):")
all_campaigns = db.query(Campaign).filter(Campaign.status == "active").limit(10).all()
print(f"Found: {len(all_campaigns)} active campaigns")
for c in all_campaigns[:3]:
    print(f"  - {c.title} (category: {c.category})")

db.close()
