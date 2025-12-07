# services/auth_manager.py
"""
Very simple Authentication Manager.
- Handles user registration.
- Handles user login.
- Uses SHA256 hashing (only for learning purposes).
"""

import hashlib
from typing import Optional

from app.models.user import User
from app.services.database_manager import DatabaseManager


class AuthManager:
    """
    A small helper class that manages user accounts.
    It works together with a DatabaseManager to read/write data.
    """

    def __init__(self, db: DatabaseManager):
        # Save the database connection so we can use it later
        self.db = db
        self.db.connect()

        # Make sure the users table exists before we try to use it
        self.db.ensure_users_table()

    # ----------------------------------------------------------------------
    # PASSWORD HELPERS
    # ----------------------------------------------------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Convert a plain password into a SHA256 hash.

        Why?
        - We never store actual passwords.
        - Hashing protects the user if the database leaks.
        """
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _check_password(plain_password: str, stored_hash: str) -> bool:
        """
        Check if the given plain password matches the stored hash.
        """
        return AuthManager._hash_password(plain_password) == stored_hash

    # ----------------------------------------------------------------------
    # USER ACTIONS
    # ----------------------------------------------------------------------

    def register_user(self, username: str, password: str, role: str = "user") -> int:
        """
        Create a new user in the database.
        Returns: the new user's ID.

        Steps:
        1. Hash the password
        2. Insert the user into the database
        3. Return the auto-generated ID
        """
        password_hash = self._hash_password(password)

        cur = self.db.execute_query(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )

        return cur.lastrowid

    def login_user(self, username: str, password: str) -> Optional[User]:
        """
        Attempt to log a user in.
        Returns:
            - User object (if login successful)
            - None (if username doesn't exist or password is wrong)
        """

        # Try to find the user in the database
        row = self.db.fetch_one(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        )

        if row is None:
            return None  # The username does not exist

        user_id, username_db, stored_hash, role_db = row

        # Check password
        if self._check_password(password, stored_hash):
            # Create a User object which will be used by the rest of the app
            return User(
                id=user_id,
                username=username_db,
                password_hash=stored_hash,
                role=role_db
            )
        return None  # Incorrect password
