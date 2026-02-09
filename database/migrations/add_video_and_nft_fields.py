"""
Database Migration: Add Transparency Video and NFT Tax Receipt Fields

This migration adds:
1. Campaign transparency video fields (IPFS-based)
2. Donation NFT tax receipt fields (blockchain-based)

Run: python database/migrations/add_video_and_nft_fields.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment")

engine = create_engine(DATABASE_URL)


def add_campaign_video_fields():
    """Add transparency video fields to campaigns table."""
    logger.info("Adding transparency video fields to campaigns table...")
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='campaigns' AND column_name='video_ipfs_hash'
        """))
        
        if result.fetchone():
            logger.info("✅ Video fields already exist in campaigns table")
            return
        
        # Add video fields
        conn.execute(text("""
            ALTER TABLE campaigns
            ADD COLUMN IF NOT EXISTS video_ipfs_hash VARCHAR(100),
            ADD COLUMN IF NOT EXISTS video_ipfs_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS video_uploaded_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS video_duration_seconds INTEGER,
            ADD COLUMN IF NOT EXISTS video_thumbnail_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS video_file_size_bytes INTEGER
        """))
        
        conn.commit()
        logger.info("✅ Added transparency video fields to campaigns table")


def add_donation_nft_fields():
    """Add NFT tax receipt fields to donations table."""
    logger.info("Adding NFT tax receipt fields to donations table...")
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='donations' AND column_name='receipt_nft_token_id'
        """))
        
        if result.fetchone():
            logger.info("✅ NFT fields already exist in donations table")
            return
        
        # Add NFT receipt fields
        conn.execute(text("""
            ALTER TABLE donations
            ADD COLUMN IF NOT EXISTS receipt_nft_token_id INTEGER,
            ADD COLUMN IF NOT EXISTS receipt_nft_contract VARCHAR(42),
            ADD COLUMN IF NOT EXISTS receipt_nft_network VARCHAR(20),
            ADD COLUMN IF NOT EXISTS receipt_nft_tx_hash VARCHAR(66),
            ADD COLUMN IF NOT EXISTS receipt_metadata_ipfs VARCHAR(100),
            ADD COLUMN IF NOT EXISTS receipt_minted_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS donor_tax_id VARCHAR(50),
            ADD COLUMN IF NOT EXISTS donor_full_legal_name VARCHAR(200),
            ADD COLUMN IF NOT EXISTS donor_wallet_address VARCHAR(42)
        """))
        
        conn.commit()
        logger.info("✅ Added NFT tax receipt fields to donations table")


def create_indexes():
    """Create indexes for better query performance."""
    logger.info("Creating indexes for new fields...")
    
    with engine.connect() as conn:
        # Index for finding campaigns with videos
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_campaigns_video 
            ON campaigns(video_ipfs_hash) 
            WHERE video_ipfs_hash IS NOT NULL
        """))
        
        # Index for finding donations with NFT receipts
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_donations_nft_token 
            ON donations(receipt_nft_token_id) 
            WHERE receipt_nft_token_id IS NOT NULL
        """))
        
        # Index for donor wallet lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_donations_wallet 
            ON donations(donor_wallet_address) 
            WHERE donor_wallet_address IS NOT NULL
        """))
        
        # Index for network-based queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_donations_nft_network 
            ON donations(receipt_nft_network)
        """))
        
        conn.commit()
        logger.info("✅ Created indexes for new fields")


def verify_migration():
    """Verify that all fields were added successfully."""
    logger.info("\nVerifying migration...")
    
    with engine.connect() as conn:
        # Check campaigns table
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='campaigns' 
            AND column_name LIKE 'video_%'
            ORDER BY column_name
        """))
        
        campaign_fields = result.fetchall()
        logger.info(f"✅ Campaign video fields: {len(campaign_fields)}")
        for field in campaign_fields:
            logger.info(f"   - {field[0]}: {field[1]}")
        
        # Check donations table
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='donations' 
            AND (column_name LIKE 'receipt_%' OR column_name LIKE 'donor_%')
            ORDER BY column_name
        """))
        
        donation_fields = result.fetchall()
        logger.info(f"✅ Donation NFT fields: {len(donation_fields)}")
        for field in donation_fields:
            logger.info(f"   - {field[0]}: {field[1]}")


def rollback():
    """Rollback migration (remove added fields)."""
    logger.warning("⚠️  Rolling back migration...")
    
    with engine.connect() as conn:
        # Remove campaign video fields
        conn.execute(text("""
            ALTER TABLE campaigns
            DROP COLUMN IF EXISTS video_ipfs_hash,
            DROP COLUMN IF EXISTS video_ipfs_url,
            DROP COLUMN IF EXISTS video_uploaded_at,
            DROP COLUMN IF EXISTS video_duration_seconds,
            DROP COLUMN IF EXISTS video_thumbnail_url,
            DROP COLUMN IF EXISTS video_file_size_bytes
        """))
        
        # Remove donation NFT fields
        conn.execute(text("""
            ALTER TABLE donations
            DROP COLUMN IF EXISTS receipt_nft_token_id,
            DROP COLUMN IF EXISTS receipt_nft_contract,
            DROP COLUMN IF EXISTS receipt_nft_network,
            DROP COLUMN IF EXISTS receipt_nft_tx_hash,
            DROP COLUMN IF EXISTS receipt_metadata_ipfs,
            DROP COLUMN IF EXISTS receipt_minted_at,
            DROP COLUMN IF EXISTS donor_tax_id,
            DROP COLUMN IF EXISTS donor_full_legal_name,
            DROP COLUMN IF EXISTS donor_wallet_address
        """))
        
        # Drop indexes
        conn.execute(text("DROP INDEX IF EXISTS idx_campaigns_video"))
        conn.execute(text("DROP INDEX IF EXISTS idx_donations_nft_token"))
        conn.execute(text("DROP INDEX IF EXISTS idx_donations_wallet"))
        conn.execute(text("DROP INDEX IF EXISTS idx_donations_nft_network"))
        
        conn.commit()
        logger.info("✅ Migration rolled back successfully")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database for video and NFT features")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    try:
        if args.rollback:
            rollback()
        else:
            logger.info("=" * 60)
            logger.info("Database Migration: Video Transparency & NFT Tax Receipts")
            logger.info("=" * 60)
            
            add_campaign_video_fields()
            add_donation_nft_fields()
            create_indexes()
            verify_migration()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ Migration completed successfully!")
            logger.info("=" * 60)
            logger.info("\nNext steps:")
            logger.info("1. Set PINATA_API_KEY and PINATA_API_SECRET in .env")
            logger.info("2. Deploy smart contract and set POLYGON_RECEIPT_CONTRACT")
            logger.info("3. Set BLOCKCHAIN_PRIVATE_KEY for NFT minting")
            logger.info("4. Test video upload endpoint")
            logger.info("5. Test NFT minting with test donation")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
