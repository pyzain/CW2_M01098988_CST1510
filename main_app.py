# main_app.py
import os
import sys
import streamlit as st
import importlib

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------- Helper: safe rerun ----------
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    elif hasattr(st, "rerun"):
        st.rerun()

# ---------- Navigation function ----------
def navigate(page_name: str):
    """Set page_choice and rerun"""
    st.session_state.page_choice = page_name
    safe_rerun()

# ---------- Import and call page functions ----------
def import_and_call(module_name: str, fn_names: list):
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        st.error(f"Failed to import {module_name}: {e}")
        return False
    for fn in fn_names:
        if fn and hasattr(module, fn):
            try:
                getattr(module, fn)()
                return True
            except Exception as e:
                st.error(f"Error running {module_name}.{fn}(): {e}")
                return False
    # fallback to module-level rendering on import
    return True

# ---------- Pages configuration ----------
MENU = [
    "Home",
    "Dashboard",
    "Dashboard Cyber",
    "Dashboard Data",
    "Dashboard IT",
    "Users",
]

PAGE_MODULES = {
    "Home": ("app.pages.home", ["login_page", "main", "render"]),
    "Dashboard": ("app.pages.dashboard", ["main"]),
    "Dashboard Cyber": ("app.pages.Dashboard_Cyber", ["cyber_dashboard"]),
    "Dashboard Data": ("app.pages.Dashboard_Data", ["data_dashboard"]),
    "Dashboard IT": ("app.pages.Dashboard_IT", ["it_dashboard"]),
    "Users": ("app.pages.users_admin", ["main"]),
}

# ---------- Main app ----------
def main():
    st.set_page_config(page_title="MDI Platform", layout="wide")

    # ----------- Initialize session_state -----------
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "page_choice" not in st.session_state:
        st.session_state.page_choice = "Home"

    # ----------- Sidebar Navigation -----------
    choice = st.session_state.page_choice

    # Sidebar minimal
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}" if st.session_state.logged_in else "MDI Platform")
        menu_choice = st.selectbox("Navigate", MENU, index=MENU.index(choice) if choice in MENU else 0)

        if menu_choice != choice:
            navigate(menu_choice)

    # ---------- Load requested page ----------
    module_info = PAGE_MODULES.get(choice)
    if module_info:
        module_name, fn_names = module_info

        # Home is allowed even if not logged in
        if choice == "Home":
            import_and_call(module_name, fn_names)
            return

        # Dashboards require login
        if not st.session_state.logged_in:
            st.warning("You must be logged in to view dashboards. Go to Home and log in.")
            return

        import_and_call(module_name, fn_names)
        return

    st.info("Select a page from the sidebar.")

# ----------- Run ----------
if __name__ == "__main__":
    main()
