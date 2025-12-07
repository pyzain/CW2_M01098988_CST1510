# services/database_manager.py
"""
Simple database manager.
Handles connecting to SQLite and creating required tables.
"""

import sqlite3
import os

class DatabaseManager:
    """Handles all DB operations in one place."""

    def __init__(self, db_path="database/platform.db"):
        # Make sure the folder exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.conn = None

    # ----------------------------------------------------------
    # Connect to DB
    # ----------------------------------------------------------
    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.conn

    # ----------------------------------------------------------
    # Ensure users table exists
    # ----------------------------------------------------------
    def ensure_users_table(self):
        """Creates the users table if it does not already exist."""
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT
        );
        """
        self.execute_query(query)

    # ----------------------------------------------------------
    # Execute write operations
    # ----------------------------------------------------------
    def execute_query(self, query, params=()):
        cursor = self.connect().cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    # ----------------------------------------------------------
    # Fetch one record
    # ----------------------------------------------------------
    def fetch_one(self, query, params=()):
        cursor = self.connect().cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
