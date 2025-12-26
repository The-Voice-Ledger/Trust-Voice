#!/usr/bin/env python3
"""
Check and fix impact_verifications table structure.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from database.db import engine

def check_and_fix_table():
    """Check existing structure and apply necessary changes"""
    
    with engine.begin() as conn:
        # Check if table exists
        inspector = inspect(engine)
        
        if 'impact_verifications' not in inspector.get_table_names():
            print("❌ Table impact_verifications doesn't exist yet")
            print("✅ Will be created by SQLAlchemy on first use")
            return
        
        # Get existing columns
        existing_columns = {col['name']: col for col in inspector.get_columns('impact_verifications')}
        print(f"📋 Existing columns: {list(existing_columns.keys())}\n")
        
        # Needed columns for our handler
        needed_columns = {
            'field_agent_id': 'UUID REFERENCES users(id)',
            'verification_date': 'TIMESTAMP DEFAULT NOW()',
            'agent_notes': 'TEXT',
            'testimonials': 'TEXT',
            'photos': 'JSON',
            'gps_latitude': 'FLOAT',
            'gps_longitude': 'FLOAT',
            'trust_score': 'INTEGER DEFAULT 0',
            'status': 'VARCHAR(20) DEFAULT \'pending\'',
            'agent_payout_amount_usd': 'FLOAT',
            'agent_payout_status': 'VARCHAR(20)',
            'agent_payout_transaction_id': 'VARCHAR(100)',
            'created_at': 'TIMESTAMP DEFAULT NOW()',
            'updated_at': 'TIMESTAMP DEFAULT NOW()'
        }
        
        # Add missing columns
        for col_name, col_type in needed_columns.items():
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE impact_verifications ADD COLUMN {col_name} {col_type}"
                    conn.execute(text(sql))
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠️  Could not add {col_name}: {e}")
        
        # Add campaign verification metrics
        campaign_columns = {
            'verification_count': 'INTEGER DEFAULT 0',
            'total_trust_score': 'FLOAT DEFAULT 0.0',
            'avg_trust_score': 'FLOAT DEFAULT 0.0'
        }
        
        campaign_existing = {col['name']: col for col in inspector.get_columns('campaigns')}
        
        for col_name, col_type in campaign_columns.items():
            if col_name not in campaign_existing:
                try:
                    sql = f"ALTER TABLE campaigns ADD COLUMN {col_name} {col_type}"
                    conn.execute(text(sql))
                    print(f"✅ Added to campaigns: {col_name}")
                except Exception as e:
                    print(f"⚠️  Could not add to campaigns {col_name}: {e}")
        
        print("\n✅ Table structure check complete!")

if __name__ == "__main__":
    check_and_fix_table()
