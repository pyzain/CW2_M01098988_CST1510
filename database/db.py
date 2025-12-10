# database/db.py
"""
Low-level SQLite connection helper.
"""
import sqlite3
from pathlib import Path
from typing import Optional

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_FILE = PROJECT_ROOT / "database" / "platform.db"

# Ensure paths exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE.parent.mkdir(parents=True, exist_ok=True)


def connect_database(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Return a sqlite3.Connection. By default uses database/platform.db."""
    if db_path is None:
        db_path = DB_FILE
    conn = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

