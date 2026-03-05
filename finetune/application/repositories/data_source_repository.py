from abc import ABC, abstractmethod


class IDataSourceRepository(ABC):
    @abstractmethod
    def load(self, source: str) -> list[dict]:
        """Load raw records from source."""
