"""
Database State Checker for Lab 5 Module Testing
Uses SQLAlchemy to query and display current database state
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_engine():
    """Create database engine"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        sys.exit(1)
    return create_engine(database_url)

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_summary(conn):
    """Display overall database summary"""
    print_section("📊 DATABASE SUMMARY")
    
    queries = {
        'Campaigns': 'SELECT COUNT(*) FROM campaigns',
        'Active Campaigns': "SELECT COUNT(*) FROM campaigns WHERE status='active'",
        'Pending Campaigns': "SELECT COUNT(*) FROM campaigns WHERE status='pending'",
        'Donations': 'SELECT COUNT(*) FROM donations',
        'Total Raised (USD)': 'SELECT COALESCE(SUM(amount_usd), 0) FROM donations WHERE status=\'completed\'',
        'Users': 'SELECT COUNT(*) FROM users',
        'Impact Verifications': 'SELECT COUNT(*) FROM impact_verifications',
        'Approved Verifications': "SELECT COUNT(*) FROM impact_verifications WHERE status='approved'",
    }
    
    for label, query in queries.items():
        result = conn.execute(text(query)).scalar()
        if 'USD' in label:
            print(f"   {label:.<30} ${result:,.2f}")
        else:
            print(f"   {label:.<30} {result}")

def check_campaigns(conn):
    """Display recent campaigns"""
    print_section("📋 MODULE 1: Recent Campaigns")
    
    query = text("""
        SELECT c.id, c.title, c.status, c.raised_amount_usd, c.goal_amount_usd, 
               c.verification_count, c.avg_trust_score, c.created_at,
               COUNT(DISTINCT d.id) as donor_count
        FROM campaigns c
        LEFT JOIN donations d ON c.id = d.campaign_id
        GROUP BY c.id, c.title, c.status, c.raised_amount_usd, c.goal_amount_usd, 
                 c.verification_count, c.avg_trust_score, c.created_at
        ORDER BY c.created_at DESC 
        LIMIT 5
    """)
    
    results = conn.execute(query).fetchall()
    if not results:
        print("   No campaigns found")
        return
    
    for row in results:
        print(f"\n   📌 {row.title}")
        print(f"      ID: {row.id}")
        print(f"      Status: {row.status}")
        print(f"      Progress: ${row.raised_amount_usd:,.2f} / ${row.goal_amount_usd:,.2f}")
        progress_pct = (row.raised_amount_usd / row.goal_amount_usd * 100) if row.goal_amount_usd > 0 else 0
        print(f"      Progress: {progress_pct:.1f}%")
        print(f"      Donors: {row.donor_count} | Verifications: {row.verification_count}")
        if row.avg_trust_score:
            print(f"      Trust Score: {row.avg_trust_score:.1f}/100")
        print(f"      Created: {row.created_at}")

def check_donations(conn):
    """Display recent donations"""
    print_section("💰 MODULE 2: Recent Donations")
    
    query = text("""
        SELECT d.id, d.amount_usd, d.currency, d.status, d.payment_method,
               d.transaction_id, c.title as campaign_title, d.created_at
        FROM donations d
        LEFT JOIN campaigns c ON d.campaign_id = c.id
        ORDER BY d.created_at DESC
        LIMIT 5
    """)
    
    results = conn.execute(query).fetchall()
    if not results:
        print("   No donations found")
        return
    
    for row in results:
        status_emoji = {"completed": "✅", "pending": "⏳", "failed": "❌"}.get(row.status, "❓")
        print(f"\n   {status_emoji} ${row.amount_usd:,.2f} ({row.currency}) - {row.status}")
        print(f"      Campaign: {row.campaign_title or 'N/A'}")
        print(f"      Method: {row.payment_method}")
        if row.transaction_id:
            print(f"      Transaction: {row.transaction_id}")
        print(f"      Created: {row.created_at}")

def check_verifications(conn):
    """Display impact verifications"""
    print_section("🔍 MODULE 4: Impact Verifications")
    
    query = text("""
        SELECT iv.id, iv.campaign_id, iv.trust_score, iv.status,
               iv.agent_payout_status, iv.agent_payout_amount_usd,
               iv.verification_date, c.title as campaign_title
        FROM impact_verifications iv
        LEFT JOIN campaigns c ON iv.campaign_id = c.id
        ORDER BY iv.created_at DESC
        LIMIT 5
    """)
    
    results = conn.execute(query).fetchall()
    if not results:
        print("   No impact verifications found")
        return
    
    for row in results:
        status_emoji = {"approved": "✅", "pending": "⏳", "rejected": "❌"}.get(row.status, "❓")
        print(f"\n   {status_emoji} Trust Score: {row.trust_score}/100 - {row.status}")
        print(f"      Campaign: {row.campaign_title or 'Unknown'}")
        print(f"      Agent Payout: {row.agent_payout_status} (${row.agent_payout_amount_usd or 0})")
        print(f"      Date: {row.verification_date}")

