import os
import json
import base64
import re
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import requests
except ImportError:
    requests = None


VISION_SYSTEM_PROMPT = """
You are SnapTrip AI, an expert local tourist guide and smart travel budget assistant.
Your task is to analyze the landmark, monument, temple, museum, or tourist attraction in the provided photo against the destination context.

You must return a STRICT, valid JSON object matching the following structure:
{
  "landmark_name": "Exact Name of the Landmark",
  "location": "City, State/Region, Country",
  "history_and_significance": [
    "Fact 1: Key historical origin, architect, or founding era.",
    "Fact 2: Cultural, religious, or architectural importance.",
    "Fact 3: Notable interesting trivia, UNESCO status, or visitor record."
  ],
  "estimated_costs": {
    "ticket_fee": 15.0,
    "local_transport": 5.0,
    "food_snacks": 8.0,
    "total_estimate": 28.0,
    "currency": "USD",
    "notes": "Brief explanation of ticketing options or transport tips."
  },
  "nearby_attractions": [
    {
      "name": "Nearby Spot 1",
      "distance": "2.0 km (10 mins by transit/auto)",
      "highlights": "One sentence summary of what to see here.",
      "estimated_cost": 5.0,
      "why_recommended": "Why this fits the user's remaining trip duration and daily budget."
    },
    {
      "name": "Nearby Spot 2",
      "distance": "3.5 km (15 mins by transit)",
      "highlights": "One sentence summary of what to see here.",
      "estimated_cost": 10.0,
      "why_recommended": "Great for continuing the cultural tour within budget."
    },
    {
      "name": "Nearby Spot 3",
      "distance": "1.2 km (Walking distance)",
      "highlights": "One sentence summary of what to see here.",
      "estimated_cost": 0.0,
      "why_recommended": "Free scenic viewpoint or public plaza fitting the travel plan."
    }
  ],
  "insider_tips": [
    "Tip 1 regarding best time to visit or photography.",
    "Tip 2 regarding ticketing queues or dress code."
  ]
}

Ensure all numeric cost values are numbers (float or int), not strings.
All recommendations and cost estimates must reflect the tourist's selected Budget Category and Currency.
"""

TRANSIT_SYSTEM_PROMPT = """
You are SnapTrip AI's expert multi-modal transit intelligence system.
Your job is to provide accurate, realistic, and practical intercity travel route breakdowns between an origin city and destination city across all modes of passenger transit:
1. Trains (direct or via major nearby boarding hubs / junction stations like GNT / BZA)
2. Flights (nearest airport pairs, airlines, non-stop vs connecting durations, and price ranges)
3. Long-Distance Buses (intercity AC sleeper / semi-sleeper operators, routes, durations, fares)
4. Inland Waterways / Ferries (feasibility check for direct navigation between the two regions, rationale, and local river cruise / water tour alternatives if applicable)

You must return a STRICT, valid JSON object matching the following structure:
{
  "route_summary": "Origin to Destination Route Summary",
  "origin": "Origin City, State/Country",
  "destination": "Destination City, State/Country",
  "distance_km": "Estimated distance by road/rail (e.g. ~1,800 km)",
  "trains": {
    "hub_info": "Boarding options (e.g. from local junction or nearby major rail hub like GNT / BZA)",
    "options": [
      {
        "train_name": "Train Name (e.g. AP Express)",
        "train_number": "Train Number (e.g. 20805 / 20806)",
        "duration": "Estimated journey time (e.g. 28h 30m)",
        "departure_frequency": "Frequency (e.g. Daily / 3 days a week)",
        "fare_tiers": {
          "sleeper": "Indicative fare (e.g. ₹750 - ₹850)",
          "3ac": "Indicative fare (e.g. ₹1,950 - ₹2,100)",
          "2ac": "Indicative fare (e.g. ₹2,800 - ₹3,050)",
          "1ac": "Indicative fare (e.g. ₹4,800 - ₹5,200)"
        },
        "notes": "Route highlights, punctuality, or key stops"
      }
    ]
  },
  "flights": {
    "airport_route": "Nearest Origin Airport (Code) -> Nearest Destination Airport (Code)",
    "distance_to_airport": "Distance / drive time from origin city center to departure airport",
    "airlines": ["Airline 1", "Airline 2"],
    "duration": "e.g. 2h 20m (Non-stop) or 4h 30m (1-stop)",
    "price_range": "e.g. ₹4,500 - ₹8,500",
    "notes": "Ticketing advice or peak season guidelines"
  },
  "buses": {
    "service_type": "Intercity AC Sleeper / Multi-Axle",
    "operators": ["Operator 1", "Operator 2"],
    "route_breakdown": "e.g. Via major highway corridor or transfer hub",
    "duration": "e.g. 30 - 34 hours",
    "fare_range": "e.g. ₹2,200 - ₹3,800",
    "notes": "Comfort guidelines or stopover suggestions"
  },
  "waterways": {
    "is_feasible": false,
    "feasibility_assessment": "Clear explanation of whether direct commercial inland passenger navigation exists between these regions.",
    "local_water_experiences": "Local river/lake cruises or ferry experiences available in the destination or origin region.",
    "recommended_alternative": "Recommended land or air transit alternative."
  }
}

Ensure the output is STRICT valid JSON with no extraneous text.
"""

