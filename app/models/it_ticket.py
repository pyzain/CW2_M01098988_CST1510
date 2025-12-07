# models/it_ticket.py
"""ITTicket entity representing an IT support ticket."""

from typing import Optional


class ITTicket:
    """Represents an IT support ticket."""

    def __init__(self, ticket_id: int, title: str, priority: str = "Normal", status: str = "Open", assigned_to: Optional[str] = None):
        self.__id = ticket_id
        self.__title = title
        self.__priority = priority
        self.__status = status
        self.__assigned_to = assigned_to or "unassigned"

    def assign_to(self, staff: str) -> None:
        self.__assigned_to = staff

    def close_ticket(self) -> None:
        self.__status = "Closed"

    def get_status(self) -> str:
        return self.__status

    def get_assigned_to(self) -> str:
        return self.__assigned_to

    def __str__(self) -> str:
        return f"Ticket {self.__id}: {self.__title} [{self.__priority}] – {self.__status} (assigned to: {self.__assigned_to})"
