import sqlite3
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, db_path="DATA/intelligence_platform.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def create_tables(self):
        """Create all required tables"""
        self.connect()
        # Users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        # Cyber incidents
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cyber_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT,
                severity TEXT,
                status TEXT,
                reported_date TEXT
            )
        """)
        # IT tickets
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_type TEXT,
                assigned_to TEXT,
                status TEXT,
                created_date TEXT
            )
        """)
        # Dataset metadata
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT,
                rows INTEGER,
                size_mb REAL,
                source TEXT
            )
        """)
        self.conn.commit()
        self.close()

    def migrate_users_from_txt(self, users_txt="DATA/users.txt"):
        """Read users.txt and insert into users table"""
        if not os.path.exists(users_txt):
            print("users.txt not found")
            return
        self.connect()
        with open(users_txt, "r") as f:
            for line in f:
                username, password_hash = line.strip().split(",", 1)
                # default role as 'user' for simplicity
                try:
                    self.cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                                        (username, password_hash, "user"))
                except sqlite3.IntegrityError:
                    pass
        self.conn.commit()
        self.close()

    # Simple CRUD for users table
    def get_user(self, username):
        self.connect()
        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = self.cursor.fetchone()
        self.close()
        return user

    def add_user(self, username, password_hash, role="user"):
        self.connect()
        self.cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                            (username, password_hash, role))
        self.conn.commit()
        self.close()

    # Add more CRUD for other tables as needed (cyber_incidents, it_tickets, datasets_metadata)
