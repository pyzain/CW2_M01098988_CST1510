# app/services/user_service.py
"""
DB-backed user service used by the auth adapter (app/common/auth_cli.py).

Provides:
- register_user_db(username, password, role='user') -> (bool, message)
- login_user_db(username, password) -> (bool, message)
- migrate_users_from_file(conn=None, filepath=USERS_TXT) -> int  (returns migrated count)
"""

from pathlib import Path
import bcrypt
import sqlite3

# locate project root and DATA/users.txt
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]   # points to project root
DATA_DIR = PROJECT_ROOT / "DATA"
USERS_TXT = DATA_DIR / "users.txt"

# import DB helpers (make sure app/data/db.py exists)
try:
    from app.data.db import connect_database
    from app.data.users import get_user_by_username, insert_user
except Exception as e:
    # If these imports fail, re-raise with a clearer message
    raise ImportError("Required app.data modules missing or misnamed. Please ensure app/data/db.py and app/data/users.py exist.") from e

def register_user_db(username: str, password: str, role: str = 'user'):
    """
    Register user into DB. Returns (True, message) or (False, message).
    """
    if not username or not password:
        return False, "Username and password required."

    # Check if user exists
    existing = get_user_by_username(username)
    if existing:
        return False, f"Username '{username}' already exists."

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    inserted_id = insert_user(username, password_hash, role)
    if inserted_id:
        return True, f"User '{username}' registered."
    else:
        return False, "Registration failed (duplicate or DB error)."

def login_user_db(username: str, password: str):
    """
    Verify username/password against DB. Returns (True,message) or (False,message).
    """
    row = get_user_by_username(username)
    if not row:
        return False, "User not found."

    stored_hash = row['password_hash'] if 'password_hash' in row.keys() else row[2]
    try:
        ok = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception:
        return False, "Stored password hash invalid."

    return (True, "Login successful.") if ok else (False, "Incorrect password.")

def migrate_users_from_file(conn: sqlite3.Connection = None, filepath: Path = USERS_TXT):
    """
    Migrate users from DATA/users.txt into DB table 'users'.
    Returns number of users migrated.
    """
    close_conn = False
    if conn is None:
        conn = connect_database()
        close_conn = True

    if not filepath.exists():
        if close_conn:
            conn.close()
        return 0

    migrated = 0
    cur = conn.cursor()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 2)
            if len(parts) >= 2:
                username = parts[0].strip()
                password_hash = parts[1].strip()
                role = parts[2].strip() if len(parts) == 3 else 'user'
                try:
                    cur.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                (username, password_hash, role))
                    if cur.rowcount > 0:
                        migrated += 1
                except sqlite3.Error:
                    # skip problematic rows
                    continue
    conn.commit()
    if close_conn:
        conn.close()
    return migrated
