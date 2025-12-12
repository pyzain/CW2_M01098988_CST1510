# main_app.py
import streamlit as st
from PIL import Image

from app.services.database_manager import DatabaseManager
from app.services.auth_manager import AuthManager
from database.db_initializer import init_database

# ----------------------------
# Page config + App Icon
# ----------------------------
icon = Image.open("img/app_icon.png")

st.set_page_config(
    page_title="MDI Platform",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# When a fresh clone runs → database + CSV data load automatically
init_database()

# Utility for reruns
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# Hide Streamlit default menu
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize DB + managers
_db = DatabaseManager()
_auth = AuthManager(_db)

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Home"

# -------------------------
# DEFINE PAGES
# -------------------------
# Default available pages
PAGES = ["Home", "Cybersecurity", "Data Science", "IT Operations", "AI Assistant"]

# DYNAMIC NAVIGATION:
# Check if a user is logged in AND is an admin
if st.session_state.user and st.session_state.user.get_role() == "admin":
    PAGES.append("Admin Panel")

# -------------------------
# SIDEBAR NAVIGATION
# -------------------------
with st.sidebar:
    st.title("Navigation")

    # Safety check: if user logs out while on Admin page, reset to Home
    if st.session_state.page not in PAGES:
        st.session_state.page = "Home"

    selected_page = st.selectbox("Go to page:", PAGES, index=PAGES.index(st.session_state.page))
    st.session_state.page = selected_page

    st.write("---")

    if st.session_state.user:
        st.write(f"Signed in: **{st.session_state.user.get_username()}**")
        st.caption(f"Role: {st.session_state.user.get_role()}")

        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "Home"
            safe_rerun()
    else:
        st.info("Not signed in")

# Header
st.markdown("<div style='padding:8px;'><h2>MDI Unified Intelligence Platform</h2></div>", unsafe_allow_html=True)

# -------------------------
# PAGE ROUTING
# -------------------------
page = st.session_state.page

if page == "Home":
    from pages.Home import render as home

    home(_auth)

elif page == "Cybersecurity":
    from pages.Cybersecurity import render as cyber

    cyber()

elif page == "Data Science":
    from pages.Data_Science import render as ds

    ds()

elif page == "IT Operations":
    from pages.IT_Operations import render as itops

    itops()

elif page == "AI Assistant":
    from pages.AI_Assistant import render as ai

    ai()

elif page == "Admin Panel":
    # Import the admin page and inject dependencies
    from pages import users_admin

    # Pass the _db and _auth instances we created at the top
    users_admin.render(_db, _auth)