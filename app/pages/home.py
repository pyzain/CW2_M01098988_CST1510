"""
Unified Home + Login file.
Replaces previous separate Login.py / home.py files.
Exposes login_page(), main(), render() for orchestrator compatibility.
Uses app.common.auth_cli (DB-backed when available, falls back to users.txt).
"""

import streamlit as st
from typing import Tuple

# auth adapter (keeps behavior consistent with earlier code)
from app.common.auth_cli import verify_password, register_user

# NEW: import central navigation helper
from app.common.navigation import navigate

# Users
from app.data.users import get_user_by_username


# ---------- Helpers ----------
def safe_rerun():
    """Backward-compatible rerun."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def _init_session():
    """Ensure session-state keys exist."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""


# ---------- Core UI: Login / Register ----------
def _login_ui() -> None:
    st.subheader("Login")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log in", type="primary"):
        if not username or not password:
            st.warning("Enter both username and password.")
            return

        try:
            ok, msg = verify_password(username, password)
        except Exception:
            st.error("Authentication error. Check server logs.")
            return

        if ok:
            st.session_state.logged_in = True
            st.session_state.username = username

            # <-- fetch role from database -->
            user_row = get_user_by_username(username)
            st.session_state.role = user_row["role"] if user_row else "user"

            st.success(msg or f"Welcome back, {username}!")
            navigate("Dashboard")  # INSTANT redirect
        else:
            st.error(msg or "Login failed.")


def _register_ui() -> None:
    st.subheader("Register")

    new_username = st.text_input("Choose a username", key="register_username")
    new_password = st.text_input("Choose a password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm password", type="password", key="register_confirm")

    if st.button("Create account"):
        if not new_username or not new_password:
            st.warning("Please fill in all fields.")
            return
        if new_password != confirm_password:
            st.error("Passwords do not match.")
            return

        try:
            ok, msg = register_user(new_username, new_password)
        except Exception:
            st.error("Registration error. Check server logs.")
            return

        if ok:
            st.success(msg or f"Account created for {new_username}.")
            st.session_state.logged_in = True
            st.session_state.username = new_username

            # <-- Default role for new user -->
            st.session_state.role = "user"

            navigate("Dashboard")  # auto redirect after register
        else:
            st.error(msg or "Registration failed.")


# ---------- Page Rendering ----------
def login_page():
    """Primary entrypoint for the login page UI."""
    st.set_page_config(page_title="Login / Register", page_icon="🔐", layout="centered")
    _init_session()

    st.title("🔐 Welcome")

    # Already logged in
    if st.session_state.logged_in:
        st.success(f"You are logged in as **{st.session_state.username}**.")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Go to Dashboard"):
                navigate("Dashboard")

        with col2:
            if st.button("Log out"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.info("Logged out.")
                navigate("Home")

        return

    # Tabs for Login / Register
    tab_login, tab_register = st.tabs(["Login", "Register"])
    with tab_login:
        _login_ui()
    with tab_register:
        _register_ui()


def main():
    login_page()


def render():
    login_page()


__all__ = ["login_page", "main", "render"]
