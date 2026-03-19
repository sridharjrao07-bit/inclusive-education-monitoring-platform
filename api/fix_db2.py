import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import School, generate_school_code

def upgrade():
    load_dotenv()
    db = SessionLocal()
    try:
        print("Adding 'registration_code' column to schools table...")
        # Add column (Postgres specific syntax, SQLite compatible usually without constraints)
        db.execute(text("ALTER TABLE schools ADD COLUMN IF NOT EXISTS registration_code VARCHAR;"))
        db.commit()
        print("Column added. Populating existing schools...")
        
        schools = db.query(School).all()
        for s in schools:
            if not s.registration_code:
                s.registration_code = generate_school_code()
        db.commit()
        
        # Add Unique constraint
        try:
            db.execute(text("ALTER TABLE schools ADD CONSTRAINT uq_registration_code UNIQUE (registration_code);"))
            db.commit()
        except Exception as e:
            print("Constraint might already exist or not supported this way:", e)
            db.rollback()
            
        print("Success! Registration codes populated.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    upgrade()
