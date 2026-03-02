import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import create_document

def add_manual_farmer():
    print("🌿 --- Manual Farmer Profile Creator --- 🌿")
    
    # ── Basic Info ──
    user_id = input("Enter User ID (from users collection): ").strip()
    name = input("Farmer Name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone: ").strip()
    
    # ── Location ──
    state = input("State: ").strip()
    district = input("District: ").strip()
    village = input("Village: ").strip()
    lat = float(input("Latitude (e.g. 30.7): ") or 0.0)
    lng = float(input("Longitude (e.g. 76.7): ") or 0.0)
    
    # ── Land & Crops ──
    acres = float(input("Land Size (Acres): ") or 0.0)
    crops = input("Crops (e.g. Rice, Wheat): ").strip()
    practices = input("Practices (e.g. No-till, Cover Cropping): ").strip()
    soil = input("Soil Type (e.g. Alluvial, Clay): ") or "Standard"
    irrigation = input("Irrigation (e.g. Drip, Rain-fed): ") or "Standard"

    # ── Build Data Object ──
    profile_data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "phone": phone,
        "state": state,
        "district": district,
        "village": village,
        "land_size_hectares": acres * 0.4047,
        "land_size_acres": acres,
        "crops": crops,
        "practices": practices,
        "crop_type": crops,
        "regenerative_practices": practices,
        "soil_practices": soil,
        "irrigation_type": irrigation,
        "location": {
            "lat": lat,
            "lng": lng,
            "state": state,
            "district": district,
            "village": village,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "documents": []
    }

    # ── Save to Firestore ──
    profile_id = create_document("farmer_profiles", profile_data)
    print(f"\n✅ Success! Created profile ID: {profile_id}")
    print("Dashboard and Gemini Marketplace will now show this farmer.")

if __name__ == "__main__":
    add_manual_farmer()
