from abc import ABC, abstractmethod

from finetune.domain.entities import EvalResult, TrainingRun


class IModelRegistryRepository(ABC):
    @abstractmethod
    def log_run(self, run: TrainingRun, eval_result: EvalResult) -> None: ...

    @abstractmethod
    def publish(self, model_path: str, version: str) -> str: ...
