# pages/Data_Science.py
"""
Data Science dashboard - shows datasets metadata and simple charts.
Dark/cyber theme consistent with Cybersecurity page.
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

# Styling reuse (simple)
def _inject_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #0b0f14; color: #e6eef6; }
        .kpi-card { background: linear-gradient(90deg, rgba(5,10,15,0.9), rgba(15,20,30,0.6)); 
                    border-radius: 8px; padding: 12px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

class DatasetsLoader:
    def __init__(self):
        self.PROJECT_ROOT = Path(__file__).resolve().parents[1]
        self.csv_path = self.PROJECT_ROOT / "data" / "datasets_metadata.csv"

    def load(self) -> pd.DataFrame:
        # Try to read from DB first (if table exists) else use CSV
        try:
            from database.db import connect_database
            conn = connect_database()
            df = pd.read_sql_query("SELECT * FROM datasets", conn)
            conn.close()
            if df is not None and not df.empty:
                return df
        except Exception:
            pass

        if self.csv_path.exists():
            # CSV content provided: id,name,rows,size_mb,owner,last_updated
            df = pd.read_csv(self.csv_path, header=None)
            # Map to columns if headerless
            if df.shape[1] >= 6:
                df.columns = ["dataset_id", "name", "rows", "size_mb", "owner", "last_updated"]
            return df
        return pd.DataFrame(columns=["dataset_id", "name", "rows", "size_mb", "owner", "last_updated"])

class DataScienceDashboard:
    def __init__(self):
        _inject_css()
        self.df = DatasetsLoader().load()
        # normalize columns
        self.df.columns = [str(c).strip().lower().replace(" ", "_") for c in self.df.columns]

    def _sidebar(self):
        st.sidebar.header("Filters")
        owners = sorted(self.df["owner"].dropna().unique().tolist())
        owner = st.sidebar.multiselect("Owner", options=owners, default=owners)
        min_rows = int(self.df["rows"].min()) if not self.df["rows"].dropna().empty else 0
        max_rows = int(self.df["rows"].max()) if not self.df["rows"].dropna().empty else 1000000
        rows_range = st.sidebar.slider("Rows range", min_value=min_rows, max_value=max_rows, value=(min_rows, max_rows))
        return owner, rows_range

    def _kpis(self, df):
        total = len(df)
        total_rows = int(df["rows"].sum()) if "rows" in df.columns else 0
        avg_size = float(df["size_mb"].mean()) if "size_mb" in df.columns and not df["size_mb"].dropna().empty else 0.0

        c1, c2, c3 = st.columns([1.5, 1, 1])
        c1.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#6ef0c5">Datasets</h3><h2 style="margin:0">{total}</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#9bd1ff">Total rows</h3><h2 style="margin:0">{total_rows}</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi-card"><h3 style="margin:0;color:#ffb86b">Avg size (MB)</h3><h2 style="margin:0">{avg_size:.1f}</h2></div>', unsafe_allow_html=True)

    def _overview(self, df):
        st.markdown("### Overview")
        self._kpis(df)
        st.write("List of datasets and owners.")
        st.dataframe(df[["dataset_id", "name", "rows", "size_mb", "owner", "last_updated"]].fillna("-"), height=300)

    def _trends(self, df):
        st.markdown("### Trends")
        if df.empty:
            st.info("No datasets metadata available.")
            return
        if "rows" in df.columns:
            fig = px.bar(df, x="name", y="rows", title="Rows per dataset")
            st.plotly_chart(fig, use_container_width=True)
        if "size_mb" in df.columns:
            fig2 = px.pie(df, names="name", values="size_mb", title="Dataset sizes (MB)")
            st.plotly_chart(fig2, use_container_width=True)

    def _data(self, df):
        st.markdown("### Data")
        st.dataframe(df, height=300)
        st.download_button("Download datasets CSV", df.to_csv(index=False).encode("utf-8"), file_name="datasets_metadata_export.csv")

    def _ai(self, df):
        st.markdown("### AI Insight")
        prompt = "Please summarize the available datasets and point out any dataset that looks unusually large or small."
        if st.button("Get AI summary"):
            if AIAssistant is None:
                st.error("AIAssistant not configured.")
                return
            try:
                ai = AIAssistant(system_prompt="You are a data platform assistant.")
                ctx = df.head(5).to_dict(orient="records")
                ans = ai.ask(f"{prompt}\n\nTop datasets: {ctx}")
                st.write(ans)
            except Exception as e:
                st.error(f"AI error: {e}")

    def render(self):
        st.title("📊 Data Science — Datasets")
        owner_sel, rows_range = self._sidebar()
        df = self.df.copy()
        if "owner" in df.columns and owner_sel:
            df = df[df["owner"].isin(owner_sel)]
        if "rows" in df.columns:
            low, high = rows_range
            df = df[(df["rows"] >= low) & (df["rows"] <= high)]

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
    DataScienceDashboard().render()
else:
    DataScienceDashboard().render()
