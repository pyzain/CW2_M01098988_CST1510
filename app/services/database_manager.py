# app/services/database_manager.py
"""
A lightweight DatabaseManager class used by services.
"""
from typing import Optional, Tuple, Any, Sequence
from database.db import connect_database

class DatabaseManager:
    """Small wrapper over sqlite3 connection/cursor providing convenience methods."""
    def __init__(self, db_path: Optional[str] = None):
        self.conn = None

    def connect(self):
        if self.conn is None:
            self.conn = connect_database()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute_query(self, sql: str, params: Optional[Sequence[Any]] = None):
        """Execute INSERT/UPDATE/DELETE and return cursor."""
        self.connect()
        cur = self.conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        self.conn.commit()
        return cur

    def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None):
        self.connect()
        cur = self.conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchone()

    def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None):
        self.connect()
        cur = self.conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchall()

    # utility
    def ensure_users_table(self):
        self.connect()
        self.execute_query(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
            """
        )
