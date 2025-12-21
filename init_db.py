"""
Initialize database tables.

Run this script to create all tables in the database.
"""

from database.db import create_tables, engine
from database.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        create_tables()
        print("\n✅ Tables created successfully!")
        
        # Print table names
        print("\nTables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        raise
