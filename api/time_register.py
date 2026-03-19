import time
import requests
import random
import string

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def run_test():
    url = "http://localhost:8000/auth/register"
    uname = random_string()
    payload = {
        "username": uname,
        "email": f"{uname}@example.com",
        "password": "password123",
        "role": "teacher",
        "new_school": {
            "name": "Perf Test School",
            "district": "Test Dist",
            "state": "TS",
            "school_type": "Urban"
        }
    }
    
    start = time.time()
    try:
        response = requests.post(url, json=payload)
        end = time.time()
        print(f"Status: {response.status_code}")
        print(f"Time taken: {end - start:.2f} seconds")
        print("Response:", response.text[:200])
    except Exception as e:
        end = time.time()
        print(f"Error: {e}")
        print(f"Time before error: {end - start:.2f} seconds")

if __name__ == "__main__":
    run_test()
