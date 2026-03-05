from finetune.application.repositories.dataset_repository import IDatasetRepository
from finetune.domain.entities import DatasetVersion, EmotionSample
from finetune.domain.services.dataset_builder import DatasetBuilderService
from finetune.infrastructure.repositories.file_dataset_repository import FileDatasetRepository


class BuildDatasetsUseCase:
    def __init__(
        self,
        builder: DatasetBuilderService,
        dataset_repo: IDatasetRepository,
        output_base: str = "data/datasets",
    ):
        self.builder = builder
        self.dataset_repo = dataset_repo
        self.output_base = output_base

    def execute(
        self,
        samples: list[EmotionSample],
        version: str = "v1.0",
    ) -> DatasetVersion:
        dataset_version, train, val, test = self.builder.build(samples, version=version)

        base = f"{self.output_base}/{version}"

        # Internal format (full sample fields — for debugging / Argilla push)
        self.dataset_repo.save_samples(train, f"{base}/train.jsonl")
        self.dataset_repo.save_samples(val, f"{base}/val.jsonl")
        self.dataset_repo.save_samples(test, f"{base}/test.jsonl")

        # ChatML format (for Unsloth SFTTrainer)
        if isinstance(self.dataset_repo, FileDatasetRepository):
            self.dataset_repo.save_as_chatml(train, f"{base}/train_chatml.jsonl")
            self.dataset_repo.save_as_chatml(val, f"{base}/val_chatml.jsonl")
            # Eval format for test set (flat input_text + expected_label)
            self.dataset_repo.save_as_eval_jsonl(test, f"{base}/test_eval.jsonl")

        return dataset_version
