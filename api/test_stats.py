from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

res = client.get("/api/stats")
print(res.status_code)
try:
    data = res.json()
    print("Keys:", data.keys())
    print("Total schools:", data.get("total_schools"))
except Exception as e:
    print(res.text)
