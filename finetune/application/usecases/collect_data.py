from finetune.application.repositories.data_source_repository import IDataSourceRepository
from finetune.domain.entities import EmotionSample
from finetune.domain.value_objects import AgreementStatus, EmotionLabel


class CollectDataUseCase:
    def __init__(self, data_source: IDataSourceRepository):
        self.data_source = data_source

    def execute(self, source_path: str, has_label: bool = False) -> list[EmotionSample]:
        """Load data from source and convert to EmotionSample entities.

        Args:
            source_path: Path to CSV/XLSX file
            has_label: If True, expects 'human_label' in records (pre-labeled)
        """
        raw_records = self.data_source.load(source_path, has_label=has_label)

        samples = []
        for r in raw_records:
            sample = EmotionSample(
                input_text=r["user_input"],
                source=r.get("source", "csv"),
            )

            # If pre-labeled, set human_label
            if has_label and "human_label" in r:
                label = r["human_label"]
                if label:
                    sample.human_label = EmotionLabel.from_string(label)
                    sample.agreement_status = AgreementStatus.AUTO_APPROVED  # Pre-labeled = gold data

            samples.append(sample)

        return samples
