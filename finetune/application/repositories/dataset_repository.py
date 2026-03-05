from abc import ABC, abstractmethod

from finetune.domain.entities import EmotionSample


class IDatasetRepository(ABC):
    @abstractmethod
    def save_samples(self, samples: list[EmotionSample], path: str) -> None: ...

    @abstractmethod
    def load_samples(self, path: str) -> list[EmotionSample]: ...
