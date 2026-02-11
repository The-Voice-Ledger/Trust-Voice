"""Trace exactly what happens for the failing voice queries."""
import sys
sys.path.insert(0, "/Users/manu/Trust-Voice")

from database.db import SessionLocal
from database.models import Campaign
from voice.nlu.nlu_infer import extract_intent_and_entities
from voice.workflows.search_flow import SearchConversation

import asyncio, logging
logging.basicConfig(level=logging.DEBUG)

db = SessionLocal()

queries = [
    "Find education campaigns",
    "List all campaigns",
    "Show me campaigns",
    "search campaigns",
]

async def test():
    for q in queries:
        print(f"\n{'='*60}")
        print(f"USER: \"{q}\"")
        print(f"{'='*60}")
        
        # Step 1: NLU
        nlu = extract_intent_and_entities(q, "en", {})
        intent = nlu["intent"]
        entities = nlu["entities"]
        print(f"  NLU → intent={intent}, entities={entities}")
        
        # Step 2: What filters does SearchConversation extract?
        if entities:
            filters = {k: v for k, v in entities.items() 
                       if k in ['category', 'region', 'keyword', 'location'] and v}
            if 'location' in filters:
                filters['region'] = filters.pop('location')
        else:
            filters = SearchConversation._parse_query(q)
        
        print(f"  Filters → {filters}")
        
        # Step 3: What does the DB query return?
        query = db.query(Campaign).filter(Campaign.status == "active")
        
        if filters.get("category"):
            cat = filters["category"]
            exact = db.query(Campaign).filter(
                Campaign.status == "active",
                Campaign.category == cat
            ).count()
            ilike = db.query(Campaign).filter(
                Campaign.status == "active",
                Campaign.category.ilike(cat)
            ).count()
            print(f"  DB category='{cat}' → exact: {exact}, ilike: {ilike}")
            query = query.filter(Campaign.category == cat)
        
        results = query.order_by(Campaign.created_at.desc()).limit(10).all()
        print(f"  Final results: {len(results)} campaigns")

asyncio.run(test())
db.close()
