"""
IT Ticket Model — stable and aligned with DB schema.

Schema (final):
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
# Get all tickets as DataFrame
# -------------------------------------------------------

def get_all_tickets_df() -> pd.DataFrame:
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
# Update ticket status
# -------------------------------------------------------

def update_ticket_status(ticket_id: int, new_status: str, resolution_time_hours: Optional[float] = None):
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
# Fetch a ticket by ID
# -------------------------------------------------------

def get_ticket_by_id(ticket_id: int) -> Optional[Dict]:
    conn = connect_database()

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
