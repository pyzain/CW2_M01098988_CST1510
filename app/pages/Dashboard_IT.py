# app/pages/Dashboard_IT.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from app.common.database_manager import DatabaseManager

def it_dashboard():
    # session check
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()

    st.title("IT Operations Dashboard")

    # Try to load from database first (if exists), else fallback to CSV
    df = None
    try:
        db = DatabaseManager()
        db.connect()
        # Try reading the table; if not present, this may raise or return empty
        try:
            df = pd.read_sql("SELECT * FROM it_tickets", db.conn)
        except Exception:
            # table might not exist or schema mismatch
            df = pd.DataFrame()
        db.close()
    except Exception:
        df = pd.DataFrame()

    # fallback to CSV in DATA/ if DB gave nothing
    if df is None or df.empty:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "DATA", "it_tickets.csv")
        csv_path = os.path.normpath(csv_path)
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                df = pd.DataFrame()  # remain empty
        except Exception as e:
            st.error("Failed to load IT tickets CSV: " + str(e))
            df = pd.DataFrame()

    # If still empty, show message
    if df.empty:
        st.info("No IT ticket data found. Make sure DATA/it_tickets.csv exists or the database has the it_tickets table.")
        return

    # Ensure consistent column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]

    # Show a quick data preview
    st.subheader("Recent tickets (preview)")
    st.dataframe(df.head(20))

    # Choose column to aggregate by - only non-free-text columns
    # Exclude likely long-text columns such as 'description'
    exclude = {"description", "details", "body", "message"}
    candidate_cols = [c for c in df.columns if c not in exclude]

    if not candidate_cols:
        st.error("No suitable columns available for aggregation/visualization.")
        return

    st.subheader("Interactive aggregation")
    # Let user choose the x-axis (categorical) and aggregation function
    x_col = st.selectbox("Group by (x-axis)", candidate_cols, index= candidate_cols.index("status") if "status" in candidate_cols else 0)
    agg_choice = st.selectbox("Aggregation", ["count", "unique_count"], index=0)

    # Build aggregation
    try:
        if agg_choice == "count":
            agg_df = df.groupby(x_col).size().reset_index(name="count")
            fig = px.bar(agg_df, x=x_col, y="count", title=f"Count of tickets by {x_col}")
        else:  # unique_count (example: number of unique ticket_id)
            # choose a sensible id column if exists
            id_col = "ticket_id" if "ticket_id" in df.columns else df.columns[0]
            agg_df = df.groupby(x_col)[id_col].nunique().reset_index(name="unique_count")
            fig = px.bar(agg_df, x=x_col, y="unique_count", title=f"Unique {id_col} count by {x_col}")

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Visualization error: {e}")

    # Additional: show filters and a filtered table
    st.subheader("Filter tickets")
    # build simple filters for up to two categorical columns
    filter_cols = [c for c in candidate_cols if df[c].nunique() < 50]  # avoid large cardinality
    selected_filters = {}
    for c in filter_cols[:2]:
        vals = sorted(df[c].dropna().unique().tolist())
        sel = st.multiselect(f"Filter {c}", options=vals, default=vals if len(vals) <= 5 else [])
        if sel:
            selected_filters[c] = sel

    # Apply filters
    df_filtered = df.copy()
    for c, sel in selected_filters.items():
        df_filtered = df_filtered[df_filtered[c].isin(sel)]

    st.subheader(f"Filtered tickets (showing {len(df_filtered)} rows)")
    st.dataframe(df_filtered.reset_index(drop=True).head(200))

    # Option to download filtered CSV
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered tickets CSV", csv_bytes, file_name="it_tickets_filtered.csv", mime="text/csv")