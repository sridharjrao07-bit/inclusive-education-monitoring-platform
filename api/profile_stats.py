import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from crud import get_dashboard_stats

def profile_stats():
    db = SessionLocal()
    try:
        print("Starting stats generation...")
        t0 = time.time()
        res = get_dashboard_stats(db)
        t1 = time.time()
        print(f"Stats generated in {t1 - t0:.2f} seconds.")
        print(res.keys())
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    profile_stats()
