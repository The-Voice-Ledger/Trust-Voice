#!/usr/bin/env python3
"""
Migration: Expand NGO Organization model
Date: 2026-03-13
Description: Add verification, mission, media, and org detail columns to ngo_organizations

Changes:
1. Add verification_status, verified_at columns
2. Add mission_statement, focus_areas, region columns
3. Add organization_type, year_established columns
4. Add logo_url, intro_video_url, intro_video_ipfs_hash columns
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")


COLUMNS_TO_ADD = [
    ("verification_status", "VARCHAR(20) DEFAULT 'PENDING'"),
    ("verified_at", "TIMESTAMP"),
    ("mission_statement", "TEXT"),
    ("focus_areas", "TEXT"),
    ("region", "VARCHAR(200)"),
    ("organization_type", "VARCHAR(100)"),
    ("year_established", "INTEGER"),
    ("logo_url", "VARCHAR(500)"),
    ("intro_video_url", "VARCHAR(500)"),
    ("intro_video_ipfs_hash", "VARCHAR(100)"),
]


def run_migration():
    """Apply the NGO expansion migration"""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        # Check which columns already exist
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'ngo_organizations'
        """))
        existing = {row[0] for row in result}

        added = []
        skipped = []

        for col_name, col_type in COLUMNS_TO_ADD:
            if col_name in existing:
                skipped.append(col_name)
            else:
                conn.execute(text(
                    f"ALTER TABLE ngo_organizations ADD COLUMN {col_name} {col_type}"
                ))
                added.append(col_name)

        # For existing NGOs that don't have verification_status set,
        # mark them as VERIFIED (they were already approved before this migration)
        if "verification_status" in added:
            conn.execute(text("""
                UPDATE ngo_organizations
                SET verification_status = 'VERIFIED', verified_at = NOW()
                WHERE verification_status IS NULL OR verification_status = 'PENDING'
            """))
            print("  → Marked all existing NGOs as VERIFIED (grandfathered)")

    print(f"\n✅ Migration complete!")
    print(f"   Added columns: {added or 'none (all existed)'}")
    print(f"   Skipped (already exist): {skipped or 'none'}")


def rollback():
    """Remove the added columns (destructive!)"""
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        for col_name, _ in COLUMNS_TO_ADD:
            try:
                conn.execute(text(
                    f"ALTER TABLE ngo_organizations DROP COLUMN IF EXISTS {col_name}"
                ))
            except SQLAlchemyError:
                pass
    print("✅ Rollback complete — columns removed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        run_migration()
