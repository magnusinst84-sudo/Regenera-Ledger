import os
import sys
import json

# Add backend to path
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
sys.path.append(BACKEND_DIR)

# Set the credentials path explicitly for the script
os.environ["FIREBASE_CREDENTIALS_PATH"] = os.path.join(BACKEND_DIR, "firebase-service-account.json")

from db import get_all_documents, get_documents_by_field

def diagnose():
    try:
        print("--- Farmer Data Investigation ---")
        
        # 1. Get all farmers
        farmers = get_all_documents("farmer_profiles")
        if not farmers:
            print("No farmers found in 'farmer_profiles' collection.")
            return
            
        # Sort by updated_at or created_at descending
        farmers.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
        
        latest_farmer = farmers[0]
        print(f"Latest Farmer ID: {latest_farmer.get('id')}")
        print(f"Name: {latest_farmer.get('name')}")
        print(f"User ID: {latest_farmer.get('user_id')}")
        
        # Print full record safely (handle non-serializable objects if any, though Firestore returns dicts)
        print("\nFull Profile Record:")
        print(json.dumps(latest_farmer, indent=2, default=str))
        
        # 2. Get estimations for this farmer
        estimations = get_documents_by_field("carbon_estimations", "farmer_id", latest_farmer["id"])
        print(f"\nEstimations found for this farmer: {len(estimations)}")
        
        if estimations:
            estimations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            latest_est = estimations[0]
            print("\nLatest Estimation Result JSON:")
            print(json.dumps(latest_est.get("result_json", {}), indent=2, default=str))
        else:
            print("No estimations found for this farmer.")
            
        # 3. Check for specific crash points in FarmerDashboard.jsx
        # acres: d.acres
        # credits_earned: d.credits_earned
        # earnings: d.earnings
        # active_matches: d.active_matches
        
        print("\n--- Summary for Dashboard ---")
        print(f"Acres field present: {'land_size_acres' in latest_farmer}")
        print(f"Land size acres value: {latest_farmer.get('land_size_acres')}")
        print(f"Land size hectares value: {latest_farmer.get('land_size_hectares')}")

    except Exception as e:
        print(f"Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
