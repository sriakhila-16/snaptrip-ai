import streamlit as st
import base64
import database as db
from auth import get_current_user, logout_user

def render_profile_view():
    st.markdown("### 👤 User Profile & Travel Dashboard")

    user = get_current_user()
    if not user:
        st.warning("Please sign in or continue as Guest to view your profile.")
        return

    is_guest = st.session_state.get("is_guest", False)

    # User Profile Header
    with st.container():
        col_avatar, col_details = st.columns([1, 4])
        with col_avatar:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4ECDC4, #556270); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.2rem; color: white; margin: 0 auto;">
                {user['username'][0].upper()}
            </div>
            """, unsafe_allow_html=True)
        with col_details:
            badge_text = "Guest Traveler" if is_guest else "Registered Explorer"
            badge_class = "badge-budget" if is_guest else "badge-luxury"
            st.markdown(f"""
            <h3 style="margin: 0;">{user['username']}</h3>
            <span class="badge {badge_class}">{badge_text}</span>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">📧 {user['email']}</div>
            """, unsafe_allow_html=True)

    st.divider()

    # Lifetime Travel Statistics
    trips = db.get_user_trips(user["id"])
    all_scans = db.get_user_scans(user["id"])

    total_trips = len(trips)
    total_scans = len(all_scans)
    total_spent = sum(s["total_cost"] for s in all_scans)
    total_budget_planned = sum(t["duration_days"] * t["daily_budget_limit"] for t in trips)

    st.markdown("#### 🌟 Lifetime Travel Statistics")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Trips", total_trips)
    with c2:
        st.metric("Landmarks Scanned", total_scans)
    with c3:
        st.metric("Total Spending", f"${total_spent:,.2f}")
    with c4:
        st.metric("Total Budget Tracked", f"${total_budget_planned:,.2f}")

    st.divider()

    # Tabs for Scans History and Trips Management
    tab_scans, tab_trips = st.tabs(["📸 Previous Landmark Scans", "🧳 Managed Trips"])

    with tab_scans:
        if not all_scans:
            st.info("No landmark scans yet. Head over to 'Snap & Identify' to scan your first landmark!")
        else:
            for s in all_scans:
                with st.expander(f"📍 {s['landmark_name']} ({s['location']}) - ${s['total_cost']:,.2f}", expanded=False):
                    col_s1, col_s2 = st.columns([1, 2])
                    with col_s1:
                        if s.get("image_data"):
                            try:
                                b_data = base64.b64decode(s["image_data"])
                                st.image(b_data, use_container_width=True)
                            except Exception:
                                st.write("🖼️ Landmark Photo")
                    with col_s2:
                        st.markdown(f"**Date Visited:** {s['scanned_at']}")
                        st.markdown(f"**Total Cost:** {s['currency']} {s['total_cost']:,.2f}")
                        st.markdown(f"- 🎟️ Tickets: {s['currency']} {s['ticket_cost']:,.2f}")
                        st.markdown(f"- 🚕 Transit: {s['currency']} {s['transport_cost']:,.2f}")
                        st.markdown(f"- 🥪 Food: {s['currency']} {s['food_cost']:,.2f}")
                        if s.get("history_points"):
                            st.markdown("**Historical Highlights:**")
                            for h in s["history_points"]:
                                st.markdown(f"* {h}")

    with tab_trips:
        if not trips:
            st.info("No trips created yet.")
        else:
            for t in trips:
                col_t1, col_t2, col_t3 = st.columns([3, 1, 1])
                with col_t1:
                    st.markdown(f"**{t['trip_name']}** — 📍 {t['destination_city']} ({t['duration_days']} Days)")
                    st.caption(f"Tier: {t['budget_tier']} | Daily Limit: {t['currency']} {t['daily_budget_limit']:,.2f}")
                with col_t2:
                    if st.button("Select Trip", key=f"sel_trip_{t['id']}", use_container_width=True):
                        st.session_state.active_trip_id = t["id"]
                        st.success(f"Switched active trip to '{t['trip_name']}'")
                        st.rerun()
                with col_t3:
                    if st.button("Delete", key=f"del_trip_{t['id']}", use_container_width=True):
                        db.delete_trip(t["id"])
                        st.success("Deleted trip.")
                        st.rerun()

    st.divider()
    if st.button("🚪 Sign Out", use_container_width=False):
        logout_user()
        st.success("Signed out.")
        st.rerun()

