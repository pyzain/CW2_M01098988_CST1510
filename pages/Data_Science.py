# pages/Data_Science.py
import streamlit as st
import pandas as pd
import plotly.express as px
from database.db import connect_database
from ai_core import AIAssistant


def _load():
    conn = connect_database()
    try:
        df = pd.read_sql_query("SELECT * FROM datasets ORDER BY id DESC", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return df


def render():
    # Require login
    if not st.session_state.get("user"):
        st.warning("Please login from Home before viewing dashboards.")
        return

    st.title("📊 Data Science")
    st.write("Dataset catalog, quick analysis, and a Data Science assistant to help interpret results.")

    # Load data
    df = _load()
    if df.empty:
        st.info("No datasets found in DB. Put datasets_metadata.csv into /data and run initializer.")
        return

    # Normalize known columns
    if "rows" not in df.columns and "Rows" in df.columns:
        df = df.rename(columns={"Rows": "rows"})
    # Ensure numeric columns exist and are safe
    df["rows"] = pd.to_numeric(df.get("rows", 0), errors="coerce").fillna(0).astype(int)
    if "file_size_mb" in df.columns:
        df["file_size_mb"] = pd.to_numeric(df.get("file_size_mb", 0), errors="coerce").fillna(0.0)

    # Sidebar filters (kept simple & friendly)
    st.sidebar.header("Filters")
    owners = sorted(df["owner"].astype(str).unique().tolist()) if "owner" in df.columns else []
    owner_sel = st.sidebar.multiselect("Owner", options=owners, default=owners if owners else [])
    min_rows = int(df["rows"].min()) if not df["rows"].dropna().empty else 0
    max_rows = int(df["rows"].max()) if not df["rows"].dropna().empty else min_rows
    rows_range = st.sidebar.slider("Rows range", min_value=min_rows, max_value=max_rows, value=(min_rows, max_rows))

    # Apply filters
    dff = df.copy()
    if owner_sel:
        dff = dff[dff["owner"].astype(str).isin(owner_sel)]
    dff = dff[(dff["rows"] >= rows_range[0]) & (dff["rows"] <= rows_range[1])]

    # Top KPI row
    c1, c2, c3 = st.columns(3)
    c1.metric("Datasets", len(dff))
    c2.metric("Total rows", int(dff["rows"].sum()))
    c3.metric("Avg size (MB)", round(dff.get("file_size_mb", 0).mean(), 2))

    st.markdown("---")

    # Visualizations section
    st.subheader("Visualizations")

    # 1) Rows distribution histogram
    try:
        fig_rows = px.histogram(dff, x="rows", nbins=30, title="Distribution of Rows per Dataset")
        st.plotly_chart(fig_rows, width="stretch")
    except Exception:
        st.info("Rows histogram unavailable (missing 'rows' column).")

    # 2) File size distribution (if available)
    if "file_size_mb" in dff.columns and not dff["file_size_mb"].dropna().empty:
        fig_size = px.histogram(dff, x="file_size_mb", nbins=30, title="Dataset Size (MB)")
        st.plotly_chart(fig_size, width="stretch")
    else:
        st.info("File size visualization unavailable (missing 'file_size_mb' column).")

    # 3) Top owners (bar)
    if "owner" in dff.columns:
        owner_counts = dff["owner"].value_counts().reset_index()
        owner_counts.columns = ["owner", "count"]
        fig_owner = px.bar(owner_counts.head(10), x="owner", y="count", title="Top Owners (by number of datasets)")
        st.plotly_chart(fig_owner, width="stretch")
    else:
        st.info("Owner information not available.")

    # 4) Rows vs File size scatter (if both present)
    if set(["rows", "file_size_mb"]).issubset(dff.columns):
        fig_scatter = px.scatter(
            dff,
            x="rows",
            y="file_size_mb",
            hover_data=["name"] if "name" in dff.columns else None,
            title="Rows vs File Size (MB)",
            labels={"rows": "Rows", "file_size_mb": "Size (MB)"}
        )
        st.plotly_chart(fig_scatter, width="stretch")
    else:
        st.info("Rows vs Size scatter requires both 'rows' and 'file_size_mb' columns.")

    st.markdown("---")

    # Dataset table with simple actions
    st.subheader("Datasets")
    st.dataframe(dff.reset_index(drop=True).head(200), width="stretch")

    st.markdown("---")

    # -----------------------------------------
    # AI Assistant (Data Science)
    # -----------------------------------------
    st.subheader("📊 Data Science Assistant")

    if "ds_chat" not in st.session_state:
        st.session_state.ds_chat = []

    for msg in st.session_state.ds_chat:
        speaker = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
        st.markdown(f"**{speaker}:** {msg['content']}")

    st.markdown("---")

    user_query = st.text_input("Ask a machine learning / analytics question...", key="ds_input")
    send = st.button("Send")
    clear = st.button("Clear Chat")

    if clear:
        st.session_state.ds_chat = []
        st.rerun()

    if send and user_query.strip():

        st.session_state.ds_chat.append({"role": "user", "content": user_query})

        history = "\n".join(
            [f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
             for m in st.session_state.ds_chat]
        )

        # ---- SMART SNAPSHOT (DATA SCIENCE) ----
        try:
            snapshot = "=== Data Science Snapshot ===\n"

            # schema
            snapshot += "\nColumns:\n" + ", ".join(dff.columns)

            # summary stats
            num_cols = dff.select_dtypes(include="number")
            if not num_cols.empty:
                snapshot += "\n\nBasic statistics:\n" + num_cols.describe().to_string()

            # missing values
            missing = dff.isna().sum()
            snapshot += "\n\nMissing values:\n" + missing.to_string()

            # sample of data
            snapshot += "\n\nSample rows (first 15):\n"
            snapshot += dff.head(15).to_string()

        except Exception:
            snapshot = "(Snapshot unavailable)"

        ai = AIAssistant(
            role_prompt=(
                "You are a senior data scientist. "
                "Explain ML concepts simply, give clear preprocessing advice, "
                "help interpret distributions, outliers, metadata, and dataset insights."
            )
        )

        reply = ai.ask(
            query=user_query,
            data_context=f"{snapshot}\n\n=== Conversation ===\n{history}"
        )

        st.session_state.ds_chat.append({"role": "assistant", "content": reply})
        st.rerun()
