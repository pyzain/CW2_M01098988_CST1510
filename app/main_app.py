# app/main_app.py

import sys
import os
import streamlit as st

# ------------------------------
# Fix Python imports for multi-folder project
# ------------------------------
# Add project root to sys.path so 'app' is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ------------------------------
# Import your modules
# ------------------------------
from app.pages.Login import login_page
from app.pages.Dashboard_Cyber import cyber_dashboard
from app.pages.Dashboard_Data import data_dashboard
from app.pages.Dashboard_IT import it_dashboard

# ------------------------------
# Main Orchestrator
# ------------------------------
def main():
    st.set_page_config(page_title="Multi-Domain Intelligence Platform", layout="wide")

    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'role' not in st.session_state:
        st.session_state.role = ""

    # ------------------------------
    # Login page
    # ------------------------------
    if not st.session_state.logged_in:
        login_page()
    else:
        # --------------------------
        # Dashboard selection (can be automatic based on role)
        # --------------------------
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        st.sidebar.write("Select Dashboard:")

        dashboard_choice = st.sidebar.radio(
            "Choose Domain",
            ("Cybersecurity", "Data Science", "IT Operations")
        )

        if dashboard_choice == "Cybersecurity":
            cyber_dashboard()
        elif dashboard_choice == "Data Science":
            data_dashboard()
        elif dashboard_choice == "IT Operations":
            it_dashboard()

# ------------------------------
# Entry point
# ------------------------------
if __name__ == "__main__":
    main()