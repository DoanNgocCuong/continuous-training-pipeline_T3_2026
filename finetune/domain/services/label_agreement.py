from ..entities import EmotionSample
from ..value_objects import AgreementStatus


class LabelAgreementService:
    """3-way agreement logic: AI vs Human vs Model output."""

    def resolve(self, sample: EmotionSample) -> EmotionSample:
        ai = sample.ai_label
        human = sample.human_label
        model = sample.model_output

        # Case 0: chỉ có AI (chưa có human, chưa có model_output)
        if human is None and model is None and ai is not None:
            sample.agreed_label = ai
            sample.agreement_status = AgreementStatus.AUTO_APPROVED
            return sample

        # Case 5: chỉ có AI + Model (chưa có human)
        if human is None:
            if ai == model and ai is not None:
                sample.agreed_label = ai
                sample.agreement_status = AgreementStatus.AUTO_APPROVED
            else:
                sample.agreement_status = AgreementStatus.PENDING
            return sample

        # Case 1: all 3 agree
        if ai == human == model:
            sample.agreed_label = human
            sample.agreement_status = AgreementStatus.AUTO_APPROVED
            return sample

        # Case 2: AI == Human != Model (model sai, valuable training data)
        if ai == human and ai != model:
            sample.agreed_label = human
            sample.agreement_status = AgreementStatus.AUTO_APPROVED
            return sample

        # Case 3: AI == Model != Human (trust human)
        if ai == model and ai != human:
            sample.agreed_label = human
            sample.agreement_status = AgreementStatus.HUMAN_RESOLVED
            return sample

        # Case 4: AI != Human (conflict)
        sample.agreement_status = AgreementStatus.FLAGGED
        return sample

    def batch_resolve(
        self, samples: list[EmotionSample]
    ) -> tuple[list[EmotionSample], list[EmotionSample]]:
        """Returns (approved, flagged)."""
        approved, flagged = [], []
        for s in samples:
            resolved = self.resolve(s)
            if resolved.agreement_status in (
                AgreementStatus.AUTO_APPROVED,
                AgreementStatus.HUMAN_RESOLVED,
            ):
                approved.append(resolved)
            else:
                flagged.append(resolved)
        return approved, flagged
