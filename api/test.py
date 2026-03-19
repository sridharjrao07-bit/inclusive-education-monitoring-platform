import urllib.request
import urllib.error

req = urllib.request.Request('http://localhost:8000/auth/seed-admin', method='POST')
try:
    response = urllib.request.urlopen(req)
    print(response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode())
except Exception as e:
    print("Other Error:", e)
