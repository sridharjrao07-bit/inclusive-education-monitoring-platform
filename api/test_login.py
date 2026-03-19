from database import SessionLocal
from main import login
from schemas import LoginRequest

db = SessionLocal()
try:
    print("Testing login with teacher1/teacher123...")
    req = LoginRequest(username="teacher1", password="teacher123")
    token = login(req, db)
    print("Login successful! Token:", token["access_token"][:20] + "...")
except Exception as e:
    print("Login failed:", e)
