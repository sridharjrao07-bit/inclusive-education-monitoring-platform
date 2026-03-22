import requests
res = requests.post("http://localhost:8000/auth/register", json={
    "username": "testteacher1",
    "email": "test@teacher.com",
    "password": "password123",
    "role": "teacher",
    "new_school": {
        "name": "New Test School",
        "district": "Test Dist",
        "state": "Test State",
        "school_type": "Urban"
    }
})
print(res.status_code, res.text)
