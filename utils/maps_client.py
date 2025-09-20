# utils/maps_client.py
import os
import googlemaps
from datetime import datetime

gmaps = None

def init_maps(key=None):
    global gmaps
    api_key = key or os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key:
        gmaps = googlemaps.Client(key=api_key)
        return gmaps
    else:
        print("Google Maps API key not provided. Maps client disabled (mock mode).")
        return None

def search_places(destination, themes, limit=5):
    """
    Returns list of place dicts (mockable)
    """
    if not gmaps:
        # mock: returns fixed sample places for demo
        return [
            {"name":"Amber Fort","address":"Amber Fort Rd","rating":4.6,"types":["tourist_attraction"]},
            {"name":"City Palace","address":"Old City","rating":4.5,"types":["museum"]},
        ][:limit]

    query = f"{themes} in {destination}" if themes else f"things to do in {destination}"
    places = gmaps.places(query=query)
    results = places.get("results", [])[:limit]
    # normalize
    normalized = []
    for r in results:
        normalized.append({
            "name": r.get("name"),
            "address": r.get("vicinity") or r.get("formatted_address"),
            "rating": r.get("rating", 0),
            "types": r.get("types", [])
        })
    return normalized

def get_directions(origin, destination):
    if not gmaps:
        return {"duration": "30 mins", "distance": "5 km", "steps": []}
    now = datetime.now()
    directions = gmaps.directions(origin, destination, mode="driving", departure_time=now)
    if not directions:
        return {"duration": None, "distance": None, "steps": []}
    leg = directions[0]["legs"][0]
    return {"duration": leg.get("duration", {}).get("text"), "distance": leg.get("distance", {}).get("text")}
