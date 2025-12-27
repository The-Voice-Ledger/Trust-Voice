#!/usr/bin/env python3
"""
Migration: Add Individual Campaign Support
Date: 2025-12-27
Description: Make campaigns support both NGO and individual creators

Changes:
1. Make ngo_id nullable (was NOT NULL)
2. Add creator_user_id for individual campaigns
3. Add index on creator_user_id for performance
4. Add check constraint to ensure XOR (exactly one owner)
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")


def run_migration():
    """Apply the individual campaigns migration"""
    engine = create_engine(DATABASE_URL)
    
    print("🔧 Starting migration: Individual Campaigns Support")
    print(f"📊 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    print()
    
    with engine.begin() as conn:
        try:
            # Step 1: Make ngo_id nullable
            print("Step 1/5: Making ngo_id nullable...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ALTER COLUMN ngo_id DROP NOT NULL
            """))
            print("✅ ngo_id is now nullable")
            
            # Step 2: Add creator_user_id column
            print("\nStep 2/5: Adding creator_user_id column...")
            conn.execute(text("""
                ALTER TABLE campaigns 
                ADD COLUMN creator_user_id INTEGER REFERENCES users(id)
            """))
            print("✅ creator_user_id column added")
            
            # Step 3: Add index for performance
            print("\nStep 3/5: Creating index on creator_user_id...")
            conn.execute(text("""
                CREATE INDEX idx_campaigns_creator ON campaigns(creator_user_id)
            """))
            print("✅ Index created")
            
            # Step 4: Add check constraint (XOR validation)
            print("\nStep 4/5: Adding XOR constraint...")
            conn.execute(text("""
                ALTER TABLE campaigns
                ADD CONSTRAINT campaigns_owner_xor 
                CHECK (
                    (ngo_id IS NOT NULL AND creator_user_id IS NULL) OR
                    (ngo_id IS NULL AND creator_user_id IS NOT NULL)
                )
            """))
            print("✅ XOR constraint added (ensures exactly one owner)")
            
            # Step 5: Add documentation comments
            print("\nStep 5/5: Adding documentation...")
            conn.execute(text("""
                COMMENT ON COLUMN campaigns.ngo_id IS 'NGO organization owner (for institutional campaigns)'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN campaigns.creator_user_id IS 'Individual user owner (for grassroots campaigns)'
            """))
            conn.execute(text("""
                COMMENT ON CONSTRAINT campaigns_owner_xor ON campaigns IS 'Ensures exactly one owner type (NGO XOR Individual)'
            """))
            print("✅ Documentation added")
            
            print("\n" + "="*60)
            print("✅ Migration completed successfully!")
            print("="*60)
            print("\n📝 Summary:")
            print("   - NGO campaigns: Set ngo_id, leave creator_user_id NULL")
            print("   - Individual campaigns: Set creator_user_id, leave ngo_id NULL")
            print("   - Voice command 'create campaign' now works for both types")
            print()
            
        except SQLAlchemyError as e:
            print(f"\n❌ Migration failed: {e}")
            raise


def verify_migration():
    """Verify the migration was applied correctly"""
    engine = create_engine(DATABASE_URL)
    
    print("\n🔍 Verifying migration...")
    
    with engine.begin() as conn:
        # Check if creator_user_id column exists
        result = conn.execute(text("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'campaigns'
            AND column_name IN ('ngo_id', 'creator_user_id')
            ORDER BY column_name
        """))
        
        columns = result.fetchall()
        print(f"\n📊 Campaign ownership columns:")
        for col in columns:
            print(f"   - {col[0]}: {col[2]} (nullable: {col[1]})")
        
        # Check if constraint exists
        result = conn.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'campaigns'
            AND constraint_name = 'campaigns_owner_xor'
        """))
        
        if result.fetchone():
            print(f"\n✅ XOR constraint verified")
        else:
            print(f"\n⚠️  XOR constraint not found")
        
        # Check if index exists
        result = conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'campaigns'
            AND indexname = 'idx_campaigns_creator'
        """))
        
        if result.fetchone():
            print(f"✅ Index verified")
        else:
            print(f"⚠️  Index not found")


if __name__ == "__main__":
    try:
        run_migration()
        verify_migration()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
