import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

def test_connection():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url or "supabase" not in db_url:
        print("\nERROR: DATABASE_URL not found in api/.env or not a Supabase URL.")
        return

    # Hide password in logs
    safe_url = db_url
    if "@" in db_url and ":" in db_url:
        parts = db_url.split("@")
        safe_url = "********@" + parts[1]

    print(f"\n[Testing connection to: {safe_url}]")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("\nSUCCESS! The database connection string is 100% correct and working.")
    except Exception as e:
        print("\nAUTHENTICATION FAILED!")
        print(f"\nError details: {str(e)}")

if __name__ == "__main__":
    test_connection()
