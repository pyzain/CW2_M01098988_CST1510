# pages/Home.py
# pages/Home.py
"""
Home page: login / register. Called by main_app.py and passed an AuthManager.
"""

import streamlit as st


# Safe rerun helper
def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.rerun()


def render(auth):
    st.title("Multi-Domain Platform Login")

    # If user already logged in
    if st.session_state.get("user"):
        st.success(f"Logged in as {st.session_state.user.get_username()}")
        st.write("Use the navigation menu on the left to access your dashboard.")
        return

    # Tabs for Login / Register
    tabs = st.tabs(["Login", "Register"])

    # --------------------
    # LOGIN TAB
    # --------------------
    with tabs[0]:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            user = auth.login_user(username, password)
            if user:
                st.session_state.user = user
                st.success("Login successful — redirecting...")
                _safe_rerun()
            else:
                st.error("Invalid username or password")

    # --------------------
    # REGISTER TAB
    # --------------------
    with tabs[1]:
        st.subheader("Register")
        new_user = st.text_input("New username", key="reg_username")
        new_pass = st.text_input("New password", type="password", key="reg_password")

        if st.button("Register"):
            try:
                auth.register_user(new_user, new_pass)
                st.success("Account created — please login.")
            except Exception as e:
                st.error(str(e))
