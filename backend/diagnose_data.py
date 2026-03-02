import os
import sys
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.integration import get_farmer_candidates
from db import get_all_documents

def diagnose():
    print("--- Backend Data Diagnosis ---")
    
    # 1. Test raw Firestore retrieval
    print("\n1. Testing get_all_documents('farmer_profiles')...")
    raw_farmers = get_all_documents("farmer_profiles")
    print(f"Raw farmers found in DB: {len(raw_farmers)}")
    if raw_farmers:
        print(f"Sample ID: {raw_farmers[0].get('id')}")
        print(f"Sample Name: {raw_farmers[0].get('name')}")
    else:
        print("No farmers found in 'farmer_profiles' collection!")

    # 2. Test integration candidate fetching
    print("\n2. Testing get_farmer_candidates()...")
    candidates = get_farmer_candidates()
    print(f"Candidates returned for Marketplace: {len(candidates)}")
    
    if candidates:
        # Check for expected fields
        sample = candidates[0]
        print(f"🧪 Sample structure: {json.dumps(list(sample.keys()), indent=2)}")
        
        # Check for estimation data
        has_est = "latest_estimation" in sample
        print(f"🎯 Has Carbon Estimation: {has_est}")
        
    print("\n--- Diagnosis Complete ---")

if __name__ == "__main__":
    diagnose()
