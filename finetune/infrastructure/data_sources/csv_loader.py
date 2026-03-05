import pandas as pd

from finetune.application.repositories.data_source_repository import IDataSourceRepository
from finetune.domain.exceptions import DataSourceError


class CsvDataSourceLoader(IDataSourceRepository):
    """Load data từ CSV export (Datadog)."""

    MARKER = "Now Pika Robot's Response need check:"

    def load(self, source: str) -> list[dict]:
        try:
            df = pd.read_csv(source)
        except FileNotFoundError:
            raise DataSourceError(f"CSV not found: {source}")
        except Exception as e:
            raise DataSourceError(f"Failed to read CSV {source}: {e}")

        records = []
        for _, row in df.iterrows():
            text = str(row.get("user_input", ""))
            cleaned = self._clean(text)
            if cleaned:
                records.append({"user_input": cleaned, "source": "datadog_csv"})
        return records

    def _clean(self, text: str) -> str:
        text = text.replace("\\n", "\n")
        if self.MARKER in text:
            return text.split(self.MARKER)[-1].strip()[:300]
        return text.strip()[:300]
