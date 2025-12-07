# pages/IT_Operations.py
"""
IT Operations dashboard - shows tickets and basic SLA view.
Dark theme consistent with other pages.
Tabs: Overview | Trends | Data | AI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

try:
    from app.services.ai_assistant import AIAssistant
except Exception:
    AIAssistant = None

def _inject_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #0b0f14; color: #e6eef6; }
        .kpi-card { background: linear-gradient(90deg, rgba(5,10,15,0.9), rgba(15,20,30,0.6)); border-radius: 8px; padding: 12px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

class TicketsLoader:
    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.csv_path = self.PROJECT_ROOT / "data" / "it_tickets.csv"

    def load(self):
        try:
            from database.db import connect_database
            conn = connect_database()
            df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
            conn.close()
            if df is not None and not df.empty:
                return df
        except Exception:
            pass

        # CSV fallback (assume columns if headerless)
        if self.csv_path.exists():
            df = pd.read_csv(self.csv_path, header=0)
            return df
        return pd.DataFrame(columns=["ticket_id", "title", "priority", "status", "assigned_to", "created_at", "resolved_at"])

class ITOperationsDashboard:
    def __init__(self):
        _inject_css()
        self.df = TicketsLoader().load()
        self.df.columns = [str(c).strip().lower().replace(" ", "_") for c in self.df.columns]

    def _sidebar(self):
        st.sidebar.header("Filters")
        priorities = sorted(self.df["priority"].dropna().unique().tolist()) if "priority" in self.df.columns else []
        statuses = sorted(self.df["status"].dropna().unique().tolist()) if "status" in self.df.columns else []
        sel_pr = st.sidebar.multiselect("Priority", options=priorities, default=priorities)
        sel_st = st.sidebar.multiselect("Status", options=statuses, default=statuses)
        return sel_pr, sel_st

    def _kpis(self, df):
        total = len(df)
        open_count = df[df["status"].str.lower() == "open"].shape[0] if "status" in df.columns else 0
        high_pr = df[df["priority"].str.lower() == "high"].shape[0] if "priority" in df.columns else 0
        avg_res_time = "-"
        if "created_at" in df.columns and "resolved_at" in df.columns and not df["resolved_at"].dropna().empty:
            try:
                created = pd.to_datetime(df["created_at"], errors="coerce")
                resolved = pd.to_datetime(df["resolved_at"], errors="coerce")
                avg = (resolved - created).dt.total_seconds().mean() / 3600.0
                avg_res_time = f"{avg:.1f}h"
            except Exception:
                avg_res_time = "-"

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#6ef0c5">Tickets</h3><h2 style="margin:0">{total}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#9bd1ff">Open</h3><h2 style="margin:0">{open_count}</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#ffb86b">High priority</h3><h2 style="margin:0">{high_pr}</h2></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#ff6b6b">Avg res time</h3><h2 style="margin:0">{avg_res_time}</h2></div>', unsafe_allow_html=True)

    def _overview(self, df):
        st.markdown("### Overview")
        self._kpis(df)
        with st.expander("Sample tickets"):
            st.dataframe(df.head(10))

    def _trends(self, df):
        st.markdown("### Trends")
        if "created_at" in df.columns:
            df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
            cts = df.groupby(df["created_at_dt"].dt.floor("d")).size().reset_index(name="count")
            fig = px.line(cts, x="created_at_dt", y="count", title="Tickets created per day")
            st.plotly_chart(fig, use_container_width=True)
        if "priority" in df.columns:
            pc = df["priority"].value_counts().reset_index()
            pc.columns = ["priority", "count"]
            fig2 = px.bar(pc, x="priority", y="count", title="Tickets by priority")
            st.plotly_chart(fig2, use_container_width=True)

    def _data(self, df):
        st.markdown("### Data")
        st.dataframe(df, height=300)
        st.download_button("Download tickets CSV", df.to_csv(index=False).encode("utf-8"), file_name="it_tickets_export.csv")

    def _ai(self, df):
        st.markdown("### AI Insight")
        prompt = "Summarize ticket workload and recommend priorities to reduce backlog."
        if st.button("Ask AI about tickets"):
            if AIAssistant is None:
                st.error("AIAssistant not available.")
                return
            try:
                ai = AIAssistant(system_prompt="You are an IT operations assistant.")
                ctx = df.head(10).to_dict(orient="records")
                ans = ai.ask(f"{prompt}\n\nSample tickets: {ctx}")
                st.write(ans)
            except Exception as e:
                st.error(f"AI error: {e}")

    def render(self):
        st.title("💻 IT Operations — Tickets")
        sel_pr, sel_st = self._sidebar()
        df = self.df.copy()
        if "priority" in df.columns and sel_pr:
            df = df[df["priority"].isin(sel_pr)]
        if "status" in df.columns and sel_st:
            df = df[df["status"].isin(sel_st)]

        t1, t2, t3, t4 = st.tabs(["Overview", "Trends", "Data", "AI"])
        with t1:
            self._overview(df)
        with t2:
            self._trends(df)
        with t3:
            self._data(df)
        with t4:
            self._ai(df)

if __name__ == "__main__":
    ITOperationsDashboard().render()
else:
    ITOperationsDashboard().render()
