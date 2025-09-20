# AI Trip Planner (GCP + Firebase prototype)

## Overview
Flask app integrating:
- Vertex AI (Gemini) for itinerary generation
- Google Maps (Places & Directions) for POIs
- Firebase Firestore for storage

The app includes mock fallbacks so you can run without services and then plug them in.

## Setup

1. Clone repo.

2. Create Python venv and install:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


3. Place credentials:
- Download Firebase Service Account JSON and save to `config/firebase-key.json`
- Download GCP Service Account JSON (with Vertex AI permissions) and save to `config/gcloud-key.json`

4. Edit `.env` (copy from `.env.example`) and set:
SECRET_KEY=...
FIREBASE_KEY_PATH=config/firebase-key.json
GCLOUD_KEY_PATH=config/gcloud-key.json
GOOGLE_MAPS_API_KEY=... # optional
PROJECT_ID=your-gcp-project-id
REGION=us-central1
VERTEX_MODEL=gemini-1.5-preview


5. Enable APIs on GCP:
- Vertex AI API
- Maps Platform (Places API, Directions API)
- Firestore API (for Firebase you likely already enabled)

6. Run:
flask run

or 

python app.py


7. Open `http://localhost:5000` and test.

## Notes
- This code attempts to use Vertex/Maps/Firestore when credentials are present; otherwise it uses mock data so you can demo offline.
- For production: use secure secret management, HTTPS, and real payment gateway integration.

