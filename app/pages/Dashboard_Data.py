import streamlit as st
from app.common.database_manager import DatabaseManager
import pandas as pd
import plotly.express as px

def data_dashboard():
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()

    st.title("Data Science Dashboard")

    db = DatabaseManager()
    db.connect()
    df = pd.read_sql("SELECT * FROM datasets_metadata", db.conn)
    db.close()

    fig = px.bar(
        df,
        x="dataset_name",
        y="rows",
        color="source",
        title="Dataset Overview"
    )
    st.plotly_chart(fig)

    st.write("🔹 Add more analytics and AI Assistant here (Week 10)")
