# pages/Cybersecurity.py
"""
Cybersecurity dashboard - Dark / cyber theme.
Simple, commented, easy to read.

Structure:
 - CyberDataLoader: load from DB (preferred) or data/cyber_incidents.csv fallback
 - CyberDashboard: renders page using small methods
 - Tabs: Overview | Trends | Data | AI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import timedelta

# DB helper (your single DB helper)
from database.db import connect_database

# AI assistant wrapper (should exist in app.services)
try:
    from app.services.ai_assistant import AIAssistant
except Exception:
    AIAssistant = None

# Optional chatbot widget (if you have it)
try:
    from app.components.chatbot_widget import render as render_chatbot
except Exception:
    def render_chatbot():  # fallback no-op
        return

# --- Styling: short cyber dark theme CSS ---
def _inject_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #0b0f14; color: #e6eef6; }
        .kpi-card { background: linear-gradient(90deg, rgba(5,10,15,0.9), rgba(15,20,30,0.6)); 
                    border-radius: 8px; padding: 12px; box-shadow: 0 4px 18px rgba(0,0,0,0.5);}
        .section-title { color: #9bd1ff; font-weight:700; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --- Data loader class (DB first, CSV fallback) ---
class CyberDataLoader:
    def __init__(self):
        # project root relative to this file
        self.PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.csv_path = self.PROJECT_ROOT / "data" / "cyber_incidents.csv"

    def _from_db(self):
        try:
            conn = connect_database()
            df = pd.read_sql_query("SELECT * FROM cyber_incidents ORDER BY id DESC", conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def _from_csv(self):
        if self.csv_path.exists():
            try:
                # CSV is simple, no header assumed sometimes - try both
                df = pd.read_csv(self.csv_path, header=0)
                return df
            except Exception:
                try:
                    df = pd.read_csv(self.csv_path, header=None)
                    # if headerless: try to assign reasonable column names
                    if df.shape[1] >= 6:
                        df.columns = ["incident_id", "timestamp", "severity", "type", "status", "description"] + list(df.columns[6:])
                    return df
                except Exception:
                    return pd.DataFrame()
        return pd.DataFrame()

    def load(self) -> pd.DataFrame:
        # Try DB first
        df = self._from_db()
        if df is None or df.empty:
            df = self._from_csv()

        if df is None:
            df = pd.DataFrame()

        # Normalize columns to known set for the dashboard
        df = df.copy()
        # Lowercase & sanitize column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Common renames
        col_map = {}
        if "id" in df.columns and "incident_id" not in df.columns:
            col_map["id"] = "incident_id"
        if "date" in df.columns and "timestamp" not in df.columns:
            col_map["date"] = "timestamp"
        if "incident_type" in df.columns and "type" not in df.columns:
            col_map["incident_type"] = "type"
        if "reported_by" in df.columns and "assigned_to" not in df.columns:
            col_map["reported_by"] = "assigned_to"

        if col_map:
            df = df.rename(columns=col_map)

        # Ensure expected columns exist
        for c in ["incident_id", "timestamp", "severity", "type", "status", "description", "assigned_to", "asset"]:
            if c not in df.columns:
                df[c] = pd.NA

        # Parse timestamp safely
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        except Exception:
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(str), errors="coerce")

        # Normalise severity/type/status strings
        df["severity"] = df["severity"].astype(str).str.lower().fillna("unknown")
        df["type"] = df["type"].astype(str).fillna("unknown")
        df["status"] = df["status"].astype(str).fillna("open")
        df["assigned_to"] = df["assigned_to"].astype(str).fillna("unassigned")
        df["asset"] = df["asset"].astype(str).fillna("unknown")

        return df


# --- Dashboard renderer class ---
class CyberDashboard:
    def __init__(self):
        _inject_css()
        self.loader = CyberDataLoader()
        self.df = self.loader.load()

    def _sidebar_filters(self):
        st.sidebar.header("Filters")
        # date range: safe defaults
        if self.df["timestamp"].dropna().empty:
            default_end = pd.Timestamp.now()
            default_start = default_end - pd.Timedelta(days=90)
        else:
            default_start = self.df["timestamp"].min().date()
            default_end = self.df["timestamp"].max().date()
        date_range = st.sidebar.date_input("Date range", value=(default_start, default_end))
        start = pd.to_datetime(date_range[0])
        end = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        severities = sorted(self.df["severity"].dropna().unique().tolist())
        types = sorted(self.df["type"].dropna().unique().tolist())
        selected_sev = st.sidebar.multiselect("Severity", options=severities, default=severities)
        selected_type = st.sidebar.multiselect("Type", options=types, default=types)

        return start, end, selected_sev, selected_type

    def _kpi_row(self, df_filtered):
        # Simple KPI cards (dark theme)
        total = len(df_filtered)
        recent = df_filtered[df_filtered["timestamp"] >= (pd.Timestamp.now() - pd.Timedelta(days=7))].shape[0] if "timestamp" in df_filtered.columns else 0
        unresolved = df_filtered[df_filtered["status"].str.lower() != "resolved"].shape[0]
        critical = df_filtered[df_filtered["severity"].str.lower() == "critical"].shape[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#6ef0c5">Total</h3><h2 style="margin:0">{total}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#9bd1ff">Last 7d</h3><h2 style="margin:0">{recent}</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#ffb86b">Unresolved</h3><h2 style="margin:0">{unresolved}</h2></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#ff6b6b">Critical</h3><h2 style="margin:0">{critical}</h2></div>', unsafe_allow_html=True)

    def _overview_tab(self, df_filtered):
        st.markdown("### Overview", unsafe_allow_html=True)
        self._kpi_row(df_filtered)

        st.markdown("**Executive summary**")
        # very simple summary heuristics
        total = len(df_filtered)
        if total == 0:
            st.info("No incidents in current filter.")
            return
        top_type = df_filtered["type"].value_counts().idxmax()
        top_sev = df_filtered["severity"].value_counts().idxmax()
        st.write(f"- Top incident type: **{top_type}**")
        st.write(f"- Most common severity: **{top_sev}**")

        with st.expander("Show sample incidents (top 10)"):
            st.dataframe(df_filtered.head(10)[["incident_id", "timestamp", "type", "severity", "status", "asset"]])

    def _trends_tab(self, df_filtered):
        st.markdown("### Trends")
        if df_filtered.empty or df_filtered["timestamp"].dropna().empty:
            st.info("Not enough time-series data for trends.")
            return
        # incidents per day
        times = df_filtered.copy()
        times["date"] = times["timestamp"].dt.floor("d")
        series = times.groupby("date").size().reset_index(name="count")
        fig = px.line(series, x="date", y="count", title="Incidents per day", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # severity breakdown
        sev = df_filtered["severity"].value_counts().reset_index()
        sev.columns = ["severity", "count"]
        fig2 = px.pie(sev, names="severity", values="count", title="Severity breakdown (pie)")
        st.plotly_chart(fig2, use_container_width=True)

    def _data_tab(self, df_filtered):
        st.markdown("### Data")
        st.write("Filtered incident table (you can export or inspect rows).")
        st.dataframe(df_filtered[["incident_id", "timestamp", "type", "severity", "status", "asset", "assigned_to", "description"]], height=400)
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download filtered CSV", csv, file_name="filtered_cyber_incidents.csv", mime="text/csv")

    def _ai_tab(self, df_filtered):
        st.markdown("### AI Insight")
        st.write("Ask the cybersecurity assistant to summarise or explain patterns.")
        q = st.text_input("Question for AI (example: 'Why are phishing incidents rising?')", key="cyber_ai_q")
        if st.button("Ask AI (concise)"):
            # prepare a short context (top 5 incidents)
            ctx = df_filtered.head(5)[["incident_id", "timestamp", "type", "severity", "asset", "description"]].to_dict(orient="records")
            prompt = f"User question: {q}\n\nTop incidents: {ctx}\n\nAnswer concisely."
            if AIAssistant is None:
                st.error("AIAssistant not available (check app.services.ai_assistant).")
                return
            try:
                ai = AIAssistant(system_prompt="You are a concise cybersecurity assistant.")
                ans = ai.ask(prompt)
                st.markdown("**Assistant reply**")
                st.write(ans)
            except Exception as e:
                st.error(f"AI call failed: {e}")

    def render(self):
        st.title("🛡 Cybersecurity — SOC Overview")
        # Sidebar filters
        start, end, sel_sev, sel_type = self._sidebar_filters()

        # Apply filters safely
        df = self.df.copy()
        mask = pd.Series(True, index=df.index)
        if "timestamp" in df.columns:
            mask = mask & (df["timestamp"] >= start) & (df["timestamp"] <= end)
        if sel_sev:
            mask = mask & df["severity"].isin(sel_sev)
        if sel_type:
            mask = mask & df["type"].isin(sel_type)
        df_filtered = df[mask].reset_index(drop=True)

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Trends", "Data", "AI"])
        with tab1:
            self._overview_tab(df_filtered)
        with tab2:
            self._trends_tab(df_filtered)
        with tab3:
            self._data_tab(df_filtered)
        with tab4:
            self._ai_tab(df_filtered)

        # Render floating chatbot widget if present
        try:
            render_chatbot()
        except Exception:
            pass


# ---- run page ----
if __name__ == "__main__":  # allows local testing
    CyberDashboard().render()
else:
    CyberDashboard().render()
