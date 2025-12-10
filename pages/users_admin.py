# pages/users_admin.py
"""
Admin: Users management view
Handles viewing users, adding new users, deleting users, and resetting passwords.
"""

import streamlit as st
import pandas as pd


def render(db_manager, auth_manager):
    """
    Render the User Administration Panel.
    Args:
        db_manager: Instance of DatabaseManager (for fetching/deleting users)
        auth_manager: Instance of AuthManager (for creating users and resetting passwords)
    """

    # --- 1. Security Check ---
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Please log in to access this page.")
        return

    current_user = st.session_state.user
    if current_user.get_role() != "admin":
        st.error("⛔ Access Denied: You do not have administrator privileges.")
        return

    st.title("👥 User Management (Admin)")
    st.markdown("Manage user accounts, roles, and security credentials.")

    # --- 2. Load Data ---
    # Fetch all users to populate tables and dropdowns
    try:
        rows = db_manager.fetch_all("SELECT id, username, role FROM users ORDER BY id ASC")
        data = [dict(row) for row in rows]
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading users: {e}")
        df = pd.DataFrame()

    # --- 3. View Users Table ---
    st.subheader(f"Registered Users ({len(df)})")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        # CSV Export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="users_export.csv", mime="text/csv")
    else:
        st.info("No users found.")

    st.markdown("---")

    # --- 4. Add New User ---
    st.subheader("Add New User")
    with st.form("create_user_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_u = st.text_input("Username")
        with c2:
            new_p = st.text_input("Password", type="password")
        with c3:
            new_r = st.selectbox("Role", ["user", "admin"])

        if st.form_submit_button("Create User"):
            if new_u and new_p:
                try:
                    auth_manager.register_user(new_u, new_p, new_r)
                    st.success(f"✅ User '{new_u}' created.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            else:
                st.warning("Username and password required.")

    st.markdown("---")

    # --- 5. Reset Password ---
    st.subheader("Reset User Password")
    st.markdown("Update a user's password securely (hashes the new password).")

    if not df.empty:
        # Create a dictionary for the dropdown: "Username (Role)" -> "Username"
        # We use username here because auth_manager.reset_password expects a username
        user_map_name = {f"{r['username']} ({r['role']})": r['username'] for r in data}

        target_user_display = st.selectbox("Select User to Reset", options=list(user_map_name.keys()))
        target_username = user_map_name[target_user_display]

        new_reset_pass = st.text_input("New Password", type="password", key="reset_pass_input")

        if st.button("Update Password"):
            if new_reset_pass:
                try:
                    success = auth_manager.reset_password(target_username, new_reset_pass)
                    if success:
                        st.success(f"✅ Password for '{target_username}' has been updated.")
                    else:
                        st.error("User not found.")
                except Exception as e:
                    st.error(str(e))
            else:
                st.warning("Please enter a new password.")
    else:
        st.info("No users available to edit.")

    st.markdown("---")

    # --- 6. Delete Users ---
    st.subheader("Delete Users")
    if not df.empty:
        # Map for ID selection
        user_map_id = {f"{r['id']}: {r['username']} ({r['role']})": r['id'] for r in data}
        selected_dels = st.multiselect("Select users to delete", options=list(user_map_id.keys()))

        if selected_dels:
            st.warning("⚠️ Deletion is permanent.")
            if st.button("Confirm Deletion", type="primary"):
                count = 0
                for label in selected_dels:
                    uid = user_map_id[label]
                    if uid == current_user.id:
                        st.error("You cannot delete yourself.")
                        continue

                    try:
                        db_manager.execute_query("DELETE FROM users WHERE id = ?", (uid,))
                        count += 1
                    except Exception as e:
                        st.error(f"Error deleting {label}: {e}")

                if count > 0:
                    st.success(f"Deleted {count} user(s).")
                    st.rerun()