def get_api_key(custom_key: Optional[str] = None) -> Optional[str]:
    """Retrieves Gemini API key from parameter, session, or .env."""
    if custom_key and custom_key.strip():
        return custom_key.strip()
    return os.getenv("GEMINI_API_KEY", "").strip() or None

def encode_image_to_base64(image_bytes: bytes) -> str:
    """Encodes raw bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Cleans markdown JSON fences and parses string into dict."""
    cleaned = raw_text.strip()
    # Remove markdown codeblocks if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        return data
    except Exception as e:
        # Fallback regex extraction of JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data
            except Exception:
                pass
        raise ValueError(f"Failed to parse Gemini response as JSON: {raw_text[:200]}...")

def sanitize_landmark_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Guarantees schema consistency even if AI skips a field."""
    costs = data.get("estimated_costs", {})
    ticket = float(costs.get("ticket_fee", 0.0) or 0.0)
    transport = float(costs.get("local_transport", 0.0) or 0.0)
    food = float(costs.get("food_snacks", 0.0) or 0.0)
    total = float(costs.get("total_estimate", ticket + transport + food) or (ticket + transport + food))

    return {
        "landmark_name": data.get("landmark_name", "Identified Landmark"),
        "location": data.get("location", "Unknown Location"),
        "history_and_significance": data.get("history_and_significance", [
            "Historical and cultural landmark of major significance."
        ]),
        "estimated_costs": {
            "ticket_fee": ticket,
            "local_transport": transport,
            "food_snacks": food,
            "total_estimate": total,
            "currency": costs.get("currency", "USD"),
            "notes": costs.get("notes", "Estimates based on typical tourist rates.")
        },
        "nearby_attractions": data.get("nearby_attractions", []),
        "insider_tips": data.get("insider_tips", [
            "Check local opening hours before visiting.",
            "Carry cash and a valid ID."
        ])
    }

# ----------------- LANDMARK VISION AI -----------------

def analyze_landmark_gemini(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    destination_city: str = "",
    origin_city: str = "",
    budget_type: str = "Moderate",
    duration_days: int = 1,
    currency: str = "USD",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes landmark photo using Gemini API.
    Tries Google GenAI SDK first, then REST API fallback, and smart demo fallback if key is missing.
    """
    key = get_api_key(api_key)

    user_instructions = f"""
Analyze this tourist landmark photograph against the traveler's itinerary:
- Tourist's Origin / Living City & State: {origin_city or 'Unspecified'}
- Destination City / Area: {destination_city or 'Determine from image'}
- Planned Trip Duration: {duration_days} day(s)
- Budget Category & Spending Tier: {budget_type}
- Local Currency: {currency} (Provide all cost values in {currency})

Identify the exact landmark and location, provide 2-3 historical and cultural significance facts, estimate visit costs (entry ticket fees, local auto/cab fares, food estimates), and suggest 3 nearby attractions fitting within the user's remaining trip duration and daily budget.
"""

    if not key:
        return get_mock_landmark_analysis(destination_city, budget_type, currency)

    # 1. Try google-genai SDK
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        VISION_SYSTEM_PROMPT + "\n\n" + user_instructions
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                if response and response.text:
                    parsed = clean_json_response(response.text)
                    return sanitize_landmark_data(parsed)
            except Exception:
                continue
    except Exception:
        pass

    # 2. Try Direct Google Generative Language REST API
    if requests:
        try:
            b64_data = encode_image_to_base64(image_bytes)
            for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": VISION_SYSTEM_PROMPT + "\n\n" + user_instructions},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": b64_data
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2
                    }
                }
                res = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = clean_json_response(raw_text)
                    return sanitize_landmark_data(parsed)
        except Exception as rest_err:
            pass

    # Fallback to simulated if all failed
    return get_mock_landmark_analysis(destination_city, budget_type, currency)


