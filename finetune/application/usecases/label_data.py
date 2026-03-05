from finetune.application.repositories.labeler_repository import ILabelerRepository
from finetune.domain.entities import EmotionSample
from finetune.domain.services.label_agreement import LabelAgreementService


class LabelDataUseCase:
    def __init__(
        self,
        labeler: ILabelerRepository,
        agreement_service: LabelAgreementService,
    ):
        self.labeler = labeler
        self.agreement = agreement_service

    def execute(
        self, samples: list[EmotionSample]
    ) -> tuple[list[EmotionSample], list[EmotionSample]]:
        """Returns (approved, flagged)."""
        labeled = self.labeler.label_batch(samples)
        return self.agreement.batch_resolve(labeled)
