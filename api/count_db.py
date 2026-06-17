import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import School, Student, User

def count_data():
    db = SessionLocal()
    try:
        schools = db.query(School).count()
        students = db.query(Student).count()
        users = db.query(User).count()
        print(f"Schools: {schools}")
        print(f"Students: {students}")
        print(f"Users: {users}")
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    count_data()
