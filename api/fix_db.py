import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal

def upgrade():
    load_dotenv()
    db = SessionLocal()
    try:
        print("Adding 'state' column to users table...")
        # Check if column exists first or just catch error
        # PostgreSQL syntax:
        db.execute(text("ALTER TABLE users ADD COLUMN state VARCHAR;"))
        db.commit()
        print("Success! Column 'state' added.")
    except Exception as e:
        print(f"Error (maybe column already exists?): {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    upgrade()
