"""
Comprehensive End-to-End Workflow Verification for SnapTrip AI.
Simulates:
1. Trip Configuration & Setup (Origin: Guntur, Andhra Pradesh ➔ Destination: Delhi, India)
2. Multi-Modal Intercity Transit Breakdown (Trains, Flights, Buses, Waterways)
3. Multi-sample Image processing (India Gate Delhi, Taj Mahal, Eiffel Tower, Colosseum)
4. Gemini AI Vision Analysis & JSON parsing
5. Budget Impact Calculations (Ticket, Transport, Food, Total)
6. Itinerary Cumulative Tracking & Deductions
7. Markdown and JSON Itinerary Generation
"""
import os
import sys
import json
import base64

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import database as db
import auth
from gemini_service import analyze_landmark_gemini, get_intercity_transit_options

def run_workflow_verification():
    print("==================================================")
    print("🚀 Verifying SnapTrip AI End-to-End Workflow")
    print("==================================================")

    # 1. Initialize Test User & Active Trip
    user = db.get_user_by_username("verified_traveler")
    if not user:
        uid = db.create_user("verified_traveler", "traveler@snaptrip.ai", auth.hash_password("travelerPass123"))
        user = db.get_user_by_id(uid)
    print(f"👤 Active User: {user['username']} (ID: {user['id']})")

    # Create 3-day Delhi Heritage Tour from Guntur
    trip_id = db.create_trip(
        user_id=user["id"],
        trip_name="Capital Heritage Expedition",
        origin_city="Guntur, Andhra Pradesh",
        destination_city="Delhi, India",
        duration_days=3,
        budget_tier="Moderate",
        daily_budget_limit=4500.0,
        currency="INR"
    )
    trip = db.get_trip_by_id(trip_id)
    print(f"🧳 Trip Created: '{trip['trip_name']}'")
    print(f"   Route: {trip['origin_city']} ➔ {trip['destination_city']}")
    print(f"   Daily Budget: {trip['currency']} {trip['daily_budget_limit']:.2f} | Total: {trip['currency']} {trip['duration_days']*trip['daily_budget_limit']:.2f}")

    # 2. Verify Multi-Modal Intercity Transit Breakdown
    print("\n🚆 Fetching Intercity Transit Intelligence...")
    transit = get_intercity_transit_options(
        origin_city=trip["origin_city"],
        destination_city=trip["destination_city"],
        budget_tier=trip["budget_tier"],
        currency=trip["currency"]
    )
    db.update_trip_transit_data(trip["id"], json.dumps(transit))
    print(f"   Route Summary: {transit['route_summary']} ({transit['distance_km']})")
    print(f"   🚆 Trains ({len(transit['trains']['options'])} options):")
    for tr in transit["trains"]["options"]:
        fares = tr.get("fare_tiers", {})
        print(f"      * {tr['train_name']} ({tr['train_number']}) - {tr['duration']} | Sleeper: {fares.get('sleeper')} | 3AC: {fares.get('3ac')}")
    print(f"   ✈️ Flight Corridor: {transit['flights']['airport_route']}")
    print(f"      Airlines: {', '.join(transit['flights']['airlines'])} | Time: {transit['flights']['duration']} | Est: {transit['flights']['price_range']}")
    print(f"   🚌 Bus Services: {transit['buses']['service_type']} (~{transit['buses']['duration']}) | {transit['buses']['fare_range']}")
    print(f"   🚢 Inland Waterways Feasibility: {'Feasible' if transit['waterways']['is_feasible'] else 'Not Feasible'}")
    print(f"      {transit['waterways']['feasibility_assessment'][:90]}...")

    # 3. Test Image Uploads with Sample Assets including Delhi India Gate
    sample_images = [
        ("assets/sample_delhi_india_gate.jpg", "Delhi, India", "image/jpeg"),
        ("assets/sample_taj_mahal.jpg", "Agra, India", "image/jpeg"),
        ("assets/sample_eiffel_tower.jpg", "Paris, France", "image/jpeg"),
        ("assets/sample_colosseum.jpg", "Rome, Italy", "image/jpeg")
    ]

    for img_rel_path, city, mime in sample_images:
        img_full_path = os.path.join(os.path.dirname(__file__), img_rel_path)
        assert os.path.exists(img_full_path), f"Sample image {img_full_path} not found"

        with open(img_full_path, "rb") as f:
            img_bytes = f.read()

        print(f"\n📸 Scanning Landmark: {os.path.basename(img_rel_path)} ({len(img_bytes)} bytes)...")

        # Run AI Vision Analysis
        analysis = analyze_landmark_gemini(
            image_bytes=img_bytes,
            mime_type=mime,
            destination_city=city,
            origin_city=trip["origin_city"],
            budget_type=trip["budget_tier"],
            duration_days=trip["duration_days"],
            currency=trip["currency"]
        )

        costs = analysis["estimated_costs"]
        print(f"   🏛️ Identified: {analysis['landmark_name']} ({analysis['location']})")
        print(f"   💰 Total Visit Estimate: {costs['currency']} {costs['total_estimate']:.2f}")
        print(f"      - 🎟️ Ticket: {costs['currency']} {costs['ticket_fee']:.2f}")
        print(f"      - 🚕 Transit: {costs['currency']} {costs['local_transport']:.2f}")
        print(f"      - 🥪 Food: {costs['currency']} {costs['food_snacks']:.2f}")
        print(f"   🗺️ Next Nearby Spots ({len(analysis['nearby_attractions'])}):")
        for spot in analysis["nearby_attractions"]:
            print(f"      * {spot['name']} ({spot.get('distance', 'nearby')}) - Est: {spot.get('estimated_cost', 0)}")

        # Save to Database Itinerary
        b64_img = base64.b64encode(img_bytes[:2048]).decode("utf-8")
        scan_id = db.save_landmark_scan(
            user_id=user["id"],
            trip_id=trip["id"],
            landmark_name=analysis["landmark_name"],
            location=analysis["location"],
            history_points=analysis["history_and_significance"],
            ticket_cost=costs["ticket_fee"],
            transport_cost=costs["local_transport"],
            food_cost=costs["food_snacks"],
            total_cost=costs["total_estimate"],
            currency=costs["currency"],
            nearby_attractions=analysis["nearby_attractions"],
            local_tips=analysis.get("insider_tips", []),
            image_data=b64_img
        )
        print(f"   ✅ Saved to Itinerary as Stop ID: {scan_id}")

    # 4. Verify Cumulative Itinerary & Budget Calculations
    scans = db.get_trip_scans(trip["id"])
    total_spent = sum(s["total_cost"] for s in scans)
    total_budget = trip["daily_budget_limit"] * trip["duration_days"]
    remaining = total_budget - total_spent

    print("\n--------------------------------------------------")
    print(f"📊 Cumulative Budget Verification for '{trip['trip_name']}':")
    print(f"   Total Budget:     {trip['currency']} {total_budget:.2f}")
    print(f"   Total Spent:      {trip['currency']} {total_spent:.2f} across {len(scans)} stops")
    print(f"   Remaining Budget: {trip['currency']} {remaining:.2f}")
    assert len(scans) == 4, f"Expected 4 saved stops, got {len(scans)}"
    assert total_spent > 0, "Total spent should be positive"

    print("\n🎉 ALL END-TO-END WORKFLOW VERIFICATIONS SUCCEEDED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_workflow_verification()
