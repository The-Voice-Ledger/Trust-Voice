"""Get real user for testing"""
import os
from dotenv import load_dotenv
load_dotenv()

from database.db import SessionLocal
from database.models import User

db = SessionLocal()
users = db.query(User).limit(5).all()

print("Available users:")
for u in users:
    print(f"  {u.telegram_user_id} - {u.full_name} - {u.role}")

db.close()