def get_mock_landmark_analysis(destination_city: str, budget_type: str, currency: str) -> Dict[str, Any]:
    """Smart demo analysis when API key is not configured yet."""
    multiplier = 1.0
    if budget_type == "Budget":
        multiplier = 0.6
    elif budget_type == "Luxury":
        multiplier = 2.5

    rates = {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.78, "INR": 83.5, "JPY": 155.0, "CAD": 1.37, "AUD": 1.52
    }
    r = rates.get(currency, 1.0)

    ticket = round(15.0 * multiplier * r, 2)
    transport = round(6.0 * multiplier * r, 2)
    food = round(10.0 * multiplier * r, 2)
    total = ticket + transport + food

    city_name = destination_city.strip() if destination_city else "Agra, India"
    landmark_title = "Historical Cultural Monument"
    if "agra" in city_name.lower():
        landmark_title = "Taj Mahal & Mughal Gardens"
    elif "delhi" in city_name.lower():
        landmark_title = "Qutub Minar & Mehrauli Complex"
    elif "paris" in city_name.lower():
        landmark_title = "Eiffel Tower & Champ de Mars"
    elif "rome" in city_name.lower():
        landmark_title = "Colosseum Amphitheatre"

    return {
        "landmark_name": landmark_title,
        "location": city_name,
        "history_and_significance": [
            f"Commissioned during the height of classical architecture as a grand testament to local heritage.",
            f"Officially recognized as a protected heritage site attracting millions of domestic and global tourists.",
            f"Features distinct architectural craftsmanship blending local stonework with classical arches."
        ],
        "estimated_costs": {
            "ticket_fee": ticket,
            "local_transport": transport,
            "food_snacks": food,
            "total_estimate": total,
            "currency": currency,
            "notes": f"Estimated for {budget_type} traveler in {currency}. Enter your GEMINI_API_KEY in the sidebar for live AI vision recognition on any photo!"
        },
        "nearby_attractions": [
            {
                "name": "Old Town Heritage Bazaar",
                "distance": "1.2 km (15 min walk)",
                "highlights": "Lively traditional market offering local crafts, textiles, and street delicacies.",
                "estimated_cost": round(4.0 * multiplier * r, 2),
                "why_recommended": "Great immersion in local culture fitting your remaining daily budget."
            },
            {
                "name": "Grand Royal Fort & Citadel",
                "distance": "2.8 km (8 min auto/cab)",
                "highlights": "Imposing ramparts with panoramic vistas across the entire city.",
                "estimated_cost": round(8.0 * multiplier * r, 2),
                "why_recommended": "Perfect historical complement fitting within your trip duration."
            },
            {
                "name": "Riverside Sunset Promenade",
                "distance": "0.8 km (10 min walk)",
                "highlights": "Scenic waterfront walking path ideal for twilight photography and relaxed evening strolls.",
                "estimated_cost": 0.0,
                "why_recommended": "Completely free, peaceful scenic views to conclude the afternoon."
            }
        ],
        "insider_tips": [
            "Visit early in the morning (around 7:00 AM) to experience the monument with soft golden lighting and minimal queues.",
            "Authorized local guides or official audio guide apps provide the richest historical context."
        ]
    }

