# pages/Cybersecurity.py
import streamlit as st
import pandas as pd
import plotly.express as px
from database.db import connect_database
from ai_core import AIAssistant
from typing import List

def _load():
    conn = connect_database()
    try:
        df = pd.read_sql_query("SELECT * FROM cyber_incidents ORDER BY id DESC", conn)
    except Exception:
        df = pd.DataFrame()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return df


def _safe_to_str(x):
    try:
        return str(x)
    except Exception:
        return ""

def render():
    # Require login
    if not st.session_state.get("user"):
        st.warning("Please login from Home before viewing dashboards.")
        return

    st.title("🛡 Cybersecurity")
    st.write("Incident triage, trends, and an AI helper to summarise and recommend actions.")

    # Load incidents
    df = _load()
    if df.empty:
        st.info("No incident data found. Put cyber_incidents.csv into /data and run the initializer.")
        return

    # Normalize common columns
    if "timestamp" not in df.columns and "date" in df.columns:
        df = df.rename(columns={"date": "timestamp"})
    if "incident_type" in df.columns and "type" not in df.columns:
        df = df.rename(columns={"incident_type": "type"})

    df["timestamp"] = pd.to_datetime(df.get("timestamp"), errors="coerce")
    df["severity"] = df.get("severity", "unknown").astype(str).str.lower().fillna("unknown")
    df["status"] = df.get("status", "open").astype(str).fillna("open")
    # ensure id/external_id as strings for display safety
    if "id" in df.columns:
        df["id"] = df["id"].astype(str)
    if "external_id" in df.columns:
        df["external_id"] = df["external_id"].astype(str)

    # Top KPIs
    total = len(df)
    now = pd.Timestamp.now()
    last7 = df[df["timestamp"] >= (now - pd.Timedelta(days=7))] if "timestamp" in df.columns else pd.DataFrame()
    unresolved = df[df["status"].str.lower() != "resolved"]
    critical = df[df["severity"].str.lower() == "critical"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total incidents", total)
    k2.metric("Last 7 days", len(last7))
    k3.metric("Unresolved", len(unresolved))
    k4.metric("Critical", len(critical))

    st.markdown("---")

    # Sidebar filters
    st.sidebar.header("Filters")
    # date range
    min_date = df["timestamp"].min() if "timestamp" in df.columns and not df["timestamp"].isna().all() else (now - pd.Timedelta(days=365))
    max_date = df["timestamp"].max() if "timestamp" in df.columns and not df["timestamp"].isna().all() else now
    date_range = st.sidebar.date_input("Date range", value=(min_date.date(), max_date.date()))
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    types = sorted(df["type"].astype(str).unique().tolist()) if "type" in df.columns else []
    severities = sorted(df["severity"].astype(str).unique().tolist()) if "severity" in df.columns else []
    statuses = sorted(df["status"].astype(str).unique().tolist()) if "status" in df.columns else []

    sel_types = st.sidebar.multiselect("Type", options=types, default=types)
    sel_sev = st.sidebar.multiselect("Severity", options=severities if severities else ["critical","high","medium","low"], default=severities if severities else ["critical","high","medium","low"])
    sel_status = st.sidebar.multiselect("Status", options=statuses, default=statuses if statuses else ["open","in progress","resolved","closed"])

    # Apply filters
    dff = df.copy()
    if "timestamp" in dff.columns:
        dff = dff[(dff["timestamp"] >= start_date) & (dff["timestamp"] <= end_date)]
    if sel_types:
        dff = dff[dff["type"].astype(str).isin(sel_types)]
    if sel_sev:
        dff = dff[dff["severity"].astype(str).isin(sel_sev)]
    if sel_status:
        dff = dff[dff["status"].astype(str).isin(sel_status)]

    st.subheader("Incident Overview")

    # 1. Timeline (daily)
    if not dff.empty and "timestamp" in dff.columns:
        times = dff.copy()
        times["date"] = times["timestamp"].dt.floor("d")
        ts = times.groupby("date").size().reset_index(name="count")
        fig = px.line(ts, x="date", y="count", title="Incidents over time (daily)")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Not enough timestamp data to show timeline.")

    # 2. Severity breakdown (bar)
    st.markdown("### Severity distribution")
    if not dff.empty:
        sev_counts = dff["severity"].value_counts().reset_index()
        sev_counts.columns = ["severity", "count"]
        fig_sev = px.bar(sev_counts, x="severity", y="count", title="Incidents by Severity", color="severity")
        st.plotly_chart(fig_sev, width="stretch")
    else:
        st.info("No severity data to display.")

    # 3. Top incident types
    st.markdown("### Incident types")
    if "type" in dff.columns and not dff["type"].dropna().empty:
        type_counts = dff["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        fig_type = px.bar(type_counts.head(12), x="type", y="count", title="Top Incident Types", color="count")
        st.plotly_chart(fig_type, width="stretch")
    else:
        st.info("No incident type data available.")

    # 4. Affected assets (top)
    st.markdown("### Affected assets")
    if "asset" in dff.columns and not dff["asset"].dropna().empty:
        asset_counts = dff["asset"].value_counts().reset_index()
        asset_counts.columns = ["asset", "count"]
        fig_asset = px.bar(asset_counts.head(12), x="asset", y="count", title="Top Affected Assets", color="count")
        st.plotly_chart(fig_asset, width="stretch")
    else:
        st.info("No asset data available.")

    st.markdown("---")

    # Immediate action queue (high priority unresolved)
    st.subheader("Immediate action queue (high priority unresolved)")
    queue_cols: List[str] = [c for c in ["id", "external_id", "timestamp", "type", "severity", "status", "asset", "summary"] if c in dff.columns]
    queue = dff[(dff["severity"].isin(["critical", "high"])) & (dff["status"].str.lower() != "resolved")]
    if not queue.empty:
        st.dataframe(queue[queue_cols].sort_values(by="timestamp", ascending=False).head(100), width="stretch")
    else:
        st.success("No high-priority unresolved incidents.")

    st.markdown("---")

    # Incident table (paginated small view)
    st.subheader("Incident table (top 200)")
    display_cols = [c for c in ["timestamp", "external_id", "type", "severity", "status", "asset", "summary"] if c in dff.columns]
    st.dataframe(dff[display_cols].head(200).reset_index(drop=True), width="stretch")

    st.markdown("---")

    # -----------------------------------------
    # AI Assistant (Universal Clean Version)
    # -----------------------------------------
    st.subheader("🔒 Cybersecurity Assistant")

    # Init chat state
    if "cyber_chat" not in st.session_state:
        st.session_state.cyber_chat = []

        # Display chat
    for msg in st.session_state.cyber_chat:
        speaker = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
        st.markdown(f"**{speaker}:** {msg['content']}")

    st.markdown("---")

    # Input + controls (buttons below)
    user_query = st.text_input("Ask a cybersecurity question...", key="cyber_input")

    send = st.button("Send")
    clear = st.button("Clear Chat")

    if clear:
        st.session_state.cyber_chat = []
        st.rerun()

    if send and user_query.strip():

        # Save user message
        st.session_state.cyber_chat.append({"role": "user", "content": user_query})

        # Build conversation history
        history = "\n".join(
            [f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
             for m in st.session_state.cyber_chat]
        )

        # --- SMART SNAPSHOT (FLEXIBLE & PRACTICAL) ---
        try:
            snapshot = "=== Cybersecurity Snapshot ===\n"

            # schema
            snapshot += "\nColumns:\n" + ", ".join(dff.columns) + "\n"

            # severity counts
            if "severity" in dff.columns:
                snapshot += "\nSeverity counts:\n" + dff["severity"].value_counts().to_string()

            # recent high-priority incidents
            if "severity" in dff.columns and "timestamp" in dff.columns:
                top_critical = dff[dff["severity"].isin(["critical", "high"])] \
                    .sort_values("timestamp", ascending=False) \
                    .head(10)
                snapshot += "\n\nRecent critical/high incidents:\n"
                snapshot += top_critical.to_string()

            # filtered selection sample (user may ask about these)
            snapshot += "\n\nFiltered sample (first 15 rows):\n"
            snapshot += dff.head(15).to_string()

        except Exception:
            snapshot = "(Snapshot unavailable)"

        # Create assistant
        ai = AIAssistant(
            role_prompt=(
                "You are a senior cybersecurity analyst. "
                "Explain findings simply, help with incident triage, "
                "and give clear actionable steps. "
                "Be concise and use the data snapshot to support answers."
            )
        )

        # Ask AI
        reply = ai.ask(
            query=user_query,
            data_context=f"{snapshot}\n\n=== Conversation ===\n{history}"
        )

        # Save reply
        st.session_state.cyber_chat.append({"role": "assistant", "content": reply})

        st.rerun()
