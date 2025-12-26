"""
Comprehensive Schema Migration for Lab 5 Voice Modules
Adds all missing columns required by voice handlers
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """Create database engine"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        sys.exit(1)
    return create_engine(database_url)

def column_exists(conn, table_name, column_name):
    """Check if column exists in table"""
    result = conn.execute(text(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        AND column_name = '{column_name}'
    """))
    return result.fetchone() is not None

def add_column_if_missing(conn, table_name, column_name, column_def):
    """Add column if it doesn't exist"""
    if not column_exists(conn, table_name, column_name):
        try:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
            conn.commit()
            print(f"✅ Added: {table_name}.{column_name}")
            return True
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Skipped: {table_name}.{column_name} - {str(e)}")
            return False
    else:
        print(f"ℹ️  Exists: {table_name}.{column_name}")
        return False

def main():
    """Run comprehensive schema migration"""
    engine = get_engine()
    
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║       Lab 5 Comprehensive Schema Migration                    ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    with engine.connect() as conn:
        # ===================================================================
        # CAMPAIGNS TABLE
        # ===================================================================
        print("📋 CAMPAIGNS TABLE")
        print("─" * 64)
        
        # Note: id is already defined, but verify it's UUID or Integer
        result = conn.execute(text("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'campaigns' AND column_name = 'id'
        """))
        id_type = result.fetchone()
        if id_type:
            print(f"ℹ️  campaigns.id type: {id_type[0]}")
        
        # Add verification metrics (already done by apply_schema_updates.py)
        add_column_if_missing(conn, "campaigns", "verification_count", "INTEGER DEFAULT 0")
        add_column_if_missing(conn, "campaigns", "total_trust_score", "FLOAT DEFAULT 0.0")
        add_column_if_missing(conn, "campaigns", "avg_trust_score", "FLOAT DEFAULT 0.0")
        
        # ===================================================================
        # DONATIONS TABLE
        # ===================================================================
        print("\n💰 DONATIONS TABLE")
        print("─" * 64)
        
        # Add amount_usd (if amount needs to be renamed)
        add_column_if_missing(conn, "donations", "amount_usd", "FLOAT")
        
        # Migrate data from amount to amount_usd if needed
        if column_exists(conn, "donations", "amount") and column_exists(conn, "donations", "amount_usd"):
            result = conn.execute(text("SELECT COUNT(*) FROM donations WHERE amount_usd IS NULL AND amount IS NOT NULL"))
            count = result.scalar()
            if count > 0:
                conn.execute(text("UPDATE donations SET amount_usd = amount WHERE amount_usd IS NULL"))
                conn.commit()
                print(f"✅ Migrated {count} rows: donations.amount -> amount_usd")
        
        # Add transaction_id
        add_column_if_missing(conn, "donations", "transaction_id", "VARCHAR(255)")
        
        # Migrate payment_intent_id to transaction_id if needed
        if column_exists(conn, "donations", "payment_intent_id") and column_exists(conn, "donations", "transaction_id"):
            result = conn.execute(text("SELECT COUNT(*) FROM donations WHERE transaction_id IS NULL AND payment_intent_id IS NOT NULL"))
            count = result.scalar()
            if count > 0:
                conn.execute(text("UPDATE donations SET transaction_id = payment_intent_id WHERE transaction_id IS NULL"))
                conn.commit()
                print(f"✅ Migrated {count} rows: donations.payment_intent_id -> transaction_id")
        
        # ===================================================================
        # IMPACT_VERIFICATIONS TABLE
        # ===================================================================
        print("\n🔍 IMPACT_VERIFICATIONS TABLE")
        print("─" * 64)
        
        # Change id to UUID if it's not already
        result = conn.execute(text("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'impact_verifications' AND column_name = 'id'
        """))
        id_type = result.fetchone()
        if id_type:
            print(f"ℹ️  impact_verifications.id type: {id_type[0]}")
        
        # Add all impact verification columns
        add_column_if_missing(conn, "impact_verifications", "field_agent_id", "VARCHAR(50)")
        add_column_if_missing(conn, "impact_verifications", "verification_date", "TIMESTAMP")
        add_column_if_missing(conn, "impact_verifications", "agent_notes", "TEXT")
        add_column_if_missing(conn, "impact_verifications", "testimonials", "TEXT")
        add_column_if_missing(conn, "impact_verifications", "photos", "JSON")
        add_column_if_missing(conn, "impact_verifications", "gps_latitude", "FLOAT")
        add_column_if_missing(conn, "impact_verifications", "gps_longitude", "FLOAT")
        add_column_if_missing(conn, "impact_verifications", "trust_score", "FLOAT DEFAULT 0")
        add_column_if_missing(conn, "impact_verifications", "status", "VARCHAR(20) DEFAULT 'pending'")
        add_column_if_missing(conn, "impact_verifications", "agent_payout_amount_usd", "FLOAT")
        add_column_if_missing(conn, "impact_verifications", "agent_payout_status", "VARCHAR(20)")
        add_column_if_missing(conn, "impact_verifications", "agent_payout_transaction_id", "VARCHAR(255)")
        add_column_if_missing(conn, "impact_verifications", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_missing(conn, "impact_verifications", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # ===================================================================
        # USERS TABLE
        # ===================================================================
        print("\n👥 USERS TABLE")
        print("─" * 64)
        
        # Verify phone_verified_at exists (renamed from is_phone_verified)
        add_column_if_missing(conn, "users", "phone_verified_at", "TIMESTAMP")
        
        # Ensure is_phone_verified also exists for backwards compatibility
        add_column_if_missing(conn, "users", "is_phone_verified", "BOOLEAN DEFAULT FALSE")
        
        # ===================================================================
        # INDEXES
        # ===================================================================
        print("\n📑 INDEXES")
        print("─" * 64)
        
        indexes = [
            ("idx_campaigns_status", "campaigns", "status"),
            ("idx_campaigns_ngo", "campaigns", "ngo_id"),
            ("idx_donations_campaign", "donations", "campaign_id"),
            ("idx_donations_status", "donations", "status"),
            ("idx_verifications_campaign", "impact_verifications", "campaign_id"),
            ("idx_verifications_agent", "impact_verifications", "field_agent_id"),
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                # Check if index exists
                result = conn.execute(text(f"""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE indexname = '{index_name}'
                """))
                if not result.fetchone():
                    conn.execute(text(f"CREATE INDEX {index_name} ON {table_name}({column_name})"))
                    conn.commit()
                    print(f"✅ Index created: {index_name}")
                else:
                    print(f"ℹ️  Index exists: {index_name}")
            except Exception as e:
                conn.rollback()
                print(f"⚠️  Index skipped: {index_name} - {str(e)}")
        
        # ===================================================================
        # CONSTRAINTS
        # ===================================================================
        print("\n🔒 CONSTRAINTS")
        print("─" * 64)
        
        # Trust score check constraint
        try:
            conn.execute(text("""
                ALTER TABLE impact_verifications 
                ADD CONSTRAINT chk_trust_score 
                CHECK (trust_score >= 0 AND trust_score <= 100)
            """))
            conn.commit()
            print("✅ Constraint added: trust_score (0-100)")
        except Exception as e:
            conn.rollback()
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print("ℹ️  Constraint exists: trust_score")
            else:
                print(f"⚠️  Constraint skipped: trust_score - {str(e)}")
    
    print("\n" + "=" * 64)
    print("✅ COMPREHENSIVE SCHEMA MIGRATION COMPLETE")
    print("=" * 64)
    print("\n💡 Next Steps:")
    print("   1. Verify schema: python database/check_schema.py")
    print("   2. Test modules: python tests/test_lab5_modules.py")
    print("   3. Check database: python tests/check_db_state.py")
    print()

if __name__ == "__main__":
    main()
