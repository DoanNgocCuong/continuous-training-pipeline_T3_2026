from typing import Optional
from finetune.application.repositories.trainer_repository import ITrainerRepository
from finetune.application.repositories.model_registry_repository import IModelRegistryRepository
from finetune.domain.entities import TrainingRun


class RunTrainingUseCase:
    def __init__(
        self,
        trainer: ITrainerRepository,
        mlflow_registry: Optional[IModelRegistryRepository] = None,
    ):
        self.trainer = trainer
        self.mlflow_registry = mlflow_registry

    def execute(
        self,
        dataset_path: str,
        config: dict,
        eval_result: Optional[object] = None,
    ) -> TrainingRun:
        """Execute training with optional MLflow logging.

        Args:
            dataset_path: Path to training dataset
            config: Training configuration
            eval_result: Optional eval result to log to MLflow
        """
        run = self.trainer.train(dataset_path, config)

        # Log to MLflow if configured
        if self.mlflow_registry and eval_result is not None:
            try:
                self.mlflow_registry.log_run(run, eval_result)
            except Exception as e:
                import logging
                logging.warning(f"Failed to log to MLflow: {e}")

        return run
