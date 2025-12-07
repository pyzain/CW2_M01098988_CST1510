# models/dataset.py
"""Dataset entity for data science artifacts."""

from typing import Optional


class Dataset:
    """Represents a data science dataset in the platform."""

    def __init__(self, dataset_id: int, name: str, size_bytes: int, rows: int, source: Optional[str] = None):
        self.__id = dataset_id
        self.__name = name
        self.__size_bytes = int(size_bytes or 0)
        self.__rows = int(rows or 0)
        self.__source = source or "unknown"

    def calculate_size_mb(self) -> float:
        """Return size in megabytes (float)."""
        return self.__size_bytes / (1024 * 1024)

    def get_source(self) -> str:
        return self.__source

    def get_rows(self) -> int:
        return self.__rows

    def __str__(self) -> str:
        size_mb = self.calculate_size_mb()
        return f"Dataset {self.__id}: {self.__name} ({size_mb:.2f} MB, {self.__rows} rows) - source: {self.__source}"
