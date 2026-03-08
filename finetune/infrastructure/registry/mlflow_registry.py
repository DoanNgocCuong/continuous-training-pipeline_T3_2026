"""MLflow integration — experiment tracking + model registry."""
import logging
import os
from typing import Optional

from finetune.application.repositories.model_registry_repository import IModelRegistryRepository
from finetune.domain.entities import EvalResult, TrainingRun

logger = logging.getLogger(__name__)


class MLflowRegistry(IModelRegistryRepository):
    """Log training runs, metrics, and artifacts to MLflow.

    Requires: pip install mlflow boto3
    Requires: MLFLOW_TRACKING_URI env var (default http://localhost:5000)
    """

    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        experiment_name: str = "emotion-finetune",
        registered_model_name: str = "qwen2.5-1.5b-emotion",
    ):
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI", "http://localhost:5000"
        )
        self.experiment_name = experiment_name
        self.registered_model_name = registered_model_name
        self._configured = False

    def _ensure_configured(self) -> None:
        if self._configured:
            return
        import mlflow
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)
        self._configured = True

    def log_run(self, run: TrainingRun, eval_result: EvalResult) -> None:
        """Log a training run with params, metrics, and adapter artifact."""
        import mlflow

        self._ensure_configured()

        with mlflow.start_run(run_name=f"train-{run.run_id[:8]}") as mlflow_run:
            mlflow.log_params({
                "run_id": run.run_id,
                "base_model": run.base_model,
                "dataset_version": run.dataset_version,
                "config_path": run.config_path,
            })

            mlflow.log_metrics({
                "training_loss": run.training_loss,
                "training_time_seconds": run.training_time_seconds,
                "accuracy": eval_result.accuracy,
                "f1_macro": eval_result.f1_macro,
                "regression_pass_rate": eval_result.regression_pass_rate,
                "benchmark_size": float(eval_result.benchmark_size),
                "eval_time_seconds": eval_result.eval_time_seconds,
            })

            for cls, f1 in eval_result.f1_per_class.items():
                mlflow.log_metric(f"f1_{cls}", f1)

            if run.adapter_path and os.path.isdir(run.adapter_path):
                mlflow.log_artifacts(run.adapter_path, artifact_path="lora_adapter")

            logger.info(
                "Logged run %s to MLflow (mlflow_run_id=%s)",
                run.run_id, mlflow_run.info.run_id,
            )

    def publish(self, model_path: str, version: str) -> str:
        """Register a model version in MLflow Model Registry.

        Transitions the new version to "Staging".
        Returns the model URI.
        """
        import mlflow
        from mlflow.tracking import MlflowClient

        self._ensure_configured()
        client = MlflowClient()

        with mlflow.start_run(run_name=f"publish-{version}"):
            model_uri = mlflow.log_artifacts(model_path, artifact_path="model")
            artifact_uri = mlflow.get_artifact_uri("model")

        result = mlflow.register_model(
            model_uri=artifact_uri,
            name=self.registered_model_name,
        )

        client.transition_model_version_stage(
            name=self.registered_model_name,
            version=result.version,
            stage="Staging",
        )

        registry_uri = f"models:/{self.registered_model_name}/{result.version}"
        logger.info(
            "Published model %s v%s to MLflow Registry (stage=Staging)",
            self.registered_model_name, result.version,
        )
        return registry_uri

    def promote_to_staging(self, version: str) -> None:
        """Transition a model version to Staging."""
        from mlflow.tracking import MlflowClient

        self._ensure_configured()
        client = MlflowClient()
        client.transition_model_version_stage(
            name=self.registered_model_name,
            version=version,
            stage="Staging",
        )
        logger.info(
            "Promoted %s v%s to Staging", self.registered_model_name, version
        )

    def promote_to_production(self, version: str) -> None:
        """Transition a staged model version to Production."""
        from mlflow.tracking import MlflowClient

        self._ensure_configured()
        client = MlflowClient()
        client.transition_model_version_stage(
            name=self.registered_model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True,
        )
        logger.info(
            "Promoted %s v%s to Production", self.registered_model_name, version
        )
