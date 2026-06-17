import requests

url = "https://inclusive-education-monitoring-platform.vercel.app/api/stats"
print(f"Testing {url}")
try:
    res = requests.get(url, timeout=20)
    print("Status:", res.status_code)
    print("Response:", res.text[:500])
except Exception as e:
    print("Error:", e)
