"""Quick test of milestone handler functions."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from database.db import SessionLocal
from voice.handlers.milestone_handler import get_milestones, get_project_treasury

async def test():
    db = SessionLocal()

    result = await get_milestones(campaign_id=28, db=db)
    print("=== get_milestones ===")
    for m in result.get("milestones", []):
        print(f"  #{m['sequence']} {m['title']:30s} ${m['target_amount_usd']:>10,.2f}  [{m['status']}]")
    print(f"  Progress: {result['progress_pct']}%")

    treasury = await get_project_treasury(campaign_id=28, db=db)
    print("\n=== get_project_treasury ===")
    print(f"  Raised:   ${treasury['total_raised_usd']:>10,.2f}")
    print(f"  Target:   ${treasury['total_milestone_target_usd']:>10,.2f}")
    print(f"  Released: ${treasury['total_released_usd']:>10,.2f}")
    print(f"  Fees:     ${treasury['total_fees_collected_usd']:>10,.2f}")
    print(f"  Held:     ${treasury['funds_held_usd']:>10,.2f}")

    db.close()

asyncio.run(test())
