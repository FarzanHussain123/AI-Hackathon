import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devsecret")

# Import utils
from utils.firebase_client import save_trip_firestore, get_trip_firestore
from utils.maps_client import init_maps, search_places, search_hotels
from utils.vertex_ai_client import init_vertex, call_vertex

# Initialize Google APIs
FIREBASE_KEY = os.getenv("FIREBASE_KEY_PATH")
GCLOUD_KEY = os.getenv("GCLOUD_KEY_PATH")
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION", "us-central1")
VERTEX_MODEL = os.getenv("VERTEX_MODEL")

init_maps(os.getenv("GOOGLE_MAPS_API_KEY"))
init_vertex(project=PROJECT_ID, region=REGION)  # removed key_path


# ---------- Helper ----------
def build_prompt(destination, dates, budget, themes, places=[]):
    """
    Build a structured prompt for Vertex AI
    """
    places_text = ""
    if places:
        places_text = "\nTop POIs:\n" + "\n".join(
            [f"- {p['name']} ({p.get('address','')})" for p in places]
        )
    prompt = f"""
You are an expert travel planner. Produce ONLY valid JSON (no extra text) with schema:
{{
  "destination": "<string>",
  "dates": "<string>",
  "days": <int>,
  "itinerary":[
    {{
      "day": <int>,
      "title": "<string>",
      "items":[{{"time":"<string>","activity":"<string>","location":"<string>","cost":<number>}}],
      "estimated_daily_cost": <number>
    }}
  ],
  "summary":"<short>",
  "estimated_total_cost": <number>,
  "suggested_hotels":[{{"name":"", "price_per_night":0, "rating":0, "address":""}}]
}}

User: destination={destination}, dates={dates}, budget={budget}, themes={themes}
{places_text}

Constraints:
- Keep itinerary practical and optimized for minimal travel times.
- Use the provided POIs when useful.
- Return approximate costs (INR).
- Return JSON only.
"""
    return prompt


# ---------- Routes ----------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.form
    destination = data.get("destination", "").strip()
    dates = data.get("dates", "").strip()
    budget_raw = data.get("budget", "0").replace("₹", "").replace(",", "").strip()
    try:
        budget = int(budget_raw) if budget_raw else 0
    except:
        budget = 0
    themes = data.get("themes", "").strip()

    if not destination or not dates:
        flash("Please add destination and dates", "danger")
        return redirect(url_for("index"))

    # Get POIs and Hotels from Maps
    pois = search_places(destination, themes, limit=5)
    hotels = search_hotels(destination, limit=5)

    # Build prompt & call Vertex AI
    prompt = build_prompt(destination, dates, budget, themes, places=pois)
    raw = call_vertex(prompt, model_name=VERTEX_MODEL)

    # Parse JSON safely
    try:
        obj = json.loads(raw)
    except Exception:
        try:
            s = raw.find("{")
            e = raw.rfind("}") + 1
            obj = json.loads(raw[s:e])
        except Exception:
            obj = {"destination": destination, "dates": dates, "itinerary": []}

    # 🔥 Override suggested_hotels with real data
    obj["suggested_hotels"] = hotels

    # Save to Firestore
    trip_doc = {
        "destination": destination,
        "dates": dates,
        "budget": budget,
        "themes": themes,
        "itinerary": obj,
        "created_at": datetime.utcnow().isoformat(),
        "status": "generated",
    }
    trip_id = save_trip_firestore(trip_doc) or f"local-{int(datetime.utcnow().timestamp())}"

    return redirect(url_for("view_itinerary", trip_id=trip_id))


@app.route("/itinerary/<trip_id>", methods=["GET"])
def view_itinerary(trip_id):
    trip = get_trip_firestore(trip_id)
    if not trip:
        try:
            with open(f"data_{trip_id}.json", "r") as f:
                trip = json.load(f)
        except Exception:
            return "Trip not found", 404

    itinerary = trip.get("itinerary")
    return render_template(
        "itinerary.html", trip={"id": trip_id, "dates": trip.get("dates")}, itinerary=itinerary
    )


@app.route("/book/<trip_id>", methods=["GET", "POST"])
def book(trip_id):
    trip = get_trip_firestore(trip_id)
    if not trip:
        try:
            with open(f"data_{trip_id}.json", "r") as f:
                trip = json.load(f)
        except Exception:
            return "Trip not found", 404

    itinerary = trip.get("itinerary")
    if request.method == "GET":
        return render_template(
            "booking.html",
            trip={
                "id": trip_id,
                "dates": trip.get("dates"),
                "destination": trip.get("destination"),
            },
            itinerary=itinerary,
        )

    # POST: Create booking
    name = request.form.get("name")
    email = request.form.get("email")
    payment_method = request.form.get("payment_method", "upi")

    booking = {
        "booking_id": f"BK-{trip_id}-{int(datetime.utcnow().timestamp())}",
        "trip_id": trip_id,
        "destination": trip.get("destination"),
        "dates": trip.get("dates"),
        "name": name,
        "email": email,
        "amount": itinerary.get("estimated_total_cost", 0),
        "payment_method": payment_method,
        "status": "pending",
    }

    save_trip_firestore({"booking": booking})

    return redirect(url_for("payment_page", booking_id=booking["booking_id"], trip_id=trip_id))


@app.route("/payment/<booking_id>/<trip_id>", methods=["GET"])
def payment_page(booking_id, trip_id):
    trip = get_trip_firestore(trip_id)
    if not trip:
        try:
            with open(f"data_{trip_id}.json", "r") as f:
                trip = json.load(f)
        except Exception:
            return "Trip not found", 404

    itinerary = trip.get("itinerary")
    booking = {
        "booking_id": booking_id,
        "trip_id": trip_id,
        "destination": trip.get("destination"),
        "dates": trip.get("dates"),
        "amount": itinerary.get("estimated_total_cost", 0),
        "payment_method": "upi",
    }
    return render_template("payment.html", booking=booking)


@app.route("/pay", methods=["POST"])
def pay():
    booking_id = request.form.get("booking_id")
    trip_id = request.form.get("trip_id")
    amount = request.form.get("amount")
    method = request.form.get("payment_method", "upi")

    status = "success"  # Mocked success

    return f"""
    <div style='padding:20px; background:#d1fae5; color:#065f46; font-family:sans-serif; border-radius:8px;'>
      ✅ Payment {status.upper()} <br><br>
      Booking ID: {booking_id} <br>
      Trip ID: {trip_id} <br>
      Amount: ₹{amount} <br>
      Method: {method}
    </div>
    """


@app.route("/api/ping", methods=["GET"])
def ping():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
