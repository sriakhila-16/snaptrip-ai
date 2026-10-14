import streamlit as st
import json
from typing import Optional, Dict, Any
import database as db
from auth import get_current_user
from gemini_service import get_intercity_transit_options

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "CA$",
    "AUD": "A$"
}

BUDGET_TIER_DEFAULTS = {
    "Budget": {"INR": 2000, "USD": 50, "EUR": 45, "GBP": 40, "JPY": 7500, "CAD": 70, "AUD": 75},
    "Moderate": {"INR": 5000, "USD": 130, "EUR": 120, "GBP": 105, "JPY": 20000, "CAD": 175, "AUD": 195},
    "Luxury": {"INR": 15000, "USD": 350, "EUR": 320, "GBP": 280, "JPY": 55000, "CAD": 480, "AUD": 520},
    "Custom": {"INR": 3500, "USD": 100, "EUR": 100, "GBP": 80, "JPY": 15000, "CAD": 135, "AUD": 150}
}

def render_trip_dashboard(custom_gemini_key: Optional[str] = None, **kwargs):
    if custom_gemini_key is None:
        custom_gemini_key = st.session_state.get("custom_gemini_key")
    user = get_current_user()

    if not user:
        st.warning("⚠️ Please log in or continue as Guest in the sidebar to configure trips.")
        return None

    user_id = user["id"]
    trips = db.get_user_trips(user_id)

    # Setup or load active trip
    if "active_trip_id" not in st.session_state and trips:
        st.session_state.active_trip_id = trips[0]["id"]
    elif not trips:
        # Create initial default trip tailored to Guntur -> Delhi
        default_id = db.create_trip(
            user_id=user_id,
            trip_name="Capital Heritage Expedition",
            origin_city="Guntur, Andhra Pradesh",
            destination_city="Delhi, India",
            duration_days=3,
            budget_tier="Moderate",
            daily_budget_limit=4500.0,
            currency="INR"
        )
        st.session_state.active_trip_id = default_id
        trips = db.get_user_trips(user_id)

    # Active Trip Selector & Trip Creation row
    col1, col2 = st.columns([3, 1])
    with col1:
        trip_options = {t["id"]: f"{t['trip_name']} ({t.get('origin_city', 'Guntur')} ➔ {t['destination_city']}) - {t['duration_days']} Days" for t in trips}
        active_id = st.session_state.get("active_trip_id")
        if active_id not in trip_options and trips:
            active_id = trips[0]["id"]
            st.session_state.active_trip_id = active_id

        selected_id = st.selectbox(
            "📍 Active Trip Itinerary",
            options=list(trip_options.keys()),
            format_func=lambda tid: trip_options[tid],
            index=list(trip_options.keys()).index(active_id) if active_id in trip_options else 0,
            key="trip_selector"
        )
        st.session_state.active_trip_id = selected_id

    with col2:
        st.write("")
        st.write("")
        show_new_trip_modal = st.button("➕ New Trip", use_container_width=True)

    # Current Active Trip Data
    active_trip = db.get_trip_by_id(st.session_state.active_trip_id)
    if not active_trip:
        return None

    # Handle New Trip Form
    if show_new_trip_modal or st.session_state.get("creating_trip", False):
        st.session_state.creating_trip = True
        with st.expander("✨ Plan a New Journey", expanded=True):
            with st.form("new_trip_form"):
                new_name = st.text_input("Trip Label / Title", value="Delhi Cultural Tour", placeholder="e.g. Delhi Heritage Tour")
                c_n1, c_n2 = st.columns(2)
                with c_n1:
                    new_origin = st.text_input("Origin / Living City & State", value="Guntur, Andhra Pradesh", placeholder="e.g. Guntur, Andhra Pradesh")
                with c_n2:
                    new_dest = st.text_input("Destination City / Area", value="Delhi, India", placeholder="e.g. Delhi, India")

                c_n3, c_n4 = st.columns(2)
                with c_n3:
                    new_days = st.slider("Trip Duration (Days)", min_value=1, max_value=7, value=3, help="Duration from 1 to 7 days")
                with c_n4:
                    new_curr = st.selectbox("Local Currency", options=list(CURRENCY_SYMBOLS.keys()), index=0)

                c_n5, c_n6 = st.columns(2)
                with c_n5:
                    new_tier = st.selectbox("Budget Category", options=["Budget", "Moderate", "Luxury", "Custom"], index=1)
                with c_n6:
                    def_limit = float(BUDGET_TIER_DEFAULTS.get(new_tier, {}).get(new_curr, 4500))
                    new_limit = st.number_input(f"Daily Spending Limit ({CURRENCY_SYMBOLS.get(new_curr, '₹')})", min_value=100.0, value=def_limit, step=500.0)

                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    submit_new = st.form_submit_button("Create Trip", use_container_width=True)
                with col_sub2:
                    cancel_new = st.form_submit_button("Cancel", use_container_width=True)

                if submit_new:
                    new_id = db.create_trip(
                        user_id=user_id,
                        trip_name=new_name,
                        origin_city=new_origin,
                        destination_city=new_dest,
                        duration_days=new_days,
                        budget_tier=new_tier,
                        daily_budget_limit=new_limit,
                        currency=new_curr
                    )
                    st.session_state.active_trip_id = new_id
                    st.session_state.creating_trip = False
                    st.success("New trip created!")
                    st.rerun()
                if cancel_new:
                    st.session_state.creating_trip = False
                    st.rerun()

    # Trip Settings & Quick Edit Card
    st.markdown("### ⚙️ Trip Setup & Budget Parameters")
    
    with st.form("edit_trip_form"):
        # Origin and Destination Inputs
        col_orig, col_dest = st.columns(2)
        with col_orig:
            trip_origin = st.text_input(
                "🏠 Origin / Current Living City & State",
                value=active_trip.get("origin_city", "Guntur, Andhra Pradesh"),
                help="Your starting location or home city"
            )
        with col_dest:
            trip_dest = st.text_input(
                "🎯 Destination City / Area",
                value=active_trip.get("destination_city", "Delhi, India"),
                help="Your planned travel destination"
            )

        # Duration, Budget Category, Limit, Currency
        col_days, col_tier, col_curr, col_limit = st.columns([1, 1, 1, 1.3])
        with col_days:
            trip_days = st.slider(
                "Trip Duration (Days)",
                min_value=1,
                max_value=7,
                value=min(max(1, int(active_trip["duration_days"])), 7),
                help="Select trip duration between 1 and 7 days"
            )
        with col_tier:
            tiers = ["Budget", "Moderate", "Luxury", "Custom"]
            tier_idx = tiers.index(active_trip["budget_tier"]) if active_trip["budget_tier"] in tiers else 1
            trip_tier = st.selectbox("Budget Category", options=tiers, index=tier_idx, help="Guides AI cost breakdowns and tailored recommendations")
        with col_curr:
            curr_keys = list(CURRENCY_SYMBOLS.keys())
            curr_idx = curr_keys.index(active_trip["currency"]) if active_trip["currency"] in curr_keys else 0
            trip_currency = st.selectbox("Currency", options=curr_keys, index=curr_idx)
        with col_limit:
            trip_limit = st.number_input(
                f"Daily Spending Limit ({CURRENCY_SYMBOLS.get(trip_currency, '₹')})",
                min_value=10.0,
                value=float(active_trip["daily_budget_limit"]),
                step=100.0
            )

        trip_name_val = st.text_input("Trip Label / Title", value=active_trip["trip_name"])

        save_changes = st.form_submit_button("💾 Save Trip Parameters & Refresh Route", use_container_width=True)
        if save_changes:
            # When route changes, invalidate cached transit data to trigger fresh Gemini intelligence
            route_changed = (trip_origin != active_trip.get("origin_city") or trip_dest != active_trip.get("destination_city"))
            new_transit = None if route_changed else active_trip.get("transit_data")

            db.update_trip(
                trip_id=active_trip["id"],
                trip_name=trip_name_val,
                origin_city=trip_origin,
                destination_city=trip_dest,
                duration_days=trip_days,
                budget_tier=trip_tier,
                daily_budget_limit=trip_limit,
                currency=trip_currency,
                transit_data=new_transit
            )
            st.success("✅ Trip parameters updated successfully!")
            st.rerun()

    # Summary Metrics Card
    curr_sym = CURRENCY_SYMBOLS.get(active_trip["currency"], "₹")
    total_budget = active_trip["duration_days"] * active_trip["daily_budget_limit"]
    total_spent = db.get_total_trip_spent(active_trip["id"])
    remaining = total_budget - total_spent

    st.markdown("#### 📊 Budget Overview")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Daily Budget Limit", f"{curr_sym}{active_trip['daily_budget_limit']:,.2f}")
    with m2:
        st.metric("Total Trip Budget", f"{curr_sym}{total_budget:,.2f}", f"{active_trip['duration_days']} Days")
    with m3:
        st.metric("Total Spent on Scans", f"{curr_sym}{total_spent:,.2f}")
    with m4:
        delta_color = "normal" if remaining >= 0 else "inverse"
        st.metric("Budget Remaining", f"{curr_sym}{remaining:,.2f}", delta=f"{curr_sym}{remaining:,.2f}", delta_color=delta_color)

    pct_used = min(1.0, max(0.0, total_spent / total_budget if total_budget > 0 else 0))
    st.progress(pct_used)
    st.caption(f"Budget Utilization: {pct_used * 100:.1f}% of total {curr_sym}{total_budget:,.2f}")

    # ----------------- MULTI-MODAL INTERCITY TRANSIT CARD -----------------
    render_transit_breakdown_section(active_trip, custom_gemini_key=custom_gemini_key)

    return active_trip


