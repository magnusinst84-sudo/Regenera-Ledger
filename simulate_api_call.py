import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta, timezone
from jose import jwt

# Add backend to path
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
sys.path.append(BACKEND_DIR)

# Load env for JWT_SECRET
from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-secret-CHANGE-BEFORE-DEPLOY")
JWT_ALGORITHM = "HS256"

def create_token(user_id, role, email):
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def test_actual_api():
    # User info found earlier
    user_id = "0symG0UYPnpXxL38MvIk"
    email = "tanmaynair07@gmail.com"
    role = "company"
    
    token = create_token(user_id, role, email)
    print(f"Generated Token for {email}")
    
    base_url = "http://localhost:8000"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Calling {base_url}/api/farmer/all ...")
    start_time = time.time()
    try:
        # Note: The server must be running! 
        # If it's not running, we'll try to import the router and call the function directly.
        resp = requests.get(f"{base_url}/api/farmer/all", headers=headers, timeout=15)
        print(f"Status Code: {resp.status_code}")
        print(f"Response Time: {time.time() - start_time:.2f}s")
        
        if resp.status_code == 200:
            data = resp.json()
            farmers = data.get("farmers", [])
            print(f"Farmers returned: {len(farmers)}")
            if farmers:
                print("First Farmer Sample:")
                print(json.dumps(farmers[0], indent=2))
        else:
            print(f"Error: {resp.text}")
            
    except Exception as e:
        print(f"Network error (is server running?): {e}")
        print("\nAttempting direct function call instead...")
        
        # Set credentials path for Firestore
        os.environ["FIREBASE_CREDENTIALS_PATH"] = os.path.join(BACKEND_DIR, "firebase-service-account.json")
        
        from utils.integration import get_farmer_candidates
        
        start_time = time.time()
        farmers = get_farmer_candidates()
        print(f"Direct call returned {len(farmers)} farmers")
        print(f"Direct call time: {time.time() - start_time:.2f}s")
        
        if farmers:
            print("First Farmer Sample (Direct):")
            print(json.dumps(farmers[0], indent=2))

if __name__ == "__main__":
    test_actual_api()
