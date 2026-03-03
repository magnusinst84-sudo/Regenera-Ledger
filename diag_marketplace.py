import os
import sys
import json

# Add backend to path
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
sys.path.append(BACKEND_DIR)

# Set the credentials path explicitly
os.environ["FIREBASE_CREDENTIALS_PATH"] = os.path.join(BACKEND_DIR, "firebase-service-account.json")

from utils.integration import get_farmer_candidates
from db import get_all_documents

def diagnose():
    try:
        print("--- Marketplace Data Diagnosis ---")
        
        # 1. Check raw profiles count
        raw = get_all_documents("farmer_profiles")
        print(f"Total farmer profiles in DB: {len(raw)}")
        
        # 2. Check candidates (the ones the API sees)
        candidates = get_farmer_candidates()
        print(f"Candidates returned by get_farmer_candidates(): {len(candidates)}")
        
        if candidates:
            sample = candidates[0]
            print("\nSample Candidate Structure:")
            print(json.dumps(sample, indent=2, default=str))
            
            # Check for fields Matching.jsx requires:
            # p.category, p.name, p.price_per_ton_usd, p.credits_available, p.durability_years, p.id
            required_fields = ['id', 'name', 'category', 'price_per_ton_usd', 'credits_available', 'durability_years']
            missing = [f for f in required_fields if f not in sample]
            print(f"\nMissing fields for Matching.jsx: {missing}")
        else:
            print("\nWARNING: No candidates returned! Checking why...")
            # If raw exists but candidates doesn't, check integration.py logic
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
