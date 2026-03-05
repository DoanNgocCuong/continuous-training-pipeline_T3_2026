from finetune.domain.entities import EvalResult
from finetune.domain.services.promotion_decider import PromotionDeciderService


class DecidePromotionUseCase:
    def __init__(self, decider: PromotionDeciderService):
        self.decider = decider

    def execute(
        self,
        candidate_eval: EvalResult,
        baseline_eval: EvalResult,
    ) -> tuple[bool, str]:
        return self.decider.decide(candidate_eval, baseline_eval)
