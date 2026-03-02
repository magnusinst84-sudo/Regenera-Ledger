import os
import sys
import json
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import create_document, get_documents_by_field, update_document

def ingest_file(file_path):
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = 0
    # Mock leads to make it feel "populated" with user info
    leads = ["Anita Desai", "Sanjay Gupta", "Priya Nair", "Rahul Sharma", "Vikram Rathore"]
    
    for i, item in enumerate(data):
        # 1. Create Farmer Profile (Seed User)
        user_id = f"managed_user_{item.get('id')}" 
        lead_name = leads[i % len(leads)]
        
        # Parse location
        loc_str = item.get("location", "India")
        # Simple split for lat/lng based on city/state (Mocked coordinates for realism)
        coords = {
            "West Bengal, India": {"lat": 22.0, "lng": 88.5},
            "Tamil Nadu, India": {"lat": 10.0, "lng": 78.5},
            "Andaman & Nicobar, India": {"lat": 11.7, "lng": 92.7},
            "Gujarat, India": {"lat": 23.0, "lng": 72.0},
            "Rajasthan, India": {"lat": 27.0, "lng": 74.0},
            "Maharashtra, India": {"lat": 19.0, "lng": 73.0},
            "Madhya Pradesh, India": {"lat": 23.5, "lng": 77.0},
            "Kerala, India": {"lat": 10.5, "lng": 76.5},
            "Himachal Pradesh, India": {"lat": 31.1, "lng": 77.1},
            "Andhra Pradesh, India": {"lat": 15.9, "lng": 79.7},
            "Odisha, India": {"lat": 20.9, "lng": 85.1}
        }
        c = coords.get(loc_str, {"lat": 20.0, "lng": 78.0})

        farmer_data = {
            "user_id": user_id,
            "project_id": item.get("id"),
            "owner_name": lead_name,
            "email": f"{lead_name.lower().replace(' ', '.')}@carbon-india.org",
            "name": item.get("project_name"),
            "location": {
                "state": loc_str.split(',')[0],
                "country": "India",
                "lat": c["lat"],
                "lng": c["lng"]
            },
            "crop_type": item.get("ui_theme", {}).get("badge_text", "Forestry"), # Categorization
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create/Update profile
        f_id = create_document("farmer_profiles", farmer_data)
        
        # 2. Create Carbon Estimation (The Data shown in Marketplace)
        # We store the rich metadata in result_json
        est_data = {
            "farmer_id": f_id,
            "analysis_type": "managed_teammate_data",
            "result_json": {
                "project_category": item.get("ui_theme", {}).get("badge_text", "Forestry").title().replace('Dac', 'DAC'),
                "sequestration_capacity_tons": item.get("allocation", {}).get("max_available_tons", 0),
                "credibility_score": item.get("financials", {}).get("credibility_score", 0),
                "project_lead": lead_name,
                "contact_email": f"{lead_name.lower().replace(' ', '.')}@carbon-india.org",
                "yearly_credit_potential": {
                    "estimated_revenue_usd_low": item.get("financials", {}).get("price_per_tco2", 0)
                },
                "audit_summary": f"Managed project verified with {item.get('durability_years')}.",
                "co_benefits": item.get("details_section", {}).get("tags", [])
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        create_document("carbon_estimations", est_data)
        count += 1
    
    print(f"Successfully ingested {count} projects from {os.path.basename(file_path)}")

def master_ingest():
    print("--- Teammate Data Ingestion ---")
    
    # Path to farmers filler relative to backend/
    filler_dir = os.path.join("..", "farmers filler")
    
    files = ["Bluecarbon (1).txt", "TechBased.txt", "forestry.txt"]
    
    for filename in files:
        path = os.path.join(filler_dir, filename)
        if os.path.exists(path):
            ingest_file(path)
        else:
            print(f"File not found: {path} (Check if 'farmers filler' exists at {os.path.abspath(filler_dir)})")

if __name__ == "__main__":
    master_ingest()
