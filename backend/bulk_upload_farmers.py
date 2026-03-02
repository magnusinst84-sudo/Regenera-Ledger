import os
import sys
import csv
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import create_document

def bulk_upload_farmers(csv_path):
    print(f"🚜 Starting bulk upload from: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return

    count = 0
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # ── Safe Type Conversion ──
                try: land_size = float(row.get("land_size_acres") or 0.0)
                except: land_size = 0.0
                
                try: lat = float(row.get("latitude") or 0.0)
                except: lat = 0.0
                
                try: lng = float(row.get("longitude") or 0.0)
                except: lng = 0.0

                # ── Build Data Object ──
                profile_data = {
                    "user_id": "seed_user_id", # Or map to actual IDs if available
                    "name": row.get("name", "").strip(),
                    "email": row.get("email", "").strip(),
                    "phone": row.get("phone", "").strip(),
                    "state": row.get("state", "").strip(),
                    "district": row.get("district", "").strip(),
                    "village": row.get("village", "").strip(),
                    "land_size_hectares": land_size * 0.4047,
                    "land_size_acres": land_size,
                    "crops": row.get("crops", "").strip(),
                    "practices": row.get("practices", "").strip(),
                    "crop_type": row.get("crops", "").strip(),
                    "regenerative_practices": row.get("practices", "").strip(),
                    "soil_practices": row.get("soil_type", "Standard"),
                    "irrigation_type": row.get("irrigation_type", "Standard"),
                    "location": {
                        "lat": lat,
                        "lng": lng,
                        "state": row.get("state", "").strip(),
                        "district": row.get("district", "").strip(),
                        "village": row.get("village", "").strip(),
                    },
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "documents": []
                }

                # ── Save to Firestore ──
                create_document("farmer_profiles", profile_data)
                count += 1
                print(f"✅ Uploaded: {profile_data['name']}")

        print(f"\n✨ Bulk upload complete! {count} farmers added to Firestore.")

    except Exception as e:
        print(f"❌ Error during bulk upload: {e}")

if __name__ == "__main__":
    path = os.path.join("..", "demo_tester", "farmer", "sample_farmers.csv")
    bulk_upload_farmers(path)
