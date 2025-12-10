# pages/IT_Operations.py
"""
💻 IT Operations Dashboard
-------------------------
- KPIs for tickets
- Visualizations for priorities, status, and assignees
- Create/update tickets
- Integrated IT assistant using AIAssistant(role_prompt)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from app.models.it_ticket import (
    get_all_tickets_df,
    create_ticket,
    update_ticket_status,
    get_ticket_by_id
)
from ai_core import AIAssistant

def render():
    # 1️⃣ Require login
    if not st.session_state.get("user"):
        st.warning("Please login from Home before viewing IT Operations dashboard.")
        return

    st.title("💻 IT Operations Dashboard")
    st.write("Monitor tickets, visualize KPIs, and get AI assistance.")

    # 2️⃣ Load tickets
    df = get_all_tickets_df()

    # 3️⃣ If no tickets, allow creating test tickets
    if df.empty:
        st.info("No IT tickets found. You can create a test ticket below.")
        with st.expander("Create a test ticket manually"):
            pr = st.selectbox("Priority", ["low", "medium", "high"], index=1)
            desc = st.text_area("Description", "")
            ass = st.text_input("Assign to", "unassigned")
            if st.button("Create ticket (test)"):
                tid = create_ticket(pr, desc, ass)
                st.success(f"Created ticket id {tid}. Refresh the page to see it.")
        return

    # 4️⃣ KPI cards
    total = len(df)
    open_cnt = df[df["status"].str.lower() != "resolved"].shape[0]
    high_pr = df[df["priority"].str.lower() == "high"].shape[0]
    avg_res_hours = round(df["resolution_time_hours"].dropna().astype(float).mean(), 2) if "resolution_time_hours" in df.columns and not df["resolution_time_hours"].dropna().empty else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total tickets", total)
    k2.metric("Open tickets", open_cnt)
    k3.metric("High priority", high_pr)
    k4.metric("Avg. resolution time (hrs)", avg_res_hours)

    st.markdown("---")

    # 5️⃣ Visualizations
    st.subheader("Ticket Visualizations")

    # Priority distribution (pie)
    fig_priority = px.pie(
        df,
        names="priority",
        title="Priority Distribution",
        hole=0.4
    )
    st.plotly_chart(fig_priority, use_container_width=True)

    # Status distribution (bar)
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status_name", "count"]  # Rename explicitly
    fig_status = px.bar(
        status_counts,
        x="status_name",
        y="count",
        labels={"status_name": "Status", "count": "Count"},
        title="Tickets by Status",
        color="status_name"
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # Tickets per assignee (bar)
    assignee_counts = df["assigned_to"].value_counts().reset_index()
    assignee_counts.columns = ["assignee", "count"]
    fig_assignee = px.bar(
        assignee_counts,
        x="assignee",
        y="count",
        labels={"assignee": "Assignee", "count": "Tickets"},
        title="Tickets per Assignee",
        color="count"
    )
    st.plotly_chart(fig_assignee, use_container_width=True)

    st.markdown("---")

    # 6️⃣ Show top 100 tickets
    st.subheader("Recent Tickets (top 100)")
    st.dataframe(df.head(100), use_container_width=True)

    st.markdown("---")

    # 7️⃣ Create new ticket form
    st.subheader("Create New Ticket")
    with st.form("create_ticket_form", clear_on_submit=True):
        p = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        description = st.text_area("Description", placeholder="Brief description")
        assigned_to = st.text_input("Assign to", value="unassigned")
        submitted = st.form_submit_button("Create Ticket")
        if submitted:
            new_id = create_ticket(p, description, assigned_to)
            st.success(f"Created ticket with ID {new_id}.")
            st.rerun()

    st.markdown("---")

    # 8️⃣ Update ticket status
    st.subheader("Update Ticket Status")
    ticket_choices = df["ticket_id"].astype(str).tolist()
    if ticket_choices:
        sel = st.selectbox("Select ticket ID", ticket_choices)
        sel_id = int(sel)
        current = get_ticket_by_id(sel_id)
        st.markdown(f"**Current Status:** {current.get('status')} — Assigned to **{current.get('assigned_to')}**")
        new_status = st.selectbox("New Status", ["open", "in progress", "resolved", "closed"], index=0)
        res_time = st.number_input("Resolution Time (hrs) — optional", min_value=0.0, value=0.0, step=0.5)
        if st.button("Apply Update"):
            rt_val = res_time if res_time > 0 else None
            update_ticket_status(sel_id, new_status, rt_val)
            st.success("Ticket updated successfully.")
            st.rerun()
    else:
        st.info("No tickets to update.")

    st.markdown("---")

    # -----------------------------------------
    # AI Assistant (IT Dashboard)
    # -----------------------------------------
    st.subheader("💻 IT Systems Assistant")

    if "it_chat" not in st.session_state:
        st.session_state.it_chat = []

    for msg in st.session_state.it_chat:
        speaker = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
        st.markdown(f"**{speaker}:** {msg['content']}")

    st.markdown("---")

    user_query = st.text_input("Ask an IT or systems question...", key="it_input")
    send = st.button("Send")
    clear = st.button("Clear Chat")

    if clear:
        st.session_state.it_chat = []
        st.rerun()

    if send and user_query.strip():

        st.session_state.it_chat.append({"role": "user", "content": user_query})

        history = "\n".join(
            [f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
             for m in st.session_state.it_chat]
        )

        # ---- SMART SNAPSHOT (IT) ----
        try:
            snapshot = "=== IT Dashboard Snapshot ===\n"

            # schema
            snapshot += "\nColumns:\n" + ", ".join(dff.columns)

            # health states
            if "status" in dff.columns:
                snapshot += "\n\nSystem status counts:\n"
                snapshot += dff["status"].value_counts().to_string()

            # recent failures / warnings
            if "status" in dff.columns and "timestamp" in dff.columns:
                failures = dff[dff["status"].isin(["error", "down", "failed"])] \
                    .sort_values("timestamp", ascending=False) \
                    .head(10)
                snapshot += "\n\nRecent failures:\n" + failures.to_string()

            # filtered sample
            snapshot += "\n\nFiltered sample (first 15):\n"
            snapshot += dff.head(15).to_string()

        except Exception:
            snapshot = "(Snapshot unavailable)"

        ai = AIAssistant(
            role_prompt=(
                "You are a senior IT systems engineer. "
                "Explain root causes, system health, troubleshooting steps, "
                "and help users understand logs or specific entries."
            )
        )

        reply = ai.ask(
            query=user_query,
            data_context=f"{snapshot}\n\n=== Conversation ===\n{history}"
        )

        st.session_state.it_chat.append({"role": "assistant", "content": reply})
        st.rerun()
