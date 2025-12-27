#!/usr/bin/env python3
"""
Migration: Add NGO Registration System
Date: 2025-12-27
Description: Create pending_ngo_registrations table for NGO approval workflow

Changes:
1. Create pending_ngo_registrations table
2. Add indexes for status and telegram_id lookups
3. Add foreign keys to users and ngo_organizations
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
    """Apply the NGO registrations migration"""
    engine = create_engine(DATABASE_URL)
    
    print("🔧 Starting migration: NGO Registration System")
    print(f"📊 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
    print()
    
    with engine.begin() as conn:
        try:
            print("Step 1/3: Creating pending_ngo_registrations table...")
            conn.execute(text("""
                CREATE TABLE pending_ngo_registrations (
                    id SERIAL PRIMARY KEY,
                    
                    -- Submitter info (if via Telegram)
                    submitted_by_telegram_id VARCHAR(50),
                    submitted_by_telegram_username VARCHAR(100),
                    submitted_by_name VARCHAR(200),
                    
                    -- NGO Organization Details
                    organization_name VARCHAR(200) NOT NULL,
                    registration_number VARCHAR(100),
                    organization_type VARCHAR(100),
                    
                    -- Contact Information
                    email VARCHAR(200),
                    phone_number VARCHAR(20),
                    website VARCHAR(500),
                    
                    -- Location
                    country VARCHAR(100),
                    region VARCHAR(200),
                    address TEXT,
                    
                    -- Organization Details
                    mission_statement TEXT,
                    focus_areas TEXT,
                    year_established INTEGER,
                    staff_size VARCHAR(50),
                    
                    -- Verification Documents
                    registration_document_url VARCHAR(500),
                    tax_certificate_url VARCHAR(500),
                    additional_documents TEXT,
                    
                    -- Banking Information
                    bank_name VARCHAR(200),
                    account_number VARCHAR(100),
                    account_name VARCHAR(200),
                    swift_code VARCHAR(50),
                    
                    -- Admin Review
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    reviewed_by_admin_id INTEGER REFERENCES users(id),
                    reviewed_at TIMESTAMP,
                    rejection_reason TEXT,
                    admin_notes TEXT,
                    
                    -- Created NGO (if approved)
                    ngo_id INTEGER REFERENCES ngo_organizations(id),
                    
                    -- Timestamps
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
            print("✅ Table created")
            
            print("\nStep 2/3: Creating indexes...")
            conn.execute(text("""
                CREATE INDEX idx_pending_ngo_status ON pending_ngo_registrations(status)
            """))
            conn.execute(text("""
                CREATE INDEX idx_pending_ngo_telegram ON pending_ngo_registrations(submitted_by_telegram_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_pending_ngo_created ON pending_ngo_registrations(created_at DESC)
            """))
            print("✅ Indexes created")
            
            print("\nStep 3/3: Adding documentation...")
            conn.execute(text("""
                COMMENT ON TABLE pending_ngo_registrations IS 'NGO registration applications awaiting admin approval'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN pending_ngo_registrations.status IS 'PENDING, APPROVED, REJECTED, or NEEDS_INFO'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN pending_ngo_registrations.ngo_id IS 'Links to created NGO record after approval'
            """))
            print("✅ Documentation added")
            
            print("\n" + "="*60)
            print("✅ Migration completed successfully!")
            print("="*60)
            print("\n📝 Summary:")
            print("   - NGOs can now submit registration applications")
            print("   - Admins can review and approve/reject via admin panel")
            print("   - Status tracking: PENDING → APPROVED/REJECTED")
            print()
            
        except SQLAlchemyError as e:
            print(f"\n❌ Migration failed: {e}")
            raise


def verify_migration():
    """Verify the migration was applied correctly"""
    engine = create_engine(DATABASE_URL)
    
    print("\n🔍 Verifying migration...")
    
    with engine.begin() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'pending_ngo_registrations'
        """))
        
        if result.fetchone():
            print("\n✅ pending_ngo_registrations table created")
        else:
            print("\n⚠️  Table not found")
            return
        
        # Check columns
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'pending_ngo_registrations'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        print(f"\n📊 Table has {len(columns)} columns")
        
        # Check indexes
        result = conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'pending_ngo_registrations'
        """))
        
        indexes = result.fetchall()
        print(f"✅ {len(indexes)} indexes created")


if __name__ == "__main__":
    try:
        run_migration()
        verify_migration()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
