"""
Database connection utilities.

Provides:
- Database engine creation
- Session management with context manager
- Helper functions for common queries
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Generator
import logging

from database.models import Base, Donor, Campaign, NGOOrganization

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

# Create engine
# pool_pre_ping=True: Check connection health before using
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Set to True to see SQL queries (debugging)
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Benefits:
    - Automatic commit on success
    - Automatic rollback on exception
    - Ensures connection is closed
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def create_tables():
    """
    Create all tables in database.
    
    WARNING: Only use in development!
    Production should use Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def drop_tables():
    """
    Drop all tables in database.
    
    WARNING: DESTRUCTIVE! Only use in testing.
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


# ============================================
# Helper Functions for Common Queries
# ============================================

def get_donor_by_phone(phone: str) -> Optional[Donor]:
    """Get donor by phone number."""
    with get_db() as db:
        return db.query(Donor).filter_by(phone_number=phone).first()


def get_donor_by_telegram_id(telegram_id: str) -> Optional[Donor]:
    """Get donor by Telegram user ID."""
    with get_db() as db:
        return db.query(Donor).filter_by(telegram_user_id=telegram_id).first()


def get_donor_by_whatsapp(whatsapp_number: str) -> Optional[Donor]:
    """Get donor by WhatsApp number."""
    with get_db() as db:
        return db.query(Donor).filter_by(whatsapp_number=whatsapp_number).first()


def get_active_campaigns():
    """Get all active campaigns."""
    with get_db() as db:
        return db.query(Campaign).filter_by(status="active").all()


def get_campaign_by_id(campaign_id: int) -> Optional[Campaign]:
    """Get campaign by ID."""
    with get_db() as db:
        return db.query(Campaign).filter_by(id=campaign_id).first()
