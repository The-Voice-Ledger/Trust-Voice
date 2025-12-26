#!/usr/bin/env python3
"""
Run database migration for impact verification fields.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.db import engine

def run_migration():
    """Execute the impact verification migration"""
    
    migration_file = Path(__file__).parent / "migrations" / "add_impact_verification_fields.sql"
    
    print(f"🔄 Running migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        with engine.begin() as conn:
            # Split and execute each statement
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute(text(statement))
                        print(f"✅ Executed statement")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            print(f"⏭️  Skipped (already exists)")
                        else:
                            print(f"⚠️  Warning: {str(e)}")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
