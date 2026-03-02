"""
Firebase Database Layer
Initializes Firebase Admin SDK and provides Firestore helpers.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from dotenv import load_dotenv

load_dotenv()

# ── Initialize Firebase Admin SDK ──
_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()


# ════════════════════════════════════════════
# Collection References
# ════════════════════════════════════════════

def get_collection(name: str):
    """Get a Firestore collection reference."""
    return db.collection(name)


# ════════════════════════════════════════════
# Generic CRUD Helpers
# ════════════════════════════════════════════

def create_document(collection: str, data: dict, doc_id: str = None) -> str:
    """
    Create a document in a collection.
    Returns the document ID.
    """
    ref = db.collection(collection)
    if doc_id:
        ref.document(doc_id).set(data)
        return doc_id
    else:
        _, doc_ref = ref.add(data)
        return doc_ref.id


def get_document(collection: str, doc_id: str) -> dict | None:
    """Get a single document by ID. Returns None if not found."""
    doc = db.collection(collection).document(doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def get_documents_by_field(collection: str, field: str, value, order_by: str = None, order_desc: bool = True, limit: int = 50) -> list[dict]:
    """Query documents where field == value."""
    query = db.collection(collection).where(field, "==", value)
    if order_by:
        direction = firestore.Query.DESCENDING if order_desc else firestore.Query.ASCENDING
        query = query.order_by(order_by, direction=direction)
    query = query.limit(limit)
    
    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def update_document(collection: str, doc_id: str, data: dict) -> bool:
    """Update a document. Returns True if successful."""
    doc_ref = db.collection(collection).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    doc_ref.update(data)
    return True


def delete_document(collection: str, doc_id: str) -> bool:
    """Delete a document. Returns True if it existed."""
    doc_ref = db.collection(collection).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    doc_ref.delete()
    return True


def get_all_documents(collection: str, order_by: str = None, order_desc: bool = True, limit: int = 100) -> list[dict]:
    """Get all documents from a collection."""
    query = db.collection(collection)
    if order_by:
        direction = firestore.Query.DESCENDING if order_desc else firestore.Query.ASCENDING
        query = query.order_by(order_by, direction=direction)
    query = query.limit(limit)
    
    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results
