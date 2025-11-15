# app/common/auth_cli.py
"""
Adapter for authentication.

Behavior:
- If DB-backed service (app.services.user_service) is available, delegate to it.
- Otherwise fall back to file-based users.txt implementation (existing behavior).
- Always return (ok: bool, message: str).
- Log exceptions to app.log.
"""

import bcrypt
import os
import traceback
from datetime import datetime
from pathlib import Path

# --- Paths / Files (same as before) ---
THIS_DIR = os.path.dirname(os.path.abspath(__file__))        # .../app/common
PROJECT_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))    # .../CW2_...
DATA_DIR = os.path.join(PROJECT_ROOT, "DATA")
USERS_FILE = os.path.join(DATA_DIR, "users.txt")
LOG_FILE = os.path.join(PROJECT_ROOT, "app.log")

os.makedirs(DATA_DIR, exist_ok=True)

def _log(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} - {msg}\n")
    except Exception:
        pass

# --- Keep the original file-based functions (unchanged behavior) ---
def _hash_password_file(plain_text_password: str) -> str:
    pw = plain_text_password.encode("utf-8")
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")

def _verify_password_file(username: str, plain_text_password: str):
    """File-based verify: returns (ok, message)."""
    try:
        if not os.path.exists(USERS_FILE):
            return False, "No users registered yet."

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                user, hashed = line.strip().split(",", 1)
                if user == username:
                    ok = bcrypt.checkpw(plain_text_password.encode("utf-8"), hashed.encode("utf-8"))
                    return (True, "Login successful.") if ok else (False, "Incorrect password.")
        return False, "Username not found."
    except Exception:
        _log("verify_password_file exception:\n" + traceback.format_exc())
        return False, "Authentication error (see app.log)."

def _register_user_file(username: str, plain_text_password: str):
    """File-based registration: returns (ok, message)."""
    try:
        if not username or not plain_text_password:
            return False, "Username and password cannot be empty."

        # check duplicates
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    user, _ = line.strip().split(",", 1)
                    if user == username:
                        return False, "Username already exists."

        hashed = _hash_password_file(plain_text_password)
        # append atomically
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{username},{hashed}\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        return True, f"User '{username}' registered successfully."
    except Exception:
        _log("register_user_file exception:\n" + traceback.format_exc())
        return False, "Registration error (see app.log)."

# --- Try to import DB-backed services (optional) ---
_USE_DB = False
try:
    from app.services.user_service import login_user_db, register_user_db
    _USE_DB = True
except Exception as e:
    # If import fails, we'll use file-based methods
    _log("DB auth not available; falling back to file-based auth. Import error: " + repr(e))
    _USE_DB = False

# --- Public API used by Login.py (keeps same names) ---
def verify_password(username: str, plain_text_password: str):
    """
    Verify username/password.
    Returns (ok: bool, message: str).
    """
    if _USE_DB:
        try:
            ok, msg = login_user_db(username, plain_text_password)
            return ok, msg
        except Exception:
            _log("verify_password (DB) exception:\n" + traceback.format_exc())
            # Fall back to file method if DB call errors
            return _verify_password_file(username, plain_text_password)
    else:
        return _verify_password_file(username, plain_text_password)

def register_user(username: str, plain_text_password: str):
    """
    Register user.
    Returns (ok: bool, message: str).
    """
    if _USE_DB:
        try:
            ok, msg = register_user_db(username, plain_text_password)
            return ok, msg
        except Exception:
            _log("register_user (DB) exception:\n" + traceback.format_exc())
            # Fall back to file method if DB call errors
            return _register_user_file(username, plain_text_password)
    else:
        return _register_user_file(username, plain_text_password)

from app.services.user_service import login_user_db, register_user_db
def verify_password(username, password):
        ok, msg = login_user_db(username, password)
        return ok, msg

def register_user(username, password):
        return register_user_db(username, password)
