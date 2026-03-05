from abc import ABC, abstractmethod

from finetune.domain.entities import EvalResult


class IEvaluatorRepository(ABC):
    @abstractmethod
    def evaluate(
        self,
        model_path: str,
        test_path: str,
        regression_path: str | None = None,
    ) -> EvalResult: ...
