# utils/vertex_ai_client.py
import os
import json

USE_VERTEX = False
try:
    # google-cloud-aiplatform provides a higher-level client. We'll attempt to import and init.
    from google.cloud import aiplatform
    from google.oauth2 import service_account
    USE_VERTEX = True
except Exception:
    USE_VERTEX = False

def init_vertex(project=None, region=None, key_path=None):
    if not USE_VERTEX:
        print("google-cloud-aiplatform not available; Vertex AI disabled (mock mode).")
        return None

    project = project or os.getenv("PROJECT_ID")
    region = region or os.getenv("REGION","us-central1")
    key_path = key_path or os.getenv("GCLOUD_KEY_PATH")
    if key_path and os.path.exists(key_path):
        creds = service_account.Credentials.from_service_account_file(key_path)
        aiplatform.init(project=project, location=region, credentials=creds)
    else:
        aiplatform.init(project=project, location=region)
    return aiplatform

def call_vertex(prompt, model_name=None, max_output_tokens=800, temperature=0.3):
    """
    Returns plain text response. If Vertex not available, returns mock JSON-string.
    """
    if not USE_VERTEX:
        return mock_response(prompt)

    model_name = model_name or os.getenv("VERTEX_MODEL", "gemini-1.5-preview")
    client = aiplatform.gapic.PredictionServiceClient()
    # NOTE: The exact usage depends on models and Vertex version.
    # For simplicity and portability, we use aiplatform's TextGenerationModel if available.
    try:
        # Try higher-level generation
        from vertexai.language_models import TextGenerationModel
        TextGenerationModel
        model = TextGenerationModel.from_pretrained(model_name)
        response = model.predict(prompt, temperature=temperature, max_output_tokens=max_output_tokens)
        return response.text
    except Exception:
        # Fallback: attempt low-level call (users might need to adapt)
        # For demo, return mock
        return mock_response(prompt)

def mock_response(prompt):
    """
    Deterministic mock generator — returns JSON string matching expected schema
    """
    base = {
      "destination": "Mock City",
      "dates": "May 15 - May 18",
      "days": 4,
      "itinerary": [],
      "summary": "Mock 4-day trip",
      "estimated_total_cost": 18500,
      "suggested_hotels": [
        {"name":"Mock Palace", "price_per_night":11200, "rating":4.6}
      ]
    }
    for d in range(1,5):
        base["itinerary"].append({
            "day": d,
            "title": f"Day {d} - Highlights",
            "items": [
                {"time":"09:00 AM","activity":"Breakfast","location":"Local Cafe","cost":200},
                {"time":"11:00 AM","activity":"Visit main attraction","location":"Heritage Site","cost":500}
            ],
            "estimated_daily_cost":1000
        })
    return json.dumps(base)
