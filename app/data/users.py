# app/data/users.py
from .db import connect_database
import sqlite3

def get_user_by_username(username):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row  # sqlite3.Row or None

def insert_user(username, password_hash, role='user'):
    conn = connect_database()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        inserted = cur.lastrowid
    except sqlite3.IntegrityError:
        inserted = None
    conn.close()
    return inserted
