from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "SnapTrip AI is running!"

# --- Your existing Streamlit code starts below this line ---import streamlit as st
import os
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Streamlit Page Config - Must be called first
st.set_page_config(
    page_title="SnapTrip AI — Smart Travel Companion",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import database as db
import auth
from components.styles import apply_custom_styles
from components.trip_dashboard import render_trip_dashboard
from components.snap_identify import render_snap_and_identify
from components.itinerary_view import render_itinerary_view
from components.profile_view import render_profile_view
from gemini_service import get_api_key

def main():
    # Apply modern glassmorphism CSS
    apply_custom_styles()

    # Initialize authentication session
    auth.init_auth_session()

    # Default to Guest Mode if no session exists so user can immediately test
    if not auth.is_authenticated():
        auth.enable_guest_mode()

    current_user = auth.get_current_user()

    # ----------------- SIDEBAR -----------------
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            <span style="font-size: 2rem;">📸✈️</span>
            <div>
                <h2 style="margin: 0; font-size: 1.4rem; font-weight: 800; background: linear-gradient(90deg, #FF6B6B, #4ECDC4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">SnapTrip AI</h2>
                <span style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">Smart Travel Companion</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User Authentication Panel
        st.markdown("#### 🔐 Traveler Profile")
        if current_user and not st.session_state.get("is_guest", False):
            st.success(f"Signed in as **{current_user['username']}**")
            if st.button("Sign Out", use_container_width=True):
                auth.logout_user()
                st.rerun()
        else:
            with st.expander("👤 Account Login / Register", expanded=False):
                auth_tab1, auth_tab2 = st.tabs(["Sign In", "Sign Up"])
                with auth_tab1:
                    with st.form("login_form"):
                        log_user = st.text_input("Username or Email")
                        log_pass = st.text_input("Password", type="password")
                        submit_login = st.form_submit_button("Sign In", use_container_width=True)
                        if submit_login:
                            ok, msg, usr = auth.authenticate_user(log_user, log_pass)
                            if ok:
                                auth.login_user(usr)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                with auth_tab2:
                    with st.form("signup_form"):
                        reg_user = st.text_input("Choose Username")
                        reg_email = st.text_input("Email Address")
                        reg_pass = st.text_input("Password (min 6 chars)", type="password")
                        submit_signup = st.form_submit_button("Create Account", use_container_width=True)
                        if submit_signup:
                            ok, msg, usr = auth.register_user(reg_user, reg_email, reg_pass)
                            if ok:
                                auth.login_user(usr)
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

            if st.session_state.get("is_guest", False):
                st.info("ℹ️ Exploring as **Guest Traveler** (Full features enabled!)")

        st.divider()

        # AI Vision API Configuration
        st.markdown("#### 🤖 Gemini Vision Settings")
        env_key = os.getenv("GEMINI_API_KEY", "")
        custom_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("custom_gemini_key", env_key),
            type="password",
            placeholder="AIzaSy...",
            help="Get your key at https://aistudio.google.com/"
        )
        if custom_key:
            st.session_state.custom_gemini_key = custom_key

        effective_key = get_api_key(st.session_state.get("custom_gemini_key"))
        if effective_key:
            st.caption("🟢 **AI Vision Live:** Connected to Google Gemini Flash")
        else:
            st.caption("🟡 **Demo Mode:** Simulating AI Vision recognition for famous landmarks. Enter an API key above for live multimodal AI.")

        st.divider()
        st.markdown("""
        <div style="font-size: 0.8rem; color: #64748B;">
            <b>How to use:</b><br/>
            1. Set your destination & budget in <b>Trip Setup</b>.<br/>
            2. Snap or upload a landmark photo in <b>Snap & Identify</b>.<br/>
            3. Review history, budget impact, and nearby attractions.<br/>
            4. Save to your interactive <b>Trip Itinerary</b>!
        </div>
        """, unsafe_allow_html=True)

    # ----------------- MAIN CONTENT -----------------

    # Hero Banner
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">SnapTrip AI 🗺️</h1>
        <div class="hero-subtitle">
            Your intelligent local travel companion. Snap any landmark to unlock historical secrets, visit cost breakdowns, and tailored nearby spots within your budget.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main Tabs Navigation
    tab_setup, tab_snap, tab_itinerary, tab_profile = st.tabs([
        "⚙️ Trip Setup & Budget",
        "📸 Snap & Identify",
        "🗺️ My Saved Itinerary",
        "👤 Traveler Profile"
    ])

    effective_key = get_api_key(st.session_state.get("custom_gemini_key"))
    active_trip = None

    with tab_setup:
        active_trip = render_trip_dashboard()
        active_trip = render_trip_dashboard(custom_gemini_key=effective_key)

    with tab_snap:
        # Load active trip for context
        if not active_trip and current_user:
            user_trips = db.get_user_trips(current_user["id"])
            if user_trips:
                active_id = st.session_state.get("active_trip_id", user_trips[0]["id"])
                active_trip = db.get_trip_by_id(active_id)

        effective_key = get_api_key(st.session_state.get("custom_gemini_key"))
        render_snap_and_identify(active_trip, custom_gemini_key=effective_key)


    with tab_itinerary:
        if not active_trip and current_user:
            user_trips = db.get_user_trips(current_user["id"])
            if user_trips:
                active_id = st.session_state.get("active_trip_id", user_trips[0]["id"])
                active_trip = db.get_trip_by_id(active_id)
        render_itinerary_view(active_trip)

    with tab_profile:
        render_profile_view()

if __name__ == "__main__":
    main()

