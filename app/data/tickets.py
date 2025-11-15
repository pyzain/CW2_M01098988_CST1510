# app/data/tickets.py
import pandas as pd
from .db import connect_database

def insert_ticket(ticket_id, priority, status, category, subject, description, created_date=None, resolved_date=None, assigned_to=None):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO it_tickets (ticket_id, priority, status, category, subject, description, created_date, resolved_date, assigned_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticket_id, priority, status, category, subject, description, created_date, resolved_date, assigned_to))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid

def get_all_tickets():
    conn = connect_database()
    df = pd.read_sql_query("SELECT * FROM it_tickets ORDER BY id DESC", conn)
    conn.close()
    return df

def update_ticket_status(ticket_id, new_status):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("UPDATE it_tickets SET status = ? WHERE ticket_id = ?", (new_status, ticket_id))
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count

def delete_ticket(ticket_id):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("DELETE FROM it_tickets WHERE ticket_id = ?", (ticket_id,))
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count
