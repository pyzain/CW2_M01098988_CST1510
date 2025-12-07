# scripts/import_csvs.py
import sqlite3
import pandas as pd
import os

# Path to your DB
DB_PATH = "database/platform.db"

# Mapping: table name -> CSV path
CSV_FILES = {
    "cyber_incidents": "data/cyber_incidents.csv",
    "it_tickets": "data/it_tickets.csv",
    "datasets_metadata": "data/datasets_metadata.csv"
}

def import_csv_to_db(db_path, csv_files):
    conn = sqlite3.connect(db_path)
    for table, csv_path in csv_files.items():
        if not os.path.exists(csv_path):
            print(f"CSV not found: {csv_path}, skipping...")
            continue
        df = pd.read_csv(csv_path)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"Imported {csv_path} into table '{table}'")
    conn.commit()
    conn.close()
    print("All CSVs imported successfully!")

if __name__ == "__main__":
    import_csv_to_db(DB_PATH, CSV_FILES)
