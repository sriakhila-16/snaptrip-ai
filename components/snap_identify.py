import streamlit as st
import os
import io
import base64
from PIL import Image
from typing import Optional, Dict, Any

from gemini_service import analyze_landmark_gemini
import database as db
from auth import get_current_user

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

def load_sample_image(filename: str) -> Optional[bytes]:
    filepath = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return f.read()
    return None

def render_snap_and_identify(active_trip: Optional[Dict[str, Any]] = None, custom_gemini_key: Optional[str] = None, **kwargs):
    if custom_gemini_key is None:
        custom_gemini_key = st.session_state.get("custom_gemini_key")

    st.markdown("### 📸 Snap & Identify Landmark")
    st.markdown("Snap or upload a photo of any landmark, temple, monument, or attraction to get instant AI identification, budget breakdown, and nearby recommendations.")

    user = get_current_user()
    if not user:
        st.warning("Please sign in or continue as Guest to scan landmarks.")
        return

    # Image source tabs
    source_tab1, source_tab2, source_tab3 = st.tabs(["📁 Upload Photo", "📷 Live Camera Snap", "🌟 Sample Landmark Photos"])

    image_bytes = None
    image_name = "uploaded_photo.jpg"

    with source_tab1:
        uploaded_file = st.file_uploader("Upload landmark image (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"], key="landmark_uploader")
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            image_name = uploaded_file.name

    with source_tab2:
        camera_photo = st.camera_input("Take a photo of the landmark", key="landmark_camera")
        if camera_photo is not None:
            image_bytes = camera_photo.getvalue()
            image_name = "camera_snapshot.jpg"

    with source_tab3:
        st.markdown("Select a sample landmark to test immediately without uploading:")
        sample_cols = st.columns(4)
        with sample_cols[0]:
            if st.button("🇮🇳 India Gate (Delhi)", use_container_width=True):
                st.session_state.active_sample = "sample_delhi_india_gate.jpg"
                st.session_state.sample_city_override = "Delhi, India"
        with sample_cols[1]:
            if st.button("🏛️ Taj Mahal (Agra)", use_container_width=True):
                st.session_state.active_sample = "sample_taj_mahal.jpg"
                st.session_state.sample_city_override = "Agra, India"
        with sample_cols[2]:
            if st.button("🗼 Eiffel Tower (Paris)", use_container_width=True):
                st.session_state.active_sample = "sample_eiffel_tower.jpg"
                st.session_state.sample_city_override = "Paris, France"
        with sample_cols[3]:
            if st.button("🏟️ Colosseum (Rome)", use_container_width=True):
                st.session_state.active_sample = "sample_colosseum.jpg"
                st.session_state.sample_city_override = "Rome, Italy"

        if "active_sample" in st.session_state:
            image_bytes = load_sample_image(st.session_state.active_sample)
            image_name = st.session_state.active_sample

    # Image Preview & Analysis Action
    if image_bytes is not None:
        st.divider()
        col_img, col_act = st.columns([1, 1])

        with col_img:
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                st.image(pil_image, caption=f"Selected: {image_name}", use_container_width=True)
            except Exception:
                st.warning("Could not render image preview.")

        with col_act:
            dest_city = active_trip["destination_city"] if active_trip else "Delhi, India"
            if "sample_city_override" in st.session_state and "active_sample" in st.session_state:
                dest_city = st.session_state.sample_city_override

            origin_city = active_trip.get("origin_city", "Guntur, Andhra Pradesh") if active_trip else "Guntur, Andhra Pradesh"
            budget_type = active_trip["budget_tier"] if active_trip else "Moderate"
            curr = active_trip["currency"] if active_trip else "INR"
            days = active_trip["duration_days"] if active_trip else 3
            daily_limit = float(active_trip["daily_budget_limit"]) if active_trip else 4500.0

            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 12px;">
                <div style="font-weight: 700; color: #1E293B; margin-bottom: 6px;">📍 Active Trip Route Context:</div>
                <div style="font-size: 0.9rem; color: #475569;">• 🏠 Origin: <b>{origin_city}</b></div>
                <div style="font-size: 0.9rem; color: #475569;">• 🎯 Destination: <b>{dest_city}</b></div>
                <div style="font-size: 0.9rem; color: #475569;">• ⏳ Duration: <b>{days} Days</b> | Tier: <b>{budget_type}</b></div>
                <div style="font-size: 0.9rem; color: #0284C7;">• 💰 Daily Budget Allowance: <b>{curr} {daily_limit:,.2f}</b></div>
            </div>
            """, unsafe_allow_html=True)

            analyze_btn = st.button("✨ Identify Landmark & Calculate Budget", type="primary", use_container_width=True)

        if analyze_btn:
            with st.spinner("🤖 Gemini Vision AI is analyzing landmark architecture & calculating visit expenses..."):
                try:
                    mime = "image/jpeg"
                    if image_name.endswith(".png"):
                        mime = "image/png"
                    elif image_name.endswith(".webp"):
                        mime = "image/webp"

                    result = analyze_landmark_gemini(
                        image_bytes=image_bytes,
                        mime_type=mime,
                        destination_city=dest_city,
                        origin_city=origin_city,
                        budget_type=budget_type,
                        duration_days=days,
                        currency=curr,
                        api_key=custom_gemini_key
                    )
                    st.session_state.last_analysis = result
                    st.session_state.last_image_bytes = image_bytes
                    st.success("🎉 Landmark identified successfully!")
                except Exception as err:
                    st.error(f"Error during AI analysis: {err}")


    # Render Analysis Results
    if "last_analysis" in st.session_state and st.session_state.last_analysis:
        analysis = st.session_state.last_analysis
        costs = analysis.get("estimated_costs", {})
        curr = costs.get("currency", active_trip["currency"] if active_trip else "USD")

        st.markdown("---")
        st.markdown(f"""
        <div class="landmark-header-card">
            <span class="badge badge-{'luxury' if (active_trip and active_trip['budget_tier']=='Luxury') else 'budget'}">
                {active_trip['budget_tier'] if active_trip else 'Moderate'} Travel Tier
            </span>
            <div class="landmark-name">📍 {analysis.get('landmark_name', 'Landmark')}</div>
            <div class="landmark-loc">🌍 {analysis.get('location', 'Global Location')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Tabs for result sections
        res_tab1, res_tab2, res_tab3 = st.tabs(["📜 History & Cultural Significance", "💰 Visit Cost Breakdown", "🗺️ Nearby Recommendations"])

        with res_tab1:
            st.markdown("#### Key Historical Facts & Significance")
            for pt in analysis.get("history_and_significance", []):
                st.markdown(f"- 🏛️ {pt}")

            if analysis.get("insider_tips"):
                st.markdown("#### 💡 Tourist Insider Tips")
                for tip in analysis.get("insider_tips", []):
                    st.markdown(f"- ⚡ {tip}")

        with res_tab2:
            st.markdown("#### Estimated Visit Expenses")
            c_tick = costs.get("ticket_fee", 0.0)
            c_trans = costs.get("local_transport", 0.0)
            c_food = costs.get("food_snacks", 0.0)
            c_total = costs.get("total_estimate", c_tick + c_trans + c_food)

            st.markdown(f"""
            <div class="cost-grid">
                <div class="cost-box">
                    <div class="cost-label">🎟️ Tickets & Entry</div>
                    <div class="cost-val">{curr} {c_tick:,.2f}</div>
                </div>
                <div class="cost-box">
                    <div class="cost-label">🚕 Local Transit</div>
                    <div class="cost-val">{curr} {c_trans:,.2f}</div>
                </div>
                <div class="cost-box">
                    <div class="cost-label">🥪 Food & Snacks</div>
                    <div class="cost-val">{curr} {c_food:,.2f}</div>
                </div>
                <div class="cost-box cost-total-box">
                    <div class="cost-label">💵 Total Visit Cost</div>
                    <div class="cost-val">{curr} {c_total:,.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if costs.get("notes"):
                st.info(f"ℹ️ **Cost Notes:** {costs['notes']}")

            # Daily Budget Impact Tracker
            if active_trip:
                daily_limit = float(active_trip["daily_budget_limit"])
                remaining_today = daily_limit - c_total
                impact_color = "#10B981" if remaining_today >= 0 else "#EF4444"
                status_text = "Within daily limit" if remaining_today >= 0 else "Exceeds daily target!"

                st.markdown(f"""
                <div class="budget-status-box">
                    <strong>💳 Daily Budget Impact Analysis:</strong><br/>
                    • Daily Spending Allowance: <b>{curr} {daily_limit:,.2f}</b><br/>
                    • This Landmark Cost: <b>-{curr} {c_total:,.2f}</b><br/>
                    • Remaining for Rest of Day: <b style="color: {impact_color};">{curr} {remaining_today:,.2f}</b> ({status_text})
                </div>
                """, unsafe_allow_html=True)

        with res_tab3:
            st.markdown("#### 3 Recommended Next Stops")
            st.caption(f"Tailored to your remaining trip duration and {active_trip['budget_tier'] if active_trip else 'Moderate'} budget:")

            attractions = analysis.get("nearby_attractions", [])
            for att in attractions:
                st.markdown(f"""
                <div class="spot-card">
                    <div class="spot-title">
                        <span>🏛️ {att.get('name', 'Attraction')}</span>
                        <span class="spot-dist">📏 {att.get('distance', 'Nearby')}</span>
                    </div>
                    <div class="spot-desc"><b>Highlights:</b> {att.get('highlights', '')}</div>
                    <div class="spot-desc"><b>Why Recommended:</b> {att.get('why_recommended', '')}</div>
                    <div class="spot-cost">💰 Estimated Cost: {curr} {float(att.get('estimated_cost', 0)):,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        # Save to Itinerary Button
        st.markdown("---")
        save_col1, save_col2 = st.columns([2, 1])
        with save_col1:
            st.write("Save this landmark scan and budget breakdown to your trip itinerary:")
        with save_col2:
            if st.button("📌 Add to My Trip Itinerary", type="primary", use_container_width=True):
                # Save into database
                trip_id = active_trip["id"] if active_trip else None
                img_b64 = None
                if "last_image_bytes" in st.session_state:
                    img_b64 = base64.b64encode(st.session_state.last_image_bytes).decode("utf-8")

                scan_id = db.save_landmark_scan(
                    user_id=user["id"],
                    trip_id=trip_id,
                    landmark_name=analysis.get("landmark_name", "Landmark"),
                    location=analysis.get("location", ""),
                    history_points=analysis.get("history_and_significance", []),
                    ticket_cost=c_tick,
                    transport_cost=c_trans,
                    food_cost=c_food,
                    total_cost=c_total,
                    currency=curr,
                    nearby_attractions=analysis.get("nearby_attractions", []),
                    local_tips=analysis.get("insider_tips", []),
                    image_data=img_b64
                )
                st.success(f"✅ Added '{analysis.get('landmark_name')}' to your itinerary! View it in the 'My Saved Itinerary' tab.")

