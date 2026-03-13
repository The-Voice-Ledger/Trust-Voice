"""Quick verification of seeded Ukulima data."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from database.db import SessionLocal
from database.models import Campaign, ProjectMilestone, CampaignContext, NGOOrganization

db = SessionLocal()

c = db.query(Campaign).first()
print(f"Campaign: id={c.id}, title={c.title}")
print(f"  goal=${c.goal_amount_usd:,.2f}, status={c.status}, milestones={c.use_milestones}, fee={c.platform_fee_rate}")

ngo = db.query(NGOOrganization).first()
print(f"NGO: id={ngo.id}, name={ngo.name}, country={ngo.country}")

ms = db.query(ProjectMilestone).filter_by(campaign_id=c.id).order_by(ProjectMilestone.sequence).all()
print(f"\nMilestones ({len(ms)}):")
for m in ms:
    print(f"  #{m.sequence} [{m.status:20s}] {m.title:30s} ${m.target_amount_usd:>10,.2f}")

ctxs = db.query(CampaignContext).filter_by(campaign_id=c.id).all()
print(f"\nContext entries: {len(ctxs)} ({[x.content_type for x in ctxs]})")

total = db.query(Campaign).count()
print(f"\nTotal campaigns in DB: {total}")
db.close()
