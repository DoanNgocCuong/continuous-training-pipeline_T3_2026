from finetune.application.repositories.model_registry_repository import IModelRegistryRepository
from finetune.domain.entities import EvalResult, TrainingRun


class PublishModelUseCase:
    def __init__(self, registry: IModelRegistryRepository):
        self.registry = registry

    def execute(
        self,
        run: TrainingRun,
        eval_result: EvalResult,
        version: str,
    ) -> str:
        self.registry.log_run(run, eval_result)
        published_url = self.registry.publish(run.adapter_path, version)
        return published_url
