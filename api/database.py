"""
Database configuration — supports SQLite (dev) and PostgreSQL (production).

Reads DATABASE_URL from environment / .env file.
If DATABASE_URL is not set, falls back to a local SQLite file.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load .env file (no-op if it doesn't exist)
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use env var if available; otherwise fall back to local SQLite
if os.getenv("VERCEL") == "1":
    # On Vercel, the filesystem is read-only except for /tmp
    default_url = "sqlite:////tmp/education.db"
else:
    default_url = f"sqlite:///{os.path.join(BASE_DIR, 'education.db')}"

DATABASE_URL = os.getenv("DATABASE_URL", default_url)

# SQLite requires check_same_thread=False; PostgreSQL does not
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
