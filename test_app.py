"""
Automated Verification & Unit Tests for SnapTrip AI
Tests Database, Authentication, Multi-Modal Intercity Transit, Gemini Vision parsing, and Business Logic.
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

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
import auth
from gemini_service import (
    sanitize_landmark_data,
    clean_json_response,
    get_mock_landmark_analysis,
    get_intercity_transit_options
)

def run_tests():
    print("==========================================")
    print("🧪 Running SnapTrip AI Automated Tests")
    print("==========================================\n")

    passed = 0
    total = 0

    # Test 1: Database Initialization & Migrations
    total += 1
    try:
        db.init_db()
        conn = db.get_connection()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        trip_cols = [c[1] for c in conn.execute("PRAGMA table_info(trips)").fetchall()]
        conn.close()

        assert "users" in tables, "users table missing"
        assert "trips" in tables, "trips table missing"
        assert "landmark_scans" in tables, "landmark_scans table missing"
        assert "origin_city" in trip_cols, "origin_city column missing from trips"
        assert "transit_data" in trip_cols, "transit_data column missing from trips"

        print("✅ [Test 1] Database tables & origin/transit schema migrations verified.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 1] DB Init failed: {e}")

    # Test 2: User Registration & Authentication
    total += 1
    try:
        test_uname = "traveler_test"
        test_email = "traveler_test@example.com"
        test_pass = "secret123"

        # Clean existing test user if any
        existing = db.get_user_by_username(test_uname)
        if existing:
            conn = db.get_connection()
            conn.execute("DELETE FROM users WHERE username = ?", (test_uname,))
            conn.commit()
            conn.close()

        ok, msg, usr = auth.register_user(test_uname, test_email, test_pass)
        assert ok, f"Registration failed: {msg}"
        assert usr["username"] == test_uname

        # Test login
        ok_login, msg_login, log_usr = auth.authenticate_user(test_uname, test_pass)
        assert ok_login, f"Login failed: {msg_login}"
        assert log_usr["id"] == usr["id"]

        # Test invalid login
        ok_bad, _, _ = auth.authenticate_user(test_uname, "wrongpassword")
        assert not ok_bad, "Invalid login succeeded unexpectedly"

        print("✅ [Test 2] User registration and password hashing auth verified.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 2] Auth test failed: {e}")

    # Test 3: Trip Creation with Origin & Destination
    total += 1
    try:
        user = db.get_user_by_username("traveler_test")
        trip_id = db.create_trip(
            user_id=user["id"],
            trip_name="Guntur to Delhi Expedition",
            origin_city="Guntur, Andhra Pradesh",
            destination_city="Delhi, India",
            duration_days=3,
            budget_tier="Moderate",
            daily_budget_limit=4500.0,
            currency="INR"
        )
        assert trip_id > 0, "Failed to create trip"

        trip = db.get_trip_by_id(trip_id)
        assert trip["origin_city"] == "Guntur, Andhra Pradesh"
        assert trip["destination_city"] == "Delhi, India"
        assert trip["duration_days"] == 3
        assert trip["daily_budget_limit"] == 4500.0
        assert trip["currency"] == "INR"

        print("✅ [Test 3] Trip creation with origin, destination & parameters verified.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 3] Trip creation test failed: {e}")

    # Test 4: Multi-Modal Intercity Transit Breakdown (Guntur -> Delhi)
    total += 1
    try:
        transit = get_intercity_transit_options(
            origin_city="Guntur, Andhra Pradesh",
            destination_city="Delhi, India",
            budget_tier="Moderate",
            currency="INR"
        )
        assert "trains" in transit, "Trains section missing"
        assert "flights" in transit, "Flights section missing"
        assert "buses" in transit, "Buses section missing"
        assert "waterways" in transit, "Waterways section missing"

        # Verify trains
        train_opts = transit["trains"]["options"]
        assert len(train_opts) >= 2, "Expected multiple train options"
        train_names = [t["train_name"] for t in train_opts]
        assert any("AP Express" in name or "Andhra Pradesh Express" in name for name in train_names), "AP Express missing"
        assert "sleeper" in train_opts[0]["fare_tiers"], "Sleeper fare tier missing"
        assert "3ac" in train_opts[0]["fare_tiers"], "3AC fare tier missing"

        # Verify flights
        assert "VGA" in transit["flights"]["airport_route"] or "Vijayawada" in transit["flights"]["airport_route"], "VGA airport missing"
        assert "DEL" in transit["flights"]["airport_route"] or "Delhi" in transit["flights"]["airport_route"], "DEL airport missing"
        assert len(transit["flights"]["airlines"]) >= 1

        # Verify buses
        assert len(transit["buses"]["operators"]) >= 1

        # Verify waterways feasibility check
        assert transit["waterways"]["is_feasible"] is False, "Direct water route should be marked unfeasible"
        assert len(transit["waterways"]["feasibility_assessment"]) > 10
        assert len(transit["waterways"]["local_water_experiences"]) > 10

        print("✅ [Test 4] Multi-Modal transit breakdown (Trains, Flights, Buses, Waterways) verified.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 4] Multi-Modal transit test failed: {e}")

    # Test 5: Landmark Scan Storage & Itinerary Tracking
    total += 1
    try:
        user = db.get_user_by_username("traveler_test")
        trips = db.get_user_trips(user["id"])
        trip_id = trips[0]["id"]

        scan_id = db.save_landmark_scan(
            user_id=user["id"],
            trip_id=trip_id,
            landmark_name="India Gate",
            location="New Delhi, India",
            history_points=["War memorial built in 1931", "Designed by Sir Edwin Lutyens"],
            ticket_cost=0.0,
            transport_cost=150.0,
            food_cost=300.0,
            total_cost=450.0,
            currency="INR",
            nearby_attractions=[{"name": "National War Memorial", "distance": "0.3 km", "estimated_cost": 0.0}],
            local_tips=["Best visited in the evening when illuminated"],
            image_data=None
        )
        assert scan_id > 0, "Failed to save landmark scan"

        scans = db.get_trip_scans(trip_id)
        assert len(scans) >= 1
        assert scans[0]["landmark_name"] == "India Gate"
        assert scans[0]["total_cost"] == 450.0

        total_spent = db.get_total_trip_spent(trip_id)
        assert total_spent == 450.0, f"Expected 450.0, got {total_spent}"

        print("✅ [Test 5] Landmark scan storage & budget deduction verified.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 5] Landmark scan test failed: {e}")

    # Test 6: Gemini Structured Output & Sanitizer
    total += 1
    try:
        mock_ai_json = """```json
        {
            "landmark_name": "Qutub Minar",
            "location": "Delhi, India",
            "history_and_significance": ["Victory tower commenced by Qutb-ud-din Aibak in 1199"],
            "estimated_costs": {
                "ticket_fee": 50.0,
                "local_transport": 120.0,
                "food_snacks": 150.0,
                "total_estimate": 320.0,
                "currency": "INR"
            },
            "nearby_attractions": [
                {"name": "Iron Pillar of Delhi", "distance": "0.05 km", "estimated_cost": 0.0}
            ],
            "insider_tips": ["Audio guide highly recommended"]
        }
        ```"""
        parsed = clean_json_response(mock_ai_json)
        sanitized = sanitize_landmark_data(parsed)
        assert sanitized["landmark_name"] == "Qutub Minar"
        assert sanitized["estimated_costs"]["ticket_fee"] == 50.0
        assert sanitized["estimated_costs"]["currency"] == "INR"

        # Test simulated fallback for Delhi
        sim = get_mock_landmark_analysis("Delhi, India", "Moderate", "INR")
        assert "Qutub Minar" in sim["landmark_name"]
        assert sim["estimated_costs"]["currency"] == "INR"
        assert len(sim["nearby_attractions"]) == 3

        print("✅ [Test 6] Gemini Vision JSON parser and simulated fallback verified.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 6] Gemini parser test failed: {e}")

    # Test 7: Sample Assets Availability
    total += 1
    try:
        sample_files = [
            "sample_delhi_india_gate.jpg",
            "sample_taj_mahal.jpg",
            "sample_eiffel_tower.jpg",
            "sample_colosseum.jpg"
        ]
        for s in sample_files:
            p = os.path.join(os.path.dirname(__file__), "assets", s)
            assert os.path.exists(p), f"Asset {s} missing"
            assert os.path.getsize(p) > 1000, f"Asset {s} is empty"
        print("✅ [Test 7] Preloaded sample landmark images (including Delhi) verified on disk.")
        passed += 1
    except Exception as e:
        print(f"❌ [Test 7] Asset verification failed: {e}")

    print("\n------------------------------------------")
    print(f"Summary: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("------------------------------------------")

    if passed == total:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        return 0
    return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
