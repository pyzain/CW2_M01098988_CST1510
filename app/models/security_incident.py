# app/models/security_incident.py
from dataclasses import dataclass

@dataclass
class SecurityIncident:
    id: int
    external_id: str
    timestamp: str
    severity: str
    incident_type: str
    status: str
    description: str
    reported_by: str
    asset: str
