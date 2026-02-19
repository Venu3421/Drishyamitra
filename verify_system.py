import requests
import sys

BASE_URL = "http://localhost:8000"

def check_health():
    try:
        resp = requests.get(f"{BASE_URL}/")
        if resp.status_code == 200:
            print(f"[PASS] Backend Root: {resp.json()}")
        else:
            print(f"[FAIL] Backend Root: {resp.status_code}")
    except Exception as e:
        print(f"[FAIL] Backend Connection: {e}")
        return False
    return True

def check_stats():
    # Login to get token
    try:
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "test@example.com", 
            "password": "password123" 
        })
        
        # If login fails, try registering first
        if login_resp.status_code != 200:
            print("[INFO] Registering test user...")
            requests.post(f"{BASE_URL}/auth/register", json={
                "email": "test@example.com", 
                "password": "password123",
                "full_name": "Test User"
            })
            login_resp = requests.post(f"{BASE_URL}/auth/login", json={
                "email": "test@example.com", 
                "password": "password123" 
            })

        if login_resp.status_code == 200:
            token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            stats_resp = requests.get(f"{BASE_URL}/stats/", headers=headers)
            if stats_resp.status_code == 200:
                print(f"[PASS] Stats Endpoint: {stats_resp.json()}")
            else:
                print(f"[FAIL] Stats Endpoint: {stats_resp.status_code} - {stats_resp.text}")
        else:
            print(f"[FAIL] Login: {login_resp.status_code} - {login_resp.text}")

    except Exception as e:
        print(f"[FAIL] Auth/Stats Check: {e}")

if __name__ == "__main__":
    if check_health():
        check_stats()
