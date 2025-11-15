import streamlit as st
import pandas as pd

def cyber_dashboard():
    st.title("Cybersecurity Dashboard")

    st.write("This is a sample Cybersecurity dashboard.")

    # Example: show sample CSV data
    try:
        df = pd.read_csv("DATA/cyber_incidents.csv")
        st.write("Incidents Data:")
        st.dataframe(df)
    except FileNotFoundError:
        st.warning("cyber_incidents.csv not found in DATA folder.")
