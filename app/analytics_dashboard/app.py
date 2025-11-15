# app/analytics_dashboard/app.py
import streamlit as st
import pandas as pd
from app.common.database_manager import DB_PATH
import sqlite3

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM it_tickets LIMIT 1000", conn)
    conn.close()
    return df

def main():
    st.title("Analytics Dashboard (Data Science)")
    df = load_data()
    st.write(df.head())
    st.bar_chart(df['status'].value_counts())

if __name__ == "__main__":
    main()
