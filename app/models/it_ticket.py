# app/models/it_ticket.py
"""
IT Ticket Model — Simple, stable, production-ready.

This file handles:
1. Creating a new IT ticket
2. Fetching all tickets (DataFrame)
3. Updating ticket status
4. Fetching a ticket by ID

Database Schema:
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT
    priority TEXT
    description TEXT
    status TEXT
    assigned_to TEXT
    created_at TEXT
    resolution_time_hours REAL
"""

from typing import Optional, Dict
import pandas as pd
from database.db import connect_database


# -------------------------------------------------------
# Create a new ticket
# -------------------------------------------------------
def create_ticket(priority: str, description: str, assigned_to: str = "unassigned") -> int:
    """
    Create a new ticket and return the generated ticket_id.
    """
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO it_tickets 
        (priority, description, status, assigned_to, created_at, resolution_time_hours)
        VALUES (?, ?, 'open', ?, datetime('now'), NULL)
        """,
        (priority, description, assigned_to),
    )

    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


# -------------------------------------------------------
# Get all tickets as a DataFrame
# -------------------------------------------------------
def get_all_tickets_df() -> pd.DataFrame:
    """
    Returns all IT tickets as a Pandas DataFrame.
    Used for dashboards, analytics, and Streamlit tables.
    """
    conn = connect_database()

    try:
        df = pd.read_sql_query(
            """
            SELECT 
                ticket_id,
                priority,
                description,
                status,
                assigned_to,
                created_at,
                resolution_time_hours
            FROM it_tickets
            ORDER BY ticket_id DESC
            """,
            conn,
        )
    except Exception:
        # Return empty DataFrame with correct columns (prevents Streamlit crashes)
        df = pd.DataFrame(
            columns=[
                "ticket_id",
                "priority",
                "description",
                "status",
                "assigned_to",
                "created_at",
                "resolution_time_hours",
            ]
        )
    finally:
        conn.close()

    return df


# -------------------------------------------------------
# Update a ticket's status
# -------------------------------------------------------
def update_ticket_status(ticket_id: int, new_status: str, resolution_time_hours: Optional[float] = None) -> None:
    """
    Update the status of a ticket.
    If resolution_time_hours is provided, it will be saved.
    """
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE it_tickets
        SET status = ?, 
            resolution_time_hours = ?
        WHERE ticket_id = ?
        """,
        (new_status, resolution_time_hours, ticket_id),
    )

    conn.commit()
    conn.close()


# -------------------------------------------------------
# Fetch a single ticket by ID
# -------------------------------------------------------
def get_ticket_by_id(ticket_id: int) -> Optional[Dict]:
    """
    Return a single ticket as a dictionary.
    Returns None if the ticket doesn't exist.
    """
    conn = connect_database()

    # Return rows as Python dictionaries
    conn.row_factory = lambda cursor, row: {
        "ticket_id": row[0],
        "priority": row[1],
        "description": row[2],
        "status": row[3],
        "assigned_to": row[4],
        "created_at": row[5],
        "resolution_time_hours": row[6],
    }

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ticket_id, priority, description, status, assigned_to, created_at, resolution_time_hours
        FROM it_tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,),
    )

    row = cursor.fetchone()
    conn.close()

    return row if row else None
