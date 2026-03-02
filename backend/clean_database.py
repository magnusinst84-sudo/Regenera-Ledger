import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import db, get_all_documents, delete_document

def clean_collection(collection_name):
    print(f"Cleaning collection: {collection_name}...")
    docs = get_all_documents(collection_name, limit=500)
    count = 0
    for doc in docs:
        delete_document(collection_name, doc["id"])
        count += 1
    print(f"Deleted {count} documents from {collection_name}.")
    return count

def master_cleanup():
    print("--- MASTER DATABASE CLEANUP ---")
    print("This will PERMANENTLY delete all data in the following collections:")
    
    collections = [
        "farmer_profiles",
        "carbon_estimations",
        "company_profiles",
        "analysis_results",
        "esg_reports",
        "matching_results",
        "audit_logs"
    ]
    
    for c in collections:
        print(f" - {c}")
    
    # Auto-confirming as per chat request
    confirm = "DELETE" 
    
    if confirm == "DELETE":
        total = 0
        for c in collections:
            total += clean_collection(c)
        print(f"\nDatabase is now CLEAN. Total documents removed: {total}")
        print("Ready for repopulation.")
    else:
        print("\nCleanup cancelled.")

if __name__ == "__main__":
    master_cleanup()
