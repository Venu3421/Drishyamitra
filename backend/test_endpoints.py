"""Test /stats/ and /photos/ endpoints with a real JWT token to get the actual error."""
import sys, os, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.auth_utils import create_access_token
from datetime import timedelta

# Create a token for the test user
token = create_access_token({"sub": "d@ex.com"}, expires_delta=timedelta(minutes=30))
headers = {"Authorization": f"Bearer {token}"}

BASE = "http://localhost:8000"

print("=== Testing /stats/ ===")
r = requests.get(f"{BASE}/stats/", headers=headers)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:2000]}")

print("\n=== Testing /photos/ ===")
r2 = requests.get(f"{BASE}/photos/?user_id=4", headers=headers)
print(f"Status: {r2.status_code}")
print(f"Body: {r2.text[:2000]}")
