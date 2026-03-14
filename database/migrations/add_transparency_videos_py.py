"""
Migration: Add Transparency Videos Table

Run with: python -m database.migrations.add_transparency_videos_py

Creates the transparency_videos table for the three-act
video transparency framework if it doesn't already exist.
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db import engine
from database.models import Base, TransparencyVideo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Create transparency_videos table using SQLAlchemy model."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    existing = inspector.get_table_names()

    if "transparency_videos" in existing:
        logger.info("✅ Table 'transparency_videos' already exists — skipping.")
        return

    logger.info("Creating 'transparency_videos' table...")
    TransparencyVideo.__table__.create(engine, checkfirst=True)
    logger.info("✅ Table 'transparency_videos' created successfully.")


if __name__ == "__main__":
    run_migration()
