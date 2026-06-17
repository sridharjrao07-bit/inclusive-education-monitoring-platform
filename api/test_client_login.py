from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

# Test form data
res_form = client.post("/auth/login", data={"username": "teacher1", "password": "teacher123"})
print("Form data response:", res_form.status_code, res_form.text)

# Test JSON data (what src/api.js uses)
res_json = client.post("/auth/login", json={"username": "teacher1", "password": "teacher123"})
print("JSON data response:", res_json.status_code, res_json.text)
