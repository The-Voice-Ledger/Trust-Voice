"""Verify the ilike fix works."""
import sys
sys.path.insert(0, "/Users/manu/Trust-Voice")

from database.db import SessionLocal
from database.models import Campaign

db = SessionLocal()

cat = "Education"  # NLU returns capitalized

exact = db.query(Campaign).filter(
    Campaign.status == "active", 
    Campaign.category == cat
).count()

ilike = db.query(Campaign).filter(
    Campaign.status == "active", 
    Campaign.category.ilike(cat)
).count()

print(f"category='{cat}': exact match={exact}, ilike match={ilike}")

# Now test through the actual fixed code
from voice.workflows.search_flow import SearchConversation

results = SearchConversation._search_with_filters({"category": "Education"}, db)
print(f"\nSearchConversation._search_with_filters(category='Education'): {len(results)} campaigns")

results2 = SearchConversation._search_with_filters({}, db)
print(f"SearchConversation._search_with_filters(no filters): {len(results2)} campaigns")

results3 = SearchConversation._search_with_filters({"category": "Water"}, db)
print(f"SearchConversation._search_with_filters(category='Water'): {len(results3)} campaigns")

if results:
    print(f"\nFirst 3 education campaigns:")
    for c in results[:3]:
        print(f"  #{c.id}: {c.title} (category={c.category})")

db.close()
