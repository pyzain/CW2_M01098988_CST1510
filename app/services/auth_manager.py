# app/services/auth_manager.py
"""
Simple AuthManager using SHA256 for the coursework (bcrypt recommended in production).
"""
import hashlib
from typing import Optional
from app.models.user import User
from app.services.database_manager import DatabaseManager

class AuthManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.db.connect()
        self.db.ensure_users_table()

    @staticmethod
    def _hash_password(password: str) -> str:
        """Internal helper to hash passwords consistently."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def register_user(self, username: str, password: str, role: str = "user") -> int:
        password_hash = self._hash_password(password)
        try:
            cur = self.db.execute_query(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            return cur.lastrowid
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise Exception("Username already exists. Please choose a different username.")
            raise Exception(f"Registration failed: {e}")

    def login_user(self, username: str, password: str) -> Optional[User]:
        row = self.db.fetch_one("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        if not row:
            return None
        user_id, username_db, stored_hash, role_db = row
        if self._hash_password(password) == stored_hash:
            return User(user_id=user_id, username=username_db, role=role_db)
        return None

    # --- NEW METHOD FOR ADMIN PANEL ---
    def reset_password(self, username: str, new_password: str) -> bool:
        """
        Updates the password for a specific user.
        Returns True if successful (user found), False otherwise.
        """
        new_hash = self._hash_password(new_password)
        try:
            cur = self.db.execute_query(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (new_hash, username)
            )
            return cur.rowcount > 0
        except Exception as e:
            raise Exception(f"Password reset failed: {e}")