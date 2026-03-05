from finetune.application.repositories.evaluator_repository import IEvaluatorRepository
from finetune.domain.entities import EvalResult


class RunEvaluationUseCase:
    def __init__(self, evaluator: IEvaluatorRepository):
        self.evaluator = evaluator

    def execute(
        self,
        model_path: str,
        benchmark_path: str,
        regression_path: str | None = None,
    ) -> EvalResult:
        return self.evaluator.evaluate(model_path, benchmark_path, regression_path)
