import requests
import json
import time

def test_api():
    base_url = "http://localhost:8000"
    
    # 1. Login to get token (if needed, but /api/farmer/all needs company role)
    # We'll use a mock token or try calling it directly if auth is disabled for debug? 
    # No, we need a real token.
    
    print("--- API Responsiveness Test ---")
    start_time = time.time()
    try:
        # We'll just test the health check first to see if the server is alive
        resp = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"Health Check: {resp.status_code} - {resp.json()}")
        print(f"Response time: {time.time() - start_time:.2f}s")
        
        # Now we'll try the farmer endpoint. 
        # Since we don't have a recent user token easily, we'll check if the server HANGS on this route
        # specifically if we hit it without auth (should 401 immediately, NOT hang)
        start_time = time.time()
        print("\nTesting /api/farmer/all (should 401 immediately)...")
        resp = requests.get(f"{base_url}/api/farmer/all", timeout=10)
        print(f"Response: {resp.status_code}")
        print(f"Response time: {time.time() - start_time:.2f}s")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
