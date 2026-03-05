from finetune.application.repositories.data_source_repository import IDataSourceRepository
from finetune.domain.entities import EmotionSample


class CollectDataUseCase:
    def __init__(self, data_source: IDataSourceRepository):
        self.data_source = data_source

    def execute(self, source_path: str) -> list[EmotionSample]:
        raw_records = self.data_source.load(source_path)
        return [
            EmotionSample(
                input_text=r["user_input"],
                source=r.get("source", "csv"),
            )
            for r in raw_records
        ]
