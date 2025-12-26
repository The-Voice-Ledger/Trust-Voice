#!/usr/bin/env python3
"""
Check database tables and schema integrity.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from database.db import engine

def check_tables():
    """Check all tables and their columns"""
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("🔍 DATABASE SCHEMA CHECK\n")
    print(f"📊 Total tables: {len(tables)}\n")
    print("=" * 80)
    
    # Expected tables
    expected_tables = [
        'users',
        'ngo_organizations',
        'campaigns',
        'donors',
        'donations',
        'impact_verifications',
        'campaign_context',
        'conversation_logs'
    ]
    
    # Check for duplicates or missing tables
    print("\n✅ TABLES STATUS:\n")
    for expected in expected_tables:
        if expected in tables:
            print(f"  ✓ {expected}")
        else:
            print(f"  ✗ {expected} (MISSING)")
    
    # Check for unexpected tables
    unexpected = [t for t in tables if t not in expected_tables and not t.startswith('alembic')]
    if unexpected:
        print(f"\n⚠️  UNEXPECTED TABLES:")
        for t in unexpected:
            print(f"  • {t}")
    
    # Detailed check for critical tables
    critical_tables = {
        'impact_verifications': [
            'id', 'campaign_id', 'field_agent_id', 'verification_date',
            'agent_notes', 'testimonials', 'photos', 'gps_latitude', 'gps_longitude',
            'beneficiary_count', 'trust_score', 'status',
            'agent_payout_amount_usd', 'agent_payout_status', 'agent_payout_transaction_id',
            'created_at', 'updated_at'
        ],
        'campaigns': [
            'id', 'ngo_id', 'title', 'description', 'goal_amount_usd', 'raised_amount_usd',
            'category', 'status', 'verification_count', 'total_trust_score', 'avg_trust_score',
            'created_at', 'updated_at'
        ],
        'users': [
            'id', 'telegram_user_id', 'full_name', 'role', 'phone_number',
            'preferred_language', 'ngo_id'
        ],
        'donations': [
            'id', 'donor_id', 'campaign_id', 'amount_usd', 'currency',
            'status', 'payment_method', 'transaction_id'
        ]
    }
    
    print("\n" + "=" * 80)
    print("\n📋 DETAILED SCHEMA CHECK:\n")
    
    for table_name, expected_cols in critical_tables.items():
        if table_name not in tables:
            print(f"\n❌ {table_name.upper()}: TABLE MISSING")
            continue
            
        print(f"\n✅ {table_name.upper()}:")
        columns = inspector.get_columns(table_name)
        col_names = [col['name'] for col in columns]
        
        print(f"   Columns: {len(col_names)}")
        
        # Check required columns
        missing = [col for col in expected_cols if col not in col_names]
        extra = [col for col in col_names if col not in expected_cols]
        
        if missing:
            print(f"   ⚠️  Missing columns: {', '.join(missing)}")
        
        if extra:
            print(f"   ℹ️  Extra columns: {', '.join(extra[:5])}{'...' if len(extra) > 5 else ''}")
        
        if not missing and not extra:
            print(f"   ✓ All expected columns present")
    
    # Check for primary key constraints
    print("\n" + "=" * 80)
    print("\n🔑 PRIMARY KEYS:\n")
    
    for table_name in critical_tables.keys():
        if table_name in tables:
            pk = inspector.get_pk_constraint(table_name)
            print(f"  {table_name}: {pk.get('constrained_columns', [])}")
    
    # Check for foreign keys
    print("\n🔗 FOREIGN KEYS:\n")
    
    for table_name in critical_tables.keys():
        if table_name in tables:
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"  {table_name}:")
                for fk in fks:
                    print(f"    • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Check for indexes
    print("\n📇 INDEXES:\n")
    
    for table_name in ['impact_verifications', 'campaigns', 'donations']:
        if table_name in tables:
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print(f"  {table_name}: {len(indexes)} indexes")
    
    print("\n" + "=" * 80)
    print("\n✅ SCHEMA CHECK COMPLETE\n")

if __name__ == "__main__":
    try:
        check_tables()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
