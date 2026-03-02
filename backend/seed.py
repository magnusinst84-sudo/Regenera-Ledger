"""
Seed Script — Populate Firestore with demo data for testing.
Run with: python seed.py
"""

import os
import sys
from datetime import datetime, timezone

# Add parent dir to path so we can import db
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from db import create_document
import bcrypt


def seed():
    print("Seeding Firestore with demo data...\n")

    # ── Demo Company User ──
    company_pw = bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()).decode()
    company_id = create_document("users", {
        "email": "company@demo.com",
        "password_hash": company_pw,
        "name": "GreenTech Industries",
        "role": "company",
        "company_name": "GreenTech Industries",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    print(f"Company user created: company@demo.com (id: {company_id})")

    # ── Demo Farmer Users ──
    farmer_pw = bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()).decode()
    
    farmers = [
        {
            "email": "farmer1@demo.com",
            "name": "Ravi Kumar",
            "profile": {
                "land_size_hectares": 45.0,
                "crop_type": "Rice",
                "soil_practices": "No-till farming, cover crops",
                "irrigation_type": "Drip irrigation",
                "regenerative_practices": "Composting, crop rotation, agroforestry",
                "location": {"lat": 28.6139, "lng": 77.2090, "name": "Delhi, India"},
            },
        },
        {
            "email": "farmer2@demo.com",
            "name": "Anita Sharma",
            "profile": {
                "land_size_hectares": 120.0,
                "crop_type": "Wheat & Mustard",
                "soil_practices": "Mulching, organic amendments",
                "irrigation_type": "Sprinkler system",
                "regenerative_practices": "Biochar application, integrated pest management",
                "location": {"lat": 26.9124, "lng": 75.7873, "name": "Jaipur, India"},
            },
        },
        {
            "email": "farmer3@demo.com",
            "name": "Suresh Patel",
            "profile": {
                "land_size_hectares": 80.0,
                "crop_type": "Cotton",
                "soil_practices": "Conservation tillage, green manure",
                "irrigation_type": "Flood irrigation",
                "regenerative_practices": "Vermicomposting, boundary plantations",
                "location": {"lat": 23.0225, "lng": 72.5714, "name": "Ahmedabad, India"},
            },
        },
    ]

    for f in farmers:
        farmer_id = create_document("users", {
            "email": f["email"],
            "password_hash": farmer_pw,
            "name": f["name"],
            "role": "farmer",
            "company_name": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        
        profile_data = f["profile"].copy()
        profile_data["user_id"] = farmer_id
        profile_data["created_at"] = datetime.now(timezone.utc).isoformat()
        profile_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        profile_id = create_document("farmer_profiles", profile_data)
        print(f"Farmer created: {f['email']} (id: {farmer_id}, profile: {profile_id})")

    # ── Sample Audit Logs ──
    create_document("audit_logs", {
        "user_id": company_id,
        "action": "user_registered",
        "entity_type": "user",
        "entity_id": company_id,
        "details": {"email": "company@demo.com", "role": "company"},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    print("\nSeed complete!")
    print("\nDemo credentials:")
    print("   Company: company@demo.com / demo123")
    print("   Farmer:  farmer1@demo.com / demo123")
    print("   Farmer:  farmer2@demo.com / demo123")
    print("   Farmer:  farmer3@demo.com / demo123")


if __name__ == "__main__":
    seed()
