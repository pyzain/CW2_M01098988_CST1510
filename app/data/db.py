# app/data/db.py
import sqlite3
import os
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "DATA"
DB_PATH = DATA_DIR / "intelligence_platform.db"

os.makedirs(DATA_DIR, exist_ok=True)

def connect_database(db_path: Path = DB_PATH):
    """Return a sqlite3.Connection (autocommit disabled)."""
    conn = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn
