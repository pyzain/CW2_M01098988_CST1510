# database/db_initializer.py
"""
Initialize the platform database and auto-load CSVs into tables.
Ensures consistent paths, prevents duplicate DBs, and handles schema automatically.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from database.db import connect_database

# Paths
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"  # CSV files live here
DB_FILE = PROJECT_ROOT / "database" / "platform.db"  # single DB

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_FILE.parent, exist_ok=True)


def init_database():
    """
    Create the main DB if it doesn't exist, and load CSVs.
    Can be run multiple times safely.
    """
    conn = connect_database()
    cursor = conn.cursor()

    # ---------------- Users table ----------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
        """
    )

    # ---------------- Cyber incidents table ----------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cyber_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            incident_type TEXT,
            severity TEXT,
            status TEXT,
            description TEXT,
            reported_by TEXT,
            asset TEXT
        )
        """
    )

    # ---------------- IT tickets table ----------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS it_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            status TEXT,
            priority TEXT,
            assigned_to TEXT,
            created_at TEXT
        )
        """
    )

    # ---------------- Datasets metadata table ----------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            owner TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()

    # ---------------- Auto-load CSVs ----------------
    csv_mapping = {
        "cyber_incidents.csv": "cyber_incidents",
        "it_tickets.csv": "it_tickets",
        "datasets_metadata.csv": "datasets",
    }

    for csv_name, table_name in csv_mapping.items():
        csv_path = DATA_DIR / csv_name
        if csv_path.exists():
            df = pd.read_csv(csv_path)

            # Only keep columns that exist in DB table
            cursor.execute(f"PRAGMA table_info({table_name})")
            db_cols = [col[1] for col in cursor.fetchall()]
            df = df[[c for c in df.columns if c in db_cols]]

            # --- remove primary key from CSV to avoid conflicts ---
            if table_name == "datasets" and "dataset_id" in df.columns:
                df = df.drop(columns=["dataset_id"])

            # Append safely
            if not df.empty:
                # Drop ID column if it exists (AUTO-INCREMENT handles it)
                id_col = {
                    "cyber_incidents": "id",
                    "it_tickets": "ticket_id",
                    "datasets": "dataset_id",
                }

                if id_col.get(table_name) in df.columns:
                    df = df.drop(columns=[id_col[table_name]])

                df.to_sql(table_name, conn, if_exists="append", index=False)

        else:
            print(f"[DB INIT] CSV not found: {csv_path}")

    conn.close()
    print("[DB INIT] Database initialized successfully.")


if __name__ == "__main__":
    init_database()
