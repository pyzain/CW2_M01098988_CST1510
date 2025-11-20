# app/pages/Dashboard_Data.py
import os
import streamlit as st
import pandas as pd
import plotly.express as px


def data_dashboard():
    """Data Science Dashboard (interactive & creative)."""

    # -------- Session check ----------
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        return

    st.title("📊 Data Science Dashboard")

    # -------- Load CSV ----------
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_path = os.path.join(project_root, "DATA", "datasets_metadata.csv")

    if not os.path.exists(csv_path):
        st.error(f"CSV not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    # -------- Data preprocessing ----------
    # Rename columns for consistency
    df = df.rename(columns={
        "name": "dataset_name",
        "uploaded_by": "source"
    })

    # Ensure rows and columns are numeric
    df["rows"] = pd.to_numeric(df["rows"], errors="coerce").fillna(0)
    df["columns"] = pd.to_numeric(df["columns"], errors="coerce").fillna(0)

    st.subheader("Dataset Overview")
    st.dataframe(df)

    # -------- Interactive Filters ----------
    st.sidebar.subheader("Filters")
    uploader_filter = st.sidebar.multiselect(
        "Select uploader(s):",
        options=df["source"].unique(),
        default=df["source"].unique()
    )
    df_filtered = df[df["source"].isin(uploader_filter)]

    # Optional: sort by rows
    sort_choice = st.sidebar.selectbox("Sort datasets by", ["rows", "columns", "dataset_name"], index=0)
    df_filtered = df_filtered.sort_values(by=sort_choice, ascending=False)

    # -------- Metrics ----------
    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total datasets", len(df_filtered))
    col2.metric("Total rows", int(df_filtered["rows"].sum()))
    col3.metric("Average rows per dataset", round(df_filtered["rows"].mean(), 2))

    # -------- Interactive Bar Chart ----------
    st.subheader("Rows per Dataset")
    fig = px.bar(
        df_filtered,
        x="dataset_name",
        y="rows",
        color="source",
        hover_data=["columns", "upload_date"],
        labels={"rows": "Number of Rows", "dataset_name": "Dataset Name", "source": "Uploader"},
        title="Rows per Dataset by Uploader"
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------- Interactive Scatter Chart ----------
    st.subheader("Rows vs Columns")
    fig2 = px.scatter(
        df_filtered,
        x="columns",
        y="rows",
        color="source",
        size="rows",
        hover_name="dataset_name",
        title="Dataset Size: Rows vs Columns"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # -------- Download filtered data ----------
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered datasets CSV", csv_bytes, file_name="filtered_datasets.csv", mime="text/csv")

    st.info("Use the sidebar filters to explore different datasets dynamically.")
