# app/data/incidents.py
import pandas as pd
from .db import connect_database

def insert_incident(date, incident_type, severity, status, description, reported_by=None):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO cyber_incidents (date, incident_type, severity, status, description, reported_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, incident_type, severity, status, description, reported_by))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid

def get_all_incidents():
    conn = connect_database()
    df = pd.read_sql_query("SELECT * FROM cyber_incidents ORDER BY id DESC", conn)
    conn.close()
    return df

def get_incident_by_id(incident_id):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cyber_incidents WHERE id = ?", (incident_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_incident_status(incident_id, new_status):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("UPDATE cyber_incidents SET status = ? WHERE id = ?", (new_status, incident_id))
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count

def delete_incident(incident_id):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("DELETE FROM cyber_incidents WHERE id = ?", (incident_id,))
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count
