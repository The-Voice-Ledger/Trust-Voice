import os
from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import Campaign

db = SessionLocal()
campaigns = db.query(Campaign).limit(5).all()

print("Available campaigns:")
for c in campaigns:
    print(f"  {c.id} - {c.title} - {c.category}")

db.close()