def render_transit_breakdown_section(active_trip: Dict[str, Any], custom_gemini_key: Optional[str] = None):
    """
    Renders dedicated '🚆 Interstate & Route Transport Options' card
    displaying Trains, Flights, Long-Distance Buses, and Inland Waterways.
    """
    st.markdown("---")
    st.markdown("### 🚆 Interstate & Route Transport Options")
    st.caption(f"Comprehensive multi-modal travel options connecting **{active_trip.get('origin_city', 'Guntur, Andhra Pradesh')}** ➔ **{active_trip.get('destination_city', 'Delhi, India')}**")

    # Load or fetch transit data
    transit_data = None
    if active_trip.get("transit_data"):
        try:
            transit_data = json.loads(active_trip["transit_data"])
        except Exception:
            transit_data = None

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn2:
        refresh_btn = st.button("🔄 Recalculate Route with Gemini", use_container_width=True)

    if not transit_data or refresh_btn:
        with st.spinner("🤖 Consulting Gemini AI for intercity train schedules, flights, bus routes, and waterways feasibility..."):
            transit_data = get_intercity_transit_options(
                origin_city=active_trip.get("origin_city", "Guntur, Andhra Pradesh"),
                destination_city=active_trip.get("destination_city", "Delhi, India"),
                budget_tier=active_trip.get("budget_tier", "Moderate"),
                currency=active_trip.get("currency", "INR"),
                api_key=custom_gemini_key
            )
            db.update_trip_transit_data(active_trip["id"], json.dumps(transit_data))
            if refresh_btn:
                st.success("✅ Transit route details updated!")
                st.rerun()

    if not transit_data:
        st.warning("Could not calculate transit breakdown at this time.")
        return

    # Route Header Hero
    st.markdown(f"""
    <div class="transit-hero">
        <div>
            <div class="transit-route">📍 {transit_data.get('origin', active_trip.get('origin_city'))} ➔ {transit_data.get('destination', active_trip.get('destination_city'))}</div>
            <div style="font-size: 0.9rem; color: #E2E8F0; margin-top: 4px;">Optimized for {active_trip.get('budget_tier', 'Moderate')} Travel Category</div>
        </div>
        <div class="transit-dist-pill">📏 {transit_data.get('distance_km', '~1,750 km')}</div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Modal Tabs
    t_tab1, t_tab2, t_tab3, t_tab4 = st.tabs([
        "🚆 Trains (Direct & Hubs)",
        "✈️ Flights (Nearest Airport)",
        "🚌 Long-Distance Buses",
        "🚢 Inland Waterways / Ferries"
    ])

    # 1. TRAINS
    with t_tab1:
        trains = transit_data.get("trains", {})
        if trains.get("hub_info"):
            st.info(f"🚉 **Boarding Hubs:** {trains['hub_info']}")

        options = trains.get("options", [])
        if not options:
            st.write("No direct train options found.")
        else:
            for t in options:
                st.markdown(f"""
                <div class="transit-mode-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <h4 style="margin: 0; color: #1E293B;">🚆 {t.get('train_name')} <span style="font-size: 0.9rem; color: #64748B;">({t.get('train_number')})</span></h4>
                        <span style="background: #E0E7FF; color: #3730A3; font-weight: 700; padding: 2px 10px; border-radius: 12px; font-size: 0.85rem;">⏱️ {t.get('duration')} | {t.get('departure_frequency', 'Regular')}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #475569; margin-top: 6px;">{t.get('notes', '')}</div>
                """, unsafe_allow_html=True)

                fares = t.get("fare_tiers", {})
                if fares:
                    st.markdown("**Indicative Class Fares:**")
                    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                    with f_col1:
                        st.markdown(f"""
                        <div class="fare-pill">
                            <div class="fare-class">Sleeper (SL)</div>
                            <div class="fare-price">{fares.get('sleeper', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with f_col2:
                        st.markdown(f"""
                        <div class="fare-pill">
                            <div class="fare-class">3 AC Tier</div>
                            <div class="fare-price">{fares.get('3ac', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with f_col3:
                        st.markdown(f"""
                        <div class="fare-pill">
                            <div class="fare-class">2 AC Tier</div>
                            <div class="fare-price">{fares.get('2ac', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with f_col4:
                        st.markdown(f"""
                        <div class="fare-pill">
                            <div class="fare-class">1 AC Tier</div>
                            <div class="fare-price">{fares.get('1ac', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

    # 2. FLIGHTS
    with t_tab2:
        flights = transit_data.get("flights", {})
        st.markdown(f"""
        <div class="transit-mode-card">
            <h4 style="margin: 0; color: #1E293B;">✈️ {flights.get('airport_route', 'Airport Corridor')}</h4>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">🚗 {flights.get('distance_to_airport', 'Drive to airport')}</div>
            <div style="margin-top: 12px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div class="cost-box">
                    <div class="cost-label">⏱️ Flight Duration</div>
                    <div class="cost-val" style="font-size: 1.05rem;">{flights.get('duration', '2h 20m')}</div>
                </div>
                <div class="cost-box cost-total-box">
                    <div class="cost-label">💵 Price Range</div>
                    <div class="cost-val" style="font-size: 1.05rem;">{flights.get('price_range', '₹4,500 - ₹9,000')}</div>
                </div>
            </div>
            <div style="margin-top: 12px; font-size: 0.9rem; color: #334155;">
                <b>Operating Airlines:</b> {", ".join(flights.get('airlines', []))}
            </div>
            <div style="font-size: 0.88rem; color: #64748B; margin-top: 6px;">
                💡 <b>Traveler Note:</b> {flights.get('notes', 'Advance booking yields substantial savings.')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. BUSES
    with t_tab3:
        buses = transit_data.get("buses", {})
        st.markdown(f"""
        <div class="transit-mode-card">
            <h4 style="margin: 0; color: #1E293B;">🚌 {buses.get('service_type', 'Intercity AC Sleeper Coaches')}</h4>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">🛣️ {buses.get('route_breakdown', 'Highway corridor')}</div>
            <div style="margin-top: 12px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
                <div class="cost-box">
                    <div class="cost-label">⏱️ Total Transit Time</div>
                    <div class="cost-val" style="font-size: 1.05rem;">{buses.get('duration', '30-35 hours')}</div>
                </div>
                <div class="cost-box">
                    <div class="cost-label">🎟️ Estimated Fare</div>
                    <div class="cost-val" style="font-size: 1.05rem;">{buses.get('fare_range', '₹2,400 - ₹4,200')}</div>
                </div>
            </div>
            <div style="margin-top: 12px; font-size: 0.9rem; color: #334155;">
                <b>Popular Operators:</b> {", ".join(buses.get('operators', []))}
            </div>
            <div style="font-size: 0.88rem; color: #64748B; margin-top: 6px;">
                ℹ️ {buses.get('notes', 'Recommended with an overnight stopover.')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 4. INLAND WATERWAYS / FERRIES
    with t_tab4:
        water = transit_data.get("waterways", {})
        is_feas = water.get("is_feasible", False)
        feas_badge = "✅ Operationally Feasible" if is_feas else "❌ Direct Route Not Feasible"
        badge_cls = "badge-budget" if is_feas else "badge-luxury"

        st.markdown(f"""
        <div class="transit-mode-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1E293B;">🚢 Inland Waterways Feasibility Assessment</h4>
                <span class="badge {badge_cls}">{feas_badge}</span>
            </div>
            <div class="water-callout">
                {water.get('feasibility_assessment', 'Direct inland waterway transport is not feasible between these points.')}
            </div>
            <div style="margin-top: 14px; font-size: 0.92rem; color: #0F172A;">
                <b>🌊 Local Water Experiences & Ferries:</b><br/>
                <span style="color: #475569;">{water.get('local_water_experiences', 'Local boating and cruises available at destination.')}</span>
            </div>
            <div style="margin-top: 10px; font-size: 0.9rem; color: #0369A1;">
                <b>💡 Recommended Route Alternative:</b> {water.get('recommended_alternative', 'Fast trains or non-stop flights.')}
            </div>
        </div>
        """, unsafe_allow_html=True)
