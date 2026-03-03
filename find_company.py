import os
import sys
import json

# Add backend to path
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
sys.path.append(BACKEND_DIR)

# Set the credentials path
os.environ["FIREBASE_CREDENTIALS_PATH"] = os.path.join(BACKEND_DIR, "firebase-service-account.json")

from db import get_collection

def find_company():
    try:
        users = get_collection("users").where("role", "==", "company").limit(1).stream()
        for doc in users:
            print(f"Found Company User: {doc.to_dict().get('email')}")
            print(f"User ID: {doc.id}")
            return
        print("No company user found!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_company()
