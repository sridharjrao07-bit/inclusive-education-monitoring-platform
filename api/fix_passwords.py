import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User
from auth import hash_password

def hard_fix_passwords():
    db = SessionLocal()
    
    defaults = {
        "admin": "admin123",
        "state_mp": "state123", 
        "teacher1": "teacher123"
    }
    
    for username, plain_pwd in defaults.items():
        user = db.query(User).filter(User.username == username).first()
        if user:
            print(f"Force updating password for {username}")
            user.hashed_password = hash_password(plain_pwd)
            db.commit()
            
    print("Done checking passwords.")
    db.close()

if __name__ == "__main__":
    load_dotenv()
    hard_fix_passwords()
