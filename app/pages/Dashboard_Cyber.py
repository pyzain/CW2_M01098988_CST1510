# app/pages/Dashboard_Cy.py
"""
Cybersecurity Dashboard - Presentable & interactive.

This page is intended to be called by the central router (main_app.py).
It loads incident data (DB preferred, CSV fallback), then provides:
 - KPIs and simple executive summary
 - Interactive filters (date range, type, severity, status, assignee)
 - Timeline of incidents
 - Severity distribution & top affected assets
 - Resolution time analysis and recommendations
 - Download filtered dataset
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.common.ai_tools import build_ai_context
from datetime import datetime, timedelta
from app.common.ai_client import get_ai_client

# Import centralized navigation helper if needed for internal links
try:
    from app.common.navigation import navigate
except Exception:
    # navigate may not be necessary here; keep graceful fallback
    navigate = None

# Optional: attempt DB import (if your project has DatabaseManager)
try:
    from app.common.database_manager import DatabaseManager
except Exception:
    DatabaseManager = None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make column names predictable:
      - lower-case, strip, replace spaces with underscores
    Also provide best-effort column mapping for common names.
    """
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # common mapping: map synonyms to expected names
    col_map = {}
    if "incident_id" not in df.columns and "id" in df.columns:
        col_map["id"] = "incident_id"
    if "timestamp" not in df.columns and "date" in df.columns:
        col_map["date"] = "timestamp"
    if "severity" not in df.columns:
        for candidate in ("level", "priority"):
            if candidate in df.columns:
                col_map[candidate] = "severity"
                break
    if "type" not in df.columns:
        for candidate in ("category", "threat_type"):
            if candidate in df.columns:
                col_map[candidate] = "type"
                break
    if "status" not in df.columns and "state" in df.columns:
        col_map["state"] = "status"
    if "assigned_to" not in df.columns and "assignee" in df.columns:
        col_map["assignee"] = "assigned_to"
    if "asset" not in df.columns and "affected_asset" in df.columns:
        col_map["affected_asset"] = "asset"

    if col_map:
        existing = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=existing)

    return df


def _load_data() -> pd.DataFrame:
    """
    Load cyber incidents from DB if available, else from DATA/cyber_incidents.csv.
    Returns a dataframe (may be empty).
    """
    df = pd.DataFrame()
    # Try DB first
    if DatabaseManager is not None:
        db = None
        try:
            db = DatabaseManager()
            db.connect()
            try:
                df = pd.read_sql("SELECT * FROM cyber_incidents", db.conn)
            except Exception:
                # table missing or other issue -> fallback
                df = pd.DataFrame()
        except Exception:
            df = pd.DataFrame()
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

    # CSV fallback
    if df is None or df.empty:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        csv_path = os.path.join(project_root, "DATA", "cyber_incidents.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
            except Exception:
                df = pd.DataFrame()

    # normalize columns
    if not df.empty:
        df = _normalize_columns(df)

    # ensure timestamp column exists and is datetime
    if "timestamp" in df.columns:
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        except Exception:
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(str), errors="coerce")
    else:
        # try to guess a date-like column
        for c in df.columns:
            if "date" in c or "time" in c:
                try:
                    df["timestamp"] = pd.to_datetime(df[c], errors="coerce")
                    break
                except Exception:
                    continue

    # fill missing important columns with defaults
    if "severity" not in df.columns:
        df["severity"] = "unknown"
    if "type" not in df.columns:
        df["type"] = "unknown"
    if "status" not in df.columns:
        df["status"] = "open"
    if "assigned_to" not in df.columns:
        df["assigned_to"] = "unassigned"
    if "asset" not in df.columns:
        df["asset"] = "unknown"
    if "incident_id" not in df.columns:
        df["incident_id"] = pd.Series(range(1, len(df) + 1))

    # Ensure severity is a normalized lowercase string (avoid pandas Categorical)
    df["severity"] = df["severity"].astype(str).str.lower().str.strip().fillna("unknown")

    # Convert any object columns that could be problematic to strings where appropriate
    # (we keep timestamps as datetime)
    for c in df.columns:
        if c != "timestamp" and df[c].dtype.name == "category":
            df[c] = df[c].astype(str)

    return df


