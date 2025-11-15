# app/it_monitoring/app.py
import streamlit as st
import pandas as pd
from app.common.database_manager import DB_PATH
import sqlite3

def load_tickets():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM it_tickets LIMIT 1000", conn)
    conn.close()
    return df

def main():
    st.title("IT — API Monitoring Dashboard")
    df = load_tickets()
    st.write(df.head())
    st.table(df[['ticket_id','status','priority']].head(20))

if __name__ == "__main__":
    main()
