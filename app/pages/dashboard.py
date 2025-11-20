#dashboard.py
"""
Central dashboard page with buttons that route
to the domain dashboards using global navigate().
"""

import streamlit as st
from app.common.navigation import navigate  # use shared navigation helper

def main():
    st.set_page_config(page_title="Select Domain Dashboard", page_icon="📊", layout="centered")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.logged_in:
        st.error("You must be logged in to access the dashboards. Go to Home and log in.")
        return

    st.title("📊 Choose a Domain Dashboard")
    st.caption(f"Logged in as **{st.session_state.username}** — pick a dashboard to continue.")
    st.markdown("")

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        if st.button("🔒 Cybersecurity", key="btn_cyber", use_container_width=True):
            navigate("Dashboard Cyber")

    with c2:
        if st.button("📈 Data Science", key="btn_data", use_container_width=True):
            navigate("Dashboard Data")

    with c3:
        if st.button("🛠 IT Operations", key="btn_it", use_container_width=True):
            navigate("Dashboard IT")

    st.divider()
    st.write("Tip: you can also use the sidebar menu to switch dashboards.")


if __name__ == "__main__":
    main()
