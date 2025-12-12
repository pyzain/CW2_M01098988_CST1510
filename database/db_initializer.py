"""
Creates the full database schema and imports CSV data exactly once.
Safe on reload (idempotent).
"""

import pandas as pd
from pathlib import Path
from database.db import connect_database

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

CSV_MAP = {
    "cyber_incidents.csv": "cyber_incidents",
    "it_tickets.csv": "it_tickets",
    "datasets_metadata.csv": "datasets",
}


# ----------------------------------------------------------
# 1. CREATE ALL TABLES
# ----------------------------------------------------------

def _create_schema(conn):
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # CYBER INCIDENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cyber_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT,
        timestamp TEXT,
        severity TEXT,
        incident_type TEXT,
        status TEXT,
        description TEXT,
        reported_by TEXT,
        asset TEXT
    )
    """)

    # IT TICKETS (correct structure)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS it_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT,
        title TEXT,
        description TEXT,
        status TEXT,
        priority TEXT,
        assigned_to TEXT,
        created_at TEXT
    )
    """)

    # DATASETS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_name TEXT,
        rows INTEGER,
        file_size_mb REAL,
        owner TEXT,
        last_updated TEXT
    )
    """)

    conn.commit()


# ----------------------------------------------------------
# 2. LOAD CSV DATA ONLY IF TABLE IS EMPTY
# ----------------------------------------------------------

def _safe_load_csv(conn, csv_path: Path, table_name: str):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    if cur.fetchone()[0] > 0:
        return  # table already populated

    if not csv_path.exists():
        return  # CSV missing

    # -------------------------------
    # LOAD DATASETS METADATA
    # -------------------------------
    if table_name == "datasets":
        df = pd.read_csv(
            csv_path,
            header=None,
            names=["id", "dataset_name", "rows", "file_size_mb", "owner", "last_updated"]
        )

        # remove id column
        df = df.drop(columns=["id"], errors="ignore")

        # type enforcement
        df["rows"] = pd.to_numeric(df["rows"], errors="coerce").fillna(0).astype(int)
        df["file_size_mb"] = pd.to_numeric(df["file_size_mb"], errors="coerce").fillna(0.0)

        df.to_sql(table_name, conn, if_exists="append", index=False)
        return

    # -------------------------------
    # LOAD CYBER INCIDENTS
    # -------------------------------
    if table_name == "cyber_incidents":
        df = pd.read_csv(
            csv_path,
            header=None,
            names=[
                "external_id", "timestamp", "severity",
                "incident_type", "status", "description",
                "reported_by", "asset"
            ],
            dtype=str
        )

        # fill missing columns if CSV is shorter
        if "reported_by" not in df.columns:
            df["reported_by"] = "unknown"
        if "asset" not in df.columns:
            df["asset"] = "unknown"

        df.to_sql(table_name, conn, if_exists="append", index=False)
        return

    # -------------------------------
    # LOAD IT TICKETS
    # -------------------------------
    if table_name == "it_tickets":
        df = pd.read_csv(csv_path, header=None)

        # Standard full format
        if df.shape[1] >= 7:
            df = df.iloc[:, :7]
            df.columns = [
                "ticket_id", "title", "description",
                "status", "priority", "assigned_to",
                "created_at"
            ]
        else:
            # fallback (rare)
            df = df.astype(str)
            for col in ["ticket_id", "title", "description", "status", "priority", "assigned_to", "created_at"]:
                if col not in df.columns:
                    df[col] = None

        df = df[["ticket_id", "title", "description", "status", "priority", "assigned_to", "created_at"]]
        df.to_sql(table_name, conn, if_exists="append", index=False)
        return


# ----------------------------------------------------------
# 3. MAIN INITIALIZER
# ----------------------------------------------------------

def init_database():
    conn = connect_database()

    # Step 1 — Create all tables
    _create_schema(conn)

    # Step 2 — Load CSVs (only if tables are empty)
    for csv_name, table_name in CSV_MAP.items():
        csv_path = DATA_DIR / csv_name
        _safe_load_csv(conn, csv_path, table_name)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
