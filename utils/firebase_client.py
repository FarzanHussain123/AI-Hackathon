# utils/firebase_client.py
import os
import firebase_admin
from firebase_admin import credentials, firestore

initialized = False
db = None

def init_firebase(key_path=None):
    global initialized, db
    if initialized:
        return db
    if not key_path:
        key_path = os.getenv("FIREBASE_KEY_PATH")
    if key_path and os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        initialized = True
        return db
    else:
        # fallback: no firebase - returns None (caller should handle)
        print("Firebase key not found. Firestore will be disabled (mock mode).")
        return None

def save_trip_firestore(data):
    """
    data: dict to save
    returns: document id or None
    """
    db = init_firebase()
    if not db:
        return None
    doc_ref = db.collection("trips").document()
    doc_ref.set(data)
    return doc_ref.id

def get_trip_firestore(trip_id):
    db = init_firebase()
    if not db:
        return None
    doc = db.collection("trips").document(trip_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()
