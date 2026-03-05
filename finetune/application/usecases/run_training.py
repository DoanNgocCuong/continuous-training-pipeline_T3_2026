from finetune.application.repositories.trainer_repository import ITrainerRepository
from finetune.domain.entities import TrainingRun


class RunTrainingUseCase:
    def __init__(self, trainer: ITrainerRepository):
        self.trainer = trainer

    def execute(self, dataset_path: str, config: dict) -> TrainingRun:
        return self.trainer.train(dataset_path, config)
