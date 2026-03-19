import traceback
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    print("Hashing admin123...")
    result = pwd_context.hash("admin123")
    print("Hash:", result)
except Exception as e:
    with open("error.txt", "w") as f:
        traceback.print_exc(file=f)
    print("Wrote traceback to error.txt")

try:
    print("Verifying admin123...")
    # hardcoded correctly hashed bcrypt for admin123:
    valid_hash = "$2b$12$Nq/tqXYJ6WqQ6.e/9W.U.e08S21W.U2O2R8f.v.Y3Y./69.p" # Example, maybe invalid length
    # Let's just catch it
    pass
except Exception as e:
    pass
