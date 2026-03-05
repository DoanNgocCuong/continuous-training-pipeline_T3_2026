from abc import ABC, abstractmethod

from finetune.domain.entities import EmotionSample


class ILabelerRepository(ABC):
    @abstractmethod
    def label_batch(self, samples: list[EmotionSample]) -> list[EmotionSample]:
        """AI label a batch of samples."""
