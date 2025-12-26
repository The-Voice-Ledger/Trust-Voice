#!/usr/bin/env python3
"""
Apply impact verification schema updates to existing table.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.db import engine

def apply_schema_updates():
    """Apply all necessary schema changes"""
    
    print("🔄 Applying Impact Verification Schema Updates...\n")
    
    with engine.begin() as conn:
        
        # 1. Add new columns to impact_verifications
        impact_columns = [
            ("field_agent_id", "INTEGER REFERENCES users(id)"),
            ("verification_date", "TIMESTAMP DEFAULT NOW()"),
            ("agent_notes", "TEXT"),
            ("testimonials", "TEXT"),
            ("photos", "JSON"),
            ("gps_latitude", "FLOAT"),
            ("gps_longitude", "FLOAT"),
            ("trust_score", "INTEGER DEFAULT 0"),
            ("status", "VARCHAR(20) DEFAULT 'pending'"),
            ("agent_payout_amount_usd", "FLOAT"),
            ("agent_payout_status", "VARCHAR(20)"),
            ("agent_payout_transaction_id", "VARCHAR(100)"),
            ("created_at", "TIMESTAMP DEFAULT NOW()"),
            ("updated_at", "TIMESTAMP DEFAULT NOW()")
        ]
        
        for col_name, col_type in impact_columns:
            try:
                sql = f"ALTER TABLE impact_verifications ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                conn.execute(text(sql))
                print(f"✅ Added: impact_verifications.{col_name}")
            except Exception as e:
                print(f"⚠️  {col_name}: {str(e)[:100]}")
        
        # 2. Add verification metrics to campaigns
        campaign_columns = [
            ("verification_count", "INTEGER DEFAULT 0"),
            ("total_trust_score", "FLOAT DEFAULT 0.0"),
            ("avg_trust_score", "FLOAT DEFAULT 0.0")
        ]
        
        for col_name, col_type in campaign_columns:
            try:
                sql = f"ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                conn.execute(text(sql))
                print(f"✅ Added: campaigns.{col_name}")
            except Exception as e:
                print(f"⚠️  {col_name}: {str(e)[:100]}")
        
        # 3. Add amount_usd to donations (if missing)
        try:
            sql = "ALTER TABLE donations ADD COLUMN IF NOT EXISTS amount_usd FLOAT"
            conn.execute(text(sql))
            print(f"✅ Added: donations.amount_usd")
            
            # Copy from amount column if exists
            sql = "UPDATE donations SET amount_usd = amount WHERE amount_usd IS NULL AND amount IS NOT NULL"
            conn.execute(text(sql))
            print(f"✅ Migrated: donations.amount -> amount_usd")
        except Exception as e:
            print(f"⚠️  amount_usd: {str(e)[:100]}")
        
        # 4. Add transaction_id to donations (if missing)
        try:
            sql = "ALTER TABLE donations ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(100)"
            conn.execute(text(sql))
            print(f"✅ Added: donations.transaction_id")
            
            # Copy from payment_intent_id if exists
            sql = "UPDATE donations SET transaction_id = payment_intent_id WHERE transaction_id IS NULL AND payment_intent_id IS NOT NULL"
            conn.execute(text(sql))
            print(f"✅ Migrated: donations.payment_intent_id -> transaction_id")
        except Exception as e:
            print(f"⚠️  transaction_id: {str(e)[:100]}")
        
        # 5. Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_impact_verifications_field_agent ON impact_verifications(field_agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_impact_verifications_campaign ON impact_verifications(campaign_id)",
            "CREATE INDEX IF NOT EXISTS idx_impact_verifications_status ON impact_verifications(status)",
            "CREATE INDEX IF NOT EXISTS idx_impact_verifications_trust_score ON impact_verifications(trust_score)",
            "CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)"
        ]
        
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                print(f"✅ Index created")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Index: {str(e)[:80]}")
        
        # 6. Add check constraint for trust score
        try:
            sql = "ALTER TABLE impact_verifications ADD CONSTRAINT check_trust_score CHECK (trust_score >= 0 AND trust_score <= 100)"
            conn.execute(text(sql))
            print(f"✅ Added: trust_score constraint")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"⚠️  Constraint: {str(e)[:80]}")
    
    print("\n✅ SCHEMA UPDATE COMPLETE!\n")

if __name__ == "__main__":
    try:
        apply_schema_updates()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
