# app/common/navigation.py
import streamlit as st
from typing import Optional

def safe_rerun():
    """Version-compatible rerun helper."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

def navigate(page_name: str, query_key: Optional[str] = "page"):
    """
    Central navigation helper used by pages and the orchestrator.

    - Sets st.session_state.page_choice so main_app can consume it.
    - Updates query params to force a full Streamlit rerun (reliable).
    """
    st.session_state.page_choice = page_name
    # update query params so Streamlit treats this as a navigation and restarts script
    try:
        st.experimental_set_query_params(**{query_key: page_name})
    except Exception:
        # fallback: some Streamlit versions may not have experimental_set_query_params
        pass
    safe_rerun()
