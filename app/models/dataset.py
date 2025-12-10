# models/dataset.py
from dataclasses import dataclass

@dataclass
class DatasetMeta:
    id: int
    dataset_name: str
    rows: int
    file_size_mb: float
    owner: str
    last_updated: str
