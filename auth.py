import hashlib
import os
from typing import Optional, Tuple, Dict, Any
import database as db

try:
    import streamlit as st
except ImportError:
    st = None


SALT = "SnapTrip_AI_Salt_2026_Secure"

def hash_password(password: str) -> str:
    """Hashes password with salt using SHA-256."""
    salted = f"{SALT}:{password}"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plain password against the stored hash."""
    return hash_password(password) == hashed

def register_user(username: str, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Registers a new user."""
    if not username or len(username.strip()) < 3:
        return False, "Username must be at least 3 characters.", None
    if not email or "@" not in email:
        return False, "Please enter a valid email address.", None
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters.", None

    if db.get_user_by_username(username):
        return False, "Username is already taken.", None
    if db.get_user_by_email(email):
        return False, "Email is already registered.", None

    hashed = hash_password(password)
    user_id = db.create_user(username, email, hashed)
    if not user_id:
        return False, "Failed to create user account. Try another username.", None

    user = db.get_user_by_id(user_id)
    return True, "Account created successfully!", user

def authenticate_user(username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Authenticates a user by username or email."""
    if not username_or_email or not password:
        return False, "Please provide username/email and password.", None

    identifier = username_or_email.strip()
    user = db.get_user_by_email(identifier)
    if not user:
        user = db.get_user_by_username(identifier)

    if not user:
        return False, "User not found.", None

    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password.", None

    return True, "Login successful!", user

def init_auth_session():
    """Initializes Streamlit session state for auth."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "is_guest" not in st.session_state:
        st.session_state.is_guest = False

def login_user(user: Dict[str, Any]):
    st.session_state.user = user
    st.session_state.is_guest = False

def enable_guest_mode():
    # Ensure guest user exists in DB
    guest_user = db.get_user_by_username("guest_traveler")
    if not guest_user:
        guest_id = db.create_user("guest_traveler", "guest@snaptrip.ai", hash_password("guest1234"))
        guest_user = db.get_user_by_id(guest_id)
    st.session_state.user = guest_user
    st.session_state.is_guest = True

def logout_user():
    st.session_state.user = None
    st.session_state.is_guest = False
    if "active_trip_id" in st.session_state:
        del st.session_state.active_trip_id

def get_current_user() -> Optional[Dict[str, Any]]:
    return st.session_state.get("user")

def is_authenticated() -> bool:
    return st.session_state.get("user") is not None
