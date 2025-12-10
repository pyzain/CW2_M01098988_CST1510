# database/db_initializer.py
"""
Create schema and import CSVs if tables are empty (idempotent).
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


def _create_schema(conn):
    cur = conn.cursor()

    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # cyber_incidents (normalized columns)
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

    # it_tickets
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

    # datasets
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


def _safe_load_csv(conn, csv_path: Path, table_name: str):
    """Load CSV into table only if table is empty. This prevents duplicate inserts on reloads."""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(1) as cnt FROM {table_name}")
    cnt = cur.fetchone()[0]
    if cnt > 0:
        # already populated
        return

    if not csv_path.exists():
        return

    # Read CSVs carefully according to expected format
    if table_name == "datasets":
        # datasets_metadata.csv: id,dataset_name,rows,file_size_mb,owner,last_updated
        df = pd.read_csv(csv_path, header=None, names=["id", "dataset_name", "rows", "file_size_mb", "owner", "last_updated"])
        df = df.drop(columns=[c for c in ["id"] if c in df.columns])
        # ensure types
        df["rows"] = pd.to_numeric(df["rows"], errors="coerce").fillna(0).astype(int)
        df["file_size_mb"] = pd.to_numeric(df["file_size_mb"], errors="coerce").fillna(0.0)
        df.to_sql(table_name, conn, if_exists="append", index=False)

    elif table_name == "cyber_incidents":
        # cyber_incidents.csv: external_id,timestamp,severity,incident_type,status,description[,asset]
        df = pd.read_csv(csv_path, header=None, names=["external_id","timestamp","severity","incident_type","status","description"], dtype=str)
        # If CSV contains asset as 7th column, capture it
        if df.shape[1] > 6:
            # already captured
            pass
        # Append with defaults
        df = df.assign(asset="unknown", reported_by="unknown")
        df.to_sql(table_name, conn, if_exists="append", index=False)

    elif table_name == "it_tickets":
        # it_tickets.csv sample: ticket_id,created_at,priority,status,category,subject,description,assigned_to
        df = pd.read_csv(csv_path, header=None)
        # Try to map by number of columns (best-effort)
        if df.shape[1] >= 8:
            df = df.iloc[:, :8]
            df.columns = ["ticket_id","created_at","priority","status","category","title","description","assigned_to"]
            df = df.rename(columns={"created_at":"created_at", "title":"title"})
        else:
            # fallback: store raw text
            df = pd.DataFrame(df.iloc[:, :].astype(str))
        # keep columns consistent with DB
        # create placeholder columns if missing
        for col in ["ticket_id","title","description","status","priority","assigned_to","created_at"]:
            if col not in df.columns:
                df[col] = None
        df = df[["ticket_id","title","description","status","priority","assigned_to","created_at"]]
        df.to_sql(table_name, conn, if_exists="append", index=False)


def init_database():
    conn = connect_database()
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS it_tickets
                (
                    ticket_id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    priority
                    TEXT,
                    description
                    TEXT,
                    status
                    TEXT,
                    assigned_to
                    TEXT,
                    created_at
                    TEXT,
                    resolution_time_hours
                    REAL
                )
                """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
