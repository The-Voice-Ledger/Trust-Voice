"""One-time migration: sync model columns missing from Neon PostgreSQL."""
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, inspect

engine = create_engine(os.environ['DATABASE_URL'])


def get_missing_columns(inspector, table_name, expected_columns):
    """Return columns from expected_columns that don't exist in the DB table."""
    try:
        db_columns = {c['name'] for c in inspector.get_columns(table_name)}
    except Exception:
        return expected_columns  # table doesn't exist at all
    return {name: defn for name, defn in expected_columns.items() if name not in db_columns}


# Define all columns that models.py has but DB might be missing
EXPECTED_ADDITIONS = {
    'campaigns': {
        'video_ipfs_hash': 'VARCHAR(100)',
        'video_ipfs_url': 'VARCHAR(500)',
        'video_uploaded_at': 'TIMESTAMP',
        'video_duration_seconds': 'INTEGER',
        'video_thumbnail_url': 'VARCHAR(500)',
        'video_file_size_bytes': 'INTEGER',
    },
    'donations': {
        'receipt_nft_token_id': 'INTEGER',
        'receipt_nft_contract': 'VARCHAR(42)',
        'receipt_nft_network': 'VARCHAR(20)',
        'receipt_nft_tx_hash': 'VARCHAR(66)',
        'receipt_metadata_ipfs': 'VARCHAR(100)',
        'receipt_minted_at': 'TIMESTAMP',
        'donor_tax_id': 'VARCHAR(50)',
        'donor_full_legal_name': 'VARCHAR(200)',
        'donor_wallet_address': 'VARCHAR(42)',
    },
}

insp = inspect(engine)

with engine.begin() as conn:
    total_added = 0
    for table, columns in EXPECTED_ADDITIONS.items():
        missing = get_missing_columns(insp, table, columns)
        if not missing:
            print(f"  ✅ {table}: all columns present")
            continue
        for col_name, col_type in missing.items():
            stmt = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            conn.execute(text(stmt))
            total_added += 1
        print(f"  ✅ {table}: added {len(missing)} columns — {list(missing.keys())}")

print(f"\n✅ Migration complete: {total_added} columns added")

# Verify
insp2 = inspect(engine)
for table, columns in EXPECTED_ADDITIONS.items():
    missing = get_missing_columns(insp2, table, columns)
    if missing:
        print(f"  ⚠️  {table} still missing: {list(missing.keys())}")
    else:
        print(f"  ✅ {table}: fully synced")
