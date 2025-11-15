# app/pages/Login.py
import streamlit as st
from app.common.auth_cli import verify_password, register_user

def safe_rerun():
    """Use the correct rerun function depending on Streamlit version."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def login_page():
    st.title("Login")

    # initialize session state keys
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "login_msg" not in st.session_state:
        st.session_state.login_msg = ""

    menu = ["Login", "Register"]
    choice = st.radio("Select an option", menu)

    if choice == "Login":
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if not username or not password:
                st.warning("Please enter username and password")
            else:
                ok, msg = verify_password(username, password)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(msg or f"Logged in as {username}")
                    safe_rerun()
                else:
                    st.error(msg)

    elif choice == "Register":
        st.subheader("Create a New Account")
        new_username = st.text_input("New Username", key="reg_user")
        new_password = st.text_input("New Password", type="password", key="reg_pass")

        if st.button("Register"):
            if not new_username or not new_password:
                st.warning("Please enter username and password for registration")
            else:
                success, message = register_user(new_username, new_password)
                if success:
                    st.success(message)
                    st.session_state.logged_in = True
                    st.session_state.username = new_username
                    safe_rerun()
                else:
                    st.error(message)
