from flask import Flask, render_template, request
import requests

app = Flask(__name__)

OPENTRIP_API_KEY = "5ae2e3f221c38a28845f05b6380496cd5327ce19e99042e35c6bde02"

def get_places_by_kind(lat, lon, kind, limit=3):
    url = (
        f"https://api.opentripmap.com/0.1/en/places/radius"
        f"?radius=5000&lon={lon}&lat={lat}"
        f"&kinds={kind}&limit={limit}"
        f"&apikey={OPENTRIP_API_KEY}"
    )
    data = requests.get(url).json()
    places = data.get("features", [])
    return [p["properties"].get("name", "Unknown") for p in places if p["properties"].get("name")]

def recommend_places(interests, places):
    recommended = []
    for place in places:
        name = place.get("name", "").lower()
        if "adventure" in interests and any(w in name for w in ["trek", "hill", "mountain", "fort"]):
            recommended.append(place)
        elif "religious" in interests and any(w in name for w in ["temple", "mosque", "church", "shrine"]):
            recommended.append(place)
        elif "nature" in interests and any(w in name for w in ["park", "lake", "garden", "forest"]):
            recommended.append(place)
    return recommended[:5] if recommended else places[:5]

@app.route("/", methods=["GET", "POST"])
def index():
    itinerary = []
    hotels = []
    shopping = []
    hospitals = []
    treatments = []

    if request.method == "POST":
        city = request.form["city"]
        days = int(request.form["days"])
        interests = request.form["interests"].lower()

        geo_url = f"https://api.opentripmap.com/0.1/en/places/geoname?name={city}&apikey={OPENTRIP_API_KEY}"
        geo = requests.get(geo_url).json()
        lat = geo.get("lat")
        lon = geo.get("lon")

        if not lat or not lon:
            itinerary=["City not found. Please try another city."]
            return render_template("index.html", itinerary=itinerary,
                                   hotels=[], shopping=[], hospitals=[], treatments=[])

        places_url = (
            f"https://api.opentripmap.com/0.1/en/places/radius"
            f"?radius=5000&lon={lon}&lat={lat}&apikey={OPENTRIP_API_KEY}"
        )
        data = requests.get(places_url).json()
        places=data.get("features", [])
        places_list=[p["properties"] for p in places]
        selected=recommend_places(interests, places_list)

        for i in range(days):
            if i < len(selected):
                itinerary.append(f"Day {i+1}: Visit {selected[i].get('name', 'Local Attraction')}")
            else:
                itinerary.append(f"Day {i+1}: Free exploration of {city}")

        hotels=get_places_by_kind(lat, lon, "accomodations", limit=5)
        if not hotels:
            hotels=[f"Hotel searches in {city} — check Booking.com or MakeMyTrip"]

        shopping=get_places_by_kind(lat, lon, "shops", limit=5)
        if not shopping:
            shopping=[f"Local markets and malls in {city}"]

        hospitals=get_places_by_kind(lat, lon, "hospitals", limit=5)
        if not hospitals:
            hospitals=[f"Search 'hospitals near {city}' on Google Maps"]

        treatments=get_places_by_kind(lat, lon, "health", limit=5)
        if not treatments:
            treatments = [
                "Ayurvedic Spa & Wellness Center",
                "Physiotherapy & Rehabilitation Clinic",
                "Yoga & Meditation Retreat",
            ]

    return render_template("index.html",
                           itinerary=itinerary,
                           hotels=hotels,
                           shopping=shopping,
                           hospitals=hospitals,
                           treatments=treatments)

if __name__ == "__main__":
    app.run(debug=True)