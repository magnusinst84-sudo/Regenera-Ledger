import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import create_document

def add_manual_company():
    print("🏢 --- Manual Company Profile Creator --- 🏢")
    
    # ── Basic Info ──
    user_id = input("Enter User ID (from users collection): ").strip()
    company_name = input("Company Name: ").strip()
    
    # ── Stats ──
    esg_score = int(input("Initial ESG Score (0-100): ") or 0)
    reported_tco2 = float(input("Reported Emissions (tCO2e): ") or 0.0)

    # ── Build Data Object ──
    profile_data = {
        "user_id": user_id,
        "company_name": company_name,
        "latest_esg_score": esg_score,
        "reported_emissions": {
            "total_tco2e": reported_tco2,
            "scope_1": reported_tco2 * 0.2, # Simple split for demo
            "scope_2": reported_tco2 * 0.3,
            "scope_3": reported_tco2 * 0.5
        },
        "last_audit_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # ── Save to Firestore ──
    profile_id = create_document("company_profiles", profile_data)
    print(f"\n✅ Success! Created Company Profile ID: {profile_id}")
    print("The Dashboard will now pull live data for this company user.")

if __name__ == "__main__":
    add_manual_company()