def check_users(conn):
    """Display user statistics"""
    print_section("👥 MODULE: User Registrations")
    
    # By role
    query = text("SELECT role, COUNT(*) as count FROM users GROUP BY role ORDER BY count DESC")
    results = conn.execute(query).fetchall()
    
    print("\n   By Role:")
    for row in results:
        print(f"      {row.role:.<20} {row.count}")
    
    # Recent users
    query = text("""
        SELECT id, phone_number, role, preferred_language, is_phone_verified, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT 5
    """)
    results = conn.execute(query).fetchall()
    
    if results:
        print("\n   Recent Users:")
        for row in results:
            verified = "✅" if row.is_phone_verified else "❌"
            print(f"      {verified} {row.phone_number} - {row.role} ({row.preferred_language})")

def check_campaign_details(conn, campaign_title):
    """Display detailed campaign information"""
    print_section(f"🔎 Campaign Details: {campaign_title}")
    
    # Campaign info
    query = text("""
        SELECT c.id, c.title, c.status, c.description, c.category, c.raised_amount_usd,
               c.goal_amount_usd, c.verification_count, c.avg_trust_score, c.created_at,
               COUNT(DISTINCT d.id) as donor_count
        FROM campaigns c
        LEFT JOIN donations d ON c.id = d.campaign_id
        WHERE c.title ILIKE :title
        GROUP BY c.id, c.title, c.status, c.description, c.category, c.raised_amount_usd,
                 c.goal_amount_usd, c.verification_count, c.avg_trust_score, c.created_at
        ORDER BY c.created_at DESC
        LIMIT 1
    """)
    
    campaign = conn.execute(query, {"title": f"%{campaign_title}%"}).fetchone()
    if not campaign:
        print(f"   Campaign not found: {campaign_title}")
        return
    
    print(f"\n   📌 {campaign.title}")
    print(f"      ID: {campaign.id}")
    print(f"      Status: {campaign.status}")
    print(f"      Category: {campaign.category}")
    print(f"      Progress: ${campaign.raised_amount_usd:,.2f} / ${campaign.goal_amount_usd:,.2f}")
    progress_pct = (campaign.raised_amount_usd / campaign.goal_amount_usd * 100) if campaign.goal_amount_usd > 0 else 0
    print(f"      Progress: {progress_pct:.1f}%")
    print(f"      Donors: {campaign.donor_count}")
    print(f"      Verifications: {campaign.verification_count}")
    if campaign.avg_trust_score:
        print(f"      Trust Score: {campaign.avg_trust_score:.1f}/100")
    
    # Donations for this campaign
    query = text("""
        SELECT amount_usd, currency, status, payment_method, created_at
        FROM donations
        WHERE campaign_id = :campaign_id
        ORDER BY created_at DESC
        LIMIT 5
    """)
    donations = conn.execute(query, {"campaign_id": campaign.id}).fetchall()
    
    if donations:
        print("\n   Recent Donations:")
        for d in donations:
            status_emoji = {"completed": "✅", "pending": "⏳", "failed": "❌"}.get(d.status, "❓")
            print(f"      {status_emoji} ${d.amount_usd:,.2f} ({d.currency}) - {d.payment_method}")
    
    # Verifications for this campaign
    query = text("""
        SELECT trust_score, status, agent_payout_status, verification_date
        FROM impact_verifications
        WHERE campaign_id = :campaign_id
        ORDER BY created_at DESC
        LIMIT 5
    """)
    verifications = conn.execute(query, {"campaign_id": campaign.id}).fetchall()
    
    if verifications:
        print("\n   Verifications:")
        for v in verifications:
            status_emoji = {"approved": "✅", "pending": "⏳", "rejected": "❌"}.get(v.status, "❓")
            print(f"      {status_emoji} Score: {v.trust_score}/100 - {v.status}")

def main():
    """Main function"""
    engine = get_engine()
    
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║         Lab 5 Module Testing - Database State Checker         ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    if len(sys.argv) > 1:
        # Check specific campaign
        campaign_title = " ".join(sys.argv[1:])
        with engine.connect() as conn:
            check_campaign_details(conn, campaign_title)
    else:
        # Full report
        with engine.connect() as conn:
            check_summary(conn)
            check_campaigns(conn)
            check_donations(conn)
            check_verifications(conn)
            check_users(conn)
    
    print("\n" + "=" * 80)
    print("✅ Database state check complete")
    print("=" * 80)
    print("\n💡 Usage:")
    print("   python tests/check_db_state.py                    # Full report")
    print("   python tests/check_db_state.py 'campaign name'    # Campaign details")
    print()

if __name__ == "__main__":
    main()
