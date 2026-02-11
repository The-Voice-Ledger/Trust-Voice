"""Quick check: what campaigns exist in DB and why search might miss them."""
from database.db import SessionLocal
from database.models import Campaign

db = SessionLocal()
campaigns = db.query(Campaign).all()
print(f"Total campaigns in DB: {len(campaigns)}\n")

for c in campaigns:
    title_short = (c.title or "")[:50]
    print(f"  #{c.id}: status={c.status!r:12s} category={c.category!r:15s} title={title_short!r}")

# Now test: how many are "active"?
active = db.query(Campaign).filter(Campaign.status == "active").all()
print(f"\nActive campaigns (status='active'): {len(active)}")

# What distinct statuses exist?
statuses = db.query(Campaign.status).distinct().all()
print(f"Distinct statuses: {[s[0] for s in statuses]}")

# What distinct categories exist?
categories = db.query(Campaign.category).distinct().all()
print(f"Distinct categories: {[c[0] for c in categories]}")

# Test: search with category="education"
edu = db.query(Campaign).filter(Campaign.status == "active", Campaign.category == "education").all()
print(f"\nActive + category='education' (exact): {len(edu)}")

edu_i = db.query(Campaign).filter(Campaign.status == "active", Campaign.category.ilike("education")).all()
print(f"Active + category ilike 'education': {len(edu_i)}")

db.close()
