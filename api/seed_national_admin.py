"""
seed_national_admin.py
======================
Run this ONCE to create your personal National Admin account in Supabase.
It will be skipped if the username already exists (safe to re-run).

Usage:
    cd api
    python seed_national_admin.py

Edit the ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD constants below
before running.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import engine, Base, SessionLocal
from models import User
from auth import hash_password

# ─────────────────────────────────────────────────────────
# ✏️  EDIT THESE BEFORE RUNNING
# ─────────────────────────────────────────────────────────
ADMIN_USERNAME = "sridhar_admin"          # Your login username
ADMIN_EMAIL    = "sridhar@edu.gov.in"     # Your email
ADMIN_PASSWORD = "Change_Me_Str0ng!2024"  # Use a strong password!
# ─────────────────────────────────────────────────────────

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if this admin already exists
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if existing:
            print(f"✅ User '{ADMIN_USERNAME}' already exists (role={existing.role}). Nothing to do.")
            return

        existing_email = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing_email:
            print(f"⚠️  Email '{ADMIN_EMAIL}' is already registered. Skipping.")
            return

        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role="national_admin",
            state=None,
            school_id=None,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"✅ National Admin created successfully!")
        print(f"   Username : {ADMIN_USERNAME}")
        print(f"   Email    : {ADMIN_EMAIL}")
        print(f"   Role     : national_admin")
        print()
        print("🔐 Login with these credentials on the platform.")
        print("   Once logged in, use the Admin Panel to create state_admin accounts.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
