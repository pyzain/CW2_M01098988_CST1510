# models/security_incident.py
"""SecurityIncident entity representing a cyber incident."""

from typing import Optional


class SecurityIncident:
    """Represents a cybersecurity incident in the platform."""

    def __init__(
        self,
        incident_id: int,
        incident_type: str,
        severity: str,
        status: str = "open",
        description: Optional[str] = "",
        asset: Optional[str] = None,
        assigned_to: Optional[str] = None,
        timestamp=None,
    ):
        # Private attributes
        self.__id = incident_id
        self.__incident_type = incident_type
        self.__severity = (severity or "unknown").lower()
        self.__status = status
        self.__description = description or ""
        self.__asset = asset or "unknown"
        self.__assigned_to = assigned_to or "unassigned"
        self.__timestamp = timestamp

    # Accessors
    def get_id(self) -> int:
        return self.__id

    def get_type(self) -> str:
        return self.__incident_type

    def get_severity(self) -> str:
        return self.__severity

    def get_status(self) -> str:
        return self.__status

    def get_description(self) -> str:
        return self.__description

    def get_asset(self) -> str:
        return self.__asset

    def get_assigned_to(self) -> str:
        return self.__assigned_to

    def get_timestamp(self):
        return self.__timestamp

    # Mutators
    def update_status(self, new_status: str) -> None:
        self.__status = new_status

    def assign_to(self, user: str) -> None:
        self.__assigned_to = user

    # Small helper
    def get_severity_level(self) -> int:
        """Return integer severity level (low=1 .. critical=4)."""
        mapping = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return mapping.get(self.__severity.lower(), 0)

    def __str__(self) -> str:
        return f"Incident {self.__id} [{self.__severity.upper()}] {self.__incident_type} - {self.__status}"
