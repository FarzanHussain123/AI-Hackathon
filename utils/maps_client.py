# utils/maps_client.py
import os
import googlemaps
from datetime import datetime

gmaps = None

def init_maps(key=None):
    """
    Initialize Google Maps client
    """
    global gmaps
    api_key = key or os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key:
        gmaps = googlemaps.Client(key=api_key)
        return gmaps
    else:
        print("⚠️ Google Maps API key not provided. Maps client disabled (mock mode).")
        return None


def search_places(destination, themes, limit=5):
    """
    Search for attractions/activities based on themes.
    Returns list of place dicts (mockable).
    """
    if not gmaps:
        # Mock sample places
        return [
            {"name": "Amber Fort", "address": "Amber Fort Rd", "rating": 4.6, "types": ["tourist_attraction"]},
            {"name": "City Palace", "address": "Old City", "rating": 4.5, "types": ["museum"]},
        ][:limit]

    query = f"{themes} in {destination}" if themes else f"things to do in {destination}"
    places = gmaps.places(query=query)
    results = places.get("results", [])[:limit]

    # Normalize output
    normalized = []
    for r in results:
        normalized.append({
            "name": r.get("name"),
            "address": r.get("vicinity") or r.get("formatted_address"),
            "rating": r.get("rating", 0),
            "types": r.get("types", [])
        })
    return normalized


def search_hotels(destination, limit=5):
    """
    Search for hotels (lodging) in a destination city.
    Returns list of hotel dicts.
    """
    if not gmaps:
        # Mock sample hotels
        return [
            {"name": "Mock Hotel", "price_per_night": 5000, "rating": 4.5, "address": "123 Main St"},
            {"name": "Sample Inn", "price_per_night": 3500, "rating": 4.2, "address": "456 High Rd"},
        ][:limit]

    try:
        results = gmaps.places(query=f"hotels in {destination}", type="lodging")
        hotels = []
        for place in results.get("results", [])[:limit]:
            hotels.append({
                "name": place.get("name"),
                "rating": place.get("rating", "N/A"),
                "address": place.get("formatted_address") or place.get("vicinity", ""),
                # Google Places does not return pricing
                "price_per_night": "N/A"
            })
        return hotels
    except Exception as e:
        print(f"⚠️ Hotel search failed: {e}")
        return []


def get_directions(origin, destination):
    """
    Get driving directions between two points.
    """
    if not gmaps:
        return {"duration": "30 mins", "distance": "5 km", "steps": []}

    now = datetime.now()
    directions = gmaps.directions(origin, destination, mode="driving", departure_time=now)
    if not directions:
        return {"duration": None, "distance": None, "steps": []}
    leg = directions[0]["legs"][0]
    return {
        "duration": leg.get("duration", {}).get("text"),
        "distance": leg.get("distance", {}).get("text"),
        "steps": [step["html_instructions"] for step in leg.get("steps", [])]
    }