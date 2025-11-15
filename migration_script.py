# migration_script.py (project root)
from app.data.db import connect_database, DB_PATH
from app.data.schema import create_all_tables
from app.services.user_service import migrate_users_from_file
from app.data.datasets import load_csv_to_table
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "DATA"

def load_csv_safe(csv_name, table_name):
    path = DATA_DIR / csv_name
    if path.exists():
        try:
            rows = load_csv_to_table(str(path), table_name, if_exists='append')
            print(f"Loaded {rows} rows from {csv_name} into {table_name}")
        except Exception as e:
            print(f"Failed to load {csv_name} -> {e}")
    else:
        print(f"CSV not found: {csv_name}; skipping.")

def setup_database_complete():
    print("Connecting to database...")
    conn = connect_database()
    create_all_tables(conn)
    migrated = migrate_users_from_file(conn)
    print(f"Migrated {migrated} users (from DATA/users.txt)")

    # Load CSVs
    load_csv_safe("cyber_incidents.csv", "cyber_incidents")
    load_csv_safe("it_tickets.csv", "it_tickets")
    load_csv_safe("datasets_metadata.csv", "datasets_metadata")

    # Verify counts
    cur = conn.cursor()
    for t in ['users', 'cyber_incidents', 'it_tickets', 'datasets_metadata']:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
        except Exception:
            count = 0
        print(f"Table {t}: {count} rows")
    conn.close()
    print("Database setup complete. DB at:", DB_PATH)

if __name__ == "__main__":
    setup_database_complete()
