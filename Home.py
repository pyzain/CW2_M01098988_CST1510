import streamlit as st

# 1️⃣ Import DB initializer
from database.db_initializer import init_database

# 2️⃣ Import services
from app.services.database_manager import DatabaseManager
from app.services.auth_manager import AuthManager


# ------------------ INITIALISE DATABASE ------------------
init_database()

# ------------------ INITIALISE AUTH + DB ------------------
db = DatabaseManager()
auth = AuthManager(db)


# ------------------ STREAMLIT UI ------------------
st.title("🔐 Multi-Domain Platform Login")

if "user" not in st.session_state:
    tabs = st.tabs(["Login", "Register"])

    # LOGIN TAB
    with tabs[0]:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = auth.login_user(username, password)
            if user:
                st.session_state.user = user
                st.success("Login successful!")
            else:
                st.error("Invalid username or password")

    # REGISTER TAB
    with tabs[1]:
        st.subheader("Create Account")
        new_user = st.text_input("New Username", key="register_user")
        new_pass = st.text_input("New Password", type="password", key="register_pass")

        if st.button("Register"):
            try:
                auth.register_user(new_user, new_pass)
                st.success("Account created! Please login.")
            except Exception:
                st.error("Username already exists")

else:
    st.subheader(f"Welcome, {st.session_state.user.get_username()}")
    st.write("Select a domain dashboard:")

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    if c1.button("🛡 Cybersecurity"):
        st.session_state.page = "Cybersecurity"
    if c2.button("💻 IT Operations"):
        st.session_state.page = "IT_Operations"
    if c3.button("📊 Data Science"):
        st.session_state.page = "Data_Science"
    if c4.button("🤖 AI Assistant"):
        st.session_state.page = "AI_Assistant"

    if "page" in st.session_state:
        page = st.session_state.page
        try:
            if page == "Cybersecurity":
                from pages.Cybersecurity import CyberDashboard
                CyberDashboard().render()
            elif page == "IT_Operations":
                from pages.IT_Operations import ITOperationsDashboard
                ITOperationsDashboard().render()
            elif page == "Data_Science":
                from pages.Data_Science import DataScienceDashboard
                DataScienceDashboard().render()
            elif page == "AI_Assistant":
                from pages.AI_Assistant import AIAssistantDashboard
                AIAssistantDashboard().render()
        except Exception as e:
            st.error(f"Error loading {page}: {e}")
