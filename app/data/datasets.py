# app/data/datasets.py
import pandas as pd
from .db import connect_database

def insert_dataset(dataset_name, category, source, last_updated, record_count, file_size_mb):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO datasets_metadata (dataset_name, category, source, last_updated, record_count, file_size_mb)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (dataset_name, category, source, last_updated, record_count, file_size_mb))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid

def get_all_datasets():
    conn = connect_database()
    df = pd.read_sql_query("SELECT * FROM datasets_metadata ORDER BY id DESC", conn)
    conn.close()
    return df

def load_csv_to_table(csv_path, table_name, if_exists='append'):
    """Convenience: read CSV and write to DB table using pandas."""
    conn = connect_database()
    df = pd.read_csv(csv_path)
    df.to_sql(name=table_name, con=conn, if_exists=if_exists, index=False)
    conn.close()
    return len(df)