# ----------------- MULTI-MODAL INTERCITY TRANSIT -----------------

def get_intercity_transit_options(
    origin_city: str,
    destination_city: str,
    budget_tier: str = "Moderate",
    currency: str = "INR",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves multi-modal intercity transit breakdown between origin and destination:
    1. Trains (Direct or connecting hubs e.g. GNT/BZA, duration, and fare tiers Sleeper/3AC/2AC/1AC)
    2. Flights (nearest airport pairs, airlines, flight duration, and price range)
    3. Buses (intercity AC sleeper, duration, fare range)
    4. Inland Waterways (feasibility check, rationale, local river cruise alternatives)
    """
    key = get_api_key(api_key)

    user_instructions = f"""
Provide a comprehensive multi-modal intercity transit breakdown for a traveler:
- Origin City & State: {origin_city}
- Destination City & Region: {destination_city}
- Budget Category: {budget_tier}
- Currency: {currency}

Cover all 4 transit modes:
1. Trains (Major direct/connecting trains with numbers, e.g. AP Express, Grand Trunk Express, Andaman Express via GNT/BZA, travel duration, indicative fares for Sleeper, 3AC, 2AC, 1AC).
2. Flights (Nearest airport route, e.g. Vijayawada VGA -> Delhi DEL, airlines IndiGo/Air India, duration, and price range).
3. Long-Distance Buses (AC sleeper options, routes, durations, and fare range).
4. Inland Waterways / Ferries (Feasibility check for direct inland navigation between the two regions, explanation, and local water tour / ferry options in origin/destination).
"""

    if not key:
        return get_mock_intercity_transit_options(origin_city, destination_city, budget_tier, currency)

    # 1. Try google-genai SDK
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=TRANSIT_SYSTEM_PROMPT + "\n\n" + user_instructions,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                if response and response.text:
                    parsed = clean_json_response(response.text)
                    return sanitize_transit_data(parsed, origin_city, destination_city)
            except Exception:
                continue
    except Exception:
        pass

    # 2. Try REST API
    if requests:
        try:
            for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": TRANSIT_SYSTEM_PROMPT + "\n\n" + user_instructions}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2
                    }
                }
                res = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = clean_json_response(raw_text)
                    return sanitize_transit_data(parsed, origin_city, destination_city)
        except Exception:
            pass

    return get_mock_intercity_transit_options(origin_city, destination_city, budget_tier, currency)


def sanitize_transit_data(data: Dict[str, Any], origin_city: str, destination_city: str) -> Dict[str, Any]:
    """Ensures consistent transit dictionary structure."""
    if not isinstance(data, dict):
        return get_mock_intercity_transit_options(origin_city, destination_city)

    trains = data.get("trains", {})
    flights = data.get("flights", {})
    buses = data.get("buses", {})
    waterways = data.get("waterways", {})

    return {
        "route_summary": data.get("route_summary", f"{origin_city} to {destination_city}"),
        "origin": data.get("origin", origin_city),
        "destination": data.get("destination", destination_city),
        "distance_km": data.get("distance_km", "~1,750 km"),
        "trains": {
            "hub_info": trains.get("hub_info", "Board from local junction or nearby major rail hub"),
            "options": trains.get("options", [])
        },
        "flights": {
            "airport_route": flights.get("airport_route", "Nearest Airport Route"),
            "distance_to_airport": flights.get("distance_to_airport", ""),
            "airlines": flights.get("airlines", ["IndiGo", "Air India"]),
            "duration": flights.get("duration", "2h 30m"),
            "price_range": flights.get("price_range", "₹4,500 - ₹8,500"),
            "notes": flights.get("notes", "")
        },
        "buses": {
            "service_type": buses.get("service_type", "Intercity AC Sleeper"),
            "operators": buses.get("operators", ["APSRTC / State Roadways", "Private Multi-Axle Operators"]),
            "route_breakdown": buses.get("route_breakdown", ""),
            "duration": buses.get("duration", "30-34 hours"),
            "fare_range": buses.get("fare_range", "₹2,200 - ₹3,800"),
            "notes": buses.get("notes", "")
        },
        "waterways": {
            "is_feasible": waterways.get("is_feasible", False),
            "feasibility_assessment": waterways.get("feasibility_assessment", "Direct inland water navigation is not feasible for this route."),
            "local_water_experiences": waterways.get("local_water_experiences", "Local river tours or ferries available."),
            "recommended_alternative": waterways.get("recommended_alternative", "Fast trains or flights are recommended.")
        }
    }


def get_mock_intercity_transit_options(
    origin_city: str = "Guntur, Andhra Pradesh",
    destination_city: str = "Delhi, India",
    budget_tier: str = "Moderate",
    currency: str = "INR"
) -> Dict[str, Any]:
    """
    High-fidelity simulated multi-modal transit options.
    Tailored specifically for routes like Guntur, Andhra Pradesh -> Delhi, India
    and adaptable for other city pairs.
    """
    orig_lower = origin_city.lower()
    dest_lower = destination_city.lower()

    if "guntur" in orig_lower or "andhra" in orig_lower or "vijayawada" in orig_lower:
        return {
            "route_summary": f"{origin_city} ➔ {destination_city}",
            "origin": origin_city,
            "destination": destination_city,
            "distance_km": "~1,750 - 1,820 km (Rail / Highway)",
            "trains": {
                "hub_info": "Direct departures from Guntur Junction (GNT) & high-frequency superfast connections via Vijayawada Junction (BZA, 32 km from Guntur via frequent 30-min express shuttle/cabs).",
                "options": [
                    {
                        "train_name": "Andhra Pradesh Express (AP Express)",
                        "train_number": "20805 / 20806",
                        "duration": "28h 30m (Fastest direct daily superfast)",
                        "departure_frequency": "Daily",
                        "fare_tiers": {
                            "sleeper": "₹780 - ₹820",
                            "3ac": "₹2,050 - ₹2,150",
                            "2ac": "₹2,950 - ₹3,100",
                            "1ac": "₹5,050 - ₹5,300"
                        },
                        "notes": "Premier daily train connecting coastal Andhra to New Delhi. Features modern LHB coaches, onboard pantry car, and high punctuality."
                    },
                    {
                        "train_name": "Grand Trunk (GT) Express",
                        "train_number": "12615",
                        "duration": "29h 15m (Boarding at Vijayawada BZA)",
                        "departure_frequency": "Daily",
                        "fare_tiers": {
                            "sleeper": "₹750",
                            "3ac": "₹2,000",
                            "2ac": "₹2,900",
                            "1ac": "₹4,980"
                        },
                        "notes": "One of Indian Railways' most legendary historic trunk routes operating via Warangal, Balharshah, Nagpur, and Bhopal to New Delhi."
                    },
                    {
                        "train_name": "Andaman Express",
                        "train_number": "16031",
                        "duration": "32h 40m",
                        "departure_frequency": "3 Days/Week (Wed, Thu, Sun)",
                        "fare_tiers": {
                            "sleeper": "₹720",
                            "3ac": "₹1,950",
                            "2ac": "₹2,800",
                            "1ac": "N/A"
                        },
                        "notes": "Connects southern corridor via Vijayawada towards New Delhi and Jammu Tawi. Affordable budget sleeper choice."
                    }
                ]
            },
            "flights": {
                "airport_route": "Vijayawada Airport, Gannavaram (VGA) ➔ Indira Gandhi International Airport, New Delhi (DEL)",
                "distance_to_airport": "Vijayawada Airport (VGA) is ~52 km from Guntur (approx 1 hr 15 mins drive via Amaravathi bypass / NH16).",
                "airlines": ["IndiGo", "Air India"],
                "duration": "2h 20m (Non-stop direct) or 4h 30m - 6h (1-stop via Hyderabad / Bengaluru)",
                "price_range": "₹4,500 - ₹9,200 (Economy standard; lower when booked 2-3 weeks in advance)",
                "notes": "Direct non-stop flight operated daily by IndiGo (6E) from VGA to DEL. Fastest option for short 1-3 day itineraries."
            },
            "buses": {
                "service_type": "Intercity Multi-Axle AC Sleeper / Semi-Sleeper",
                "operators": ["APSRTC (Amaravathi / Dolphin Cruise)", "Orange Travels", "VRL Travels", "SRS Travels"],
                "route_breakdown": "Guntur ➔ Hyderabad (MGBS / Gachibowli, 5 hrs) ➔ Connecting interstate sleeper to Delhi via NH44 (Agra corridor).",
                "duration": "30 - 35 hours total journey time",
                "fare_range": "₹2,400 - ₹4,200",
                "notes": "Recommended to split with an evening stopover in Hyderabad. Best suited as a contingency if train tickets are waitlisted."
            },
            "waterways": {
                "is_feasible": False,
                "feasibility_assessment": "❌ Direct inland commercial water navigation between Guntur (Krishna River basin) and Delhi (Yamuna River) is NOT geographically feasible. India's National Waterways (NW-4 on Krishna/Godavari in AP and NW-1/NW-110 on Yamuna in Delhi) are separated by the Deccan plateau and central mountain divides with no navigable inter-river passenger canal system.",
                "local_water_experiences": "🚢 Local River Experiences: At origin: Krishna River Bhavani Island ferry & speedboats (Vijayawada/Prakasam Barrage). At destination: Yamuna River morning boat rides at Yamuna Ghat (Kashmere Gate) & boating at Delhi Purana Qila lake.",
                "recommended_alternative": "🚆 AP Express (Train 20805) for comfortable overland travel or ✈️ direct non-stop flight (VGA ➔ DEL, 2h 20m) for fast transit."
            }
        }

    # Generic realistic fallback for other city pairs
    return {
        "route_summary": f"{origin_city} ➔ {destination_city}",
        "origin": origin_city,
        "destination": destination_city,
        "distance_km": "~800 - 1,500 km",
        "trains": {
            "hub_info": f"Frequent direct and connecting train services connecting {origin_city} and {destination_city}.",
            "options": [
                {
                    "train_name": "Superfast Intercity Express",
                    "train_number": "12001 / 12002",
                    "duration": "14h - 22h",
                    "departure_frequency": "Daily",
                    "fare_tiers": {
                        "sleeper": "₹550 - ₹750",
                        "3ac": "₹1,450 - ₹1,850",
                        "2ac": "₹2,100 - ₹2,600",
                        "1ac": "₹3,500 - ₹4,400"
                    },
                    "notes": "Convenient overnight or daytime superfast connection."
                }
            ]
        },
        "flights": {
            "airport_route": f"Nearest Airport to {origin_city} ➔ Nearest Airport to {destination_city}",
            "distance_to_airport": "Approx 30-60 mins drive from city center.",
            "airlines": ["IndiGo", "Air India", "SpiceJet"],
            "duration": "1h 30m - 2h 45m (Direct)",
            "price_range": "₹3,800 - ₹7,500",
            "notes": "Fastest passenger transit mode. Pre-booking yields significant savings."
        },
        "buses": {
            "service_type": "Interstate AC Multi-Axle Sleeper",
            "operators": ["State Road Transport Corporation", "Private AC Sleeper Coaches"],
            "route_breakdown": "Direct highway transit via National Highway network.",
            "duration": "16 - 24 hours",
            "fare_range": "₹1,200 - ₹2,800",
            "notes": "Overnight sleeper buses available with reclining berths and charging points."
        },
        "waterways": {
            "is_feasible": False,
            "feasibility_assessment": f"Direct commercial passenger inland waterway transit is not available between {origin_city} and {destination_city} due to lack of connected navigable national waterways across these inland points.",
            "local_water_experiences": "Explore local scenic river cruises, lake shikara rides, or harbor ferries within the destination region.",
            "recommended_alternative": "High-speed rail express or commercial flights are recommended."
        }
    }
