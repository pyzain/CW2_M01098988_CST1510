# pages/AI_Assistant.py
import streamlit as st
import pandas as pd
import os
from ai_core import AIAssistant


def load_all_data():
    """
    Loads all CSV files and merges them into a long text context block
    for the AI to read.
    """
    data_context = ""
    paths = {
        "IT Tickets": "data/it_tickets.csv",
        "Cyber Logs": "data/cyber_logs.csv",
        "Data Science Notes": "data/ds_notes.csv",
    }

    for name, path in paths.items():
        data_context += f"\n\n=== {name} ===\n"

        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                data_context += df.to_string()
            except Exception as e:
                data_context += f"(Error loading file: {e})"
        else:
            data_context += "(No file found)"

    return data_context



def render():
    st.title("💡 Unified AI Assistant (Brain)")
    st.write("This assistant has access to **ALL** modules and **ALL** data files.")

    user_query = st.text_area("Ask anything:", placeholder="Type your question here...")

    if st.button("Ask AI"):
        if not user_query.strip():
            st.warning("Please enter a question.")
            return

        # Load all data files
        all_data = load_all_data()

        # Master Assistant (Unified Role)
        ai = AIAssistant(
            role_prompt=(
                "You are the master AI assistant with access to cybersecurity logs, "
                "IT tickets, and data science notes. "
                "Always give simple, clear, and helpful answers."
            )
        )

        # Ask the AI
        response = ai.ask(user_query, data_context=all_data)

        st.markdown("### 🧠 AI Response:")
        st.write(response)



if __name__ == "__main__":
    render()
