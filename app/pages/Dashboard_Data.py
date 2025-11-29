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

# ===== HF AI Assistant: Data =====
from app.common.ai_client import generate_answer_hf, get_history

DATA_SYSTEM_PROMPT = """You are a data science expert assistant.
Help with analysis, visualization, and statistical insights."""

# Ensure keys exist
if "ai_q_data" not in st.session_state:
    st.session_state["ai_q_data"] = ""
if "ai_last_response_data" not in st.session_state:
    st.session_state["ai_last_response_data"] = ""

with st.expander("AI Assistant — Data Science (Ask about datasets, analysis)"):
    with st.form(key="ai_form_data", clear_on_submit=False):
        st.text("Tip: Ask about dataset size, archiving suggestions, or visualization ideas.")
        q = st.text_area("Question for Data assistant:", key="ai_q_data", height=120)
        submit = st.form_submit_button("Ask Data Assistant")

    if submit:
        if not st.session_state["ai_q_data"].strip():
            st.warning("Please type a question.")
        else:
            with st.spinner("AI thinking..."):
                answer = generate_answer_hf("data", st.session_state["ai_q_data"], system_prompt=DATA_SYSTEM_PROMPT)
                st.session_state["ai_last_response_data"] = answer

    # show errors if any
    if "_ai_last_error" in st.session_state:
        st.error(st.session_state["_ai_last_error"])

    # display last answer
    if st.session_state.get("ai_last_response_data"):
        st.markdown("**AI:**")
        st.write(st.session_state["ai_last_response_data"])

    # display short chat history
    hist = get_history("data")
    if hist:
        st.markdown("**Chat history (latest first)**")
        for item in reversed(hist[-12:]):
            role = item.get("role", "")
            text = item.get("text", "")
            label = "**Assistant:**" if role.lower() == "assistant" else "**User:**"
            st.write(f"{label} {text}")


