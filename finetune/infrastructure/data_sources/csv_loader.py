import logging

import pandas as pd

from finetune.application.repositories.data_source_repository import IDataSourceRepository
from finetune.domain.exceptions import DataSourceError

logger = logging.getLogger(__name__)

MARKER = "Now Pika Robot's Response need check:"


class CsvDataSourceLoader(IDataSourceRepository):
    """Load data từ CSV export (Datadog) hoặc pre-labeled CSV."""

    def load(self, source: str, has_label: bool = False) -> list[dict]:
        """Load data from CSV/XLSX file.

        Args:
            source: Path to CSV/XLSX file
            has_label: If True, expects 'text' and 'label' columns (pre-labeled)
                       If False, expects 'user_input' column (Datadog format)
        """
        # Support both CSV and XLSX
        if source.endswith(".xlsx"):
            try:
                df = pd.read_excel(source)
            except Exception as e:
                raise DataSourceError(f"Failed to read XLSX {source}: {e}")
        else:
            try:
                df = pd.read_csv(source)
            except FileNotFoundError:
                raise DataSourceError(f"CSV not found: {source}")
            except Exception as e:
                raise DataSourceError(f"Failed to read CSV {source}: {e}")

        if has_label:
            # Pre-labeled format: 'text' + 'label' columns
            return self._load_prelabeled(df)
        else:
            # Unlabeled format: Datadog 'user_input' column
            return self._load_unlabeled(df)

    def _load_prelabeled(self, df: pd.DataFrame) -> list[dict]:
        """Load pre-labeled data (has 'text'/'input' and 'label'/'output' columns)."""
        records = []
        for _, row in df.iterrows():
            # Support multiple column naming conventions
            text = str(row.get("text", row.get("input", row.get("user_input", ""))))
            label = str(row.get("label", row.get("output", ""))).strip()

            if text and text != "nan":
                record = {
                    "user_input": text[:300],
                    "source": "prelabeled",
                }
                if label and label != "nan":
                    record["human_label"] = label
                records.append(record)

        logger.info("Loaded %d pre-labeled records", len(records))
        return records

    def _load_unlabeled(self, df: pd.DataFrame) -> list[dict]:
        """Load unlabeled data from Datadog CSV format."""
        records = []
        for _, row in df.iterrows():
            text = str(row.get("user_input", ""))
            cleaned = self._clean(text)
            if cleaned:
                records.append({"user_input": cleaned, "source": "datadog_csv"})
        logger.info("Loaded %d unlabeled records", len(records))
        return records

    def _clean(self, text: str) -> str:
        text = text.replace("\\n", "\n")
        if MARKER in text:
            return text.split(MARKER)[-1].strip()[:300]
        return text.strip()[:300]
