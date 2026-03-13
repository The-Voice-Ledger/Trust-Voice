"""
Seed the Ukulima (Moringa Oasis Zimbabwe) campaign with milestones.

This script:
1. Deletes all existing fake/test campaigns and their dependent records
2. Creates an "Ukulima" NGO organization
3. Creates the Ukulima campaign ($400K goal, milestone-gated)
4. Creates 4 milestones matching the financial breakdown from the landing page

Run:
    python -m scripts.seed_ukulima
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import (
    Campaign, CampaignContext, Donation, ImpactVerification,
    NGOOrganization, ProjectMilestone, MilestoneVerification,
    ProjectUpdate, PlatformFee, Payout, MilestoneStatus,
)
from datetime import datetime, timezone, timedelta
from decimal import Decimal

def run():
    db = SessionLocal()
    try:
        # ── 1. Clean out ALL existing campaigns + dependencies ──────────
        print("\n🧹 Cleaning existing data...")

        # Delete in FK-safe order
        for model, label in [
            (MilestoneVerification, "milestone verifications"),
            (ProjectMilestone, "milestones"),
            (ProjectUpdate, "project updates"),
            (PlatformFee, "platform fees"),
            (Payout, "payouts"),
            (ImpactVerification, "impact verifications"),
            (CampaignContext, "campaign contexts"),
            (Donation, "donations"),
            (Campaign, "campaigns"),
            (NGOOrganization, "NGO organizations"),
        ]:
            count = db.query(model).delete()
            if count:
                print(f"   Deleted {count} {label}")

        db.flush()
        print("   ✅ All test data removed\n")

        # ── 2. Create the Ukulima NGO org ───────────────────────────────
        ngo = NGOOrganization(
            name="Ukulima Collective",
            description=(
                "A community-driven agricultural initiative building a 10-hectare "
                "Moringa farm, processing facility, and eco-lodge in Zimbabwe. "
                "Community-funded. Self-sustaining."
            ),
            country="Zimbabwe",
            contact_email="hello@ukulima.farm",
            is_active=True,
        )
        db.add(ngo)
        db.flush()  # get ngo.id
        print(f"🏢 Created NGO: {ngo.name} (id={ngo.id})")

        # ── 3. Create the Ukulima Campaign ──────────────────────────────
        campaign = Campaign(
            ngo_id=ngo.id,
            title="Moringa Oasis Zimbabwe",
            description=(
                "A 10-hectare sanctuary combining high-density Moringa production, "
                "on-site processing, and a \"Live-Work-Learn\" eco-lodge where "
                "contributors become community.\n\n"
                "Help us build the farm, the processing facility, and the eco-lodge. "
                "In return, come be part of it — stay, harvest, create, and grow with us.\n\n"
                "Every contribution is tracked with immutable transparency on the "
                "TrustVoice platform. Fund the farm, come live and learn on it, "
                "and watch it grow itself."
            ),
            goal_amount_usd=Decimal("400000.00"),
            raised_amount_usd=Decimal("0.00"),
            raised_amounts={},
            category="agriculture",
            location_country="Zimbabwe",
            location_region="Rural Zimbabwe",
            status="active",
            use_milestones=True,
            platform_fee_rate=Decimal("0.0600"),
            start_date=datetime.now(timezone.utc),
        )
        db.add(campaign)
        db.flush()  # get campaign.id
        print(f"🌿 Created Campaign: {campaign.title} (id={campaign.id})")
        print(f"   Goal: ${campaign.goal_amount_usd:,.2f}  |  Milestones: ON  |  Fee: 6%")

        # ── 4. Create 4 Milestones ──────────────────────────────────────
        milestones_data = [
            {
                "sequence": 1,
                "title": "Agri-Infrastructure",
                "description": (
                    "Solar drip irrigation system, borehole drilling, and "
                    "high-yield Moringa seedlings for the 10-hectare farm. "
                    "This is the foundation — water, power, and trees."
                ),
                "target_amount_usd": Decimal("110000.00"),
                "status": MilestoneStatus.ACTIVE.value,
            },
            {
                "sequence": 2,
                "title": "Processing Facility",
                "description": (
                    "Industrial dehydrators, pulverizers, and cold-press oil "
                    "expellers. This is where raw Moringa leaves become "
                    "exportable powder, capsules, and oil — the value creation engine."
                ),
                "target_amount_usd": Decimal("50000.00"),
                "status": MilestoneStatus.PENDING.value,
            },
            {
                "sequence": 3,
                "title": "Eco-Lodge",
                "description": (
                    "6 solar-powered cottages ($30K each) for contributors "
                    "and travelers to live, work, and learn on the farm. "
                    "The \"Live-Work-Learn\" experience that makes Ukulima unique."
                ),
                "target_amount_usd": Decimal("180000.00"),
                "status": MilestoneStatus.PENDING.value,
            },
            {
                "sequence": 4,
                "title": "Operations & Certification",
                "description": (
                    "EU/UK Organic certification and market access so the farm "
                    "can sell globally from day one. This milestone unlocks "
                    "international revenue channels and self-sustainability."
                ),
                "target_amount_usd": Decimal("60000.00"),
                "status": MilestoneStatus.PENDING.value,
            },
        ]

        for m in milestones_data:
            milestone = ProjectMilestone(
                campaign_id=campaign.id,
                title=m["title"],
                description=m["description"],
                sequence=m["sequence"],
                target_amount_usd=m["target_amount_usd"],
                released_amount_usd=Decimal("0.00"),
                platform_fee_usd=Decimal("0.00"),
                status=m["status"],
            )
            db.add(milestone)

        db.flush()
        print(f"\n📋 Created 4 milestones:")
        for m in milestones_data:
            marker = "🟢" if m["status"] == "active" else "⏳"
            print(f"   {marker} #{m['sequence']}  {m['title']:30s}  ${m['target_amount_usd']:>10,.2f}")

        total = sum(m["target_amount_usd"] for m in milestones_data)
        print(f"\n   {'Total':33s}  ${total:>10,.2f}")
        assert total == campaign.goal_amount_usd, "Milestone totals must equal campaign goal!"

        # ── 5. Add campaign context for the AI agent (RAG) ─────────────
        contexts = [
            CampaignContext(
                campaign_id=campaign.id,
                content_type="description",
                content=(
                    "Ukulima — Moringa Oasis Zimbabwe. A 10-hectare Moringa farm, "
                    "processing facility, and eco-lodge in rural Zimbabwe. "
                    "Community-funded and designed to be self-sustaining. "
                    "The global Moringa market is worth $10.78 billion and growing "
                    "at 9.7% annually. Ukulima targets the $1.2B serviceable market "
                    "with an 800% margin increase through value-addition (powder, "
                    "capsules, cold-pressed oil). 8 harvests per year, 200 tonnes "
                    "CO2 sequestered annually, entirely solar-powered."
                ),
            ),
            CampaignContext(
                campaign_id=campaign.id,
                content_type="faq",
                content=(
                    "Q: What is Ukulima?\n"
                    "A: Ukulima is a 10-hectare Moringa farm, processing facility, "
                    "and eco-lodge in Zimbabwe. It combines high-density Moringa "
                    "production, on-site processing, and a 'Live-Work-Learn' "
                    "eco-lodge where contributors become community.\n\n"
                    "Q: How much does it cost to build?\n"
                    "A: $400,000 total, broken into 4 milestones: "
                    "Agri-Infrastructure ($110K), Processing Facility ($50K), "
                    "Eco-Lodge ($180K), and Operations & Certification ($60K).\n\n"
                    "Q: What are the revenue projections?\n"
                    "A: Year 1: $180K (building phase), Year 2: $1.25M (growing), "
                    "Year 3: $3.1M (self-sustaining).\n\n"
                    "Q: How are funds released?\n"
                    "A: Through milestone-based releases. Funds for each phase are "
                    "only released after a field agent verifies the work is complete. "
                    "Every transaction is tracked on-chain for full transparency.\n\n"
                    "Q: Can I visit the farm?\n"
                    "A: Yes! The eco-lodge (Milestone 3) creates 6 solar-powered "
                    "cottages where contributors and travelers can live, work, and "
                    "learn on the farm."
                ),
            ),
            CampaignContext(
                campaign_id=campaign.id,
                content_type="impact",
                content=(
                    "Revenue pillars: Moringa B2B sales (powder, oil, capsules to "
                    "health brands), direct-to-consumer sales, and Live-Work-Learn "
                    "eco-lodge stays. Strategic advantages: 800% margin increase "
                    "with value addition, 8 harvests per year in Zimbabwe's climate, "
                    "200 tonnes CO2 sequestered per year, fully solar-powered "
                    "operations. The farm is designed to be self-sustaining by "
                    "Year 3 with projected $3.1M revenue."
                ),
            ),
        ]
        for ctx in contexts:
            db.add(ctx)

        db.flush()
        print(f"\n📚 Created {len(contexts)} campaign context entries (RAG)")

        # ── 6. Commit everything ────────────────────────────────────────
        db.commit()
        print("\n✅ All data committed successfully!")
        print(f"\n{'='*60}")
        print(f"  Campaign ID : {campaign.id}")
        print(f"  NGO ID      : {ngo.id}")
        print(f"  Title       : {campaign.title}")
        print(f"  Goal        : ${campaign.goal_amount_usd:,.2f}")
        print(f"  Status      : {campaign.status}")
        print(f"  Milestones  : 4 (first one ACTIVE)")
        print(f"  Fee Rate    : {float(campaign.platform_fee_rate)*100:.1f}%")
        print(f"{'='*60}\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
