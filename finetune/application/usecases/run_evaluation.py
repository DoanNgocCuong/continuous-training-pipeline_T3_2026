from typing import Optional
from finetune.application.repositories.evaluator_repository import IEvaluatorRepository
from finetune.application.repositories.model_registry_repository import IModelRegistryRepository
from finetune.domain.entities import EvalResult


class RunEvaluationUseCase:
    def __init__(
        self,
        evaluator: IEvaluatorRepository,
        mlflow_registry: Optional[IModelRegistryRepository] = None,
    ):
        self.evaluator = evaluator
        self.mlflow_registry = mlflow_registry

    def execute(
        self,
        model_path: str,
        benchmark_path: str,
        regression_path: str | None = None,
    ) -> EvalResult:
        """Execute evaluation with optional MLflow logging.

        Args:
            model_path: Path to model
            benchmark_path: Path to test dataset
            regression_path: Optional path to regression dataset

        Returns:
            EvalResult with metrics
        """
        result = self.evaluator.evaluate(model_path, benchmark_path, regression_path)

        # Log metrics to MLflow if configured
        if self.mlflow_registry:
            try:
                import mlflow
                mlflow.log_metrics({
                    "accuracy": result.accuracy,
                    "f1_macro": result.f1_macro,
                    "f1_weighted": result.f1_weighted,
                    "precision": result.precision,
                    "recall": result.recall,
                    "regression_pass_rate": result.regression_pass_rate or 0.0,
                    "benchmark_size": float(result.benchmark_size),
                })
                for cls, f1 in result.f1_per_class.items():
                    mlflow.log_metric(f"f1_{cls}", f1)
            except Exception as e:
                import logging
                logging.warning(f"Failed to log to MLflow: {e}")

        return result
