import traceback
from database import SessionLocal
from main import seed_admin

db = SessionLocal()
try:
    print("Testing seed_admin...")
    seed_admin(db)
    print("Success")
except Exception as e:
    traceback.print_exc()
