"""
Migration Script: Add Phase 4D Authentication Fields

Run this script to add authentication fields to existing users table
and create the pending_registrations table.

Usage:
    python database/migrate_phase_4d.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.db import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Apply Phase 4D schema changes."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting Phase 4D migration...")
        
        # Check if columns already exist
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='telegram_user_id'
        """))
        
        if result.fetchone():
            logger.info("✅ Migration already applied!")
            return
        
        logger.info("Adding Telegram identity fields to users table...")
        
        # Add Telegram identity fields
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN telegram_user_id VARCHAR(50) UNIQUE,
            ADD COLUMN telegram_username VARCHAR(100),
            ADD COLUMN telegram_first_name VARCHAR(100),
            ADD COLUMN telegram_last_name VARCHAR(100),
            ADD COLUMN preferred_language VARCHAR(2) DEFAULT 'en'
        """))
        
        # Add approval fields
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN is_approved BOOLEAN DEFAULT TRUE,
            ADD COLUMN approved_at TIMESTAMP,
            ADD COLUMN approved_by_admin_id INTEGER
        """))
        
        logger.info("Adding PIN authentication fields...")
        
        # Add PIN authentication fields
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN pin_hash VARCHAR(255),
            ADD COLUMN pin_set_at TIMESTAMP,
            ADD COLUMN failed_login_attempts INTEGER DEFAULT 0,
            ADD COLUMN locked_until TIMESTAMP,
            ADD COLUMN last_login_at TIMESTAMP
        """))
        
        logger.info("Adding phone verification fields...")
        
        # Add phone verification fields
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN phone_number VARCHAR(20) UNIQUE,
            ADD COLUMN phone_verified_at TIMESTAMP
        """))
        
        logger.info("Creating indexes...")
        
        # Create indexes
        db.execute(text("CREATE INDEX idx_telegram_user_id ON users(telegram_user_id)"))
        db.execute(text("CREATE INDEX idx_users_role ON users(role)"))
        db.execute(text("CREATE INDEX idx_is_approved ON users(is_approved)"))
        db.execute(text("CREATE INDEX idx_phone_number ON users(phone_number)"))
        
        logger.info("Creating pending_registrations table...")
        
        # Create pending_registrations table
        db.execute(text("""
            CREATE TABLE pending_registrations (
                id SERIAL PRIMARY KEY,
                telegram_user_id VARCHAR(50) NOT NULL,
                telegram_username VARCHAR(100),
                telegram_first_name VARCHAR(100),
                telegram_last_name VARCHAR(100),
                
                requested_role VARCHAR(50) NOT NULL,
                
                full_name VARCHAR(200),
                organization_name VARCHAR(200),
                location VARCHAR(200),
                phone_number VARCHAR(20),
                reason TEXT,
                
                verification_experience TEXT,
                coverage_regions TEXT,
                has_gps_phone BOOLEAN,
                
                pin_hash VARCHAR(255),
                
                status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                reviewed_by_admin_id INTEGER,
                reviewed_at TIMESTAMP,
                rejection_reason TEXT,
                
                created_at TIMESTAMP DEFAULT NOW(),
                
                FOREIGN KEY (reviewed_by_admin_id) REFERENCES users(id)
            )
        """))
        
        # Create indexes for pending_registrations
        db.execute(text("CREATE INDEX idx_pending_status ON pending_registrations(status)"))
        db.execute(text("CREATE INDEX idx_pending_telegram_user ON pending_registrations(telegram_user_id)"))
        
        # Make email nullable (for Telegram users)
        db.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
        db.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
        
        db.commit()
        
        logger.info("✅ Phase 4D migration completed successfully!")
        logger.info("\nNew fields added to users table:")
        logger.info("  - telegram_user_id, telegram_username, telegram_first_name, telegram_last_name")
        logger.info("  - is_approved, approved_at, approved_by_admin_id")
        logger.info("  - pin_hash, pin_set_at, failed_login_attempts, locked_until, last_login_at")
        logger.info("  - phone_number, phone_verified_at")
        logger.info("\nNew table created:")
        logger.info("  - pending_registrations")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4D Migration: Authentication & Registration")
    print("=" * 60)
    print()
    
    try:
        run_migration()
        print()
        print("=" * 60)
        print("Migration completed successfully! ✅")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Migration failed: {e}")
        print("=" * 60)
        sys.exit(1)
