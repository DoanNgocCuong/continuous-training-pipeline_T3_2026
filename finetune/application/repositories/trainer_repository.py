from abc import ABC, abstractmethod

from finetune.domain.entities import TrainingRun


class ITrainerRepository(ABC):
    @abstractmethod
    def train(self, dataset_path: str, config: dict) -> TrainingRun: ...
