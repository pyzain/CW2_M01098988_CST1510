# app/cybersec_dashboard/app.py
import streamlit as st
import pandas as pd
from app.common.database_manager import DB_PATH
import sqlite3

def load_incidents():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM cyber_incidents LIMIT 1000", conn)
    conn.close()
    return df

def main():
    st.title("CyberSec — Alerting Tool")
    df = load_incidents()
    st.write(df.head())
    st.line_chart(df['severity'].value_counts())

if __name__ == "__main__":
    main()
