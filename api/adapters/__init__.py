"""
Data Ingestion Adapters — base interface and adapter registration.

Use the Adapter Pattern to support different data formats (CSV, JSON)
from government sources like UDISE+.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAdapter(ABC):
    """Abstract base class for all data ingestion adapters."""

    @abstractmethod
    def parse(self, raw_data: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parse raw file bytes into a list of record dicts.
        Each dict should map to a SchoolCreate / StudentCreate / FacilityBase schema.
        """
        ...

    @abstractmethod
    def validate(self, records: List[Dict[str, Any]]) -> tuple:
        """
        Validate parsed records.
        Returns: (valid_records: list, errors: list[str])
        """
        ...

    def get_format_name(self) -> str:
        return self.__class__.__name__
