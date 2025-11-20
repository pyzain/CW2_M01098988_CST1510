# app/common/auth_cli.py
"""
Clean authentication adapter using DATABASE ONLY.
File-based users.txt logic has been fully removed.

This module provides two simple functions:
- verify_password(username, password)
- register_user(username, password)

These delegate directly to user_service, which handles all
interaction with the SQLite database.
"""

from app.services.user_service import login_user_db, register_user_db


def verify_password(username: str, plain_text_password: str):
    """Authenticate a user using the database."""
    try:
        ok, msg = login_user_db(username, plain_text_password)
        return ok, msg
    except Exception as e:
        return False, f"Authentication failed: {e}"


def register_user(username: str, plain_text_password: str):
    """Register a new user into the database."""
    try:
        ok, msg = register_user_db(username, plain_text_password)
        return ok, msg
    except Exception as e:
        return False, f"Registration failed: {e}"