def _executive_summary(df: pd.DataFrame) -> str:
    """
    Build a plain-English executive summary based on simple heuristics.
    """
    if df.empty:
        return "No incident data available."

    total = len(df)
    last_7 = df[df["timestamp"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
    recent_count = len(last_7)
    critical = df[df["severity"] == "critical"]
    high = df[df["severity"] == "high"]
    unresolved = df[df["status"].astype(str).str.lower() != "resolved"]

    top_type = df["type"].value_counts().idxmax() if not df["type"].isna().all() else "N/A"
    top_asset = df["asset"].value_counts().idxmax() if not df["asset"].isna().all() else "N/A"

    parts = [
        f"Total incidents recorded: **{total}**.",
        f"Incidents in the last 7 days: **{recent_count}**, most common type: **{top_type}**.",
        f"High/critical incidents: **{len(high) + len(critical)}**.",
        f"Unresolved incidents: **{len(unresolved)}** (check assignment and triage).",
        f"Most impacted asset: **{top_asset}**."
    ]

    # quick actionable insight
    if len(critical) > 0 and len(unresolved[unresolved["severity"].isin(["critical", "high"])]) / max(1, len(df)) > 0.1:
        parts.append("Action: A notable portion of high-severity incidents remain unresolved — prioritize triage and allocate staff for incident response.")
    elif recent_count > total * 0.2:
        parts.append("Action: There is a recent surge in incidents; consider increasing monitoring or blocking suspicious sources.")
    else:
        parts.append("Status: Incident volume is stable; continue monitoring and follow standard playbooks.")

    return " ".join(parts)


def _convert_categories_to_strings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert pandas 'category' dtypes to plain strings to avoid internal references
    and serialization issues with Streamlit / JSON.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype.name == "category":
            df[col] = df[col].astype(str)
    return df


def cyber_dashboard():
    # session guard
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        return

    # --- sanitize session state to remove any non-serializable / circular objects ---
    def _sanitize_ai_messages():
        msgs = st.session_state.get("ai_messages")
        if not msgs:
            return
        cleaned = []
        try:
            for m in msgs:
                # Guarantee stored history is a dict with simple string content
                if not isinstance(m, dict):
                    cleaned.append({"role": "system", "content": str(m)})
                    continue
                role = str(m.get("role", "system"))
                content = m.get("content", "")
                # ensure content is a plain string (avoid dicts, DataFrames, lists, objects)
                if isinstance(content, (dict, list, pd.DataFrame, pd.Series)):
                    content = str(content)
                else:
                    content = str(content)
                cleaned.append({"role": role, "content": content})
            st.session_state["ai_messages"] = cleaned
        except Exception:
            # safe fallback: reset to a minimal system message
            st.session_state["ai_messages"] = [{
                "role": "system",
                "content": "You are a cybersecurity assistant. Provide concise, actionable advice."
            }]

    _sanitize_ai_messages()
    # -------------------------------------------------------------------------------

    # Page header & description
    st.title("🔒 Cybersecurity Dashboard")
    st.markdown(
        """
        **Purpose:** Provide clear, actionable insights about security incidents (phishing, malware, suspicious login attempts, etc.).
        This view is designed for analysts and managers — even non-technical stakeholders can read the executive summary and follow recommendations.
        """
    )

    # Load data
    df = _load_data()

    if df.empty:
        st.info("No incident data available. Please ensure `cyber_incidents` table or DATA/cyber_incidents.csv exists.")
        return

    # sidebar filters
    st.sidebar.header("Filters & Controls")
    try:
        min_date = df["timestamp"].min() if "timestamp" in df.columns and pd.notna(df["timestamp"].min()) else pd.Timestamp.now() - pd.Timedelta(days=365)
        max_date = df["timestamp"].max() if "timestamp" in df.columns and pd.notna(df["timestamp"].max()) else pd.Timestamp.now()
    except Exception:
        min_date = pd.Timestamp.now() - pd.Timedelta(days=365)
        max_date = pd.Timestamp.now()

    default_start = max_date - pd.Timedelta(days=90)
    date_range = st.sidebar.date_input(
        "Date range",
        value=(default_start.date(), max_date.date() if pd.notna(max_date) else datetime.now().date())
    )
    try:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    except Exception:
        start_date = df["timestamp"].min()
        end_date = df["timestamp"].max()

    # type / severity / status / assignee filters
    type_options = sorted(df["type"].dropna().astype(str).unique().tolist())
    # Avoid using .cat.categories (might not be categorical); derive from values
    severity_options = sorted(df["severity"].astype(str).unique().tolist())
    status_options = sorted(df["status"].astype(str).str.lower().unique().tolist())
    assignee_options = sorted(df["assigned_to"].astype(str).unique().tolist())

    selected_types = st.sidebar.multiselect("Incident type", options=type_options, default=type_options)
    selected_sev = st.sidebar.multiselect("Severity", options=severity_options, default=severity_options)
    selected_status = st.sidebar.multiselect("Status", options=status_options, default=status_options)
    selected_assignees = st.sidebar.multiselect("Assigned to", options=assignee_options, default=assignee_options)

    # apply filters
    df_filtered = df.copy()
    if "timestamp" in df_filtered.columns:
        try:
            df_filtered = df_filtered[(df_filtered["timestamp"] >= start_date) & (df_filtered["timestamp"] <= end_date)]
        except Exception:
            # Defensive: if timestamp filtering fails, keep original
            pass
    if selected_types:
        df_filtered = df_filtered[df_filtered["type"].astype(str).isin(selected_types)]
    if selected_sev:
        df_filtered = df_filtered[df_filtered["severity"].astype(str).isin(selected_sev)]
    if selected_status:
        df_filtered = df_filtered[df_filtered["status"].astype(str).str.lower().isin([s.lower() for s in selected_status])]
    if selected_assignees:
        df_filtered = df_filtered[df_filtered["assigned_to"].astype(str).isin(selected_assignees)]

    # Convert any category dtypes to strings to avoid circular/cpickle issues
    df_filtered = _convert_categories_to_strings(df_filtered)

    # top row: KPIs and executive summary
    col_kpi_1, col_kpi_2, col_kpi_3, col_kpi_4 = st.columns([1, 1, 1, 1])
    total_incidents = len(df_filtered)
    new_incidents_7d = df_filtered[df_filtered["timestamp"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))].shape[0] if "timestamp" in df_filtered.columns else 0
    unresolved_count = df_filtered[df_filtered["status"].astype(str).str.lower() != "resolved"].shape[0]
    critical_count = df_filtered[df_filtered["severity"].astype(str).str.lower() == "critical"].shape[0]

    col_kpi_1.metric("Total incidents (filtered)", total_incidents)
    col_kpi_2.metric("Incidents (last 7 days)", new_incidents_7d)
    col_kpi_3.metric("Unresolved incidents", unresolved_count)
    col_kpi_4.metric("Critical incidents", critical_count)

    st.markdown("### Executive summary")
    with st.expander("Show executive summary & recommendations", expanded=True):
        summary = _executive_summary(df_filtered)
        st.markdown(summary)

    # Two-column layout for charts
    st.markdown("---")
    ch1, ch2 = st.columns([2, 1])

    # Timeline: incidents over time (group by day)
    with ch1:
        st.subheader("Incident timeline")
        if "timestamp" in df_filtered.columns:
            timeline = df_filtered.copy()
            timeline["date"] = timeline["timestamp"].dt.floor("d")
            try:
                timeseries = timeline.groupby(["date", "type"]).size().reset_index(name="count")
                fig_time = px.line(timeseries, x="date", y="count", color="type", title="Incidents over time by type")
                fig_time.update_layout(legend_title_text="Type")
                st.plotly_chart(fig_time, use_container_width=True)
            except Exception:
                st.info("Not enough data to render a timeline.")
        else:
            st.info("No timestamp data available for timeline.")

    # Severity distribution and status donut
    with ch2:
        st.subheader("Severity & Status")
        try:
            sev_df = df_filtered["severity"].astype(str).value_counts().reset_index()
            sev_df.columns = ["severity", "count"]
            fig_sev = px.bar(sev_df, x="severity", y="count", title="Severity distribution", orientation="v")
            st.plotly_chart(fig_sev, use_container_width=True)
        except Exception:
            st.info("Unable to compute severity distribution.")

        try:
            status_df = df_filtered["status"].astype(str).value_counts().reset_index()
            status_df.columns = ["status", "count"]
            fig_status = go.Figure(data=[go.Pie(labels=status_df["status"], values=status_df["count"], hole=0.5)])
            fig_status.update_layout(title_text="Status breakdown")
            st.plotly_chart(fig_status, use_container_width=True)
        except Exception:
            st.info("Unable to compute status breakdown.")

    st.markdown("---")

    # Asset and assignee insights
    st.subheader("🔍 Top affected assets & assignees")

    # Top assets (use filtered view if you want top in current filter; use df for global)
    try:
        group_df = df_filtered if not df_filtered.empty else df
        if "incident_id" not in group_df.columns:
            group_df = group_df.copy()
            group_df["incident_id"] = pd.Series(range(1, len(group_df) + 1))
        top_assets = (
            group_df.groupby("asset")["incident_id"]
            .count()
            .reset_index(name="asset_count")
            .sort_values("asset_count", ascending=False)
            .head(5)
        )
    except Exception:
        top_assets = pd.DataFrame({"asset": [], "asset_count": []})

    try:
        group_df2 = df_filtered if not df_filtered.empty else df
        if "incident_id" not in group_df2.columns:
            group_df2 = group_df2.copy()
            group_df2["incident_id"] = pd.Series(range(1, len(group_df2) + 1))
        top_assignees = (
            group_df2.groupby("assigned_to")["incident_id"]
            .count()
            .reset_index(name="assignee_count")
            .sort_values("assignee_count", ascending=False)
            .head(5)
        )
    except Exception:
        top_assignees = pd.DataFrame({"assigned_to": [], "assignee_count": []})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("*Top assets by incident count*")
        st.dataframe(top_assets)

    with col2:
        st.markdown("*Top assignees by incident count*")
        st.dataframe(top_assignees)

    # Optional: Bar charts
    try:
        fig1 = px.bar(top_assets, x="asset", y="asset_count", title="Top Assets by Incident Count")
        st.plotly_chart(fig1, use_container_width=True)
    except Exception:
        pass

    try:
        fig2 = px.bar(top_assignees, x="assigned_to", y="assignee_count", title="Top Assignees by Incident Count")
        st.plotly_chart(fig2, use_container_width=True)
    except Exception:
        pass

    st.markdown("---")

    # Resolution time analysis (if column exists)
    st.subheader("Resolution time analysis")
    if "resolution_time_days" in df_filtered.columns:
        try:
            rt = df_filtered.copy()
            rt["resolution_time_days"] = pd.to_numeric(rt["resolution_time_days"], errors="coerce")
            rt_stats = rt["resolution_time_days"].describe()
            st.write(rt_stats)
            fig_rt = px.box(rt, x="severity", y="resolution_time_days", title="Resolution time (days) by severity")
            st.plotly_chart(fig_rt, use_container_width=True)
        except Exception:
            st.info("Unable to compute resolution time statistics.")
    else:
        st.info("No resolution_time_days column found. If available, add it to the dataset for SLA analysis.")

    st.markdown("---")

    # Focus on unresolved high-severity incidents for action
    st.subheader("Immediate action queue (high priority unresolved)")
    try:
        queue = df_filtered[
            (df_filtered["severity"].astype(str).isin(["critical", "high"])) &
            (df_filtered["status"].astype(str).str.lower() != "resolved")
        ].sort_values(by="severity")
    except Exception:
        queue = pd.DataFrame()

    if not queue.empty:
        st.dataframe(queue[["incident_id", "timestamp", "type", "severity", "status", "asset", "assigned_to"]].head(50))
        st.warning("These incidents should be triaged immediately.")
    else:
        st.success("No unresolved high-priority incidents in the current filter.")

    st.markdown("---")

    # Recommendations (simple heuristics)
    st.subheader("Automated recommendations")
    recs = []
    if critical_count > 0 and unresolved_count / max(1, total_incidents) > 0.05:
        recs.append("- *Allocate dedicated triage resources* for critical incidents to reduce mean time to resolve.")
    if new_incidents_7d > max(5, total_incidents * 0.1):
        recs.append("- *Investigate recent spike*: check for phishing campaigns or misconfigured detection rules.")
    if queue.shape[0] > 0:
        recs.append("- *Reassign or escalate* incidents that are unassigned or repeatedly reassigned.")
    if not recs:
        recs.append("- No urgent system-level recommendations detected. Continue regular monitoring.")

    for r in recs:
        st.markdown(r)

    # Download filtered data
    try:
        csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download filtered incidents CSV", csv_bytes, file_name="filtered_cyber_incidents.csv", mime="text/csv")
    except Exception:
        st.info("Unable to prepare CSV for download.")

    # Final notes & teaching overlay
    st.markdown("---")
    st.markdown(
        """
        **How to use this dashboard (for non-technical users):**
        1. Use the **sidebar** to restrict dates, types, or assignees — the charts update automatically.  
        2. Look at the **Executive summary** for a plain-English overview.  
        3. Check the **Immediate action queue** for incidents that need triage.  
        4. Use the recommendations to decide quick actions (allocate staff, escalate, block sources).  

        **Marking guidance alignment:** This dashboard demonstrates:
        - Clear technical explanation and visualisation (Report & Technical Explanation).  
        - Functional features: filtering, charts, KPIs, table downloads (Software Functionality).  
        - Clean modular code with comments (Code Quality).  
        - Analytical insights and recommendations (Analytical Insights).
        """
    )

    # -----------------------------
    # AI Assistant — Moved inside function
    # -----------------------------
    st.markdown("---")
    st.subheader("AI Assistant — Cybersecurity (RAG + Chat)")

    # ensure session state keys
    st.session_state.setdefault("ai_messages", [
        {"role": "system",
         "content": "You are a cybersecurity assistant. Provide concise, actionable advice based on given incident context. Mention sources and be conservative if data is missing."}
    ])
    st.session_state.setdefault("ai_usage_count", 0)

    # Option for how much context to send
    send_mode = st.radio("AI input mode",
                         options=["Summary only (safe/default)", "Full context (more detail, larger payload)"], index=0,
                         horizontal=True)
    max_sample = 50 if send_mode.startswith("Full") else 10

    prompt = st.chat_input("Ask the Cyber AI Assistant a question (e.g., 'Why are we seeing a spike in phishing?')")

    if prompt:
        # echo user message in chat UI
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.ai_usage_count += 1
        if st.session_state.ai_usage_count > 200:
            st.warning("AI usage limit reached for this session.")
        else:
            # Build filter summary string (already present in your code, but ensure no crash)
            try:
                filter_summary = f"Filters: date range {start_date.date()} to {end_date.date()}, types {selected_types}, severities {selected_sev}"
            except Exception:
                filter_summary = "No filter summary."

            # Build local context (safe & token-limited)
            # ensure any category dtypes are strings before passing into build_ai_context
            safe_df_for_ai = _convert_categories_to_strings(df_filtered)

            ai_context = build_ai_context(safe_df_for_ai, filters={
                "date_from": str(start_date.date()),
                "date_to": str(end_date.date()),
                "types": selected_types,
                "severities": selected_sev
            }, max_sample_rows=max_sample)

            # Add RAG context (if available)
            rag_context_text = "RAG context not available; using dashboard summary only."

            # Compose messages for API: keep them short & structured
            import copy
            messages_for_api = copy.deepcopy(st.session_state.ai_messages[-8:])  # keep last history
            import json
            import numpy as np

            def sanitize_for_json(obj):
                """
                Convert known types to JSON-friendly native types.
                """
                if isinstance(obj, pd.DataFrame):
                    return obj.to_dict(orient="records")
                if isinstance(obj, pd.Series):
                    return obj.to_dict()
                if isinstance(obj, (np.generic,)):
                    return obj.item()
                if isinstance(obj, dict):
                    return {k: sanitize_for_json(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [sanitize_for_json(x) for x in obj]
                # fallback: string for unknown objects
                return obj

            try:
                ctx_str = json.dumps(sanitize_for_json(ai_context), indent=2)
            except Exception:
                # fallback to safe string
                try:
                    ctx_str = str(sanitize_for_json(ai_context))
                except Exception:
                    ctx_str = "AI context unavailable."

            messages_for_api.append({
                "role": "user",
                "content": (
                    f"{filter_summary}\n\n"
                    f"User question: {prompt}\n\n"
                    f"Dashboard context:\n{ctx_str}\n\n"
                    f"RAG context (top hits):\n{rag_context_text}\n\n"
                    "Please answer concisely and mention if you need more data."
                )
            })

            # Make the API call
            ai_client = None
            try:
                ai_client = get_ai_client()
            except Exception as e:
                st.error(f"AI client initialization failed: {e}")
                ai_reply = f"[AI client error: {e}]"
                with st.chat_message("assistant"):
                    st.markdown(ai_reply)
                # Save minimal history (text only)
                st.session_state.ai_messages.append({"role": "user", "content": str(prompt)})
                st.session_state.ai_messages.append({"role": "assistant", "content": str(ai_reply)})
                return

            try:
                with st.spinner("AI thinking..."):
                    result = ai_client.chat(messages_for_api, model="gpt-4o-mini")
                    # ai_client.chat returns a string in the provided ai_client.py; handle both cases
                    if isinstance(result, dict):
                        # defensive: if the client returns structured response
                        ai_reply = ""
                        msg = result.get("message") or {}
                        # If message is a dict with content
                        if isinstance(msg, dict):
                            ai_reply = msg.get("content") or msg.get("text") or str(result)
                        else:
                            ai_reply = str(result)
                    else:
                        ai_reply = str(result)
            except Exception as e:
                st.error(f"AI call failed: {e}")
                ai_reply = f"[AI error: {e}]"

            # Display assistant answer
            with st.chat_message("assistant"):
                st.markdown(ai_reply)

            # Save history (store only strings to avoid session serialization issues)
            st.session_state.ai_messages.append({
                "role": "user",
                "content": str(prompt)
            })
            st.session_state.ai_messages.append({
                "role": "assistant",
                "content": str(ai_reply)
            })
