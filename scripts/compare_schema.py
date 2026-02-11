"""
Compare SQLAlchemy models with actual Neon PostgreSQL database schema.
Reports all columns defined in models.py that are MISSING from the DB.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, inspect
from database.models import Base

def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in environment")
        sys.exit(1)

    # Fix for newer SQLAlchemy: postgres:// -> postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to: {database_url[:40]}...")
    engine = create_engine(database_url)
    inspector = inspect(engine)

    # Get all tables defined in models
    model_tables = {}
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        table = cls.__table__
        table_name = table.name
        columns = {}
        for col in table.columns:
            col_type = str(col.type)
            columns[col.name] = col_type
        model_tables[table_name] = columns

    # Get actual DB tables
    db_tables = inspector.get_table_names()

    print(f"\n{'='*70}")
    print(f"SCHEMA COMPARISON: SQLAlchemy Models vs Neon PostgreSQL")
    print(f"{'='*70}")
    print(f"\nModel tables: {sorted(model_tables.keys())}")
    print(f"DB tables:    {sorted(db_tables)}")

    # Find tables in model but not in DB
    missing_tables = set(model_tables.keys()) - set(db_tables)
    if missing_tables:
        print(f"\n⚠️  TABLES IN MODEL BUT NOT IN DB: {sorted(missing_tables)}")

    extra_tables = set(db_tables) - set(model_tables.keys())
    if extra_tables:
        print(f"\nℹ️  TABLES IN DB BUT NOT IN MODEL: {sorted(extra_tables)}")

    # Compare columns for each table
    print(f"\n{'='*70}")
    print("MISSING COLUMNS (in model but NOT in database)")
    print(f"{'='*70}")

    any_missing = False
    for table_name in sorted(model_tables.keys()):
        if table_name not in db_tables:
            print(f"\n❌ {table_name}: ENTIRE TABLE MISSING FROM DB")
            for col_name, col_type in sorted(model_tables[table_name].items()):
                print(f"     - {col_name} ({col_type})")
            any_missing = True
            continue

        db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        model_columns = model_tables[table_name]

        missing_cols = set(model_columns.keys()) - db_columns
        if missing_cols:
            any_missing = True
            print(f"\n🔴 {table_name}:")
            for col_name in sorted(missing_cols):
                print(f"     - {col_name} ({model_columns[col_name]})")

        # Also check for extra DB columns not in model
        extra_cols = db_columns - set(model_columns.keys())
        if extra_cols:
            print(f"\n🔵 {table_name} (extra columns in DB, not in model):")
            for col_name in sorted(extra_cols):
                print(f"     + {col_name}")

    if not any_missing:
        print("\n✅ All model columns exist in the database!")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    total_missing = 0
    for table_name in sorted(model_tables.keys()):
        if table_name not in db_tables:
            count = len(model_tables[table_name])
            total_missing += count
            print(f"  {table_name}: ENTIRE TABLE MISSING ({count} columns)")
            continue
        db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        missing = set(model_tables[table_name].keys()) - db_columns
        if missing:
            total_missing += len(missing)
            print(f"  {table_name}: {len(missing)} missing columns")

    if total_missing == 0:
        print("  All columns present! ✅")
    else:
        print(f"\n  TOTAL MISSING COLUMNS: {total_missing}")

    engine.dispose()

if __name__ == "__main__":
    main()
