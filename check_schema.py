from database.db import engine
from sqlalchemy import text

# Check campaigns table
query = text("""
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'campaigns' AND column_name = 'id';
""")

with engine.connect() as conn:
    result = conn.execute(query)
    row = result.fetchone()
    if row:
        print(f'campaigns.id type: {row[1]}')
    else:
        print('campaigns table not found')
    
    # Check users table
    query = text("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'id';
    """)
    result = conn.execute(query)
    row = result.fetchone()
    if row:
        print(f'users.id type: {row[1]}')
    else:
        print('users table not found')
        
    # Check impact_verifications foreign keys
    query = text("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'impact_verifications' 
    AND column_name IN ('campaign_id', 'field_agent_id')
    ORDER BY column_name;
    """)
    result = conn.execute(query)
    print('\nimpact_verifications foreign keys:')
    for row in result:
        print(f'  {row[0]}: {row[1]}')

